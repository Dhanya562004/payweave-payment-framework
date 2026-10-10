"""
Unit tests for Python reference implementation mirroring Haskell domain logic.
Tests pure functions, explicit Result error returns, ADT behaviors, and decision rules.
"""

import pytest
from payweave.runtime.functional_core import (
    PaymentRequest, PaymentContext, ProviderHealth, Result,
    validate_request, evaluate_risk, build_execution_plan
)
from payweave.dsl.schema import MerchantConfig, AuthMode


def make_context():
    cfg = MerchantConfig()
    health_map = {
        "psp-a": ProviderHealth("psp-a", 0.985, 140.0, 0.015, True, 0.70, 95.0),
        "psp-b": ProviderHealth("psp-b", 0.990, 110.0, 0.010, True, 0.85, 90.0),
        "psp-c": ProviderHealth("psp-c", 0.965, 220.0, 0.035, True, 0.30, 100.0)
    }
    return PaymentContext(merchant_config=cfg, provider_health_map=health_map)


def test_validate_request_valid():
    ctx = make_context()
    req = PaymentRequest.create(amount=100.0, currency="INR", payment_method="upi")
    res = validate_request(req, ctx)
    assert res.is_ok
    assert res.unwrap().is_valid is True


def test_validate_request_invalid_amount():
    ctx = make_context()
    req = PaymentRequest.create(amount=-50.0, currency="INR", payment_method="upi")
    res = validate_request(req, ctx)
    assert res.is_error
    assert "greater than zero" in res.error()


def test_evaluate_risk_allowed():
    ctx = make_context()
    req = PaymentRequest.create(amount=500.0, risk_score=0.10)
    res = evaluate_risk(req, ctx)
    assert res.is_ok
    assert res.unwrap().action == "ALLOW"


def test_evaluate_risk_exceeded():
    ctx = make_context()
    ctx.merchant_config.risk.max_score = 0.30
    req = PaymentRequest.create(amount=500.0, risk_score=0.75)
    res = evaluate_risk(req, ctx)
    assert res.is_error
    assert "Transaction risk score" in res.error()


def test_build_execution_plan_pipeline_success():
    ctx = make_context()
    req = PaymentRequest.create(amount=1200.0, currency="INR", payment_method="upi", risk_score=0.05)
    plan_res = build_execution_plan(req, ctx)
    assert plan_res.is_ok
    plan = plan_res.unwrap()
    assert plan.routing.selected_provider in ["psp-a", "psp-b", "psp-c"]
    assert plan.ready_for_execution is True


def test_validate_request_empty_customer_id():
    ctx = make_context()
    req = PaymentRequest(
        request_id="pay_empty_cust",
        amount=500.0,
        currency="INR",
        payment_method="upi",
        customer_id=""
    )
    res = validate_request(req, ctx)
    assert res.is_error
    assert "Customer ID cannot be empty" in res.error()


def test_routing_no_healthy_provider_fails():
    ctx = make_context()
    unhealthy_map = {
        "psp-a": ProviderHealth("psp-a", 0.0, 500.0, 1.0, False, 0.70, 0.0),
        "psp-b": ProviderHealth("psp-b", 0.0, 600.0, 1.0, False, 0.85, 0.0),
        "psp-c": ProviderHealth("psp-c", 0.0, 700.0, 1.0, False, 0.30, 0.0)
    }
    unhealthy_ctx = PaymentContext(merchant_config=ctx.merchant_config, provider_health_map=unhealthy_map)
    req = PaymentRequest.create(amount=100.0, currency="INR", payment_method="upi")
    plan_res = build_execution_plan(req, unhealthy_ctx)
    assert plan_res.is_error
    assert "No healthy provider available" in plan_res.error()


def test_routing_open_circuit_breaker_excluded():
    ctx = make_context()
    cb_map = {
        "psp-a": ProviderHealth("psp-a", 0.99, 100.0, 0.01, True, 0.50, 90.0, circuit_breaker="OPEN"),
        "psp-b": ProviderHealth("psp-b", 0.98, 120.0, 0.02, True, 0.50, 90.0, circuit_breaker="CLOSED"),
    }
    cb_ctx = PaymentContext(merchant_config=ctx.merchant_config, provider_health_map=cb_map)
    req = PaymentRequest.create(amount=100.0, currency="INR", payment_method="upi")
    plan_res = build_execution_plan(req, cb_ctx)
    assert plan_res.is_ok
    # Must select psp-b because psp-a has circuit breaker OPEN
    assert plan_res.unwrap().routing.selected_provider == "psp-b"


def test_routing_deterministic_tie_breaking():
    ctx = make_context()
    # Exactly identical metrics
    tie_map = {
        "psp-z": ProviderHealth("psp-z", 0.99, 100.0, 0.01, True, 0.50, 90.0),
        "psp-a": ProviderHealth("psp-a", 0.99, 100.0, 0.01, True, 0.50, 90.0),
    }
    tie_ctx = PaymentContext(merchant_config=ctx.merchant_config, provider_health_map=tie_map)
    req = PaymentRequest.create(amount=100.0, currency="INR", payment_method="upi")
    plan_res = build_execution_plan(req, tie_ctx)
    assert plan_res.is_ok
    # Deterministic tie-breaking picks psp-a alphabetically
    assert plan_res.unwrap().routing.selected_provider == "psp-a"


def test_payment_state_machine_transitions():
    from payweave.runtime.functional_core import PaymentState, transition_payment_state
    
    # Valid transitions
    assert transition_payment_state(PaymentState.CREATED, PaymentState.PENDING).is_ok
    assert transition_payment_state(PaymentState.PENDING, PaymentState.SUCCEEDED).is_ok
    assert transition_payment_state(PaymentState.PENDING, PaymentState.FAILED).is_ok
    assert transition_payment_state(PaymentState.PENDING, PaymentState.UNCERTAIN_TIMEOUT).is_ok
    assert transition_payment_state(PaymentState.UNCERTAIN_TIMEOUT, PaymentState.SUCCEEDED).is_ok
    assert transition_payment_state(PaymentState.UNCERTAIN_TIMEOUT, PaymentState.FAILED).is_ok

    # Invalid transitions
    inv1 = transition_payment_state(PaymentState.CREATED, PaymentState.SUCCEEDED)
    assert inv1.is_error
    assert "Invalid payment state transition" in inv1.error()

    inv2 = transition_payment_state(PaymentState.SUCCEEDED, PaymentState.PENDING)
    assert inv2.is_error
    assert "Invalid payment state transition" in inv2.error()


def test_retry_eligibility_classification():
    from payweave.runtime.functional_core import is_retry_eligible

    # Retryable errors
    assert is_retry_eligible("Gateway timeout 504") is True
    assert is_retry_eligible("Connection reset by peer") is True
    assert is_retry_eligible("Circuit breaker tripped to HALF_OPEN probe failed") is True

    # Non-retryable errors
    assert is_retry_eligible("Payment amount must be greater than zero.") is False
    assert is_retry_eligible("Transaction risk score exceeds max threshold.") is False
    assert is_retry_eligible("Currency 'JPY' is not accepted.") is False
    assert is_retry_eligible("Customer ID cannot be empty.") is False

