"""
PayWeave Anomaly Detector Benchmark Suite.
Executes reproducible, deterministic statistical anomaly detection benchmarks against synthetic telemetry streams.
"""

import os
import sys
import json
import time
import random
import statistics
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from payweave.anomaly.detector import AnomalyDetector
from payweave.anomaly.simulator import TelemetrySimulator


def run_anomaly_benchmark(num_batches: int = 50, records_per_batch: int = 40, seed: int = 42) -> Dict[str, Any]:
    """Runs anomaly detector across multiple deterministic telemetry batches."""
    random.seed(seed)
    detector = AnomalyDetector(z_threshold=2.5)

    total_observations = 0
    anomalies_detected_count = 0
    execution_times_ms: List[float] = []
    severity_counts: Dict[str, int] = {"NORMAL": 0, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    anomaly_types_counts: Dict[str, int] = {}

    for b in range(num_batches):
        inject_provider = "psp-a" if (b % 5 == 0) else None
        records = TelemetrySimulator.generate_telemetry_stream(
            num_records=records_per_batch,
            inject_anomaly_provider=inject_provider
        )
        total_observations += len(records)

        t0 = time.perf_counter()
        reports = detector.detect_batch_anomalies(records, sensitivity_threshold=0.65)
        t1 = time.perf_counter()

        execution_times_ms.append((t1 - t0) * 1000.0)

        for rep in reports:
            if rep.anomaly_detected:
                anomalies_detected_count += 1
            severity_counts[rep.severity] = severity_counts.get(rep.severity, 0) + 1
            anomaly_types_counts[rep.anomaly_type] = anomaly_types_counts.get(rep.anomaly_type, 0) + 1

    sorted_times = sorted(execution_times_ms)
    mean_time = statistics.mean(execution_times_ms)
    p95_time = sorted_times[int(0.95 * len(sorted_times))]

    return {
        "benchmark_name": "Statistical Anomaly Detector Benchmark",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "random_seed": seed,
        "num_batches_evaluated": num_batches,
        "records_per_batch": records_per_batch,
        "total_observations_evaluated": total_observations,
        "anomalies_detected_count": anomalies_detected_count,
        "z_score_threshold": detector.z_threshold,
        "severity_distribution": severity_counts,
        "anomaly_types_distribution": anomaly_types_counts,
        "execution_time_stats_ms": {
            "mean_batch_latency_ms": round(mean_time, 4),
            "p95_batch_latency_ms": round(p95_time, 4),
            "min_batch_latency_ms": round(sorted_times[0], 4),
            "max_batch_latency_ms": round(sorted_times[-1], 4)
        }
    }


def main():
    print("=" * 60)
    print("Running PayWeave Anomaly Detector Benchmark Suite...")
    print("=" * 60)

    anomaly_res = run_anomaly_benchmark(num_batches=50, records_per_batch=40, seed=42)

    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))
    os.makedirs(results_dir, exist_ok=True)

    json_path = os.path.join(results_dir, "anomaly_benchmark.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(anomaly_res, f, indent=2)

    print(f"[OK] Anomaly benchmark output saved to: {json_path}")
    print(f"   - Total Observations: {anomaly_res['total_observations_evaluated']}")
    print(f"   - Anomalies Found:     {anomaly_res['anomalies_detected_count']}")
    print(f"   - Mean Batch Time:     {anomaly_res['execution_time_stats_ms']['mean_batch_latency_ms']} ms")
    print(f"   - Severities:          {anomaly_res['severity_distribution']}")


if __name__ == "__main__":
    main()
