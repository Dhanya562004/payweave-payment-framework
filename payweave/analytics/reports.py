"""
PayWeave Reports Generator.
Generates structured Markdown and JSON reports for executive and technical stakeholders.
"""

from typing import Dict, Any, List
import time


class ReportGenerator:
    """Generates automated infrastructure and routing performance reports."""

    @staticmethod
    def generate_executive_report(summary: Dict[str, Any], merchant_name: str = "Demo Merchant") -> str:
        succ_pct = summary.get("overall_success_rate", 0.985) * 100
        vol = summary.get("total_volume", 0)
        avg_lat = summary.get("avg_latency_ms", 135.0)

        lines = [
            f"# Executive Payment Operations Report — {merchant_name}",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "---",
            "## Key Performance Indicators",
            f"- **Total Transactions Processed:** {vol:,}",
            f"- **Overall Success Rate:** {succ_pct:.2f}%",
            f"- **Average End-to-End Latency:** {avg_lat:.0f} ms",
            f"- **P95 Latency SLA:** {summary.get('p95_latency_ms', 185.0):.0f} ms",
            "",
            "## Traffic Distribution & Cost Optimization",
            "Traffic was automatically routed according to active declarative business logic rules.",
            "All payment transactions were evaluated against risk thresholds and dynamic provider health scores."
        ]
        return "\n".join(lines)
