"""
Mock PSP-A Adapter implementation.
Primary enterprise payment gateway with high success rate and moderate cost score.
"""

import random
import time
from payweave.providers.base import BasePSPAdapter, TransactionResult, ProviderStatus


class MockPSPAdapterA(BasePSPAdapter):
    """PSP-A: Enterprise Gateway (98.5% default success rate, 140ms latency, cost 0.70)."""

    def __init__(self):
        super().__init__(
            provider_id="psp-a",
            name="PSP-A Enterprise Gateway",
            default_success_rate=0.985,
            default_latency_ms=140.0,
            cost_score=0.70,
            capacity_pct=95.0
        )

    def process_payment(self, request_id: str, amount: float, currency: str,
                        method: str, force_fail: bool = False) -> TransactionResult:
        simulated_lat = self.current_latency_ms + random.uniform(-15.0, 25.0)
        time.sleep(min(simulated_lat / 1000.0, 0.05))  # Sleep up to 50ms for realistic UI feel

        if force_fail or not self.is_available or random.random() > self.current_success_rate:
            return TransactionResult(
                transaction_id=f"tx_pspa_fail_{random.randint(1000, 9999)}",
                request_id=request_id,
                provider_id=self.provider_id,
                status=ProviderStatus.FAILED,
                response_code="PSP_A_GATEWAY_DECLINE",
                latency_ms=round(simulated_lat, 2),
                message="PSP-A transaction declined by host bank."
            )

        return TransactionResult(
            transaction_id=f"tx_pspa_succ_{random.randint(10000, 99999)}",
            request_id=request_id,
            provider_id=self.provider_id,
            status=ProviderStatus.SUCCESS,
            response_code="200_OK",
            latency_ms=round(simulated_lat, 2),
            message="PSP-A payment processed successfully."
        )
