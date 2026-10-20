"""
PayWeave SQLite Database Storage.
Provides persistence for merchant DSL configurations, transaction history,
self-healing audit timelines, anomaly logs, system metrics,
and ACID-consistent payment lifecycles (payments, audit trails, idempotent webhooks, and refunds).
"""

import sqlite3
import json
import time
import hashlib
import threading
from typing import Dict, Any, List, Optional, Tuple
from payweave.dsl.schema import MerchantConfig
from payweave.dsl.parser import DSLParser
from payweave.dsl.validator import DSLValidator
from payweave.runtime.functional_core import PaymentState, transition_payment_state, Result


class PayWeaveDatabase:
    """Local SQLite database manager for PayWeave simulation."""

    def __init__(self, db_path: str = "payweave_local.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._write_lock = threading.Lock()
        self._all_conns: List[sqlite3.Connection] = []
        self._all_conns_lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout = 30000;")
            self._local.conn = conn
            with self._all_conns_lock:
                self._all_conns.append(conn)
        return conn

    def _execute_write(self, write_fn):
        """Executes write_fn inside process write lock with exponential backoff on SQLITE_BUSY."""
        max_retries = 5
        base_backoff = 0.01
        for attempt in range(max_retries):
            try:
                with self._write_lock:
                    return write_fn()
            except sqlite3.OperationalError as e:
                err_str = str(e).lower()
                if ("locked" in err_str or "busy" in err_str) and attempt < max_retries - 1:
                    time.sleep(base_backoff * (2 ** attempt))
                    continue
                raise

    def close(self):
        """Closes all open connections tracked across threads."""
        with self._all_conns_lock:
            for conn in self._all_conns:
                try:
                    conn.close()
                except Exception:
                    pass
            self._all_conns.clear()
        self._local = threading.local()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _init_db(self):
        def _do_init():
            conn = self._get_connection()
            cursor = conn.cursor()
            if self.db_path != ":memory:":
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA synchronous = NORMAL;")
            cursor.execute("PRAGMA busy_timeout = 30000;")
            cursor.execute("PRAGMA cache_size = -64000;")
            cursor.execute("PRAGMA temp_store = MEMORY;")

            # Merchant configs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS merchant_configs (
                    merchant_id TEXT PRIMARY KEY,
                    version TEXT,
                    config_yaml TEXT,
                    updated_at REAL
                )
            """)

            # Merchant config historical versions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS merchant_config_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merchant_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    config_yaml TEXT NOT NULL,
                    comment TEXT,
                    created_by TEXT,
                    created_at REAL NOT NULL,
                    UNIQUE(merchant_id, version)
                )
            """)

            # Legacy transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    request_id TEXT,
                    merchant_id TEXT,
                    amount REAL,
                    currency TEXT,
                    payment_method TEXT,
                    provider_used TEXT,
                    attempted_providers TEXT,
                    retries_count INTEGER,
                    total_latency_ms REAL,
                    status TEXT,
                    status_code TEXT,
                    message TEXT,
                    created_at REAL
                )
            """)

            # Payments table with finite lifecycle states
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id TEXT PRIMARY KEY,
                    idempotency_key TEXT UNIQUE,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provider_used TEXT,
                    refunded_amount REAL DEFAULT 0.0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)

            # Transactional Payment Audit Trail
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id TEXT NOT NULL,
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    created_at REAL NOT NULL
                )
            """)

            # Idempotent Webhook Events Store
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_webhooks (
                    event_id TEXT PRIMARY KEY,
                    payment_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_hash TEXT,
                    processed_at REAL NOT NULL
                )
            """)

            # Refunds Ledger with Cumulative Limits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS refunds (
                    refund_id TEXT PRIMARY KEY,
                    payment_id TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    created_at REAL NOT NULL
                )
            """)

            # Self healing timeline events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS self_healing_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_id TEXT,
                    event_type TEXT,
                    severity TEXT,
                    description TEXT,
                    action_taken TEXT,
                    created_at REAL
                )
            """)

            # Config audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merchant_id TEXT,
                    changed_field TEXT,
                    previous_value TEXT,
                    new_value TEXT,
                    user_role TEXT,
                    updated_at REAL
                )
            """)

            # Indexes for fast concurrency performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payment_audit_trail_payment_id ON payment_audit_trail(payment_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_webhooks_payment_id ON processed_webhooks(payment_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_refunds_payment_id ON refunds(payment_id)")

            conn.commit()

        self._execute_write(_do_init)

    # --- Merchant Configuration Persistence & Versioning ---

    def save_merchant_config(
        self,
        config: MerchantConfig,
        user_role: str = "Merchant Admin",
        comment: str = "Configuration update"
    ) -> None:
        """
        Validates and saves a merchant configuration, creating a versioned snapshot.
        Raises ValueError if configuration fails semantic or schema validation.
        """
        validation_result = DSLValidator.validate_dict(config.model_dump())
        if not validation_result.is_valid:
            error_msgs = [f"{e.field}: {e.message}" for e in validation_result.errors]
            raise ValueError(f"Invalid merchant configuration: {'; '.join(error_msgs)}")

        yaml_content = DSLParser.to_yaml(config)
        now = time.time()
        conn = self._get_connection()

        def _do_save():
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            # 1. Update or insert current active config
            cursor.execute("""
                INSERT OR REPLACE INTO merchant_configs (merchant_id, version, config_yaml, updated_at)
                VALUES (?, ?, ?, ?)
            """, (config.merchant.id, config.version, yaml_content, now))

            # 2. Store historical version snapshot
            cursor.execute("""
                INSERT OR REPLACE INTO merchant_config_versions (
                    merchant_id, version, config_yaml, comment, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (config.merchant.id, config.version, yaml_content, comment, user_role, now))

            # 3. Audit trail
            cursor.execute("""
                INSERT INTO config_audit_log (
                    merchant_id, changed_field, previous_value, new_value, user_role, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (config.merchant.id, "config_version", "active", f"version:{config.version}", user_role, now))
            conn.commit()

        self._execute_write(_do_save)

    def get_merchant_config(
        self,
        merchant_id: str = "merchant_demo",
        version: Optional[str] = None
    ) -> Optional[MerchantConfig]:
        """
        Retrieves active configuration for merchant_id, or a specific historical version if version is provided.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        if version:
            cursor.execute(
                "SELECT config_yaml FROM merchant_config_versions WHERE merchant_id = ? AND version = ?",
                (merchant_id, version)
            )
        else:
            cursor.execute(
                "SELECT config_yaml FROM merchant_configs WHERE merchant_id = ?",
                (merchant_id,)
            )
        row = cursor.fetchone()
        if row:
            config, _ = DSLParser.parse_yaml(row["config_yaml"])
            return config
        return None

    def list_config_versions(self, merchant_id: str = "merchant_demo") -> List[Dict[str, Any]]:
        """
        Lists all recorded configuration versions for a merchant ordered newest first.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT version, comment, created_by, created_at
            FROM merchant_config_versions
            WHERE merchant_id = ?
            ORDER BY created_at DESC
        """, (merchant_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def rollback_merchant_config(
        self,
        merchant_id: str,
        target_version: str,
        user_role: str = "Merchant Admin"
    ) -> MerchantConfig:
        """
        Rolls back the active merchant configuration to target_version.
        Raises ValueError if target_version does not exist.
        """
        conn = self._get_connection()

        def _do_rollback():
            cursor = conn.cursor()
            cursor.execute(
                "SELECT config_yaml FROM merchant_config_versions WHERE merchant_id = ? AND version = ?",
                (merchant_id, target_version)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Version '{target_version}' not found for merchant '{merchant_id}'.")

            yaml_content = row["config_yaml"]
            config, _ = DSLParser.parse_yaml(yaml_content)
            now = time.time()

            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute("""
                INSERT OR REPLACE INTO merchant_configs (merchant_id, version, config_yaml, updated_at)
                VALUES (?, ?, ?, ?)
            """, (merchant_id, target_version, yaml_content, now))

            cursor.execute("""
                INSERT INTO config_audit_log (
                    merchant_id, changed_field, previous_value, new_value, user_role, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (merchant_id, "rollback", "previous_active", f"restored:{target_version}", user_role, now))
            conn.commit()
            return config

        return self._execute_write(_do_rollback)

    # --- Payment State Machine & Lifecycle Persistence ---

    def create_or_get_payment(
        self,
        payment_id: str,
        amount: float,
        currency: str,
        payment_method: str,
        customer_id: str,
        idempotency_key: Optional[str] = None
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Creates a payment record in CREATED state with idempotency protection.
        Returns (payment_dict, is_new).
        """
        now = time.time()
        conn = self._get_connection()

        # Fast-path read check: if idempotency_key already exists, return existing
        if idempotency_key:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE idempotency_key = ?", (idempotency_key,))
            existing = cursor.fetchone()
            if existing:
                return dict(existing), False

        def _do_create():
            cursor = conn.cursor()
            # Double-check idempotency under lock in case of concurrent insert race
            if idempotency_key:
                cursor.execute("SELECT * FROM payments WHERE idempotency_key = ?", (idempotency_key,))
                existing = cursor.fetchone()
                if existing:
                    return dict(existing), False

            try:
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("""
                    INSERT INTO payments (
                        payment_id, idempotency_key, amount, currency, payment_method,
                        customer_id, status, provider_used, refunded_amount, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?)
                """, (payment_id, idempotency_key, amount, currency, payment_method,
                      customer_id, PaymentState.CREATED.value, None, now, now))

                cursor.execute("""
                    INSERT INTO payment_audit_trail (payment_id, from_state, to_state, event_type, details, created_at)
                    VALUES (?, NULL, ?, 'PAYMENT_CREATED', 'Payment initiated via checkout', ?)
                """, (payment_id, PaymentState.CREATED.value, now))

                conn.commit()
            except sqlite3.IntegrityError:
                conn.rollback()
                if idempotency_key:
                    cursor.execute("SELECT * FROM payments WHERE idempotency_key = ?", (idempotency_key,))
                    existing = cursor.fetchone()
                    if existing:
                        return dict(existing), False
                raise
            except Exception:
                conn.rollback()
                raise

            new_record = {
                "payment_id": payment_id,
                "idempotency_key": idempotency_key,
                "amount": amount,
                "currency": currency,
                "payment_method": payment_method,
                "customer_id": customer_id,
                "status": PaymentState.CREATED.value,
                "provider_used": None,
                "refunded_amount": 0.0,
                "created_at": now,
                "updated_at": now
            }
            return new_record, True

        return self._execute_write(_do_create)

    def transition_payment(
        self,
        payment_id: str,
        to_state: PaymentState,
        event_type: str = "STATE_TRANSITION",
        details: str = "",
        provider_used: Optional[str] = None
    ) -> Result[Dict[str, Any], str]:
        """
        Executes an atomic payment state transition guarded by the state machine invariants.
        """
        now = time.time()
        conn = self._get_connection()

        def _do_transition():
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            row = cursor.fetchone()
            if not row:
                return Result.fail(f"Payment with ID {payment_id} does not exist.")

            current_status = PaymentState(row["status"])
            transition_res = transition_payment_state(current_status, to_state)
            if transition_res.is_error:
                return Result.fail(transition_res.error())

            used_p = provider_used or row["provider_used"]
            try:
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("""
                    UPDATE payments
                    SET status = ?, provider_used = ?, updated_at = ?
                    WHERE payment_id = ?
                """, (to_state.value, used_p, now, payment_id))

                cursor.execute("""
                    INSERT INTO payment_audit_trail (payment_id, from_state, to_state, event_type, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (payment_id, current_status.value, to_state.value, event_type, details, now))

                conn.commit()
            except Exception:
                conn.rollback()
                raise

            cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            return Result.ok(dict(cursor.fetchone()))

        return self._execute_write(_do_transition)

    def process_webhook(
        self,
        event_id: str,
        payment_id: str,
        event_type: str,
        new_status: Optional[PaymentState] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Result[Dict[str, Any], str]:
        """
        Idempotent provider callback/webhook processor.
        Validates event ID, ignores duplicates, and ensures states/balances are never changed twice.
        """
        now = time.time()
        payload_str = json.dumps(payload or {}, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        conn = self._get_connection()

        # 1. Fast-path check if event_id has already been processed
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM processed_webhooks WHERE event_id = ?", (event_id,))
        existing_event = cursor.fetchone()
        if existing_event:
            cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            p_row = cursor.fetchone()
            return Result.ok({
                "status": "DUPLICATE_IGNORED",
                "event_id": event_id,
                "payment_id": payment_id,
                "payment": dict(p_row) if p_row else None,
                "message": f"Webhook event {event_id} has already been processed. Ignored duplicate."
            })

        def _do_webhook():
            c = conn.cursor()
            c.execute("SELECT * FROM processed_webhooks WHERE event_id = ?", (event_id,))
            existing_event = c.fetchone()
            if existing_event:
                c.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
                p_row = c.fetchone()
                return Result.ok({
                    "status": "DUPLICATE_IGNORED",
                    "event_id": event_id,
                    "payment_id": payment_id,
                    "payment": dict(p_row) if p_row else None,
                    "message": f"Webhook event {event_id} has already been processed. Ignored duplicate."
                })

            # Check if target payment exists
            c.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            p_row = c.fetchone()
            if not p_row:
                return Result.fail(f"Target payment {payment_id} not found for webhook.")

            # Transition payment state if requested
            if new_status:
                current_status = PaymentState(p_row["status"])
                if current_status == new_status:
                    details = f"Webhook {event_id} confirmed existing state {new_status.value}."
                else:
                    trans_res = transition_payment_state(current_status, new_status)
                    if trans_res.is_error:
                        return Result.fail(f"Webhook state transition failed: {trans_res.error()}")
                    details = f"Webhook {event_id} transitioned state from {current_status.value} to {new_status.value}."
            else:
                details = f"Webhook {event_id} logged event {event_type}."

            try:
                c.execute("BEGIN IMMEDIATE")
                if new_status and current_status != new_status:
                    c.execute("""
                        UPDATE payments SET status = ?, updated_at = ? WHERE payment_id = ?
                    """, (new_status.value, now, payment_id))

                c.execute("""
                    INSERT INTO processed_webhooks (event_id, payment_id, event_type, payload_hash, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (event_id, payment_id, event_type, payload_hash, now))

                c.execute("""
                    INSERT INTO payment_audit_trail (payment_id, from_state, to_state, event_type, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (payment_id, p_row["status"], new_status.value if new_status else p_row["status"],
                      f"WEBHOOK_{event_type}", details, now))

                conn.commit()
            except sqlite3.IntegrityError:
                conn.rollback()
                c.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
                return Result.ok({
                    "status": "DUPLICATE_IGNORED",
                    "event_id": event_id,
                    "payment_id": payment_id,
                    "payment": dict(c.fetchone()),
                    "message": f"Webhook event {event_id} has already been processed. Ignored duplicate."
                })
            except Exception:
                conn.rollback()
                raise

            c.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            return Result.ok({
                "status": "PROCESSED",
                "event_id": event_id,
                "payment_id": payment_id,
                "payment": dict(c.fetchone()),
                "message": f"Webhook {event_id} processed successfully."
            })

        return self._execute_write(_do_webhook)

    def process_refund(
        self,
        refund_id: str,
        payment_id: str,
        amount: float,
        idempotency_key: Optional[str] = None,
        reason: str = "Customer requested refund"
    ) -> Result[Dict[str, Any], str]:
        """
        Processes a refund with strict idempotency and cumulative limit enforcement.
        Rejects refunds exceeding initial captured amount or for non-succeeded payments.
        """
        if amount <= 0:
            return Result.fail("Refund amount must be greater than zero.")

        now = time.time()
        conn = self._get_connection()

        # 1. Fast-path idempotency check on refund
        if idempotency_key:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM refunds WHERE idempotency_key = ?", (idempotency_key,))
            existing_refund = cursor.fetchone()
            if existing_refund:
                return Result.ok({
                    "status": "DUPLICATE_IDEMPOTENT",
                    "refund": dict(existing_refund),
                    "message": "Refund already processed with this idempotency key."
                })

        def _do_refund():
            c = conn.cursor()
            if idempotency_key:
                c.execute("SELECT * FROM refunds WHERE idempotency_key = ?", (idempotency_key,))
                existing_refund = c.fetchone()
                if existing_refund:
                    return Result.ok({
                        "status": "DUPLICATE_IDEMPOTENT",
                        "refund": dict(existing_refund),
                        "message": "Refund already processed with this idempotency key."
                    })

            # Check payment status and capture amount
            c.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            payment = c.fetchone()
            if not payment:
                return Result.fail(f"Payment {payment_id} does not exist.")

            if payment["status"] != PaymentState.SUCCEEDED.value:
                return Result.fail(
                    f"Refunds can only be processed for SUCCEEDED payments. Current status: {payment['status']}."
                )

            current_refunded = payment["refunded_amount"]
            total_amount = payment["amount"]

            # Enforce cumulative refund limit
            if (current_refunded + amount) > (total_amount + 1e-6):
                return Result.fail(
                    f"Cumulative refund amount (₹{current_refunded + amount:.2f}) exceeds total payment captured (₹{total_amount:.2f})."
                )

            new_refunded = current_refunded + amount
            try:
                c.execute("BEGIN IMMEDIATE")
                c.execute("""
                    UPDATE payments SET refunded_amount = ?, updated_at = ? WHERE payment_id = ?
                """, (new_refunded, now, payment_id))

                c.execute("""
                    INSERT INTO refunds (refund_id, payment_id, idempotency_key, amount, status, reason, created_at)
                    VALUES (?, ?, ?, ?, 'COMPLETED', ?, ?)
                """, (refund_id, payment_id, idempotency_key, amount, reason, now))

                c.execute("""
                    INSERT INTO payment_audit_trail (payment_id, from_state, to_state, event_type, details, created_at)
                    VALUES (?, ?, ?, 'REFUND_PROCESSED', ?, ?)
                """, (payment_id, payment["status"], payment["status"],
                      f"Processed refund of ₹{amount:,.2f} ({reason}). Total refunded: ₹{new_refunded:,.2f}.", now))

                conn.commit()
            except sqlite3.IntegrityError:
                conn.rollback()
                if idempotency_key:
                    c.execute("SELECT * FROM refunds WHERE idempotency_key = ?", (idempotency_key,))
                    existing = c.fetchone()
                    if existing:
                        return Result.ok({
                            "status": "DUPLICATE_IDEMPOTENT",
                            "refund": dict(existing),
                            "message": "Refund already processed with this idempotency key."
                        })
                raise
            except Exception:
                conn.rollback()
                raise

            c.execute("SELECT * FROM refunds WHERE refund_id = ?", (refund_id,))
            return Result.ok({
                "status": "COMPLETED",
                "refund": dict(c.fetchone()),
                "total_refunded": new_refunded,
                "message": f"Successfully refunded ₹{amount:,.2f}."
            })

        return self._execute_write(_do_refund)

    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_payment_audit_trail(self, payment_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, payment_id, from_state, to_state, event_type, details, created_at
            FROM payment_audit_trail WHERE payment_id = ? ORDER BY id ASC
        """, (payment_id,))
        return [dict(r) for r in cursor.fetchall()]

    # --- Legacy Transaction History & Self Healing Logs ---

    def log_transaction(self, outcome: Any) -> None:
        now = time.time()
        attempted_str = ",".join(outcome.attempted_providers)
        conn = self._get_connection()

        def _do_log():
            cursor = conn.cursor()
            try:
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, request_id, merchant_id, amount, currency,
                        payment_method, provider_used, attempted_providers, retries_count,
                        total_latency_ms, status, status_code, message, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    outcome.transaction_id,
                    outcome.execution_plan.request.request_id,
                    outcome.execution_plan.request.customer_id,
                    outcome.amount,
                    outcome.currency,
                    outcome.payment_method,
                    outcome.provider_used,
                    attempted_str,
                    outcome.retries_count,
                    outcome.total_latency_ms,
                    "SUCCESS" if outcome.success else ("UNCERTAIN_TIMEOUT" if getattr(outcome, "is_uncertain_timeout", False) else "FAILED"),
                    outcome.status_code,
                    outcome.message,
                    now
                ))
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        self._execute_write(_do_log)

    def log_self_healing_event(self, provider_id: str, event_type: str, severity: str,
                               description: str, action_taken: str) -> None:
        now = time.time()
        conn = self._get_connection()

        def _do_log_event():
            cursor = conn.cursor()
            try:
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("""
                    INSERT INTO self_healing_events (provider_id, event_type, severity, description, action_taken, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (provider_id, event_type, severity, description, action_taken, now))
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        self._execute_write(_do_log_event)

    def get_self_healing_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT provider_id, event_type, severity, description, action_taken, created_at
            FROM self_healing_events ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT merchant_id, changed_field, previous_value, new_value, user_role, updated_at
            FROM config_audit_log ORDER BY updated_at DESC LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_transaction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT transaction_id, request_id, amount, currency, payment_method,
                   provider_used, retries_count, total_latency_ms, status, status_code, created_at
            FROM transactions ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def reset_tables(self) -> None:
        conn = self._get_connection()

        def _do_reset():
            cursor = conn.cursor()
            try:
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("DELETE FROM transactions")
                cursor.execute("DELETE FROM payments")
                cursor.execute("DELETE FROM payment_audit_trail")
                cursor.execute("DELETE FROM processed_webhooks")
                cursor.execute("DELETE FROM refunds")
                cursor.execute("DELETE FROM self_healing_events")
                cursor.execute("DELETE FROM config_audit_log")
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        self._execute_write(_do_reset)
