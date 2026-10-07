"""
PayWeave Aggregations.
Generates tabular dataframes and comparison matrices for provider benchmarking.
"""

from typing import List, Dict, Any
import pandas as pd


class AnalyticsAggregator:
    """Utilities for converting telemetry streams into Pandas DataFrames for visualization."""

    @staticmethod
    def build_provider_comparison_df(health_map: Dict[str, Any]) -> pd.DataFrame:
        data = []
        for pid, h in health_map.items():
            succ = getattr(h, "success_rate", 0.95) * 100
            lat = getattr(h, "latency_ms", 150)
            cost = getattr(h, "cost_score", 0.5)
            cap = getattr(h, "capacity_pct", 100)
            healthy = getattr(h, "is_healthy", True)

            data.append({
                "Provider": pid.upper(),
                "Status": "HEALTHY 🟢" if healthy else "DEGRADED 🔴",
                "Success Rate (%)": f"{succ:.1f}%",
                "Avg Latency (ms)": f"{lat:.0f}ms",
                "Cost Score": f"{cost:.2f}",
                "Capacity (%)": f"{cap:.0f}%"
            })
        return pd.DataFrame(data)

    @staticmethod
    def build_transaction_timeline_df(telemetry_records: List[Dict[str, Any]]) -> pd.DataFrame:
        if not telemetry_records:
            return pd.DataFrame()
        return pd.DataFrame(telemetry_records)
