"""
Mock PSP-B Adapter implementation.
Ultra-fast low-latency payment gateway with high success rate and premium cost score.
"""

import random
import time
from payweave.providers.base import BasePSPAdapter, TransactionResult, ProviderStatus


class MockPSPAdapterB(BasePSPAdapter):
    """PSP-B: SpeedPay Express (99.0% default success rate, 110ms latency, cost 0.85)."""

    def __init__(self):
        super().__init__(
            provider_id="psp-b",
            name="PSP-B SpeedPay Express",
            default_success_rate=0.990,
            default_latency_ms=110.0,
            cost_score=0.85,
            capacity_pct=88.0
        )

    def process_payment(self, request_id: str, amount: float, currency: str,
                        method: str, force_fail: bool = False) -> TransactionResult:
        simulated_lat = self.current_latency_ms + random.uniform(-10.0, 15.0)
        time.sleep(min(simulated_lat / 1000.0, 0.05))

        if force_fail or not self.is_available or random.random() > self.current_success_rate:
            return TransactionResult(
                transaction_id=f"tx_pspb_fail_{random.randint(1000, 9999)}",
                request_id=request_id,
                provider_id=self.provider_id,
                status=ProviderStatus.FAILED,
                response_code="PSP_B_TIMEOUT",
                latency_ms=round(simulated_lat, 2),
                message="PSP-B connection timed out during execution."
            )

        return TransactionResult(
            transaction_id=f"tx_pspb_succ_{random.randint(10000, 99999)}",
            request_id=request_id,
            provider_id=self.provider_id,
            status=ProviderStatus.SUCCESS,
            response_code="200_OK",
            latency_ms=round(simulated_lat, 2),
            message="PSP-B payment executed with ultra-low latency."
        )
