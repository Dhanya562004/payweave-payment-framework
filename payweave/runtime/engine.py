"""
PayWeave Core Engine.
Coordinates declarative DSL configuration, functional execution core,
intelligent routing, self-healing, anomaly detection, and SQLite persistence.
"""

from typing import Dict, Any, List, Optional
import time
from payweave.dsl.schema import MerchantConfig
from payweave.dsl.parser import DSLParser
from payweave.runtime.functional_core import (
    PaymentRequest, PaymentContext, ProviderHealth, build_execution_plan, Result
)
from payweave.runtime.payment_logic import PaymentProcessor, ProcessingOutcome
from payweave.providers.mock_psp_a import MockPSPAdapterA
from payweave.providers.mock_psp_b import MockPSPAdapterB
from payweave.providers.mock_psp_c import MockPSPAdapterC
from payweave.routing.provider_health import ProviderHealthTracker
from payweave.routing.self_healing import SelfHealingEngine
from payweave.storage.database import PayWeaveDatabase


class PayWeaveEngine:
    """Master PayWeave Runtime Engine."""

    def __init__(self, config: MerchantConfig = None, db_path: str = "payweave_local.db"):
        self.config = config or MerchantConfig()
        self.db = PayWeaveDatabase(db_path=db_path)
        
        # Instantiate provider adapters
        self.providers = {
            "psp-a": MockPSPAdapterA(),
            "psp-b": MockPSPAdapterB(),
            "psp-c": MockPSPAdapterC()
        }
        
        self.health_tracker = ProviderHealthTracker(self.providers)
        self.self_healing = SelfHealingEngine(self.health_tracker)
        self.processor = PaymentProcessor(self.providers, health_tracker=self.health_tracker)

    def reload_config(self, config: MerchantConfig) -> None:
        """Reloads active merchant DSL configuration."""
        self.config = config
        self.db.save_merchant_config(config)

    def get_provider_health_map(self) -> Dict[str, ProviderHealth]:
        """Fetches current live health metrics for all configured providers."""
        return self.health_tracker.get_health_map()

    def create_payment_context(self) -> PaymentContext:
        """Constructs immutable payment context with current health metrics & config."""
        health_map = self.get_provider_health_map()
        return PaymentContext(
            merchant_config=self.config,
            provider_health_map=health_map,
            timestamp=time.time()
        )

    def generate_plan(self, req: PaymentRequest) -> Result:
        """Generates immutable payment execution plan using functional core pipeline."""
        ctx = self.create_payment_context()
        return build_execution_plan(req, ctx)

    def process_payment(self, amount: float, payment_method: str = "upi", currency: str = "INR",
                        customer_id: str = "cust_demo", risk_score: float = 0.1,
                        simulate_failure_provider: str = None) -> ProcessingOutcome:
        """End-to-end payment request execution pipeline."""
        req = PaymentRequest.create(
            amount=amount,
            payment_method=payment_method,
            currency=currency,
            customer_id=customer_id,
            risk_score=risk_score
        )

        plan_res = self.generate_plan(req)
        if plan_res.is_error:
            raise ValueError(f"Execution plan build failed: {plan_res.error()}")

        plan = plan_res.unwrap()
        outcome = self.processor.execute_plan(plan, simulate_failure_provider=simulate_failure_provider)

        # Update telemetry & provider health metrics based on outcome
        self.health_tracker.record_transaction(
            provider_id=outcome.provider_used,
            success=outcome.success,
            latency_ms=outcome.total_latency_ms
        )

        # Check self-healing triggers
        self.self_healing.evaluate_and_heal()

        # Log transaction to database
        self.db.log_transaction(outcome)

        return outcome

    def reset_simulation(self) -> None:
        """Resets provider health, self-healing events, and telemetry state."""
        self.health_tracker.reset()
        self.self_healing.reset()
        self.db.reset_tables()
