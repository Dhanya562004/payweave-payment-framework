"""
PayWeave High Level Payment Processor.
Executes built execution plans against simulated payment providers,
handles automatic retries/fallbacks, and collects live execution telemetry.
"""

import time
import random
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from payweave.runtime.functional_core import PaymentExecutionPlan, PaymentRequest, ProviderHealth
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


class PaymentProcessor:
    """Orchestrates actual transaction simulation using providers and fallback policies."""

    def __init__(self, provider_adapters: Dict[str, BasePSPAdapter]):
        self.providers = provider_adapters

    def execute_plan(self, plan: PaymentExecutionPlan, simulate_failure_provider: str = None) -> ProcessingOutcome:
        start_time = time.time()
        attempted: List[str] = []
        retries = 0

        target_provider_id = plan.routing.selected_provider
        fallback_candidates = [target_provider_id] + plan.routing.fallback_chain

        max_retries = plan.request.metadata.get("max_retries", len(fallback_candidates) - 1)

        last_result: Optional[TransactionResult] = None

        for p_id in fallback_candidates:
            if retries > max_retries:
                break

            attempted.append(p_id)
            adapter = self.providers.get(p_id)
            
            if not adapter:
                continue

            # Force synthetic failure if requested by simulation
            force_fail = (simulate_failure_provider == p_id)

            res = adapter.process_payment(
                request_id=plan.request.request_id,
                amount=plan.request.amount,
                currency=plan.request.currency,
                method=plan.request.payment_method,
                force_fail=force_fail
            )
            last_result = res

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
                    execution_plan=plan
                )

            retries += 1

        elapsed_ms = (time.time() - start_time) * 1000 + (last_result.latency_ms if last_result else 100.0)
        return ProcessingOutcome(
            success=False,
            transaction_id=f"tx_fail_{random.randint(10000, 99999)}",
            amount=plan.request.amount,
            currency=plan.request.currency,
            payment_method=plan.request.payment_method,
            provider_used=attempted[-1] if attempted else target_provider_id,
            attempted_providers=attempted,
            retries_count=retries - 1,
            total_latency_ms=round(elapsed_ms, 2),
            status_code=last_result.response_code if last_result else "EXHAUSTED_FALLBACKS",
            message=f"Payment failed after attempting {len(attempted)} provider(s): {attempted}",
            execution_plan=plan
        )
