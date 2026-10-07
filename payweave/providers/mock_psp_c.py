"""
Mock PSP-C Adapter implementation.
Budget-friendly payment processor with ultra-low cost score and moderate latency.
"""

import random
import time
from payweave.providers.base import BasePSPAdapter, TransactionResult, ProviderStatus


class MockPSPAdapterC(BasePSPAdapter):
    """PSP-C: ValuePay Direct (96.5% default success rate, 220ms latency, cost 0.30)."""

    def __init__(self):
        super().__init__(
            provider_id="psp-c",
            name="PSP-C ValuePay Direct",
            default_success_rate=0.965,
            default_latency_ms=220.0,
            cost_score=0.30,
            capacity_pct=100.0
        )

    def process_payment(self, request_id: str, amount: float, currency: str,
                        method: str, force_fail: bool = False) -> TransactionResult:
        simulated_lat = self.current_latency_ms + random.uniform(-20.0, 35.0)
        time.sleep(min(simulated_lat / 1000.0, 0.05))

        if force_fail or not self.is_available or random.random() > self.current_success_rate:
            return TransactionResult(
                transaction_id=f"tx_pspc_fail_{random.randint(1000, 9999)}",
                request_id=request_id,
                provider_id=self.provider_id,
                status=ProviderStatus.FAILED,
                response_code="PSP_C_INSUFFICIENT_FUNDS",
                latency_ms=round(simulated_lat, 2),
                message="PSP-C authorization failed."
            )

        return TransactionResult(
            transaction_id=f"tx_pspc_succ_{random.randint(10000, 99999)}",
            request_id=request_id,
            provider_id=self.provider_id,
            status=ProviderStatus.SUCCESS,
            response_code="200_OK",
            latency_ms=round(simulated_lat, 2),
            message="PSP-C low-cost payment settled."
        )
