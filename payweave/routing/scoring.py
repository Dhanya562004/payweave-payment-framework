"""
PayWeave Routing Score Engine.
Computes multi-dimensional provider scoring based on success rate, latency,
health, cost efficiency, and capacity.
"""

from typing import Dict, List, Tuple
from payweave.runtime.functional_core import ProviderHealth
from payweave.dsl.schema import RoutingStrategy, RoutingConfig


class RoutingScoreCalculator:
    """Calculates weighted routing scores for payment provider selection."""

    @staticmethod
    def calculate_score(health: ProviderHealth, weights: Dict[str, float],
                        max_latency_ref: float = 500.0) -> float:
        """
        routing_score = (w_succ * success_rate)
                      + (w_lat * (1 - latency / max_latency))
                      + (w_health * health_score)
                      + (w_cost * (1 - cost_score))
                      + (w_cap * capacity_pct / 100)
        """
        if not health.is_healthy:
            return 0.0

        w_succ = weights.get("success_rate", 0.40)
        w_lat = weights.get("latency", 0.30)
        w_health = weights.get("health", 0.15)
        w_cost = weights.get("cost", 0.10)
        w_cap = weights.get("capacity", 0.05)

        succ_score = health.success_rate
        lat_score = max(0.0, 1.0 - (min(health.latency_ms, max_latency_ref) / max_latency_ref))
        health_score = 1.0 if health.is_healthy else 0.0
        cost_factor = max(0.0, 1.0 - health.cost_score)
        cap_factor = max(0.0, min(1.0, health.capacity_pct / 100.0))

        score = (
            (w_succ * succ_score) +
            (w_lat * lat_score) +
            (w_health * health_score) +
            (w_cost * cost_factor) +
            (w_cap * cap_factor)
        )
        return round(score, 4)

    @staticmethod
    def rank_providers(providers_health: Dict[str, ProviderHealth],
                       routing_config: RoutingConfig) -> List[Tuple[str, float, str]]:
        """Ranks providers according to the selected strategy and weights."""
        strategy = routing_config.strategy
        weights = routing_config.weights

        if strategy == RoutingStrategy.HIGHEST_SUCCESS_RATE:
            effective_weights = {"success_rate": 0.80, "health": 0.20, "latency": 0.0, "cost": 0.0, "capacity": 0.0}
        elif strategy == RoutingStrategy.LOWEST_LATENCY:
            effective_weights = {"latency": 0.80, "health": 0.20, "success_rate": 0.0, "cost": 0.0, "capacity": 0.0}
        elif strategy == RoutingStrategy.LOWEST_COST:
            effective_weights = {"cost": 0.80, "success_rate": 0.10, "health": 0.10, "latency": 0.0, "capacity": 0.0}
        elif strategy == RoutingStrategy.BALANCED:
            effective_weights = {"success_rate": 0.30, "latency": 0.30, "cost": 0.20, "health": 0.10, "capacity": 0.10}
        else:  # INTELLIGENT
            effective_weights = weights

        max_lat = max([p.latency_ms for p in providers_health.values()] or [500.0])
        ranked = []

        for pid, health in providers_health.items():
            score = RoutingScoreCalculator.calculate_score(health, effective_weights, max_latency_ref=max_lat)
            explanation = (
                f"Success: {health.success_rate*100:.1f}%, Latency: {health.latency_ms:.0f}ms, "
                f"Cost factor: {health.cost_score:.2f}, Capacity: {health.capacity_pct:.0f}%"
            )
            ranked.append((pid, score, explanation))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
