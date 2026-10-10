from payweave.dsl.schema import MerchantConfig, REGISTERED_PROVIDERS
from typing import List, Tuple
from pydantic import ValidationError


class ValidationIssue:
    def __init__(self, level: str, code: str, message: str, field: str = ""):
        self.level = level  # "ERROR" or "WARNING"
        self.code = code
        self.message = message
        self.field = field

    def __repr__(self) -> str:
        return f"[{self.level}] ({self.code}) {self.field}: {self.message}"

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "field": self.field
        }


class ValidationResult:
    def __init__(self, is_valid: bool, config: MerchantConfig = None, issues: List[ValidationIssue] = None):
        self.is_valid = is_valid
        self.config = config
        self.issues = issues or []

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "ERROR"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "WARNING"]


class DSLValidator:
    """Validates MerchantConfig data structures for semantic correctness."""

    @staticmethod
    def validate_dict(data: dict) -> ValidationResult:
        issues: List[ValidationIssue] = []
        try:
            config = MerchantConfig(**data)
        except ValidationError as ve:
            for err in ve.errors():
                loc_str = " -> ".join([str(loc) for loc in err["loc"]])
                issues.append(ValidationIssue(
                    level="ERROR",
                    code="SCHEMA_VALIDATION_ERROR",
                    message=err["msg"],
                    field=loc_str
                ))
            return ValidationResult(is_valid=False, config=None, issues=issues)

        # Perform semantic validation checks
        issues.extend(DSLValidator._check_semantic_rules(config))

        has_errors = any(i.level == "ERROR" for i in issues)
        return ValidationResult(is_valid=not has_errors, config=config, issues=issues)

    @staticmethod
    def _check_semantic_rules(config: MerchantConfig) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        # 1. Routing weights validation: MUST sum to 1.0 (or 100%) and be non-negative
        weights = config.routing.weights
        if not weights:
            issues.append(ValidationIssue(
                level="ERROR",
                code="ROUTING_WEIGHTS_EMPTY",
                message="Routing weights dictionary cannot be empty.",
                field="routing.weights"
            ))
        else:
            negative_weights = {k: v for k, v in weights.items() if v < 0}
            if negative_weights:
                issues.append(ValidationIssue(
                    level="ERROR",
                    code="ROUTING_WEIGHT_NEGATIVE",
                    message=f"Routing weights cannot be negative: {negative_weights}",
                    field="routing.weights"
                ))
            total_weight = sum(weights.values())
            # Accept either normalized (1.0 +/- 0.001) or percentage (100.0 +/- 0.1)
            is_one = abs(total_weight - 1.0) <= 0.001
            is_hundred = abs(total_weight - 100.0) <= 0.1
            if not is_one and not is_hundred:
                issues.append(ValidationIssue(
                    level="ERROR",
                    code="ROUTING_WEIGHTS_SUM_INVALID",
                    message=f"Routing weights MUST sum to 1.0 (or 100%), got {total_weight:.4f}.",
                    field="routing.weights"
                ))

        # 2. Registered provider validation: all fallback providers must be registered
        for p in config.routing.fallback.fallback_providers:
            if p not in REGISTERED_PROVIDERS:
                issues.append(ValidationIssue(
                    level="ERROR",
                    code="UNREGISTERED_PROVIDER",
                    message=f"Provider '{p}' is not a registered provider. Valid providers are: {sorted(list(REGISTERED_PROVIDERS))}.",
                    field="routing.fallback.fallback_providers"
                ))

        # 3. Anomaly and threshold bounds
        if config.anomaly.threshold < 0.0 or config.anomaly.threshold > 1.0:
            issues.append(ValidationIssue(
                level="ERROR",
                code="INVALID_ANOMALY_THRESHOLD",
                message=f"Anomaly threshold must be between 0.0 and 1.0, got {config.anomaly.threshold}.",
                field="anomaly.threshold"
            ))

        if config.anomaly.z_score_threshold <= 0.0:
            issues.append(ValidationIssue(
                level="ERROR",
                code="INVALID_Z_SCORE_THRESHOLD",
                message=f"Z-score threshold must be strictly positive (> 0.0), got {config.anomaly.z_score_threshold}.",
                field="anomaly.z_score_threshold"
            ))

        # 4. Infrastructure SLA bounds
        if config.infrastructure.max_latency_ms <= 0.0:
            issues.append(ValidationIssue(
                level="ERROR",
                code="INVALID_MAX_LATENCY",
                message=f"Max SLA latency must be strictly positive, got {config.infrastructure.max_latency_ms}.",
                field="infrastructure.max_latency_ms"
            ))

        # 5. Fallback retry bounds
        if config.routing.fallback.max_retries < 0 or config.routing.fallback.max_retries > 10:
            issues.append(ValidationIssue(
                level="ERROR",
                code="INVALID_MAX_RETRIES",
                message=f"Fallback max_retries must be between 0 and 10, got {config.routing.fallback.max_retries}.",
                field="routing.fallback.max_retries"
            ))

        # 6. Payment methods check
        if not config.payment.methods:
            issues.append(ValidationIssue(
                level="ERROR",
                code="EMPTY_PAYMENT_METHODS",
                message="At least one payment method must be configured in 'payment.methods'.",
                field="payment.methods"
            ))

        # 7. UI methods subset check
        invalid_ui_methods = [m for m in config.payment_page.methods if m not in config.payment.methods]
        if invalid_ui_methods:
            issues.append(ValidationIssue(
                level="ERROR",
                code="UI_METHOD_NOT_ENABLED",
                message=f"UI references payment methods not enabled in merchant config: {invalid_ui_methods}",
                field="payment_page.methods"
            ))

        # 8. DC redundancy check (warning)
        if config.infrastructure.primary_dc == config.infrastructure.failover_dc:
            issues.append(ValidationIssue(
                level="WARNING",
                code="DC_NO_REDUNDANCY",
                message="Primary DC and Failover DC are identical. Single point of failure detected.",
                field="infrastructure.failover_dc"
            ))

        # 9. Fallback configuration check (warning)
        if config.routing.fallback.enabled and not config.routing.fallback.fallback_providers:
            issues.append(ValidationIssue(
                level="WARNING",
                code="FALLBACK_ENABLED_NO_PROVIDERS",
                message="Fallback is enabled but no fallback_providers are specified.",
                field="routing.fallback.fallback_providers"
            ))

        # 10. Step-up threshold conflict check (warning)
        if config.authentication.step_up_threshold > config.risk.max_score:
            issues.append(ValidationIssue(
                level="WARNING",
                code="THRESHOLD_CONFLICT",
                message=f"Step-up auth threshold ({config.authentication.step_up_threshold}) exceeds max allowed risk score ({config.risk.max_score}). Transactions will be blocked before step-up auth is triggered.",
                field="authentication.step_up_threshold"
            ))

        return issues

