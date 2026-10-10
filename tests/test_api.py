"""
PayWeave FastAPI REST API Unit Tests.
Uses FastAPI TestClient to test all REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_api_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UP"
    assert data["system"] == "PayWeave Framework"


def test_api_validate_config_valid():
    yaml_payload = """
merchant:
  id: api_merchant
  name: API Test Merchant
payment:
  methods:
    - upi
    - card
"""
    res = client.post("/validate-config", json={"yaml_config": yaml_payload})
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True


def test_api_routing_decision():
    payload = {
        "amount": 2500.0,
        "currency": "INR",
        "payment_method": "upi",
        "customer_id": "cust_test_api",
        "risk_score": 0.15
    }
    res = client.post("/routing/decision", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "selected_provider" in data
    assert "score" in data


def test_api_simulate_payment():
    payload = {
        "amount": 1200.0,
        "payment_method": "upi",
        "currency": "INR",
        "risk_score": 0.10
    }
    res = client.post("/payment/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "transaction_id" in data


def test_api_anomaly_detect():
    res = client.post("/anomaly/detect", json={"inject_anomaly_provider": "psp-a"})
    assert res.status_code == 200
    data = res.json()
    assert "reports" in data


def test_api_infrastructure_simulate():
    res = client.post("/infrastructure/simulate", json={"action": "simulate_dc_failure", "dc_id": "dc1"})
    assert res.status_code == 200
    data = res.json()
    assert data["infrastructure_state"]["active_dc"] == "dc2"

    # Recover DC
    res_rec = client.post("/infrastructure/simulate", json={"action": "recover_dc", "dc_id": "dc1"})
    assert res_rec.status_code == 200


def test_api_metrics_endpoint():
    res = client.get("/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "telemetry_summary" in data
    assert "provider_health" in data


def test_api_providers_list():
    res = client.get("/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) == 3


def test_api_get_and_update_merchant_config():
    res_get = client.get("/merchant/config")
    assert res_get.status_code == 200
    cfg = res_get.json()
    
    cfg["merchant"]["name"] = "Updated API Merchant Name"
    res_post = client.post("/merchant/config", json=cfg)
    assert res_post.status_code == 200
    assert res_post.json()["config"]["merchant"]["name"] == "Updated API Merchant Name"


def test_api_create_payment_and_idempotency():
    import uuid
    idem_key = f"idem_api_{uuid.uuid4().hex}"
    res = client.post("/payment/create", json={
        "amount": 1999.0,
        "currency": "INR",
        "payment_method": "upi",
        "customer_id": "cust_api_10",
        "idempotency_key": idem_key
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_new"] is True
    p_id = data["payment"]["payment_id"]

    # Duplicate call with identical key
    res_dup = client.post("/payment/create", json={
        "amount": 1999.0,
        "currency": "INR",
        "payment_method": "upi",
        "customer_id": "cust_api_10",
        "idempotency_key": idem_key
    })
    assert res_dup.status_code == 200
    assert res_dup.json()["is_new"] is False
    assert res_dup.json()["payment"]["payment_id"] == p_id


def test_api_webhook_and_audit_trail():
    import uuid
    create_res = client.post("/payment/create", json={
        "amount": 2500.0,
        "currency": "INR",
        "payment_method": "upi",
        "customer_id": "cust_api_20"
    })
    p_id = create_res.json()["payment"]["payment_id"]

    # Transition to PENDING first
    from api import engine
    from payweave.runtime.functional_core import PaymentState
    engine.db.transition_payment(p_id, PaymentState.PENDING)

    evt_id = f"evt_api_{uuid.uuid4().hex}"
    # Deliver webhook
    wh_res = client.post("/payment/webhook", json={
        "event_id": evt_id,
        "payment_id": p_id,
        "event_type": "PAYMENT_CAPTURED",
        "new_status": "SUCCEEDED"
    })
    assert wh_res.status_code == 200
    assert wh_res.json()["status"] == "PROCESSED"

    # Redeliver duplicate webhook
    wh_dup = client.post("/payment/webhook", json={
        "event_id": evt_id,
        "payment_id": p_id,
        "event_type": "PAYMENT_CAPTURED",
        "new_status": "SUCCEEDED"
    })
    assert wh_dup.status_code == 200
    assert wh_dup.json()["status"] == "DUPLICATE_IGNORED"

    # Fetch payment details and audit trail
    get_res = client.get(f"/payment/{p_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["payment"]["status"] == "SUCCEEDED"
    assert len(data["audit_trail"]) >= 3


def test_api_refund_and_cumulative_limits():
    import uuid
    create_res = client.post("/payment/create", json={
        "amount": 3000.0,
        "currency": "INR",
        "payment_method": "card",
        "customer_id": "cust_api_30"
    })
    p_id = create_res.json()["payment"]["payment_id"]
    from api import engine
    from payweave.runtime.functional_core import PaymentState
    engine.db.transition_payment(p_id, PaymentState.PENDING)
    engine.db.transition_payment(p_id, PaymentState.SUCCEEDED)

    ref_idem = f"ref_idem_{uuid.uuid4().hex}"
    # Partial refund
    ref_res = client.post("/payment/refund", json={
        "payment_id": p_id,
        "amount": 1000.0,
        "idempotency_key": ref_idem,
        "reason": "customer_return"
    })
    assert ref_res.status_code == 200
    assert ref_res.json()["status"] == "COMPLETED"
    assert ref_res.json()["total_refunded"] == 1000.0

    # Over-refund exceeding remaining 2000
    ref_over = client.post("/payment/refund", json={
        "payment_id": p_id,
        "amount": 2500.0,
        "reason": "excess_refund"
    })
    assert ref_over.status_code == 400
    assert "exceeds total payment" in ref_over.json()["detail"]
