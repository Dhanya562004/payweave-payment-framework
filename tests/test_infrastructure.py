"""
PayWeave Infrastructure Simulation Unit Tests.
Verifies Infrastructure DSL parsing, Mermaid topology diagram generation, multi-DC failover, and edge evaluation.
"""

import pytest
from payweave.infrastructure.infrastructure_dsl import InfrastructureDSLParser
from payweave.infrastructure.topology import TopologyVisualizer
from payweave.infrastructure.multi_dc import MultiDCSimulator
from payweave.infrastructure.edge import EdgeComputingSimulator


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
