"""
PayWeave Edge Computing Simulator.
Simulates edge worker nodes making localized risk assessment and low-latency routing decisions.
"""

import random
from typing import Dict, Any, List
from payweave.infrastructure.infrastructure_dsl import EdgeNodeSpec


class EdgeComputingSimulator:
    """Simulates distributed edge nodes intercepting and processing requests."""

    def __init__(self, edge_nodes: List[EdgeNodeSpec] = None):
        self.edge_nodes = edge_nodes or [
            EdgeNodeSpec(id="edge_delhi", location="Delhi NCR", nearest_dc="dc1", latency_overhead_ms=12.0),
            EdgeNodeSpec(id="edge_mumbai", location="Mumbai Region", nearest_dc="dc1", latency_overhead_ms=5.0),
            EdgeNodeSpec(id="edge_bengaluru", location="Bengaluru Tech Park", nearest_dc="dc2", latency_overhead_ms=8.0)
        ]

    def evaluate_request_at_edge(self, edge_id: str, amount: float, risk_score: float) -> Dict[str, Any]:
        node = next((n for n in self.edge_nodes if n.id == edge_id), self.edge_nodes[0])
        
        # Local edge risk pre-filtering
        edge_decision = "PASSED_LOCAL_CHECK"
        if risk_score > 0.85:
            edge_decision = "BLOCKED_AT_EDGE"

        total_latency = node.latency_overhead_ms + (140.0 if node.nearest_dc == "dc1" else 110.0)

        return {
            "edge_node_id": node.id,
            "location": node.location,
            "status": node.status,
            "nearest_dc": node.nearest_dc,
            "edge_latency_overhead_ms": node.latency_overhead_ms,
            "total_estimated_latency_ms": total_latency,
            "edge_decision": edge_decision,
            "cache_hit": random.choice([True, False])
        }

    def get_nodes_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": n.id,
                "location": n.location,
                "nearest_dc": n.nearest_dc,
                "latency_overhead_ms": n.latency_overhead_ms,
                "status": n.status
            }
            for n in self.edge_nodes
        ]
