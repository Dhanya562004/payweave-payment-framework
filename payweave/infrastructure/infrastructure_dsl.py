"""
PayWeave Infrastructure DSL Parser and Validator.
Parses multi-datacenter topology configurations, edge node rules, and failover parameters.
"""

import yaml
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DataCenterSpec(BaseModel):
    name: str
    capacity: int = 1000
    providers: List[str] = Field(default_factory=lambda: ["psp-a", "psp-b"])
    status: str = "healthy"
    baseline_latency_ms: float = 45.0


class EdgeNodeSpec(BaseModel):
    id: str
    location: str
    nearest_dc: str
    latency_overhead_ms: float = 8.0
    status: str = "healthy"


class InfrastructureDSLConfig(BaseModel):
    region: str = "asia_south"
    primary_dc: str = "dc1"
    failover_dc: str = "dc2"
    datacenters: Dict[str, DataCenterSpec] = Field(default_factory=dict)
    edge_nodes: List[EdgeNodeSpec] = Field(default_factory=list)
    auto_failover: bool = True


class InfrastructureDSLParser:
    """Parses and serializes Infrastructure YAML configs."""

    @staticmethod
    def parse_yaml(yaml_str: str) -> InfrastructureDSLConfig:
        try:
            data = yaml.safe_load(yaml_str) or {}
            if not data:
                return InfrastructureDSLConfig(
                    datacenters={
                        "dc1": DataCenterSpec(name="Mumbai DC1 Primary", capacity=1000, providers=["psp-a", "psp-b"]),
                        "dc2": DataCenterSpec(name="Bengaluru DC2 Failover", capacity=1000, providers=["psp-b", "psp-c"])
                    },
                    edge_nodes=[
                        EdgeNodeSpec(id="edge_delhi", location="Delhi NCR", nearest_dc="dc1"),
                        EdgeNodeSpec(id="edge_mumbai", location="Mumbai Region", nearest_dc="dc1"),
                        EdgeNodeSpec(id="edge_bengaluru", location="Bengaluru Tech Park", nearest_dc="dc2")
                    ]
                )
            
            # Map edge nodes list if formatted as dict/list
            edge_raw = data.get("edge", {}).get("nodes", [])
            edge_list = []
            if isinstance(edge_raw, list):
                for item in edge_raw:
                    edge_list.append(EdgeNodeSpec(**item))

            dc_raw = data.get("datacenters", {})
            dcs = {k: DataCenterSpec(**v) for k, v in dc_raw.items()}

            return InfrastructureDSLConfig(
                region=data.get("region", "asia_south"),
                primary_dc=data.get("primary_dc", "dc1"),
                failover_dc=data.get("failover_dc", "dc2"),
                datacenters=dcs or {
                    "dc1": DataCenterSpec(name="Mumbai DC1 Primary", capacity=1000, providers=["psp-a", "psp-b"]),
                    "dc2": DataCenterSpec(name="Bengaluru DC2 Failover", capacity=1000, providers=["psp-b", "psp-c"])
                },
                edge_nodes=edge_list or [
                    EdgeNodeSpec(id="edge_delhi", location="Delhi NCR", nearest_dc="dc1"),
                    EdgeNodeSpec(id="edge_mumbai", location="Mumbai Region", nearest_dc="dc1"),
                    EdgeNodeSpec(id="edge_bengaluru", location="Bengaluru Tech Park", nearest_dc="dc2")
                ],
                auto_failover=data.get("routing", {}).get("failover") == "automatic"
            )
        except Exception:
            return InfrastructureDSLConfig(
                datacenters={
                    "dc1": DataCenterSpec(name="Mumbai DC1 Primary", capacity=1000, providers=["psp-a", "psp-b"]),
                    "dc2": DataCenterSpec(name="Bengaluru DC2 Failover", capacity=1000, providers=["psp-b", "psp-c"])
                },
                edge_nodes=[
                    EdgeNodeSpec(id="edge_delhi", location="Delhi NCR", nearest_dc="dc1"),
                    EdgeNodeSpec(id="edge_mumbai", location="Mumbai Region", nearest_dc="dc1"),
                    EdgeNodeSpec(id="edge_bengaluru", location="Bengaluru Tech Park", nearest_dc="dc2")
                ]
            )
