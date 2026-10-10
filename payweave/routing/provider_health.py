"""
PayWeave Provider Health Tracker.
Monitors real-time provider statistics, maintains rolling window metrics,
and triggers circuit breaker degraded status.
"""

from typing import Dict, Any, List, Optional
from collections import deque
import time
from payweave.runtime.functional_core import ProviderHealth
from payweave.providers.base import BasePSPAdapter
from payweave.routing.circuit_breaker import CircuitBreaker, CircuitState


class ProviderHealthTracker:
    """Tracks live success rates, latencies, and circuit breaker status for PSP adapters."""

    def __init__(self, provider_adapters: Dict[str, BasePSPAdapter], window_size: int = 50,
                 circuit_failure_threshold: int = 3, circuit_cooldown_seconds: float = 5.0,
                 shared_state: Any = None):
        self.adapters = provider_adapters
        self.window_size = window_size
        self.shared_state = shared_state
        self._history: Dict[str, deque] = {
            pid: deque(maxlen=window_size) for pid in provider_adapters
        }
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            pid: CircuitBreaker(
                provider_id=pid,
                failure_threshold=circuit_failure_threshold,
                cooldown_seconds=circuit_cooldown_seconds
            )
            for pid in provider_adapters
        }

    def record_transaction(self, provider_id: str, success: bool, latency_ms: float, is_timeout: bool = False) -> None:
        """Records a transaction outcome into the rolling window and updates circuit breaker."""
        if provider_id in self._history:
            self._history[provider_id].append({
                "success": success,
                "latency": latency_ms,
                "timestamp": time.time()
            })
        if provider_id in self.circuit_breakers:
            if success:
                self.circuit_breakers[provider_id].record_success()
            else:
                self.circuit_breakers[provider_id].record_failure(is_timeout=is_timeout)

        # Sync to distributed shared state store if configured
        if self.shared_state:
            try:
                cb = self.circuit_breakers.get(provider_id)
                if cb:
                    self.shared_state.set_circuit_breaker_state(provider_id, cb.to_dict())
                h = self.get_health(provider_id)
                self.shared_state.set_provider_health(provider_id, {
                    "success_rate": h.success_rate,
                    "latency_ms": h.latency_ms,
                    "is_healthy": h.is_healthy,
                    "circuit_breaker": h.circuit_breaker
                })
            except Exception:
                pass

    def get_circuit_breaker(self, provider_id: str) -> Optional[CircuitBreaker]:
        return self.circuit_breakers.get(provider_id)

    def get_health(self, provider_id: str) -> ProviderHealth:
        """Computes current rolling window health metrics for a provider."""
        adapter = self.adapters.get(provider_id)
        cb = self.circuit_breakers.get(provider_id)
        cb_state = cb.state.value if cb else "CLOSED"

        if not adapter:
            return ProviderHealth(
                provider_id=provider_id,
                success_rate=0.0,
                latency_ms=999.0,
                error_rate=1.0,
                is_healthy=False,
                cost_score=1.0,
                capacity_pct=0.0,
                circuit_breaker="OPEN"
            )

        history = self._history.get(provider_id, deque())
        
        if not history:
            # Return adapter default configuration values if no telemetry yet
            is_healthy = adapter.is_available and adapter.current_success_rate >= 0.50 and (cb_state != "OPEN")
            return ProviderHealth(
                provider_id=provider_id,
                success_rate=adapter.current_success_rate,
                latency_ms=adapter.current_latency_ms,
                error_rate=round(1.0 - adapter.current_success_rate, 3),
                is_healthy=is_healthy,
                cost_score=adapter.cost_score,
                capacity_pct=adapter.capacity_pct,
                circuit_breaker=cb_state
            )

        total_tx = len(history)
        successes = sum(1 for item in history if item["success"])
        succ_rate = round(successes / total_tx, 4)
        avg_lat = round(sum(item["latency"] for item in history) / total_tx, 2)
        err_rate = round(1.0 - succ_rate, 4)

        # Healthy if adapter available, circuit not open, success rate >= 60%, and latency <= 700ms
        is_healthy = adapter.is_available and (cb_state != "OPEN") and (succ_rate >= 0.60) and (avg_lat <= 700.0)

        return ProviderHealth(
            provider_id=provider_id,
            success_rate=succ_rate,
            latency_ms=avg_lat,
            error_rate=err_rate,
            is_healthy=is_healthy,
            cost_score=adapter.cost_score,
            capacity_pct=adapter.capacity_pct,
            circuit_breaker=cb_state
        )

    def get_health_map(self) -> Dict[str, ProviderHealth]:
        return {pid: self.get_health(pid) for pid in self.adapters}

    def reset(self) -> None:
        for q in self._history.values():
            q.clear()
        for cb in self.circuit_breakers.values():
            cb.reset()
        for adapter in self.adapters.values():
            adapter.recover()
        if self.shared_state:
            try:
                self.shared_state.reset_state()
            except Exception:
                pass
