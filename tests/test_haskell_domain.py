"""
Unit tests for Python reference implementation mirroring Haskell domain logic.
Tests pure functions, explicit Result error returns, ADT behaviors, and decision rules.
"""

import pytest
from payweave.runtime.functional_core import (
    PaymentRequest, PaymentContext, ProviderHealth, Result,
    validate_request, evaluate_risk, build_execution_plan
)
from payweave.dsl.schema import MerchantConfig, AuthMode


def make_context():
    cfg = MerchantConfig()
    health_map = {
        "psp-a": ProviderHealth("psp-a", 0.985, 140.0, 0.015, True, 0.70, 95.0),
        "psp-b": ProviderHealth("psp-b", 0.990, 110.0, 0.010, True, 0.85, 90.0),
        "psp-c": ProviderHealth("psp-c", 0.965, 220.0, 0.035, True, 0.30, 100.0)
    }
    return PaymentContext(merchant_config=cfg, provider_health_map=health_map)


def test_validate_request_valid():
    ctx = make_context()
    req = PaymentRequest.create(amount=100.0, currency="INR", payment_method="upi")
    res = validate_request(req, ctx)
    assert res.is_ok
    assert res.unwrap().is_valid is True


def test_validate_request_invalid_amount():
    ctx = make_context()
    req = PaymentRequest.create(amount=-50.0, currency="INR", payment_method="upi")
    res = validate_request(req, ctx)
    assert res.is_error
    assert "greater than zero" in res.error()


def test_evaluate_risk_allowed():
    ctx = make_context()
    req = PaymentRequest.create(amount=500.0, risk_score=0.10)
    res = evaluate_risk(req, ctx)
    assert res.is_ok
    assert res.unwrap().action == "ALLOW"


def test_evaluate_risk_exceeded():
    ctx = make_context()
    ctx.merchant_config.risk.max_score = 0.30
    req = PaymentRequest.create(amount=500.0, risk_score=0.75)
    res = evaluate_risk(req, ctx)
    assert res.is_error
    assert "Transaction risk score" in res.error()


def test_build_execution_plan_pipeline_success():
    ctx = make_context()
    req = PaymentRequest.create(amount=1200.0, currency="INR", payment_method="upi", risk_score=0.05)
    plan_res = build_execution_plan(req, ctx)
    assert plan_res.is_ok
    plan = plan_res.unwrap()
    assert plan.routing.selected_provider in ["psp-a", "psp-b", "psp-c"]
    assert plan.ready_for_execution is True
