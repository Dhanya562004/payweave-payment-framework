"""
Unit tests for benchmark execution suite.
Verifies router, failover, and anomaly benchmarks execute deterministically and generate expected schemas.
"""

import pytest
from benchmarks.benchmark_router import run_router_benchmark, run_failover_benchmark
from benchmarks.benchmark_anomaly import run_anomaly_benchmark


def test_run_router_benchmark_execution():
    res = run_router_benchmark(num_requests=50, seed=42)
    assert res["workload_size"] == 50
    assert res["successful_decisions"] == 50
    assert res["throughput_requests_per_sec"] > 0
    assert "mean" in res["latency_stats_ms"]


def test_run_failover_benchmark_execution():
    res = run_failover_benchmark(seed=42)
    assert res["stage1_healthy_psp_a_count"] == 100
    assert res["stage2_degraded_psp_a_count"] == 0
    assert res["rerouted_requests_count"] == 100
    assert res["failover_successful"] is True


def test_run_anomaly_benchmark_execution():
    res = run_anomaly_benchmark(num_batches=5, records_per_batch=20, seed=42)
    assert res["num_batches_evaluated"] == 5
    assert res["records_per_batch"] == 20
    assert res["total_observations_evaluated"] == 100
    assert "mean_batch_latency_ms" in res["execution_time_stats_ms"]


@pytest.mark.anyio
async def test_run_http_benchmark_execution():
    from benchmarks.http_benchmarks import run_scenario
    res = await run_scenario(
        name="Test Routing Endpoint",
        method="POST",
        endpoint="/routing/decision",
        payload_factory=lambda: {
            "amount": 1000.0,
            "currency": "INR",
            "payment_method": "upi",
            "customer_id": "cust_test_bench",
            "risk_score": 0.05
        },
        total_requests=20,
        concurrency=5
    )
    assert res["total_requests"] == 20
    assert res["successes"] == 20
    assert res["throughput_rps"] > 0.0
    assert "p50" in res["latency_ms"]

