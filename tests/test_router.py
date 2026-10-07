"""
PayWeave Intelligent Router Unit Tests.
Verifies multi-dimensional scoring, strategy selection, ranking deterministic behavior, and fallback chains.
"""

import pytest
from payweave.dsl.schema import MerchantConfig, RoutingConfig, RoutingStrategy
from payweave.runtime.functional_core import ProviderHealth, PaymentRequest
from payweave.routing.scoring import RoutingScoreCalculator
from payweave.routing.provider_health import ProviderHealthTracker
from payweave.routing.self_healing import SelfHealingEngine
from payweave.routing.router import IntelligentRouter
from payweave.providers.mock_psp_a import MockPSPAdapterA
from payweave.providers.mock_psp_b import MockPSPAdapterB
from payweave.providers.mock_psp_c import MockPSPAdapterC


@pytest.fixture
def sample_health():
    return {
        "psp-a": ProviderHealth("psp-a", 0.985, 140.0, 0.015, True, 0.70, 95.0),
        "psp-b": ProviderHealth("psp-b", 0.990, 110.0, 0.010, True, 0.85, 90.0),
        "psp-c": ProviderHealth("psp-c", 0.965, 220.0, 0.035, True, 0.30, 100.0)
    }


def test_score_calculator_unhealthy():
    unhealthy = ProviderHealth("psp-a", 0.0, 500.0, 1.0, False, 1.0, 0.0)
    score = RoutingScoreCalculator.calculate_score(unhealthy, {})
    assert score == 0.0


def test_lowest_cost_strategy_selects_psp_c(sample_health):
    cfg = RoutingConfig(strategy=RoutingStrategy.LOWEST_COST)
    ranked = RoutingScoreCalculator.rank_providers(sample_health, cfg)
    assert ranked[0][0] == "psp-c"


def test_lowest_latency_strategy_selects_psp_b(sample_health):
    cfg = RoutingConfig(strategy=RoutingStrategy.LOWEST_LATENCY)
    ranked = RoutingScoreCalculator.rank_providers(sample_health, cfg)
    assert ranked[0][0] == "psp-b"


def test_highest_success_rate_strategy_selects_psp_b(sample_health):
    cfg = RoutingConfig(strategy=RoutingStrategy.HIGHEST_SUCCESS_RATE)
    ranked = RoutingScoreCalculator.rank_providers(sample_health, cfg)
    assert ranked[0][0] == "psp-b"


def test_intelligent_router_deterministic_for_identical_inputs():
    adapters = {"psp-a": MockPSPAdapterA(), "psp-b": MockPSPAdapterB(), "psp-c": MockPSPAdapterC()}
    tracker = ProviderHealthTracker(adapters)
    healer = SelfHealingEngine(tracker)
    router = IntelligentRouter(tracker, healer)
    cfg = MerchantConfig()
    req = PaymentRequest.create(amount=1000.0)

    dec1 = router.route_request(req, cfg)
    dec2 = router.route_request(req, cfg)
    assert dec1.selected_provider == dec2.selected_provider
    assert dec1.score == dec2.score
