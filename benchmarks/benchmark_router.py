"""
PayWeave Intelligent Router Benchmark Suite.
Executes reproducible, deterministic performance and failover benchmarks using actual
PayWeave application routing logic.
"""

import os
import sys
import json
import time
import random
import statistics
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from payweave.runtime.engine import PayWeaveEngine
from payweave.runtime.functional_core import PaymentRequest
from payweave.routing.provider_health import ProviderHealthTracker
from payweave.routing.self_healing import SelfHealingEngine
from payweave.routing.router import IntelligentRouter
from payweave.dsl.schema import MerchantConfig, RoutingStrategy


def run_router_benchmark(num_requests: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """Runs 1,000+ deterministic payment request routing benchmark."""
    random.seed(seed)
    engine = PayWeaveEngine()
    config = engine.config

    methods = ["upi", "card"]
    latencies_ms: List[float] = []
    provider_counts: Dict[str, int] = {}
    successful_decisions = 0
    failed_decisions = 0

    start_total_time = time.perf_counter()

    for i in range(num_requests):
        amt = round(random.uniform(50.0, 15000.0), 2)
        method = random.choice(methods)
        risk = round(random.uniform(0.01, 0.25), 3)  # Keep within merchant max risk 0.30
        cust_id = f"cust_bench_{i:04d}"

        req = PaymentRequest.create(
            amount=amt,
            currency="INR",
            payment_method=method,
            customer_id=cust_id,
            risk_score=risk
        )

        t0 = time.perf_counter()
        plan_res = engine.generate_plan(req)
        t1 = time.perf_counter()

        lat_ms = (t1 - t0) * 1000.0
        latencies_ms.append(lat_ms)

        if plan_res.is_ok:
            successful_decisions += 1
            plan = plan_res.unwrap()
            selected = plan.routing.selected_provider
            provider_counts[selected] = provider_counts.get(selected, 0) + 1
        else:
            failed_decisions += 1

    total_duration_sec = time.perf_counter() - start_total_time
    throughput_rps = num_requests / total_duration_sec if total_duration_sec > 0 else 0.0

    sorted_lats = sorted(latencies_ms)
    mean_lat = statistics.mean(latencies_ms)
    median_lat = statistics.median(latencies_ms)
    p95_idx = int(0.95 * len(sorted_lats))
    p99_idx = int(0.99 * len(sorted_lats))
    p95_lat = sorted_lats[min(p95_idx, len(sorted_lats) - 1)]
    p99_lat = sorted_lats[min(p99_idx, len(sorted_lats) - 1)]

    provider_dist_pct = {
        pid: round((cnt / num_requests) * 100.0, 2)
        for pid, cnt in provider_counts.items()
    }

    return {
        "benchmark_name": "Intelligent Router Performance Benchmark",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "random_seed": seed,
        "workload_size": num_requests,
        "routing_strategy": config.routing.strategy,
        "total_duration_seconds": round(total_duration_sec, 4),
        "throughput_requests_per_sec": round(throughput_rps, 2),
        "successful_decisions": successful_decisions,
        "failed_decisions": failed_decisions,
        "provider_distribution_counts": provider_counts,
        "provider_distribution_pct": provider_dist_pct,
        "latency_stats_ms": {
            "mean": round(mean_lat, 4),
            "median": round(median_lat, 4),
            "p95": round(p95_lat, 4),
            "p99": round(p99_lat, 4),
            "min": round(sorted_lats[0], 4),
            "max": round(sorted_lats[-1], 4)
        }
    }


def run_failover_benchmark(seed: int = 42) -> Dict[str, Any]:
    """Simulates provider degradation and measures real failover & rerouting behavior."""
    random.seed(seed)
    engine = PayWeaveEngine()
    health_tracker = engine.health_tracker
    self_healing = engine.self_healing
    router = IntelligentRouter(health_tracker, self_healing)
    config = engine.config

    # Set PSP-A as healthiest initially
    engine.providers["psp-a"].current_success_rate = 0.998
    engine.providers["psp-a"].current_latency_ms = 40.0

    # Stage 1: Healthy routing (100 requests) -> PSP-A wins
    stage1_selected: List[str] = []
    for i in range(100):
        req = PaymentRequest.create(amount=1000.0, customer_id=f"cust_s1_{i}", risk_score=0.05)
        dec = router.route_request(req, config)
        stage1_selected.append(dec.selected_provider)

    # Stage 2: Degrade PSP-A (simulate high error / latency spike)
    t0_degrade = time.perf_counter()
    engine.providers["psp-a"].current_success_rate = 0.40
    engine.providers["psp-a"].current_latency_ms = 850.0
    for _ in range(5):
        health_tracker.record_transaction("psp-a", success=False, latency_ms=850.0)
    t1_degrade = time.perf_counter()

    failover_detection_lat_ms = (t1_degrade - t0_degrade) * 1000.0

    # Run 100 requests during degradation -> Should reroute to PSP-B/PSP-C
    stage2_selected: List[str] = []
    for i in range(100):
        req = PaymentRequest.create(amount=1000.0, customer_id=f"cust_s2_{i}", risk_score=0.05)
        dec = router.route_request(req, config)
        stage2_selected.append(dec.selected_provider)

    psp_a_stage1_cnt = stage1_selected.count("psp-a")
    psp_a_stage2_cnt = stage2_selected.count("psp-a")
    rerouted_cnt = psp_a_stage1_cnt - psp_a_stage2_cnt

    # Stage 3: Recovery
    engine.providers["psp-a"].recover()
    engine.providers["psp-a"].current_success_rate = 0.998
    engine.providers["psp-a"].current_latency_ms = 40.0
    health_tracker.reset()

    stage3_selected: List[str] = []
    for i in range(100):
        req = PaymentRequest.create(amount=1000.0, customer_id=f"cust_s3_{i}", risk_score=0.05)
        dec = router.route_request(req, config)
        stage3_selected.append(dec.selected_provider)

    return {
        "benchmark_name": "Provider Failover & Rerouting Benchmark",
        "stage1_healthy_psp_a_count": psp_a_stage1_cnt,
        "stage2_degraded_psp_a_count": psp_a_stage2_cnt,
        "rerouted_requests_count": rerouted_cnt,
        "failover_decision_latency_ms": round(failover_detection_lat_ms, 4),
        "stage3_recovered_psp_a_count": stage3_selected.count("psp-a"),
        "failover_successful": psp_a_stage2_cnt < psp_a_stage1_cnt
    }


def main():
    print("=" * 60)
    print("Running PayWeave Real Router & Failover Benchmark Suite...")
    print("=" * 60)

    router_res = run_router_benchmark(num_requests=1000, seed=42)
    failover_res = run_failover_benchmark(seed=42)

    combined_results = {
        "router_benchmark": router_res,
        "failover_benchmark": failover_res
    }

    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))
    os.makedirs(results_dir, exist_ok=True)

    json_path = os.path.join(results_dir, "router_benchmark.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined_results, f, indent=2)

    print(f"[OK] Router benchmark output saved to: {json_path}")
    print(f"   - Workload Size:   {router_res['workload_size']} requests")
    print(f"   - Throughput:      {router_res['throughput_requests_per_sec']} req/sec")
    print(f"   - Mean Latency:    {router_res['latency_stats_ms']['mean']} ms")
    print(f"   - P95 Latency:     {router_res['latency_stats_ms']['p95']} ms")
    print(f"   - P99 Latency:     {router_res['latency_stats_ms']['p99']} ms")
    print(f"   - Provider Dist:   {router_res['provider_distribution_pct']}")
    print(f"   - Failover Rerouted: {failover_res['rerouted_requests_count']} requests")


if __name__ == "__main__":
    main()
