"""
PayWeave DSL Parser.
Parses human-readable YAML configurations into validated typed objects,
and handles bidirectional conversion between YAML, MerchantConfig, and visual flow graphs.
"""

import yaml
from typing import Dict, Any, Tuple, List
from payweave.dsl.schema import MerchantConfig, FlowNode
from payweave.dsl.validator import DSLValidator, ValidationResult


class DSLParser:
    """Parses, validates, and serializes PayWeave Declarative DSL configurations."""

    @staticmethod
    def parse_yaml(yaml_str: str) -> Tuple[MerchantConfig, ValidationResult]:
        """Parses a YAML string into a MerchantConfig object and returns validation results."""
        try:
            data = yaml.safe_load(yaml_str) or {}
        except Exception as e:
            from payweave.dsl.validator import ValidationIssue
            issue = ValidationIssue(
                level="ERROR",
                code="YAML_SYNTAX_ERROR",
                message=f"Invalid YAML syntax: {str(e)}",
                field="root"
            )
            return MerchantConfig(), ValidationResult(is_valid=False, config=None, issues=[issue])

        validation_result = DSLValidator.validate_dict(data)
        config = validation_result.config or MerchantConfig()
        return config, validation_result

    @staticmethod
    def to_yaml(config: MerchantConfig) -> str:
        """Serializes a MerchantConfig object into clean YAML syntax."""
        data = config.model_dump(mode="json", exclude_none=True)
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    @staticmethod
    def config_to_flow_nodes(config: MerchantConfig) -> List[dict]:
        """Generates visual graph nodes from a MerchantConfig object."""
        nodes = [
            {
                "id": "node_start",
                "label": "START",
                "type": "start",
                "description": f"Merchant: {config.merchant.name} ({config.merchant.id})"
            },
            {
                "id": "node_validate",
                "label": "VALIDATE REQUEST",
                "type": "validate",
                "description": f"Supported: {', '.join(config.payment.methods)}"
            },
            {
                "id": "node_risk",
                "label": "RISK ASSESSMENT",
                "type": "risk_check",
                "description": f"Max Score: {config.risk.max_score:.2f} | Block: {config.risk.block_high_risk}"
            },
            {
                "id": "node_auth",
                "label": "AUTHENTICATE",
                "type": "authenticate",
                "description": f"Mode: {config.authentication.mode} | Step-up: {config.authentication.step_up_threshold}"
            },
            {
                "id": "node_route",
                "label": "SELECT PROVIDER",
                "type": "select_provider",
                "description": f"Strategy: {config.routing.strategy} | Prefers: {', '.join(config.routing.prefer)}"
            },
            {
                "id": "node_payment",
                "label": "PAYMENT EXECUTION",
                "type": "payment",
                "description": f"DC: {config.infrastructure.primary_dc} (Edge: {config.infrastructure.edge_enabled})"
            },
            {
                "id": "node_fallback",
                "label": "FALLBACK ROUTE",
                "type": "fallback",
                "description": f"Enabled: {config.routing.fallback.enabled} | Retries: {config.routing.fallback.max_retries}"
            },
            {
                "id": "node_anomaly",
                "label": "ANOMALY MONITOR",
                "type": "anomaly",
                "description": f"Active: {config.anomaly.enabled} | Threshold: {config.anomaly.threshold}"
            }
        ]
        return nodes

    @staticmethod
    def flow_nodes_to_config(nodes: List[dict], base_config: MerchantConfig = None) -> MerchantConfig:
        """Updates a MerchantConfig instance based on updated visual flow nodes."""
        cfg = base_config.model_copy(deep=True) if base_config else MerchantConfig()
        
        for node in nodes:
            ntype = node.get("type")
            node_cfg = node.get("config", {})
            
            if ntype == "risk_check" and "max_score" in node_cfg:
                cfg.risk.max_score = float(node_cfg["max_score"])
            elif ntype == "authenticate" and "mode" in node_cfg:
                cfg.authentication.mode = node_cfg["mode"]
            elif ntype == "select_provider" and "strategy" in node_cfg:
                cfg.routing.strategy = node_cfg["strategy"]
            elif ntype == "fallback" and "max_retries" in node_cfg:
                cfg.routing.fallback.max_retries = int(node_cfg["max_retries"])
            elif ntype == "anomaly" and "threshold" in node_cfg:
                cfg.anomaly.threshold = float(node_cfg["threshold"])
                
        return cfg
