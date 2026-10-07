"""
PayWeave Python Functional Reference Runtime.
Implements pure functional payment logic, monadic transformations (Result/Either),
algebraic data types, pattern matching, and immutable pipelines.
Serves as the portable reference engine mirroring functional-core/PayWeave.hs.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Generic, TypeVar, Callable
from enum import Enum
import uuid
import time
from payweave.dsl.schema import MerchantConfig, AuthMode, RoutingStrategy

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    """Pure monadic Either / Result data structure for immutable pipeline state."""

    def __init__(self, value: Optional[T] = None, error: Optional[E] = None, is_ok: bool = True):
        self._value = value
        self._error = error
        self._is_ok = is_ok

    @staticmethod
    def ok(value: T) -> "Result[T, E]":
        return Result(value=value, is_ok=True)

    @staticmethod
    def fail(error: E) -> "Result[T, E]":
        return Result(error=error, is_ok=False)

    @property
    def is_ok(self) -> bool:
        return self._is_ok

    @property
    def is_error(self) -> bool:
        return not self._is_ok

    def unwrap(self) -> T:
        if not self._is_ok:
            raise ValueError(f"Cannot unwrap error Result: {self._error}")
        return self._value

    def error(self) -> E:
        return self._error

    def map(self, fn: Callable[[T], Any]) -> "Result[Any, E]":
        if self._is_ok:
            return Result.ok(fn(self._value))
        return Result.fail(self._error)

    def flat_map(self, fn: Callable[[T], "Result[Any, E]"]) -> "Result[Any, E]":
        if self._is_ok:
            return fn(self._value)
        return Result.fail(self._error)


class PaymentMethodEnum(str, Enum):
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"


@dataclass(frozen=True)
class PaymentRequest:
    request_id: str
    amount: float
    currency: str
    payment_method: str
    customer_id: str
    risk_score: float = 0.1
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(amount: float, payment_method: str = "upi", currency: str = "INR",
               customer_id: str = "cust_demo", risk_score: float = 0.1, metadata: dict = None) -> "PaymentRequest":
        return PaymentRequest(
            request_id=f"pay_{uuid.uuid4().hex[:10]}",
            amount=amount,
            currency=currency,
            payment_method=payment_method.lower(),
            customer_id=customer_id,
            risk_score=risk_score,
            metadata=metadata or {}
        )


@dataclass(frozen=True)
class ProviderHealth:
    provider_id: str
    success_rate: float  # 0.0 - 1.0
    latency_ms: float
    error_rate: float
    is_healthy: bool
    cost_score: float  # 0.0 - 1.0 (lower is cheaper)
    capacity_pct: float  # 0 - 100


@dataclass(frozen=True)
class PaymentContext:
    merchant_config: MerchantConfig
    provider_health_map: Dict[str, ProviderHealth]
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class ValidationDecision:
    is_valid: bool
    reason: str


@dataclass(frozen=True)
class RiskDecision:
    passed: bool
    risk_score: float
    max_score: float
    action: str  # "ALLOW", "BLOCK", "STEP_UP"


@dataclass(frozen=True)
class AuthenticationDecision:
    requires_2fa: bool
    mode: str
    reason: str


@dataclass(frozen=True)
class RoutingDecision:
    selected_provider: str
    fallback_chain: List[str]
    score: float
    rationale: str


@dataclass(frozen=True)
class ExecutionStep:
    name: str
    status: str  # "SUCCESS", "SKIPPED", "FAILED"
    details: str
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class PaymentExecutionPlan:
    request: PaymentRequest
    validation: ValidationDecision
    risk: RiskDecision
    auth: AuthenticationDecision
    routing: RoutingDecision
    steps: List[ExecutionStep]
    estimated_latency_ms: float
    ready_for_execution: bool


# Pure Functions for Functional Payment Engine Pipeline

def validate_request(req: PaymentRequest, ctx: PaymentContext) -> Result[ValidationDecision, str]:
    """Pure function: Validates payment request against merchant DSL capabilities."""
    if req.amount <= 0:
        return Result.fail("Payment amount must be greater than zero.")
    
    supported_methods = ctx.merchant_config.payment.methods
    if req.payment_method not in supported_methods:
        return Result.fail(
            f"Payment method '{req.payment_method}' is not supported by merchant DSL configuration. "
            f"Supported: {supported_methods}"
        )

    supported_currencies = ctx.merchant_config.payment.currencies
    if req.currency not in supported_currencies:
        return Result.fail(
            f"Currency '{req.currency}' is not accepted. Supported: {supported_currencies}"
        )

    return Result.ok(ValidationDecision(is_valid=True, reason="Request parameters valid against merchant DSL."))


def evaluate_risk(req: PaymentRequest, ctx: PaymentContext) -> Result[RiskDecision, str]:
    """Pure function: Evaluates fraud risk score against merchant DSL thresholds."""
    max_score = ctx.merchant_config.risk.max_score
    block_high_risk = ctx.merchant_config.risk.block_high_risk

    if req.risk_score > max_score and block_high_risk:
        return Result.fail(
            f"Transaction risk score ({req.risk_score:.2f}) exceeds max allowed threshold ({max_score:.2f}). Transaction blocked."
        )

    action = "ALLOW"
    if req.risk_score >= ctx.merchant_config.authentication.step_up_threshold:
        action = "STEP_UP"

    return Result.ok(RiskDecision(
        passed=True,
        risk_score=req.risk_score,
        max_score=max_score,
        action=action
    ))


def determine_authentication(req: PaymentRequest, risk_dec: RiskDecision, ctx: PaymentContext) -> AuthenticationDecision:
    """Pure function: Determines authentication requirements based on risk & amount."""
    mode = ctx.merchant_config.authentication.mode
    step_up_threshold = ctx.merchant_config.authentication.step_up_threshold
    require_2fa_above = ctx.merchant_config.authentication.require_2fa_above_amount

    if mode == AuthMode.ALWAYS_2FA:
        return AuthenticationDecision(requires_2fa=True, mode=mode, reason="Merchant policy forces 2FA for all transactions.")
    
    if mode == AuthMode.FRICTIONLESS:
        if req.amount > require_2fa_above:
            return AuthenticationDecision(
                requires_2fa=True, mode=mode,
                reason=f"Amount ₹{req.amount:,.2f} exceeds frictionless cap ₹{require_2fa_above:,.2f}."
            )
        return AuthenticationDecision(requires_2fa=False, mode=mode, reason="Frictionless checkout approved.")

    # Adaptive mode
    if risk_dec.risk_score >= step_up_threshold or req.amount >= require_2fa_above:
        return AuthenticationDecision(
            requires_2fa=True, mode=mode,
            reason=f"Adaptive security triggered: risk ({req.risk_score:.2f}) or amount (₹{req.amount:,.2f}) exceeded step-up limits."
        )

    return AuthenticationDecision(requires_2fa=False, mode=mode, reason="Adaptive risk assessment passed without 2FA.")


def evaluate_routing(req: PaymentRequest, ctx: PaymentContext) -> RoutingDecision:
    """Pure function: Selects optimal PSP based on weights, strategy, and provider health."""
    health_map = ctx.provider_health_map
    strategy = ctx.merchant_config.routing.strategy
    weights = ctx.merchant_config.routing.weights
    fallbacks = ctx.merchant_config.routing.fallback.fallback_providers

    scored_providers = []
    max_lat = max([p.latency_ms for p in health_map.values()] or [500.0])

    for pid, p in health_map.items():
        if not p.is_healthy:
            continue

        succ_component = p.success_rate * weights.get("success_rate", 0.4)
        lat_component = (1.0 - (min(p.latency_ms, max_lat) / (max_lat + 1e-5))) * weights.get("latency", 0.3)
        health_component = (1.0 if p.is_healthy else 0.0) * weights.get("health", 0.15)
        cost_component = (1.0 - p.cost_score) * weights.get("cost", 0.1)
        cap_component = (p.capacity_pct / 100.0) * weights.get("capacity", 0.05)

        total_score = succ_component + lat_component + health_component + cost_component + cap_component
        scored_providers.append((pid, total_score, p))

    scored_providers.sort(key=lambda x: x[1], reverse=True)

    if not scored_providers:
        # Fallback if no healthy provider found
        best_pid = fallbacks[0] if fallbacks else "psp-a"
        return RoutingDecision(
            selected_provider=best_pid,
            fallback_chain=fallbacks,
            score=0.0,
            rationale="All primary providers degraded. Routing directly to emergency fallback."
        )

    best_pid, best_score, best_p = scored_providers[0]
    fallback_chain = [p[0] for p in scored_providers[1:]] + [f for f in fallbacks if f != best_pid]

    rationale = (
        f"Selected {best_pid.upper()} (Score: {best_score:.3f}). "
        f"Success: {best_p.success_rate * 100:.1f}%, Latency: {best_p.latency_ms:.0f}ms, Cost factor: {best_p.cost_score:.2f}."
    )

    return RoutingDecision(
        selected_provider=best_pid,
        fallback_chain=fallback_chain,
        score=best_score,
        rationale=rationale
    )


def build_execution_plan(req: PaymentRequest, ctx: PaymentContext) -> Result[PaymentExecutionPlan, str]:
    """
    Pure functional pipeline composition.
    Combines validateRequest -> evaluateRisk -> determineAuthentication -> evaluateRouting -> buildExecutionPlan.
    """
    val_res = validate_request(req, ctx)
    if val_res.is_error:
        return Result.fail(val_res.error())
    val_dec = val_res.unwrap()

    risk_res = evaluate_risk(req, ctx)
    if risk_res.is_error:
        return Result.fail(risk_res.error())
    risk_dec = risk_res.unwrap()

    auth_dec = determine_authentication(req, risk_dec, ctx)
    routing_dec = evaluate_routing(req, ctx)

    p_health = ctx.provider_health_map.get(routing_dec.selected_provider)
    est_latency = p_health.latency_ms if p_health else 150.0

    steps = [
        ExecutionStep(name="VALIDATE_REQUEST", status="SUCCESS", details=val_dec.reason),
        ExecutionStep(name="RISK_CHECK", status="SUCCESS", details=f"Risk Score: {risk_dec.risk_score:.2f} (Action: {risk_dec.action})"),
        ExecutionStep(name="AUTHENTICATION", status="SUCCESS", details=auth_dec.reason),
        ExecutionStep(name="INTELLIGENT_ROUTING", status="SUCCESS", details=routing_dec.rationale),
    ]

    plan = PaymentExecutionPlan(
        request=req,
        validation=val_dec,
        risk=risk_dec,
        auth=auth_dec,
        routing=routing_dec,
        steps=steps,
        estimated_latency_ms=est_latency,
        ready_for_execution=True
    )
    return Result.ok(plan)
