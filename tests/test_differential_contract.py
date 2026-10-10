"""
PayWeave Differential & Contract Parity Test Suite.
Validates parity between the formal Haskell domain specification and the Python reference runtime
using shared declarative JSON fixtures in tests/fixtures/.
"""

import os
import json
import pytest
from payweave.runtime.functional_core import (
    PaymentRequest, PaymentContext, ProviderHealth, Result,
    PaymentState, transition_payment_state, is_retry_eligible,
    validate_request, build_execution_plan, evaluate_routing
)
from payweave.dsl.schema import MerchantConfig


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(filename: str):
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_contract_validation_parity():
    """Verify validation contract matches between Python runtime and specification."""
    cases = load_fixture("validation_contracts.json")
    cfg = MerchantConfig()
    health_map = {
        "psp-a": ProviderHealth("psp-a", 0.985, 140.0, 0.015, True, 0.70, 95.0)
    }
    ctx = PaymentContext(merchant_config=cfg, provider_health_map=health_map)

    for case in cases:
        req_data = case["request"]
        req = PaymentRequest(
            request_id=f"diff_{case['id']}",
            amount=req_data["amount"],
            currency=req_data["currency"],
            payment_method=req_data["payment_method"],
            customer_id=req_data["customer_id"],
            risk_score=req_data["risk_score"]
        )
        res = validate_request(req, ctx)
        if case["expected_valid"]:
            assert res.is_ok, f"Case {case['id']} expected valid, but got error: {res.error()}"
        else:
            assert res.is_error, f"Case {case['id']} expected failure, but passed"
            expected_needle = case["expected_error_contains"]
            if expected_needle:
                assert expected_needle.lower() in res.error().lower(), (
                    f"Case {case['id']}: expected error containing '{expected_needle}', got '{res.error()}'"
                )


def test_contract_routing_parity():
    """Verify provider routing decisions match specification contracts."""
    cases = load_fixture("routing_contracts.json")
    cfg = MerchantConfig()

    for case in cases:
        health_map = {
            pid: ProviderHealth(
                provider_id=pid,
                success_rate=p["success_rate"],
                latency_ms=p["latency_ms"],
                error_rate=1.0 - p["success_rate"],
                is_healthy=p["is_healthy"],
                cost_score=p["cost_score"],
                capacity_pct=p["capacity_pct"],
                circuit_breaker=p.get("circuit_breaker", "CLOSED")
            )
            for pid, p in case["providers"].items()
        }
        ctx = PaymentContext(merchant_config=cfg, provider_health_map=health_map)
        req = PaymentRequest.create(amount=1000.0, currency="INR", payment_method="upi")

        res = evaluate_routing(req, ctx)
        if case["expected_success"]:
            assert res.is_ok, f"Case {case['id']} expected routing success, got: {res.error()}"
            selected = res.unwrap().selected_provider
            assert selected == case["expected_selected_provider"], (
                f"Case {case['id']}: expected provider '{case['expected_selected_provider']}', got '{selected}'"
            )
        else:
            assert res.is_error, f"Case {case['id']} expected failure, but succeeded with {res.unwrap().selected_provider}"
            if case["expected_error"]:
                assert case["expected_error"].lower() in res.error().lower(), (
                    f"Case {case['id']}: expected error '{case['expected_error']}', got '{res.error()}'"
                )


def test_contract_state_machine_matrix():
    """Verify finite state machine transition matrix."""
    cases = load_fixture("state_machine_contracts.json")
    for case in cases:
        from_st = PaymentState(case["from"])
        to_st = PaymentState(case["to"])
        res = transition_payment_state(from_st, to_st)
        if case["valid"]:
            assert res.is_ok, f"Transition {case['from']} -> {case['to']} should be valid, but failed: {res.error()}"
            assert res.unwrap() == to_st
        else:
            assert res.is_error, f"Transition {case['from']} -> {case['to']} should be invalid, but succeeded"


def test_contract_retry_eligibility():
    """Verify retry eligibility contracts distinguishing transient and permanent errors."""
    cases = load_fixture("retry_contracts.json")
    for case in cases:
        err_msg = case["error_message"]
        expected_eligibility = case["is_retry_eligible"]
        actual = is_retry_eligible(err_msg)
        assert actual == expected_eligibility, (
            f"Retry mismatch for '{err_msg}': expected {expected_eligibility}, got {actual}"
        )
