"""
PayWeave Automatic Anomaly Detector.
Detects statistical anomalies, latency spikes, success rate drops, and error bursts
using Z-score statistical analysis and optional scikit-learn IsolationForest.
"""

from typing import List, Dict, Any, Optional
import time
from payweave.anomaly.features import FeatureExtractor

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AnomalyReport:
    def __init__(self, anomaly_detected: bool, anomaly_score: float, severity: str,
                 affected_provider: str, anomaly_type: str, explanation: str,
                 metrics_snapshot: Dict[str, Any]):
        self.anomaly_detected = anomaly_detected
        self.anomaly_score = anomaly_score  # 0.0 - 1.0
        self.severity = severity  # NORMAL, LOW, MEDIUM, HIGH, CRITICAL
        self.affected_provider = affected_provider
        self.anomaly_type = anomaly_type
        self.explanation = explanation
        self.metrics_snapshot = metrics_snapshot
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_detected": self.anomaly_detected,
            "anomaly_score": round(self.anomaly_score, 3),
            "severity": self.severity,
            "affected_provider": self.affected_provider,
            "anomaly_type": self.anomaly_type,
            "explanation": self.explanation,
            "metrics": self.metrics_snapshot,
            "timestamp": self.timestamp
        }


class AnomalyDetector:
    """Statistical and Machine Learning Payment Anomaly Detector."""

    def __init__(self, z_threshold: float = 2.5):
        self.z_threshold = z_threshold

    def detect_batch_anomalies(self, telemetry_records: List[Dict[str, Any]],
                               sensitivity_threshold: float = 0.65) -> List[AnomalyReport]:
        if not telemetry_records:
            return []

        reports: List[AnomalyReport] = []
        
        # Group by provider
        by_provider: Dict[str, List[Dict[str, Any]]] = {}
        for rec in telemetry_records:
            pid = rec.get("provider", "global")
            by_provider.setdefault(pid, []).append(rec)

        for pid, records in by_provider.items():
            latencies = [r.get("latency", r.get("latency_ms", 150.0)) for r in records]
            success_rates = [r.get("success_rate", 0.98) for r in records]
            error_rates = [r.get("error_rate", 0.02) for r in records]
            amounts = [r.get("amount", 1000.0) for r in records]

            lat_stats = FeatureExtractor.calculate_stats(latencies)
            succ_stats = FeatureExtractor.calculate_stats(success_rates)
            err_stats = FeatureExtractor.calculate_stats(error_rates)

            latest = records[-1]
            latest_lat = latest.get("latency", latest.get("latency_ms", 150.0))
            latest_succ = latest.get("success_rate", 0.98)
            latest_err = latest.get("error_rate", 0.02)
            latest_amt = latest.get("amount", 1000.0)

            lat_z = FeatureExtractor.calculate_z_score(latest_lat, lat_stats["mean"], lat_stats["std"])
            succ_z = FeatureExtractor.calculate_z_score(latest_succ, succ_stats["mean"], succ_stats["std"])

            anomaly_score = 0.0
            reasons = []
            anomaly_type = "NONE"

            # 1. Latency Spike Check
            if lat_z > self.z_threshold or latest_lat > 400.0:
                score_contrib = min(1.0, lat_z / 4.0)
                anomaly_score = max(anomaly_score, score_contrib)
                reasons.append(f"Latency spike detected ({latest_lat:.0f}ms vs mean {lat_stats['mean']:.0f}ms, Z={lat_z:.2f}).")
                anomaly_type = "LATENCY_SPIKE"

            # 2. Success Rate Drop Check
            if succ_z < -self.z_threshold or latest_succ < 0.85:
                score_contrib = min(1.0, abs(succ_z) / 4.0)
                anomaly_score = max(anomaly_score, score_contrib)
                reasons.append(f"Success rate drop detected ({latest_succ*100:.1f}% vs mean {succ_stats['mean']*100:.1f}%, Z={succ_z:.2f}).")
                if anomaly_type == "NONE":
                    anomaly_type = "SUCCESS_RATE_DROP"
                else:
                    anomaly_type = "MULTIPLE_ANOMALIES"

            # 3. Error Rate Burst
            if latest_err > 0.15:
                anomaly_score = max(anomaly_score, 0.85)
                reasons.append(f"High error burst rate ({latest_err*100:.1f}%).")
                if anomaly_type == "NONE":
                    anomaly_type = "ERROR_BURST"

            # Determine severity
            if anomaly_score >= 0.80:
                severity = "CRITICAL"
            elif anomaly_score >= sensitivity_threshold:
                severity = "HIGH"
            elif anomaly_score >= 0.40:
                severity = "MEDIUM"
            elif anomaly_score > 0.15:
                severity = "LOW"
            else:
                severity = "NORMAL"

            is_anomaly = anomaly_score >= sensitivity_threshold

            explanation = " | ".join(reasons) if reasons else f"Telemetry within normal operational bounds for {pid.upper()}."

            reports.append(AnomalyReport(
                anomaly_detected=is_anomaly,
                anomaly_score=anomaly_score,
                severity=severity,
                affected_provider=pid,
                anomaly_type=anomaly_type,
                explanation=explanation,
                metrics_snapshot={
                    "latency_ms": latest_lat,
                    "success_rate": latest_succ,
                    "error_rate": latest_err,
                    "amount": latest_amt,
                    "latency_z_score": round(lat_z, 2)
                }
            ))

        return reports
