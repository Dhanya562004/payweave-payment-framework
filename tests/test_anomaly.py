"""
PayWeave Anomaly Detection Unit Tests.
Verifies statistical Z-score features, telemetry generation, and latency anomaly flagging.
"""

import pytest
from payweave.anomaly.features import FeatureExtractor
from payweave.anomaly.detector import AnomalyDetector
from payweave.anomaly.simulator import TelemetrySimulator


def test_feature_extractor_stats():
    vals = [10.0, 20.0, 30.0]
    stats = FeatureExtractor.calculate_stats(vals)
    assert stats["mean"] == 20.0
    assert stats["count"] == 3


def test_feature_extractor_z_score():
    z = FeatureExtractor.calculate_z_score(val=30.0, mean=20.0, std=5.0)
    assert z == 2.0


def test_telemetry_simulator_generation():
    records = TelemetrySimulator.generate_telemetry_stream(num_records=30)
    assert len(records) == 30
    assert "provider" in records[0]
    assert "latency" in records[0]


def test_anomaly_detector_flags_injected_latency_spike():
    records = TelemetrySimulator.generate_telemetry_stream(num_records=40, inject_anomaly_provider="psp-a")
    detector = AnomalyDetector(z_threshold=2.0)
    reports = detector.detect_batch_anomalies(records, sensitivity_threshold=0.50)
    
    psp_a_report = next((r for r in reports if r.affected_provider == "psp-a"), None)
    assert psp_a_report is not None
    assert psp_a_report.anomaly_detected is True
    assert psp_a_report.severity in ["HIGH", "CRITICAL"]
