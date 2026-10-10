"""
PayWeave Infrastructure Simulation & Distributed Coordination Unit Tests.
Verifies Infrastructure DSL parsing, Mermaid topology diagram generation, multi-DC failover,
edge evaluation, Redis/in-memory shared state management, and Docker Compose generation.
"""

import pytest
import tempfile
import os
import json
from payweave.infrastructure.infrastructure_dsl import InfrastructureDSLParser
from payweave.infrastructure.topology import TopologyVisualizer
from payweave.infrastructure.multi_dc import MultiDCSimulator
from payweave.infrastructure.edge import EdgeComputingSimulator
from payweave.infrastructure.docker_generator import DockerComposeGenerator
from payweave.routing.shared_state import SharedStateManager
from payweave.dsl.schema import MerchantConfig


def test_infrastructure_dsl_parser_defaults():
    cfg = InfrastructureDSLParser.parse_yaml("")
    assert cfg.primary_dc == "dc1"
    assert cfg.failover_dc == "dc2"
    assert len(cfg.edge_nodes) >= 3


def test_topology_visualizer_mermaid_output():
    cfg = InfrastructureDSLParser.parse_yaml("")
    mermaid = TopologyVisualizer.generate_mermaid(cfg)
    assert "graph TD" in mermaid
    assert "Edge Layer" in mermaid
    assert "Data Center Layer" in mermaid


def test_multi_dc_failover_simulation():
    sim = MultiDCSimulator()
    assert sim.active_dc == "dc1"
    
    event = sim.simulate_dc_failure("dc1")
    assert event["event"] == "DC OUTAGE DETECTED on DC1"
    assert sim.active_dc == "dc2"
    assert sim.config.datacenters["dc1"].status == "unhealthy"
    
    rec_event = sim.recover_dc("dc1")
    assert rec_event["event"] == "DC RECOVERY CONFIRMED on DC1"
    assert sim.active_dc == "dc1"


def test_edge_node_evaluation():
    sim = EdgeComputingSimulator()
    res = sim.evaluate_request_at_edge("edge_delhi", amount=5000.0, risk_score=0.10)
    assert res["edge_node_id"] == "edge_delhi"
    assert res["edge_decision"] == "PASSED_LOCAL_CHECK"
    assert res["total_estimated_latency_ms"] > 0.0


def test_shared_state_in_memory_fallback():
    # Provide an invalid Redis port to force fallback to in-memory store
    store = SharedStateManager(redis_url="redis://localhost:9999/0")
    assert store.is_using_redis is False

    # Storing and retrieving provider health
    store.set_provider_health("psp-a", {"success_rate": 0.99, "latency_ms": 120.0, "is_healthy": True})
    health = store.get_provider_health("psp-a")
    assert health is not None
    assert health["success_rate"] == 0.99
    assert health["latency_ms"] == 120.0
    assert health["is_healthy"] is True

    # Storing and retrieving circuit breaker state
    store.set_circuit_breaker_state("psp-b", {"state": "OPEN", "consecutive_failures": 3})
    cb = store.get_circuit_breaker_state("psp-b")
    assert cb is not None
    assert cb["state"] == "OPEN"
    assert cb["consecutive_failures"] == 3

    # Reset
    store.reset_state()
    assert store.get_provider_health("psp-a") is None
    assert store.get_circuit_breaker_state("psp-b") is None


def test_shared_state_with_mock_redis():
    class MockRedisClient:
        def __init__(self):
            self.data = {}

        def ping(self):
            return True

        def set(self, key, value, ex=None):
            self.data[key] = value

        def get(self, key):
            return self.data.get(key)

        def keys(self, pattern):
            return list(self.data.keys())

        def delete(self, *keys):
            for k in keys:
                self.data.pop(k, None)

    mock_client = MockRedisClient()
    store = SharedStateManager(client=mock_client)
    assert store.is_using_redis is True

    store.set_provider_health("psp-c", {"success_rate": 0.95, "latency_ms": 250.0})
    health = store.get_provider_health("psp-c")
    assert health["success_rate"] == 0.95

    # Check that data was written to mock Redis client with expected key
    assert "payweave:health:psp-c" in mock_client.data

    store.reset_state()
    assert store.get_provider_health("psp-c") is None


def test_docker_compose_generator():
    cfg = MerchantConfig()
    cfg.merchant.id = "merchant_test"
    cfg.routing.fallback.fallback_providers = ["psp-a", "psp-b"]

    compose_dict = DockerComposeGenerator.generate_dict(cfg)
    assert compose_dict["version"] == "3.8"
    assert "services" in compose_dict

    services = compose_dict["services"]
    assert "payweave-api" in services
    assert "payweave-ui" in services
    assert "redis" in services
    assert "mock-psp-a" in services
    assert "mock-psp-b" in services

    # Verify ports and environment
    assert "8000:8000" in services["payweave-api"]["ports"]
    assert "6379:6379" in services["redis"]["ports"]
    assert services["payweave-api"]["environment"]["MERCHANT_ID"] == "merchant_test"

    yaml_str = DockerComposeGenerator.generate(cfg)
    assert "payweave-api" in yaml_str
    assert "redis:7-alpine" in yaml_str


def test_docker_compose_file_writing(tmp_path):
    target = str(tmp_path / "docker-compose.yml")
    cfg = MerchantConfig()
    written = DockerComposeGenerator.write_compose_file(output_path=target, config=cfg)
    assert os.path.exists(target)
    assert "payweave-api" in written

