"""
PayWeave Topology Visualizer.
Generates structural Mermaid diagrams and topology graphs of edge nodes, data centers, and PSPs.
"""

from typing import Dict, Any, List
from payweave.infrastructure.infrastructure_dsl import InfrastructureDSLConfig


class TopologyVisualizer:
    """Renders topological infrastructure connections."""

    @staticmethod
    def generate_mermaid(config: InfrastructureDSLConfig) -> str:
        lines = ["graph TD"]
        lines.append("    subgraph Edge Layer")
        for edge in config.edge_nodes:
            status_symbol = "🟢" if edge.status == "healthy" else "🔴"
            lines.append(f"        {edge.id}[\"{status_symbol} {edge.location} ({edge.id})\"]")
        lines.append("    end")

        lines.append("    subgraph Data Center Layer")
        for dc_id, dc in config.datacenters.items():
            is_primary = (dc_id == config.primary_dc)
            tag = "PRIMARY" if is_primary else "FAILOVER"
            status_symbol = "🟢" if dc.status == "healthy" else "🔴 OUTAGE"
            lines.append(f"        {dc_id}[\"{status_symbol} {dc.name} [{tag}] | Cap: {dc.capacity}\"]")
        lines.append("    end")

        lines.append("    subgraph Payment Provider Layer")
        lines.append("        pspa[\"PSP-A Enterprise Gateway\"]")
        lines.append("        pspb[\"PSP-B SpeedPay Express\"]")
        lines.append("        pspc[\"PSP-C ValuePay Direct\"]")
        lines.append("    end")

        # Edge -> DC connections
        for edge in config.edge_nodes:
            lines.append(f"    {edge.id} --> {edge.nearest_dc}")

        # DC -> PSP connections
        for dc_id, dc in config.datacenters.items():
            if dc.status == "healthy":
                for p in dc.providers:
                    pid_clean = p.replace("-", "")
                    lines.append(f"    {dc_id} ==> {pid_clean}")
            else:
                lines.append(f"    {dc_id} -. OUTAGE .-> {config.failover_dc}")

        return "\n".join(lines)
