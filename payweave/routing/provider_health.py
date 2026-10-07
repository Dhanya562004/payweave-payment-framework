"""
PayWeave Provider Health Tracker.
Monitors real-time provider statistics, maintains rolling window metrics,
and triggers circuit breaker degraded status.
"""

from typing import Dict, Any, List
from collections import deque
import time
from payweave.runtime.functional_core import ProviderHealth
from payweave.providers.base import BasePSPAdapter


class ProviderHealthTracker:
    """Tracks live success rates, latencies, and circuit breaker status for PSP adapters."""

    def __init__(self, provider_adapters: Dict[str, BasePSPAdapter], window_size: int = 50):
        self.adapters = provider_adapters
        self.window_size = window_size
        self._history: Dict[str, deque] = {
            pid: deque(maxlen=window_size) for pid in provider_adapters
        }

    def record_transaction(self, provider_id: str, success: bool, latency_ms: float) -> None:
        """Records a transaction outcome into the rolling window for the provider."""
        if provider_id in self._history:
            self._history[provider_id].append({
                "success": success,
                "latency": latency_ms,
                "timestamp": time.time()
            })

    def get_health(self, provider_id: str) -> ProviderHealth:
        """Computes current rolling window health metrics for a provider."""
        adapter = self.adapters.get(provider_id)
        if not adapter:
            return ProviderHealth(
                provider_id=provider_id,
                success_rate=0.0,
                latency_ms=999.0,
                error_rate=1.0,
                is_healthy=False,
                cost_score=1.0,
                capacity_pct=0.0
            )

        history = self._history.get(provider_id, deque())
        
        if not history:
            # Return adapter default configuration values if no telemetry yet
            return ProviderHealth(
                provider_id=provider_id,
                success_rate=adapter.current_success_rate,
                latency_ms=adapter.current_latency_ms,
                error_rate=round(1.0 - adapter.current_success_rate, 3),
                is_healthy=adapter.is_available and adapter.current_success_rate >= 0.50,
                cost_score=adapter.cost_score,
                capacity_pct=adapter.capacity_pct
            )

        total_tx = len(history)
        successes = sum(1 for item in history if item["success"])
        succ_rate = round(successes / total_tx, 4)
        avg_lat = round(sum(item["latency"] for item in history) / total_tx, 2)
        err_rate = round(1.0 - succ_rate, 4)

        # Circuit breaker rule: healthy if success rate >= 60% and latency <= 700ms
        is_healthy = adapter.is_available and (succ_rate >= 0.60) and (avg_lat <= 700.0)

        return ProviderHealth(
            provider_id=provider_id,
            success_rate=succ_rate,
            latency_ms=avg_lat,
            error_rate=err_rate,
            is_healthy=is_healthy,
            cost_score=adapter.cost_score,
            capacity_pct=adapter.capacity_pct
        )

    def get_health_map(self) -> Dict[str, ProviderHealth]:
        return {pid: self.get_health(pid) for pid in self.adapters}

    def reset(self) -> None:
        for q in self._history.values():
            q.clear()
        for adapter in self.adapters.values():
            adapter.recover()
