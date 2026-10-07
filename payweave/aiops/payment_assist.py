"""
PayWeave Assist Query Engine.
Handles natural language questions about payment performance, routing decisions,
provider health, and system incidents.
"""

from typing import Dict, Any, List
from payweave.aiops.llm_client import LLMClient
from payweave.dsl.schema import MerchantConfig


class PayWeaveAssist:
    """Natural Language Payment Operations Assistant."""

    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()

    def ask(self, question: str, config: MerchantConfig, health_map: Dict[str, Any],
            recent_events: List[Dict[str, Any]] = None) -> str:
        """Processes user question with contextual telemetry snapshot."""
        context_str = self._build_context_snapshot(config, health_map, recent_events)
        return self.llm.generate_response(prompt=question, system_context=context_str)

    def _build_context_snapshot(self, config: MerchantConfig, health_map: Dict[str, Any],
                                 recent_events: List[Dict[str, Any]]) -> str:
        lines = [
            f"Merchant: {config.merchant.name} (ID: {config.merchant.id})",
            f"Routing Strategy: {config.routing.strategy}",
            f"Fallback Enabled: {config.routing.fallback.enabled} (Retries: {config.routing.fallback.max_retries})",
            "Provider Health Status:"
        ]
        for pid, h in health_map.items():
            succ = getattr(h, "success_rate", 0.95) * 100
            lat = getattr(h, "latency_ms", 150)
            healthy = getattr(h, "is_healthy", True)
            lines.append(f"  - {pid.upper()}: Success={succ:.1f}%, Latency={lat:.0f}ms, Healthy={healthy}")

        if recent_events:
            lines.append("Recent Self-Healing Events:")
            for ev in recent_events[:3]:
                lines.append(f"  - [{ev.get('time', 'NOW')}] {ev.get('provider_id', '')}: {ev.get('description', '')}")

        return "\n".join(lines)
