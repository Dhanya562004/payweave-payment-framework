"""
PayWeave SQLite Database Storage.
Provides persistence for merchant DSL configurations, transaction history,
self-healing audit timelines, anomaly logs, and system metrics.
"""

import sqlite3
import json
import time
from typing import Dict, Any, List, Optional
from payweave.dsl.schema import MerchantConfig
from payweave.dsl.parser import DSLParser


class PayWeaveDatabase:
    """Local SQLite database manager for PayWeave simulation."""

    def __init__(self, db_path: str = "payweave_local.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Merchant configs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS merchant_configs (
                    merchant_id TEXT PRIMARY KEY,
                    version TEXT,
                    config_yaml TEXT,
                    updated_at REAL
                )
            """)

            # Transactions table
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

            conn.commit()

    def save_merchant_config(self, config: MerchantConfig, user_role: str = "Merchant Admin") -> None:
        yaml_content = DSLParser.to_yaml(config)
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO merchant_configs (merchant_id, version, config_yaml, updated_at)
                VALUES (?, ?, ?, ?)
            """, (config.merchant.id, config.version, yaml_content, now))
            
            cursor.execute("""
                INSERT INTO config_audit_log (merchant_id, changed_field, previous_value, new_value, user_role, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (config.merchant.id, "full_config", "previous_version", config.merchant.name, user_role, now))
            conn.commit()

    def get_merchant_config(self, merchant_id: str = "merchant_demo") -> Optional[MerchantConfig]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT config_yaml FROM merchant_configs WHERE merchant_id = ?", (merchant_id,))
            row = cursor.fetchone()
            if row:
                config, _ = DSLParser.parse_yaml(row["config_yaml"])
                return config
        return None

    def log_transaction(self, outcome: Any) -> None:
        now = time.time()
        attempted_str = ",".join(outcome.attempted_providers)
        with self._get_connection() as conn:
            cursor = conn.cursor()
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
                "SUCCESS" if outcome.success else "FAILED",
                outcome.status_code,
                outcome.message,
                now
            ))
            conn.commit()

    def log_self_healing_event(self, provider_id: str, event_type: str, severity: str,
                               description: str, action_taken: str) -> None:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO self_healing_events (provider_id, event_type, severity, description, action_taken, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (provider_id, event_type, severity, description, action_taken, now))
            conn.commit()

    def get_self_healing_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT provider_id, event_type, severity, description, action_taken, created_at
                FROM self_healing_events ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT merchant_id, changed_field, previous_value, new_value, user_role, updated_at
                FROM config_audit_log ORDER BY updated_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_transaction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT transaction_id, request_id, amount, currency, payment_method,
                       provider_used, retries_count, total_latency_ms, status, status_code, created_at
                FROM transactions ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def reset_tables(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM self_healing_events")
            cursor.execute("DELETE FROM config_audit_log")
            conn.commit()
