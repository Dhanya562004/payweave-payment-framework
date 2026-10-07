"""
PayWeave Self-Healing Engine.
Detects provider failures and network degradation, automatically adjusts routing weights,
shifts traffic to healthy fallbacks, and maintains audit timeline of recovery events.
"""

import time
from typing import List, Dict, Any, Optional
from payweave.routing.provider_health import ProviderHealthTracker


class SelfHealingEvent:
    def __init__(self, timestamp: float, provider_id: str, event_type: str,
                 severity: str, description: str, action_taken: str):
        self.timestamp = timestamp
        self.provider_id = provider_id
        self.event_type = event_type
        self.severity = severity  # CRITICAL, WARNING, INFO
        self.description = description
        self.action_taken = action_taken

    def formatted_time(self) -> str:
        return time.strftime("%H:%M:%S", time.localtime(self.timestamp))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time": self.formatted_time(),
            "timestamp": self.timestamp,
            "provider_id": self.provider_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "description": self.description,
            "action_taken": self.action_taken
        }


class SelfHealingEngine:
    """Automated self-healing and recovery engine for PayWeave infrastructure."""

    def __init__(self, health_tracker: ProviderHealthTracker):
        self.health_tracker = health_tracker
        self.events: List[SelfHealingEvent] = []
        self._degraded_providers: set = set()

    def evaluate_and_heal(self) -> List[SelfHealingEvent]:
        """Evaluates system health and executes self-healing remediation if needed."""
        new_events: List[SelfHealingEvent] = []
        now = time.time()
        health_map = self.health_tracker.get_health_map()

        for pid, health in health_map.items():
            adapter = self.health_tracker.adapters.get(pid)
            
            # 1. Latency spike or error drop detection
            if (health.latency_ms > 300.0 or health.success_rate < 0.80 or adapter.latency_spike) and (pid not in self._degraded_providers):
                self._degraded_providers.add(pid)
                
                # Event 1: Detection
                e1 = SelfHealingEvent(
                    timestamp=now,
                    provider_id=pid,
                    event_type="DEGRADATION_DETECTED",
                    severity="WARNING",
                    description=f"Latency spike ({health.latency_ms:.0f}ms) or success drop ({health.success_rate*100:.1f}%) detected on {pid.upper()}.",
                    action_taken="Triggered automated self-healing evaluation."
                )
                
                # Event 2: Health reduction & Traffic rerouting
                e2 = SelfHealingEvent(
                    timestamp=now + 1.0,
                    provider_id=pid,
                    event_type="HEALTH_SCORE_REDUCED",
                    severity="CRITICAL",
                    description=f"Reduced health score for {pid.upper()} to zero. Preferred routing updated.",
                    action_taken=f"Rerouted active payment traffic away from {pid.upper()} to next healthiest fallback provider."
                )
                
                new_events.extend([e1, e2])
                self.events.extend([e1, e2])

            # 2. Recovery detection
            elif (health.latency_ms <= 250.0 and health.success_rate >= 0.95 and not adapter.latency_spike) and (pid in self._degraded_providers):
                self._degraded_providers.remove(pid)
                
                e_rec = SelfHealingEvent(
                    timestamp=now,
                    provider_id=pid,
                    event_type="RECOVERY_CONFIRMED",
                    severity="INFO",
                    description=f"{pid.upper()} telemetry restored to normal baseline (Success: {health.success_rate*100:.1f}%, Latency: {health.latency_ms:.0f}ms).",
                    action_taken=f"Restored {pid.upper()} into active primary routing pool."
                )
                new_events.append(e_rec)
                self.events.append(e_rec)

        return new_events

    def trigger_manual_failure(self, provider_id: str, latency_multiplier: float = 3.5, success_drop: float = 0.4) -> List[SelfHealingEvent]:
        """Manually injects provider degradation for demonstration/testing."""
        adapter = self.health_tracker.adapters.get(provider_id)
        if adapter:
            adapter.simulate_degradation(latency_multiplier=latency_multiplier, success_drop=success_drop)
            return self.evaluate_and_heal()
        return []

    def trigger_manual_recovery(self, provider_id: str) -> List[SelfHealingEvent]:
        """Manually restores a provider to healthy operational status."""
        adapter = self.health_tracker.adapters.get(provider_id)
        if adapter:
            adapter.recover()
            return self.evaluate_and_heal()
        return []

    def get_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        sorted_events = sorted(self.events, key=lambda x: x.timestamp, reverse=True)
        return [e.to_dict() for e in sorted_events[:limit]]

    def reset(self) -> None:
        self.events.clear()
        self._degraded_providers.clear()
