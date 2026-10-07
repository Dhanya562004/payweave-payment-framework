"""
PayWeave Declarative DSL Schemas.
Pydantic data models for merchant configuration, routing policies, payment rules,
UI layouts, and visual flow graph specifications.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class RoutingStrategy(str, Enum):
    HIGHEST_SUCCESS_RATE = "highest_success_rate"
    LOWEST_LATENCY = "lowest_latency"
    LOWEST_COST = "lowest_cost"
    BALANCED = "balanced"
    INTELLIGENT = "intelligent"


class AuthMode(str, Enum):
    FRICTIONLESS = "frictionless"
    ADAPTIVE = "adaptive"
    ALWAYS_2FA = "always_2fa"


class UILayout(str, Enum):
    COMPACT = "compact"
    STANDARD = "standard"
    EXPANDED = "expanded"


class UITheme(str, Enum):
    MINIMAL = "minimal"
    DARK_GLASS = "dark_glass"
    LIGHT_CORPORATE = "light_corporate"
    VIBRANT_FINTECH = "vibrant_fintech"


class MerchantInfo(BaseModel):
    id: str = Field(default="merchant_demo", description="Unique merchant ID")
    name: str = Field(default="Demo Merchant", description="Display name of merchant")
    environment: str = Field(default="simulation", description="Environment stage")


class PaymentConfig(BaseModel):
    methods: List[str] = Field(default_factory=lambda: ["upi", "card"], description="Supported payment methods")
    currencies: List[str] = Field(default_factory=lambda: ["INR", "USD"], description="Supported currencies")
    default_method: str = Field(default="upi", description="Default selected method")


class FallbackConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable provider fallback")
    max_retries: int = Field(default=2, ge=0, le=5, description="Max retries before failing")
    fallback_providers: List[str] = Field(default_factory=lambda: ["psp-b", "psp-c"], description="Ordered fallback PSPs")


class RoutingConfig(BaseModel):
    strategy: RoutingStrategy = Field(default=RoutingStrategy.INTELLIGENT, description="Routing algorithm")
    prefer: List[str] = Field(
        default_factory=lambda: ["lowest_latency", "highest_success_rate"],
        description="Priority factors"
    )
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "success_rate": 0.40,
            "latency": 0.30,
            "health": 0.15,
            "cost": 0.10,
            "capacity": 0.05
        },
        description="Routing weights adding up to 1.0"
    )
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)


class AuthenticationConfig(BaseModel):
    mode: AuthMode = Field(default=AuthMode.ADAPTIVE, description="Auth mode")
    step_up_threshold: float = Field(default=0.75, ge=0.0, le=1.0, description="Risk threshold to trigger 2FA")
    require_2fa_above_amount: float = Field(default=50000.0, description="Amount above which 2FA is forced")


class RiskConfig(BaseModel):
    max_score: float = Field(default=0.80, ge=0.0, le=1.0, description="Max allowed risk score")
    block_high_risk: bool = Field(default=True, description="Automatically block high risk requests")
    velocity_limit_per_min: int = Field(default=100, ge=1, description="Velocity cap")


class AnomalyConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable live anomaly monitoring")
    threshold: float = Field(default=0.65, ge=0.0, le=1.0, description="Anomaly alert score threshold")
    z_score_threshold: float = Field(default=2.5, description="Statistical Z-score cut-off")


class InfrastructureConfig(BaseModel):
    primary_dc: str = Field(default="dc1", description="Primary data center code")
    failover_dc: str = Field(default="dc2", description="Failover data center code")
    edge_enabled: bool = Field(default=True, description="Enable edge node evaluation")
    max_latency_ms: float = Field(default=400.0, description="SLA max latency limit in ms")


class UIConfig(BaseModel):
    layout: UILayout = Field(default=UILayout.COMPACT)
    theme: UITheme = Field(default=UITheme.VIBRANT_FINTECH)
    methods: List[str] = Field(default_factory=lambda: ["upi", "card"])
    show_saved_payment: bool = Field(default=True)
    brand_name: str = Field(default="PayWeave Merchant")
    primary_color: str = Field(default="#6366F1")


class FlowNode(BaseModel):
    id: str
    label: str
    type: str  # start, validate, risk_check, authenticate, select_provider, payment, success, fallback
    config: Dict[str, Any] = Field(default_factory=dict)


class MerchantConfig(BaseModel):
    version: str = Field(default="1.0.0")
    merchant: MerchantInfo = Field(default_factory=MerchantInfo)
    payment: PaymentConfig = Field(default_factory=PaymentConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    anomaly: AnomalyConfig = Field(default_factory=AnomalyConfig)
    infrastructure: InfrastructureConfig = Field(default_factory=InfrastructureConfig)
    payment_page: UIConfig = Field(default_factory=UIConfig)
    flow_nodes: Optional[List[FlowNode]] = Field(default=None)
