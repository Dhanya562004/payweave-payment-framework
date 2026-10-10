"""
PayWeave Phase 5 Payment Lifecycle & Webhook Idempotency Tests.
Validates state machine transitions (CREATED -> PENDING -> SUCCEEDED/FAILED/UNCERTAIN_TIMEOUT),
idempotent payment creation, duplicate webhook deduplication, cumulative refund limits,
and transaction audit trails in SQLite.
"""

import pytest
import uuid
from payweave.storage.database import PayWeaveDatabase
from payweave.runtime.functional_core import PaymentState


@pytest.fixture
def db(tmp_path):
    db_file = str(tmp_path / "test_lifecycle.db")
    return PayWeaveDatabase(db_path=db_file)


def test_payment_creation_and_idempotency(db):
    idem_key = f"idem_{uuid.uuid4().hex}"
    p_id_1 = f"pay_{uuid.uuid4().hex[:8]}"

    # First creation
    payment, is_new = db.create_or_get_payment(
        payment_id=p_id_1,
        amount=1000.0,
        currency="INR",
        payment_method="upi",
        customer_id="cust_test",
        idempotency_key=idem_key
    )
    assert is_new is True
    assert payment["payment_id"] == p_id_1
    assert payment["status"] == PaymentState.CREATED.value

    # Second creation with identical idempotency key
    p_id_2 = f"pay_{uuid.uuid4().hex[:8]}"
    dup_payment, is_new_dup = db.create_or_get_payment(
        payment_id=p_id_2,
        amount=1000.0,
        currency="INR",
        payment_method="upi",
        customer_id="cust_test",
        idempotency_key=idem_key
    )
    assert is_new_dup is False
    assert dup_payment["payment_id"] == p_id_1
    assert dup_payment["idempotency_key"] == idem_key


def test_valid_state_transitions_and_audit_trail(db):
    p_id = f"pay_{uuid.uuid4().hex[:8]}"
    db.create_or_get_payment(
        payment_id=p_id,
        amount=2500.0,
        currency="INR",
        payment_method="card",
        customer_id="cust_test"
    )

    # CREATED -> PENDING
    r1 = db.transition_payment(p_id, PaymentState.PENDING, event_type="SUBMITTED_TO_GATEWAY", details="Routing to PSP-B")
    assert r1.is_ok
    assert r1.unwrap()["status"] == PaymentState.PENDING.value

    # PENDING -> SUCCEEDED
    r2 = db.transition_payment(p_id, PaymentState.SUCCEEDED, event_type="GATEWAY_CONFIRMED", details="Capture success")
    assert r2.is_ok
    assert r2.unwrap()["status"] == PaymentState.SUCCEEDED.value

    # Check audit trail
    trail = db.get_payment_audit_trail(p_id)
    assert len(trail) == 3
    assert trail[0]["event_type"] == "PAYMENT_CREATED"
    assert trail[1]["event_type"] == "SUBMITTED_TO_GATEWAY"
    assert trail[2]["event_type"] == "GATEWAY_CONFIRMED"


def test_invalid_state_transition_rejected(db):
    p_id = f"pay_{uuid.uuid4().hex[:8]}"
    db.create_or_get_payment(
        payment_id=p_id,
        amount=500.0,
        currency="INR",
        payment_method="upi",
        customer_id="cust_test"
    )

    # CREATED -> SUCCEEDED is illegal (cannot bypass PENDING)
    r_inv = db.transition_payment(p_id, PaymentState.SUCCEEDED, event_type="ILLEGAL_JUMP")
    assert r_inv.is_error
    assert "Invalid payment state transition" in r_inv.error()


def test_timeout_modeled_as_uncertain_and_webhook_resolution(db):
    p_id = f"pay_{uuid.uuid4().hex[:8]}"
    db.create_or_get_payment(p_id, 1500.0, "INR", "upi", "cust_test")
    db.transition_payment(p_id, PaymentState.PENDING)

    # Upstream timed out: transition to UNCERTAIN_TIMEOUT (not failure)
    r_timeout = db.transition_payment(
        p_id,
        PaymentState.UNCERTAIN_TIMEOUT,
        event_type="GATEWAY_TIMEOUT",
        details="Socket timed out at 3000ms. Outcome uncertain."
    )
    assert r_timeout.is_ok
    assert r_timeout.unwrap()["status"] == PaymentState.UNCERTAIN_TIMEOUT.value

    # Later async webhook confirms success
    webhook_res = db.process_webhook(
        event_id="evt_cb_timeout_resolved",
        payment_id=p_id,
        event_type="ASYNC_CAPTURE_SUCCESS",
        new_status=PaymentState.SUCCEEDED
    )
    assert webhook_res.is_ok
    assert webhook_res.unwrap()["status"] == "PROCESSED"
    assert webhook_res.unwrap()["payment"]["status"] == PaymentState.SUCCEEDED.value


def test_idempotent_webhook_deduplication(db):
    p_id = f"pay_{uuid.uuid4().hex[:8]}"
    db.create_or_get_payment(p_id, 2000.0, "INR", "upi", "cust_test")
    db.transition_payment(p_id, PaymentState.PENDING)

    evt_id = "evt_capture_1001"
    # First delivery of webhook
    w1 = db.process_webhook(
        event_id=evt_id,
        payment_id=p_id,
        event_type="PAYMENT_CAPTURED",
        new_status=PaymentState.SUCCEEDED
    )
    assert w1.is_ok
    assert w1.unwrap()["status"] == "PROCESSED"

    # Second delivery with identical event ID
    w2 = db.process_webhook(
        event_id=evt_id,
        payment_id=p_id,
        event_type="PAYMENT_CAPTURED",
        new_status=PaymentState.SUCCEEDED
    )
    assert w2.is_ok
    assert w2.unwrap()["status"] == "DUPLICATE_IGNORED"

    # Verify audit trail contains exactly 1 webhook entry
    trail = db.get_payment_audit_trail(p_id)
    webhook_entries = [t for t in trail if "WEBHOOK" in t["event_type"]]
    assert len(webhook_entries) == 1


def test_refunds_and_cumulative_limit_enforcement(db):
    p_id = f"pay_{uuid.uuid4().hex[:8]}"
    db.create_or_get_payment(p_id, 5000.0, "INR", "card", "cust_test")
    db.transition_payment(p_id, PaymentState.PENDING)
    db.transition_payment(p_id, PaymentState.SUCCEEDED)

    # 1. Partial refund 1 (₹2,000)
    ref1 = db.process_refund("ref_1", p_id, 2000.0, idempotency_key="ref_idem_1", reason="Partial return")
    assert ref1.is_ok
    assert ref1.unwrap()["status"] == "COMPLETED"
    assert ref1.unwrap()["total_refunded"] == 2000.0

    # 2. Duplicate refund request with same idempotency key
    ref1_dup = db.process_refund("ref_1_dup", p_id, 2000.0, idempotency_key="ref_idem_1")
    assert ref1_dup.is_ok
    assert ref1_dup.unwrap()["status"] == "DUPLICATE_IDEMPOTENT"

    # 3. Partial refund 2 (₹3,000) - hits exactly 100% cap
    ref2 = db.process_refund("ref_2", p_id, 3000.0, idempotency_key="ref_idem_2")
    assert ref2.is_ok
    assert ref2.unwrap()["total_refunded"] == 5000.0

    # 4. Over-refund attempt (₹500 more) - must be rejected
    ref_over = db.process_refund("ref_over", p_id, 500.0)
    assert ref_over.is_error
    assert "Cumulative refund amount" in ref_over.error()


def test_refund_on_pending_or_failed_payment_rejected(db):
    p_id = f"pay_{uuid.uuid4().hex[:8]}"
    db.create_or_get_payment(p_id, 1000.0, "INR", "upi", "cust_test")
    # Payment is in CREATED status
    ref = db.process_refund("ref_bad", p_id, 500.0)
    assert ref.is_error
    assert "only be processed for SUCCEEDED payments" in ref.error()
