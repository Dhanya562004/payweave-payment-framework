"""
PayWeave Functional Core Rules Unit Tests.
Verifies pure monadic transformations, risk evaluation, and adaptive authentication logic.
"""

import pytest
from payweave.dsl.schema import MerchantConfig, AuthMode
from payweave.runtime.functional_core import (
    PaymentRequest, PaymentContext, ProviderHealth, validate_request,
    evaluate_risk, determine_authentication, build_execution_plan, Result
)


@pytest.fixture
def sample_context():
    cfg = MerchantConfig()
    health_map = {
        "psp-a": ProviderHealth("psp-a", 0.985, 140.0, 0.015, True, 0.70, 95.0),
        "psp-b": ProviderHealth("psp-b", 0.990, 110.0, 0.010, True, 0.85, 90.0),
        "psp-c": ProviderHealth("psp-c", 0.965, 220.0, 0.035, True, 0.30, 100.0)
    }
    return PaymentContext(merchant_config=cfg, provider_health_map=health_map)


def test_monadic_result_ok():
    res = Result.ok(42)
    assert res.is_ok is True
    assert res.unwrap() == 42


def test_monadic_result_fail():
    res = Result.fail("Error occurred")
    assert res.is_ok is False
    assert res.error() == "Error occurred"


def test_validate_request_success(sample_context):
    req = PaymentRequest.create(amount=500.0, payment_method="upi", currency="INR")
    res = validate_request(req, sample_context)
    assert res.is_ok is True


def test_validate_request_invalid_method(sample_context):
    req = PaymentRequest.create(amount=500.0, payment_method="crypto")
    res = validate_request(req, sample_context)
    assert res.is_ok is False
    assert "crypto" in res.error()


def test_evaluate_risk_allowed(sample_context):
    req = PaymentRequest.create(amount=100.0, risk_score=0.20)
    res = evaluate_risk(req, sample_context)
    assert res.is_ok is True
    assert res.unwrap().action == "ALLOW"


def test_evaluate_risk_blocked(sample_context):
    req = PaymentRequest.create(amount=100.0, risk_score=0.95)
    res = evaluate_risk(req, sample_context)
    assert res.is_ok is False
    assert "exceeds max allowed threshold" in res.error()


def test_determine_authentication_adaptive_low_risk(sample_context):
    req = PaymentRequest.create(amount=100.0, risk_score=0.10)
    risk_dec = evaluate_risk(req, sample_context).unwrap()
    auth_dec = determine_authentication(req, risk_dec, sample_context)
    assert auth_dec.requires_2fa is False


def test_determine_authentication_adaptive_high_amount(sample_context):
    req = PaymentRequest.create(amount=60000.0, risk_score=0.10)
    risk_dec = evaluate_risk(req, sample_context).unwrap()
    auth_dec = determine_authentication(req, risk_dec, sample_context)
    assert auth_dec.requires_2fa is True


def test_build_execution_plan_pipeline(sample_context):
    req = PaymentRequest.create(amount=1500.0, payment_method="upi")
    plan_res = build_execution_plan(req, sample_context)
    assert plan_res.is_ok is True
    plan = plan_res.unwrap()
    assert plan.routing.selected_provider in ["psp-a", "psp-b", "psp-c"]
    assert len(plan.steps) == 4
