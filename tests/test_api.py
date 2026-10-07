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
