"""
PayWeave Declarative DSL Unit & Integration Tests.
Verifies parsing, JSON schema export, validation rules (weights, providers, thresholds),
semantic conflict detection, YAML serialization, and configuration versioning & rollback.
"""

import pytest
import os
import tempfile
from payweave.dsl.schema import (
    MerchantConfig,
    RoutingStrategy,
    AuthMode,
    REGISTERED_PROVIDERS,
    get_dsl_json_schema,
    write_dsl_json_schema,
)
from payweave.dsl.parser import DSLParser
from payweave.dsl.validator import DSLValidator
from payweave.storage.database import PayWeaveDatabase


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
  weights:
    success_rate: 0.50
    latency: 0.50
  fallback:
    fallback_providers:
      - psp-b
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


def test_routing_weights_must_sum_to_one():
    # Weights summing to 0.70 should be strictly rejected
    data = {
        "routing": {
            "weights": {
                "success_rate": 0.40,
                "latency": 0.30
            }
        }
    }
    val_res = DSLValidator.validate_dict(data)
    assert val_res.is_valid is False
    assert any(e.code == "ROUTING_WEIGHTS_SUM_INVALID" for e in val_res.errors)


def test_negative_routing_weights_rejected():
    data = {
        "routing": {
            "weights": {
                "success_rate": 1.2,
                "latency": -0.2
            }
        }
    }
    val_res = DSLValidator.validate_dict(data)
    assert val_res.is_valid is False
    assert any(e.code == "ROUTING_WEIGHT_NEGATIVE" for e in val_res.errors)


def test_percentage_weights_accepted():
    # Percentage weights summing to 100.0 are accepted
    data = {
        "routing": {
            "weights": {
                "success_rate": 40.0,
                "latency": 30.0,
                "health": 15.0,
                "cost": 10.0,
                "capacity": 5.0
            }
        }
    }
    val_res = DSLValidator.validate_dict(data)
    assert val_res.is_valid is True


def test_unregistered_fallback_provider_rejected():
    data = {
        "routing": {
            "fallback": {
                "fallback_providers": ["psp-a", "unregistered_external_gateway"]
            }
        }
    }
    val_res = DSLValidator.validate_dict(data)
    assert val_res.is_valid is False
    assert any(e.code == "UNREGISTERED_PROVIDER" for e in val_res.errors)


def test_out_of_bounds_thresholds_rejected():
    # Anomaly threshold > 1.0 or Z-score <= 0
    data = {
        "anomaly": {
            "threshold": 1.5,
            "z_score_threshold": -1.0
        }
    }
    val_res = DSLValidator.validate_dict(data)
    assert val_res.is_valid is False


def test_malformed_yaml_syntax_rejected():
    malformed_yaml = "merchant:\n  id: test\n  [invalid: syntax: {"
    config, val_res = DSLParser.parse_yaml(malformed_yaml)
    assert val_res.is_valid is False
    assert any(e.code == "YAML_SYNTAX_ERROR" for e in val_res.errors)


def test_json_schema_generation():
    schema = get_dsl_json_schema()
    assert "$schema" in schema
    assert "properties" in schema
    assert "routing" in schema["properties"]
    assert "payment" in schema["properties"]


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


def test_database_configuration_versioning_and_rollback(tmp_path):
    temp_db = str(tmp_path / "test_config_versioning.db")
    db = PayWeaveDatabase(db_path=temp_db)

    # 1. Save initial version 1.0.0
    v1 = MerchantConfig(version="1.0.0")
    v1.merchant.id = "merchant_test"
    v1.merchant.name = "Initial Store"
    v1.routing.strategy = RoutingStrategy.HIGHEST_SUCCESS_RATE
    db.save_merchant_config(v1, user_role="Ops Lead", comment="Initial deployment")

    # 2. Save upgraded version 1.1.0
    v2 = MerchantConfig(version="1.1.0")
    v2.merchant.id = "merchant_test"
    v2.merchant.name = "Updated Store"
    v2.routing.strategy = RoutingStrategy.LOWEST_LATENCY
    db.save_merchant_config(v2, user_role="Ops Lead", comment="Latency optimization")

    # 3. Verify active config is 1.1.0
    active = db.get_merchant_config("merchant_test")
    assert active is not None
    assert active.version == "1.1.0"
    assert active.merchant.name == "Updated Store"
    assert active.routing.strategy == RoutingStrategy.LOWEST_LATENCY

    # 4. Check list of versions
    versions = db.list_config_versions("merchant_test")
    assert len(versions) == 2
    version_names = [v["version"] for v in versions]
    assert "1.0.0" in version_names
    assert "1.1.0" in version_names

    # 5. Fetch specific historical version
    historical_v1 = db.get_merchant_config("merchant_test", version="1.0.0")
    assert historical_v1 is not None
    assert historical_v1.version == "1.0.0"
    assert historical_v1.merchant.name == "Initial Store"

    # 6. Rollback to version 1.0.0
    restored = db.rollback_merchant_config("merchant_test", "1.0.0", user_role="SRE On-Call")
    assert restored.version == "1.0.0"

    # 7. Verify active config is now restored to 1.0.0
    active_after_rollback = db.get_merchant_config("merchant_test")
    assert active_after_rollback.version == "1.0.0"
    assert active_after_rollback.merchant.name == "Initial Store"
    assert active_after_rollback.routing.strategy == RoutingStrategy.HIGHEST_SUCCESS_RATE

    # 8. Rollback to non-existent version raises ValueError
    with pytest.raises(ValueError, match="not found"):
        db.rollback_merchant_config("merchant_test", "9.9.9")


def test_database_rejects_invalid_configuration(tmp_path):
    temp_db = str(tmp_path / "test_invalid_config.db")
    db = PayWeaveDatabase(db_path=temp_db)
    invalid_cfg = MerchantConfig()
    invalid_cfg.routing.weights = {"latency": 0.20}  # Does not sum to 1.0

    with pytest.raises(ValueError, match="Invalid merchant configuration"):
        db.save_merchant_config(invalid_cfg)

