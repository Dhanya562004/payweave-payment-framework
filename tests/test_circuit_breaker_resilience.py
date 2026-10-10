"""
PayWeave Phase 4 Resilience & Circuit Breaker Tests.
Validates explicit circuit breaker states (CLOSED, OPEN, HALF_OPEN), cooldown timers,
probe recovery, failover rerouting, bounded retries with backoff, and non-retryable error termination.
"""

import time
import pytest
from payweave.routing.circuit_breaker import CircuitBreaker, CircuitState
from payweave.routing.provider_health import ProviderHealthTracker
from payweave.providers.base import BasePSPAdapter, TransactionResult, ProviderStatus
from payweave.providers.mock_psp_a import MockPSPAdapterA
from payweave.providers.mock_psp_b import MockPSPAdapterB
from payweave.providers.mock_psp_c import MockPSPAdapterC
from payweave.runtime.payment_logic import PaymentProcessor
from payweave.runtime.functional_core import (
    PaymentRequest, PaymentContext, build_execution_plan, is_retry_eligible
)
from payweave.dsl.schema import MerchantConfig


def test_circuit_breaker_closed_to_open_transition():
    cb = CircuitBreaker(provider_id="psp-test", failure_threshold=3, cooldown_seconds=0.2)
    assert cb.state == CircuitState.CLOSED
    assert cb.is_available() is True

    # 1st and 2nd failure - remains CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    # 3rd failure trips to OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.is_available() is False


def test_circuit_breaker_cooldown_and_half_open_probe_recovery():
    cb = CircuitBreaker(provider_id="psp-test", failure_threshold=2, cooldown_seconds=0.05)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Wait for cooldown to expire
    time.sleep(0.06)
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.is_available() is True

    # Successful probe recovers to CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.is_available() is True


def test_circuit_breaker_half_open_probe_failure_re_trips_to_open():
    cb = CircuitBreaker(provider_id="psp-test", failure_threshold=2, cooldown_seconds=0.05)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    time.sleep(0.06)
    assert cb.state == CircuitState.HALF_OPEN

    # Failed probe immediately re-trips to OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.is_available() is False


def test_failover_when_primary_circuit_trips():
    adapters = {
        "psp-a": MockPSPAdapterA(),
        "psp-b": MockPSPAdapterB(),
        "psp-c": MockPSPAdapterC()
    }
    tracker = ProviderHealthTracker(adapters, circuit_failure_threshold=2, circuit_cooldown_seconds=1.0)
    cfg = MerchantConfig()

    # Trip PSP-A circuit breaker
    cb_a = tracker.get_circuit_breaker("psp-a")
    cb_a.trip_open_manually()

    h_map = tracker.get_health_map()
    assert h_map["psp-a"].circuit_breaker == "OPEN"
    assert h_map["psp-a"].is_healthy is False

    ctx = PaymentContext(merchant_config=cfg, provider_health_map=h_map)
    req = PaymentRequest.create(amount=1000.0, currency="INR", payment_method="upi")

    plan_res = build_execution_plan(req, ctx)
    assert plan_res.is_ok
    plan = plan_res.unwrap()
    # Must failover away from PSP-A
    assert plan.routing.selected_provider in ["psp-b", "psp-c"]
    assert plan.routing.selected_provider != "psp-a"


def test_all_providers_open_circuit_fails_with_no_healthy_provider():
    adapters = {
        "psp-a": MockPSPAdapterA(),
        "psp-b": MockPSPAdapterB()
    }
    tracker = ProviderHealthTracker(adapters)
    for cb in tracker.circuit_breakers.values():
        cb.trip_open_manually()

    ctx = PaymentContext(merchant_config=MerchantConfig(), provider_health_map=tracker.get_health_map())
    req = PaymentRequest.create(amount=500.0)

    plan_res = build_execution_plan(req, ctx)
    assert plan_res.is_error
    assert "No healthy provider available" in plan_res.error()


def test_payment_processor_does_not_retry_non_retryable_errors():
    class DecliningAdapter(BasePSPAdapter):
        def __init__(self):
            super().__init__(
                provider_id="psp-a",
                name="Declining PSP",
                default_success_rate=0.999,
                default_latency_ms=70.0,
                cost_score=0.10
            )

        def process_payment(self, *args, **kwargs):
            return TransactionResult(
                transaction_id="tx_dec",
                request_id="req_dec",
                provider_id="psp-a",
                status=ProviderStatus.FAILED,
                latency_ms=20.0,
                response_code="CARD_EXPIRED",
                message="Card expired: validation failed by issuer"
            )

    adapters = {
        "psp-a": DecliningAdapter(),
        "psp-b": MockPSPAdapterB()
    }
    tracker = ProviderHealthTracker(adapters)
    processor = PaymentProcessor(adapters, health_tracker=tracker)
    req = PaymentRequest.create(amount=500.0)
    ctx = PaymentContext(merchant_config=MerchantConfig(), provider_health_map=tracker.get_health_map())
    plan = build_execution_plan(req, ctx).unwrap()
    assert plan.routing.selected_provider == "psp-a"
    assert "psp-b" in plan.routing.fallback_chain

    # Execute plan - since psp-a returned non-retryable CARD_EXPIRED, it must NOT fallback to psp-b
    outcome = processor.execute_plan(plan, enable_backoff_sleep=False)
    assert outcome.success is False
    assert outcome.retries_count == 0
    assert outcome.attempted_providers == ["psp-a"]
    assert "Non-retryable" in outcome.message


def test_payment_processor_retries_transient_failures_up_to_max():
    adapters = {
        "psp-a": MockPSPAdapterA(),
        "psp-b": MockPSPAdapterB(),
        "psp-c": MockPSPAdapterC()
    }
    tracker = ProviderHealthTracker(adapters)
    processor = PaymentProcessor(adapters, health_tracker=tracker)
    req = PaymentRequest.create(amount=500.0)
    ctx = PaymentContext(merchant_config=MerchantConfig(), provider_health_map=tracker.get_health_map())
    plan = build_execution_plan(req, ctx).unwrap()

    # Simulate forced failure on the primary chosen provider
    target = plan.routing.selected_provider
    outcome = processor.execute_plan(plan, simulate_failure_provider=target, enable_backoff_sleep=False)
    assert outcome.success is True
    assert outcome.retries_count >= 1
    assert outcome.provider_used != target
    assert target in outcome.attempted_providers
