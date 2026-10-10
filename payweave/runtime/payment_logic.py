"""
PayWeave High Level Payment Processor.
Executes built execution plans against simulated payment providers,
handles bounded retries with exponential backoff and jitter for eligible failures,
distinguishes uncertain timeouts from definitive failures, and records telemetry.
"""

import time
import random
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from payweave.runtime.functional_core import (
    PaymentExecutionPlan, PaymentRequest, ProviderHealth, is_retry_eligible
)
from payweave.providers.base import BasePSPAdapter, TransactionResult, ProviderStatus


@dataclass
class ProcessingOutcome:
    success: bool
    transaction_id: str
    amount: float
    currency: str
    payment_method: str
    provider_used: str
    attempted_providers: List[str]
    retries_count: int
    total_latency_ms: float
    status_code: str
    message: str
    execution_plan: PaymentExecutionPlan
    is_uncertain_timeout: bool = False


class PaymentProcessor:
    """Orchestrates actual transaction simulation using providers and fallback policies."""

    def __init__(self, provider_adapters: Dict[str, BasePSPAdapter], health_tracker=None):
        self.providers = provider_adapters
        self.health_tracker = health_tracker

    def execute_plan(
        self,
        plan: PaymentExecutionPlan,
        simulate_failure_provider: str = None,
        base_backoff_ms: float = 2.0,
        max_backoff_ms: float = 20.0,
        enable_backoff_sleep: bool = True
    ) -> ProcessingOutcome:
        start_time = time.time()
        attempted: List[str] = []
        retries = 0

        target_provider_id = plan.routing.selected_provider
        fallback_candidates = [target_provider_id] + plan.routing.fallback_chain

        max_retries = plan.request.metadata.get("max_retries", len(fallback_candidates) - 1)
        last_result: Optional[TransactionResult] = None
        was_uncertain_timeout = False

        for p_id in fallback_candidates:
            if retries > max_retries:
                break

            attempted.append(p_id)
            adapter = self.providers.get(p_id)

            if not adapter:
                continue

            # Force synthetic failure if requested by simulation
            force_fail = (simulate_failure_provider == p_id)

            # Apply bounded exponential backoff with jitter on retries
            if retries > 0 and enable_backoff_sleep:
                backoff_ms = min(max_backoff_ms, base_backoff_ms * (2 ** (retries - 1)))
                jitter_ms = random.uniform(0.5, 2.0)
                sleep_sec = (backoff_ms + jitter_ms) / 1000.0
                time.sleep(sleep_sec)

            res = adapter.process_payment(
                request_id=plan.request.request_id,
                amount=plan.request.amount,
                currency=plan.request.currency,
                method=plan.request.payment_method,
                force_fail=force_fail
            )
            last_result = res

            # Record telemetry in health tracker if wired
            if self.health_tracker:
                is_timeout = (res.status == ProviderStatus.TIMEOUT)
                self.health_tracker.record_transaction(
                    provider_id=p_id,
                    success=(res.status == ProviderStatus.SUCCESS),
                    latency_ms=res.latency_ms,
                    is_timeout=is_timeout
                )

            # 1. Success case
            if res.status == ProviderStatus.SUCCESS:
                elapsed_ms = (time.time() - start_time) * 1000 + res.latency_ms
                return ProcessingOutcome(
                    success=True,
                    transaction_id=res.transaction_id,
                    amount=plan.request.amount,
                    currency=plan.request.currency,
                    payment_method=plan.request.payment_method,
                    provider_used=p_id,
                    attempted_providers=attempted,
                    retries_count=retries,
                    total_latency_ms=round(elapsed_ms, 2),
                    status_code=res.response_code,
                    message=f"Payment successfully processed via {p_id.upper()} ({retries} retries).",
                    execution_plan=plan,
                    is_uncertain_timeout=False
                )

            # 2. Timeout case: uncertain outcome, eligible for fallback
            if res.status == ProviderStatus.TIMEOUT:
                was_uncertain_timeout = True
                retries += 1
                continue

            # 3. Definite Failure case: check retry eligibility
            err_reason = f"{res.response_code}: {res.message}"
            if not is_retry_eligible(err_reason):
                # Non-retryable business failure (e.g. validation, card decline) -> terminate immediately
                elapsed_ms = (time.time() - start_time) * 1000 + res.latency_ms
                return ProcessingOutcome(
                    success=False,
                    transaction_id=f"tx_fail_{random.randint(10000, 99999)}",
                    amount=plan.request.amount,
                    currency=plan.request.currency,
                    payment_method=plan.request.payment_method,
                    provider_used=p_id,
                    attempted_providers=attempted,
                    retries_count=retries,
                    total_latency_ms=round(elapsed_ms, 2),
                    status_code=res.response_code,
                    message=f"Non-retryable provider error: {res.message} (status: {res.response_code})",
                    execution_plan=plan,
                    is_uncertain_timeout=False
                )

            retries += 1

        elapsed_ms = (time.time() - start_time) * 1000 + (last_result.latency_ms if last_result else 100.0)
        status_code = last_result.response_code if last_result else "EXHAUSTED_FALLBACKS"
        msg = (
            f"Payment uncertain: upstream timed out across {len(attempted)} provider(s)."
            if was_uncertain_timeout
            else f"Payment failed after attempting {len(attempted)} provider(s): {attempted}"
        )

        return ProcessingOutcome(
            success=False,
            transaction_id=f"tx_fail_{random.randint(10000, 99999)}",
            amount=plan.request.amount,
            currency=plan.request.currency,
            payment_method=plan.request.payment_method,
            provider_used=attempted[-1] if attempted else target_provider_id,
            attempted_providers=attempted,
            retries_count=max(0, retries - 1),
            total_latency_ms=round(elapsed_ms, 2),
            status_code=status_code,
            message=msg,
            execution_plan=plan,
            is_uncertain_timeout=was_uncertain_timeout
        )
