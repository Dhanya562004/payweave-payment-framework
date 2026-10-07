"""
PayWeave Benchmark Orchestrator.
Executes all benchmark suites, verifies results, and generates JSON + CSV summary reports.
"""

import os
import sys
import json
import csv
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmarks.benchmark_router import run_router_benchmark, run_failover_benchmark
from benchmarks.benchmark_anomaly import run_anomaly_benchmark


def main():
    print("==================================================")
    print("Executing Complete PayWeave Benchmark Suite")
    print("==================================================")

    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))
    os.makedirs(results_dir, exist_ok=True)

    # 1. Router & Failover Benchmark
    router_res = run_router_benchmark(num_requests=1000, seed=42)
    failover_res = run_failover_benchmark(seed=42)
    combined_router = {
        "router_benchmark": router_res,
        "failover_benchmark": failover_res
    }
    with open(os.path.join(results_dir, "router_benchmark.json"), "w", encoding="utf-8") as f:
        json.dump(combined_router, f, indent=2)

    # 2. Anomaly Benchmark
    anomaly_res = run_anomaly_benchmark(num_batches=50, records_per_batch=40, seed=42)
    with open(os.path.join(results_dir, "anomaly_benchmark.json"), "w", encoding="utf-8") as f:
        json.dump(anomaly_res, f, indent=2)

    # 3. CSV Summary Report
    csv_path = os.path.join(results_dir, "benchmark_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric Domain", "Metric Name", "Measured Value", "Unit / Context"])
        
        # Router Metrics
        writer.writerow(["Routing", "Total Workload", router_res["workload_size"], "requests"])
        writer.writerow(["Routing", "Throughput", router_res["throughput_requests_per_sec"], "req/sec"])
        writer.writerow(["Routing", "Mean Latency", router_res["latency_stats_ms"]["mean"], "ms"])
        writer.writerow(["Routing", "Median Latency", router_res["latency_stats_ms"]["median"], "ms"])
        writer.writerow(["Routing", "P95 Latency", router_res["latency_stats_ms"]["p95"], "ms"])
        writer.writerow(["Routing", "P99 Latency", router_res["latency_stats_ms"]["p99"], "ms"])
        
        for pid, pct in router_res["provider_distribution_pct"].items():
            writer.writerow(["Routing Allocation", f"Provider {pid.upper()} Allocation", pct, "%"])

        # Failover Metrics
        writer.writerow(["Failover", "Stage 1 PSP-A Count", failover_res["stage1_healthy_psp_a_count"], "requests"])
        writer.writerow(["Failover", "Stage 2 Degraded PSP-A Count", failover_res["stage2_degraded_psp_a_count"], "requests"])
        writer.writerow(["Failover", "Rerouted Requests Count", failover_res["rerouted_requests_count"], "requests"])
        writer.writerow(["Failover", "Decision Latency", failover_res["failover_decision_latency_ms"], "ms"])

        # Anomaly Metrics
        writer.writerow(["Anomaly Detection", "Total Observations", anomaly_res["total_observations_evaluated"], "records"])
        writer.writerow(["Anomaly Detection", "Anomalies Flagged", anomaly_res["anomalies_detected_count"], "events"])
        writer.writerow(["Anomaly Detection", "Mean Batch Latency", anomaly_res["execution_time_stats_ms"]["mean_batch_latency_ms"], "ms"])
        writer.writerow(["Anomaly Detection", "P95 Batch Latency", anomaly_res["execution_time_stats_ms"]["p95_batch_latency_ms"], "ms"])

    print("\n[SUCCESS] Benchmark Suite Completed Successfully!")
    print(f"   - JSON Results: {results_dir}")
    print(f"   - CSV Summary:  {csv_path}")
    print("==================================================")


if __name__ == "__main__":
    main()
