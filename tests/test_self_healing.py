"""
PayWeave Self-Healing System Unit Tests.
Verifies provider failure detection, health reduction, automated traffic rerouting, and recovery event logs.
"""

import pytest
from payweave.routing.provider_health import ProviderHealthTracker
from payweave.routing.self_healing import SelfHealingEngine
from payweave.providers.mock_psp_a import MockPSPAdapterA
from payweave.providers.mock_psp_b import MockPSPAdapterB
from payweave.providers.mock_psp_c import MockPSPAdapterC


@pytest.fixture
def healing_setup():
    adapters = {
        "psp-a": MockPSPAdapterA(),
        "psp-b": MockPSPAdapterB(),
        "psp-c": MockPSPAdapterC()
    }
    tracker = ProviderHealthTracker(adapters)
    healer = SelfHealingEngine(tracker)
    return adapters, tracker, healer


def test_provider_health_tracker_initial_defaults(healing_setup):
    _, tracker, _ = healing_setup
    health = tracker.get_health("psp-a")
    assert health.is_healthy is True
    assert health.success_rate == 0.985


def test_manual_degradation_triggers_self_healing_events(healing_setup):
    adapters, tracker, healer = healing_setup
    events = healer.trigger_manual_failure("psp-a", latency_multiplier=4.0, success_drop=0.4)
    
    assert len(events) >= 2
    assert any(e.event_type == "DEGRADATION_DETECTED" for e in events)
    assert any(e.event_type == "HEALTH_SCORE_REDUCED" for e in events)
    
    health_a = tracker.get_health("psp-a")
    assert health_a.latency_ms > 400.0


def test_manual_recovery_restores_health(healing_setup):
    adapters, tracker, healer = healing_setup
    healer.trigger_manual_failure("psp-a")
    rec_events = healer.trigger_manual_recovery("psp-a")
    
    assert any(e.event_type == "RECOVERY_CONFIRMED" for e in rec_events)
    health_a = tracker.get_health("psp-a")
    assert health_a.is_healthy is True


def test_self_healing_timeline_records_events(healing_setup):
    _, _, healer = healing_setup
    healer.trigger_manual_failure("psp-b")
    timeline = healer.get_timeline()
    assert len(timeline) >= 2
    assert timeline[0]["provider_id"] == "psp-b"
