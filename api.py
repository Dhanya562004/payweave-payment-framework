"""
PayWeave FastAPI REST API Application.
Provides RESTful endpoints for DSL validation, intelligent routing, payment simulation,
anomaly detection, multi-DC infrastructure simulation, and live metrics.
"""

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import time

from payweave.dsl.schema import MerchantConfig
from payweave.dsl.parser import DSLParser
from payweave.dsl.validator import DSLValidator
from payweave.runtime.engine import PayWeaveEngine
from payweave.runtime.functional_core import PaymentRequest
from payweave.anomaly.detector import AnomalyDetector
from payweave.anomaly.simulator import TelemetrySimulator
from payweave.infrastructure.multi_dc import MultiDCSimulator
from payweave.analytics.metrics import MetricsCollector

app = FastAPI(
    title="PayWeave Declarative Payment & Infrastructure API",
    description="RESTful API endpoints for the PayWeave payment application framework simulation.",
    version="1.0.0"
)

# Global engine singleton instance
engine = PayWeaveEngine()
multi_dc_sim = MultiDCSimulator()
anomaly_detector = AnomalyDetector()


# Request / Response Schemas
class ValidateConfigRequest(BaseModel):
    yaml_config: str = Field(..., description="YAML DSL string to parse and validate")


class RoutingDecisionRequest(BaseModel):
    amount: float = Field(default=1500.0, gt=0)
    currency: str = Field(default="INR")
    payment_method: str = Field(default="upi")
    customer_id: str = Field(default="cust_api_demo")
    risk_score: float = Field(default=0.10, ge=0.0, le=1.0)


class PaymentSimulateRequest(BaseModel):
    amount: float = Field(default=2500.0, gt=0)
    currency: str = Field(default="INR")
    payment_method: str = Field(default="upi")
    customer_id: str = Field(default="cust_sim")
    risk_score: float = Field(default=0.15, ge=0.0, le=1.0)
    simulate_failure_provider: Optional[str] = Field(default=None, description="Force provider failure for testing")


class AnomalyDetectRequest(BaseModel):
    telemetry_records: Optional[List[Dict[str, Any]]] = Field(default=None)
    inject_anomaly_provider: Optional[str] = Field(default=None)


class InfraSimulateRequest(BaseModel):
    action: str = Field(..., description="simulate_dc_failure or recover_dc")
    dc_id: str = Field(default="dc1", description="Target data center ID")


# Endpoints

@app.get("/health", summary="System Health Check")
def health_check():
    return {
        "status": "UP",
        "system": "PayWeave Framework",
        "timestamp": time.time(),
        "routing_engine": "Intelligent",
        "self_healing": "Active"
    }


@app.post("/validate-config", summary="Validate Merchant YAML DSL")
def validate_config(body: ValidateConfigRequest):
    config, val_res = DSLParser.parse_yaml(body.yaml_config)
    return {
        "is_valid": val_res.is_valid,
        "errors": [e.to_dict() for e in val_res.errors],
        "warnings": [w.to_dict() for w in val_res.warnings],
        "parsed_config": config.model_dump() if val_res.is_valid else None
    }


@app.post("/routing/decision", summary="Get Intelligent Routing Decision")
def get_routing_decision(body: RoutingDecisionRequest):
    req = PaymentRequest.create(
        amount=body.amount,
        currency=body.currency,
        payment_method=body.payment_method,
        customer_id=body.customer_id,
        risk_score=body.risk_score
    )
    plan_res = engine.generate_plan(req)
    if plan_res.is_error:
        raise HTTPException(status_code=400, detail=plan_res.error())
    
    plan = plan_res.unwrap()
    return {
        "request_id": plan.request.request_id,
        "selected_provider": plan.routing.selected_provider,
        "fallback_chain": plan.routing.fallback_chain,
        "score": plan.routing.score,
        "rationale": plan.routing.rationale,
        "requires_2fa": plan.auth.requires_2fa,
        "estimated_latency_ms": plan.estimated_latency_ms
    }


@app.post("/payment/simulate", summary="Simulate Payment Request Execution")
def simulate_payment(body: PaymentSimulateRequest):
    try:
        outcome = engine.process_payment(
            amount=body.amount,
            payment_method=body.payment_method,
            currency=body.currency,
            customer_id=body.customer_id,
            risk_score=body.risk_score,
            simulate_failure_provider=body.simulate_failure_provider
        )
        return {
            "success": outcome.success,
            "transaction_id": outcome.transaction_id,
            "amount": outcome.amount,
            "currency": outcome.currency,
            "payment_method": outcome.payment_method,
            "provider_used": outcome.provider_used,
            "attempted_providers": outcome.attempted_providers,
            "retries_count": outcome.retries_count,
            "total_latency_ms": outcome.total_latency_ms,
            "status_code": outcome.status_code,
            "message": outcome.message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/payment/flow", summary="Generate Visual Flow Graph")
def generate_payment_flow(config: MerchantConfig = Body(...)):
    nodes = DSLParser.config_to_flow_nodes(config)
    return {"flow_nodes": nodes}


@app.post("/anomaly/detect", summary="Run Telemetry Anomaly Detection")
def detect_anomalies(body: AnomalyDetectRequest):
    records = body.telemetry_records
    if not records:
        records = TelemetrySimulator.generate_telemetry_stream(
            num_records=40, inject_anomaly_provider=body.inject_anomaly_provider
        )
    
    reports = anomaly_detector.detect_batch_anomalies(records)
    return {
        "anomalies_found": any(r.anomaly_detected for r in reports),
        "reports": [r.to_dict() for r in reports]
    }


@app.post("/infrastructure/simulate", summary="Simulate Multi-DC Outage & Failover")
def simulate_infrastructure(body: InfraSimulateRequest):
    if body.action == "simulate_dc_failure":
        res = multi_dc_sim.simulate_dc_failure(body.dc_id)
    elif body.action == "recover_dc":
        res = multi_dc_sim.recover_dc(body.dc_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use simulate_dc_failure or recover_dc.")
    
    return {
        "event_result": res,
        "infrastructure_state": multi_dc_sim.get_dc_status_summary()
    }


@app.get("/metrics", summary="Get Live System Metrics Summary")
def get_metrics():
    tx_history = engine.db.get_transaction_history(limit=100)
    summary = MetricsCollector.compute_summary(tx_history)
    health_map = engine.get_provider_health_map()
    return {
        "telemetry_summary": summary,
        "provider_health": {
            pid: {
                "success_rate": h.success_rate,
                "latency_ms": h.latency_ms,
                "error_rate": h.error_rate,
                "is_healthy": h.is_healthy,
                "cost_score": h.cost_score,
                "capacity_pct": h.capacity_pct
            }
            for pid, h in health_map.items()
        }
    }


@app.get("/providers", summary="Get Configured PSP Adapters")
def get_providers():
    return [
        {"id": "psp-a", "name": "PSP-A Enterprise Gateway", "default_success_rate": 0.985, "cost_score": 0.70},
        {"id": "psp-b", "name": "PSP-B SpeedPay Express", "default_success_rate": 0.990, "cost_score": 0.85},
        {"id": "psp-c", "name": "PSP-C ValuePay Direct", "default_success_rate": 0.965, "cost_score": 0.30}
    ]


@app.get("/merchant/config", summary="Get Active Merchant DSL Config")
def get_merchant_config():
    return engine.config.model_dump()


@app.post("/merchant/config", summary="Update Active Merchant DSL Config")
def update_merchant_config(config: MerchantConfig):
    val_res = DSLValidator.validate_dict(config.model_dump())
    if not val_res.is_valid:
        raise HTTPException(status_code=422, detail=[e.to_dict() for e in val_res.errors])
    engine.reload_config(config)
    return {"message": "Merchant DSL configuration updated successfully.", "config": engine.config.model_dump()}
