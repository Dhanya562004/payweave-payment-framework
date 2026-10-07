"""
PayWeave Execution Plan Visualizer & Serializer.
Formally represents payment execution steps, dependency order, timeline, and step outputs.
"""

from typing import Dict, Any, List
from payweave.runtime.functional_core import PaymentExecutionPlan, ExecutionStep


class ExecutionPlanFormatter:
    """Utilities for serializing and rendering execution plans."""

    @staticmethod
    def to_dict(plan: PaymentExecutionPlan) -> Dict[str, Any]:
        return {
            "request_id": plan.request.request_id,
            "amount": plan.request.amount,
            "currency": plan.request.currency,
            "method": plan.request.payment_method,
            "customer_id": plan.request.customer_id,
            "risk_score": plan.request.risk_score,
            "requires_2fa": plan.auth.requires_2fa,
            "selected_provider": plan.routing.selected_provider,
            "fallback_providers": plan.routing.fallback_chain,
            "routing_score": round(plan.routing.score, 4),
            "routing_rationale": plan.routing.rationale,
            "estimated_latency_ms": plan.estimated_latency_ms,
            "ready_for_execution": plan.ready_for_execution,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status,
                    "details": s.details,
                    "timestamp": s.timestamp
                }
                for s in plan.steps
            ]
        }

    @staticmethod
    def to_mermaid(plan: PaymentExecutionPlan) -> str:
        """Generates a Mermaid graph diagram representing the execution flow."""
        lines = ["graph TD"]
        lines.append(f"    Start([Request: {plan.request.request_id}]) --> Val[Validate DSL & Request]")
        lines.append(f"    Val --> Risk[Evaluate Risk: {plan.risk.risk_score:.2f}]")
        
        if plan.auth.requires_2fa:
            lines.append("    Risk --> Auth[2FA Step-up Required]")
            lines.append("    Auth --> Route[Intelligent Router]")
        else:
            lines.append("    Risk --> Route[Intelligent Router]")

        lines.append(f"    Route --> PSP[Execute via {plan.routing.selected_provider.upper()}]")
        
        if plan.routing.fallback_chain:
            fb_list = " -> ".join([p.upper() for p in plan.routing.fallback_chain[:2]])
            lines.append(f"    PSP -. Fallback .-> FB[{fb_list}]")
        
        lines.append("    PSP --> Done([Payment Result])")
        return "\n".join(lines)
