"""
PayWeave Declarative DSL Unit Tests.
Verifies parsing, validation rules, semantic conflict detection, and YAML serialization.
"""

import pytest
from payweave.dsl.schema import MerchantConfig, RoutingStrategy, AuthMode
from payweave.dsl.parser import DSLParser
from payweave.dsl.validator import DSLValidator


def test_default_config_schema():
    cfg = MerchantConfig()
    assert cfg.merchant.id == "merchant_demo"
    assert "upi" in cfg.payment.methods
    assert cfg.routing.strategy == RoutingStrategy.INTELLIGENT


def test_parse_valid_yaml():
    yaml_str = """
merchant:
  id: test_m1
  name: Test Merchant

payment:
  methods:
    - upi
    - card

routing:
  strategy: lowest_latency
    """
    config, val_res = DSLParser.parse_yaml(yaml_str)
    assert val_res.is_valid is True
    assert config.merchant.id == "test_m1"
    assert config.routing.strategy == RoutingStrategy.LOWEST_LATENCY


def test_yaml_roundtrip():
    original = MerchantConfig()
    yaml_str = DSLParser.to_yaml(original)
    reconstructed, val_res = DSLParser.parse_yaml(yaml_str)
    assert val_res.is_valid is True
    assert reconstructed.merchant.id == original.merchant.id
    assert reconstructed.payment.methods == original.payment.methods


def test_empty_payment_methods_error():
    data = {
        "payment": {"methods": []}
    }
    val_res = DSLValidator.validate_dict(data)
    assert val_res.is_valid is False
    assert any(e.code == "EMPTY_PAYMENT_METHODS" for e in val_res.errors)


def test_ui_method_conflict_error():
    data = {
        "payment": {"methods": ["upi"]},
        "payment_page": {"methods": ["upi", "card"]}
    }
    val_res = DSLValidator.validate_dict(data)
    assert val_res.is_valid is False
    assert any(e.code == "UI_METHOD_NOT_ENABLED" for e in val_res.errors)


def test_dc_no_redundancy_warning():
    data = {
        "infrastructure": {"primary_dc": "dc1", "failover_dc": "dc1"}
    }
    val_res = DSLValidator.validate_dict(data)
    assert val_res.is_valid is True
    assert any(w.code == "DC_NO_REDUNDANCY" for w in val_res.warnings)


def test_step_up_threshold_conflict_warning():
    data = {
        "authentication": {"step_up_threshold": 0.90},
        "risk": {"max_score": 0.50}
    }
    val_res = DSLValidator.validate_dict(data)
    assert val_res.is_valid is True
    assert any(w.code == "THRESHOLD_CONFLICT" for w in val_res.warnings)


def test_config_to_flow_nodes():
    cfg = MerchantConfig()
    nodes = DSLParser.config_to_flow_nodes(cfg)
    assert len(nodes) >= 6
    assert any(n["type"] == "risk_check" for n in nodes)
