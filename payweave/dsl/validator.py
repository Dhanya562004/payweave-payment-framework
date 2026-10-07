"""
PayWeave DSL Validator.
Validates parsed YAML/JSON configurations for schema correctness, missing fields,
and semantic rule conflicts with human-readable diagnostic messages.
"""

from typing import List, Tuple
from pydantic import ValidationError
from payweave.dsl.schema import MerchantConfig


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

        # 1. Routing weights sum check
        weights = config.routing.weights
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.05:
            issues.append(ValidationIssue(
                level="WARNING",
                code="ROUTING_WEIGHTS_NOT_NORMALIZED",
                message=f"Routing weights sum to {total_weight:.2f} instead of 1.0. Engine will auto-normalize.",
                field="routing.weights"
            ))

        # 2. Payment methods check
        if not config.payment.methods:
            issues.append(ValidationIssue(
                level="ERROR",
                code="EMPTY_PAYMENT_METHODS",
                message="At least one payment method must be configured in 'payment.methods'.",
                field="payment.methods"
            ))

        # 3. UI methods subset check
        invalid_ui_methods = [m for m in config.payment_page.methods if m not in config.payment.methods]
        if invalid_ui_methods:
            issues.append(ValidationIssue(
                level="ERROR",
                code="UI_METHOD_NOT_ENABLED",
                message=f"UI references payment methods not enabled in merchant config: {invalid_ui_methods}",
                field="payment_page.methods"
            ))

        # 4. DC redundancy check
        if config.infrastructure.primary_dc == config.infrastructure.failover_dc:
            issues.append(ValidationIssue(
                level="WARNING",
                code="DC_NO_REDUNDANCY",
                message="Primary DC and Failover DC are identical. Single point of failure detected.",
                field="infrastructure.failover_dc"
            ))

        # 5. Fallback configuration check
        if config.routing.fallback.enabled and not config.routing.fallback.fallback_providers:
            issues.append(ValidationIssue(
                level="WARNING",
                code="FALLBACK_ENABLED_NO_PROVIDERS",
                message="Fallback is enabled but no fallback_providers are specified.",
                field="routing.fallback.fallback_providers"
            ))

        # 6. Step-up threshold conflict check
        if config.authentication.step_up_threshold > config.risk.max_score:
            issues.append(ValidationIssue(
                level="WARNING",
                code="THRESHOLD_CONFLICT",
                message=f"Step-up auth threshold ({config.authentication.step_up_threshold}) exceeds max allowed risk score ({config.risk.max_score}). Transactions will be blocked before step-up auth is triggered.",
                field="authentication.step_up_threshold"
            ))

        return issues
