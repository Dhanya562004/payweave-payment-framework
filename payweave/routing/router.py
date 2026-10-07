"""
PayWeave Intelligent Router.
High-level routing coordinator combining multi-dimensional scoring, provider health tracking,
and self-healing automated rerouting.
"""

from typing import Dict, Any, List
from payweave.runtime.functional_core import PaymentRequest, RoutingDecision, ProviderHealth
from payweave.dsl.schema import MerchantConfig, RoutingStrategy
from payweave.routing.scoring import RoutingScoreCalculator
from payweave.routing.provider_health import ProviderHealthTracker
from payweave.routing.self_healing import SelfHealingEngine


class IntelligentRouter:
    """Intelligent Payment Routing Engine."""

    def __init__(self, health_tracker: ProviderHealthTracker, self_healing: SelfHealingEngine):
        self.health_tracker = health_tracker
        self.self_healing = self_healing

    def route_request(self, req: PaymentRequest, config: MerchantConfig) -> RoutingDecision:
        """Determines best provider and fallback chain for a payment request."""
        # 1. Trigger self-healing check before routing
        self.self_healing.evaluate_and_heal()

        # 2. Fetch live health map
        health_map = self.health_tracker.get_health_map()

        # 3. Rank providers
        ranked = RoutingScoreCalculator.rank_providers(health_map, config.routing)

        if not ranked or ranked[0][1] == 0.0:
            # Emergency fallback logic
            fallbacks = config.routing.fallback.fallback_providers or ["psp-b", "psp-c"]
            return RoutingDecision(
                selected_provider=fallbacks[0],
                fallback_chain=fallbacks[1:],
                score=0.0,
                rationale="EMERGENCY_FALLBACK: All primary providers degraded or unavailable."
            )

        best_pid, best_score, explanation = ranked[0]
        fallback_chain = [item[0] for item in ranked[1:] if item[1] > 0.0]

        # Append configured fallback providers if not already present
        for fb in config.routing.fallback.fallback_providers:
            if fb not in fallback_chain and fb != best_pid:
                fallback_chain.append(fb)

        rationale = f"Selected {best_pid.upper()} (Routing Score: {best_score:.3f}) via {config.routing.strategy} strategy. Details: {explanation}"

        return RoutingDecision(
            selected_provider=best_pid,
            fallback_chain=fallback_chain,
            score=best_score,
            rationale=rationale
        )
