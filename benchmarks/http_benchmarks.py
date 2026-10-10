"""
PayWeave HTTP Endpoint Load & Performance Benchmark.
Executes reproducible, concurrent load tests against the actual FastAPI application endpoints:
  - POST /routing/decision (Intelligent scoring & routing plan generation)
  - POST /payment/create (ACID state machine & idempotency key persistence)
  - POST /payment/simulate (End-to-end pipeline execution with provider adapters)

Calculates real measured throughput (RPS), error rates, and p50/p95/p99 latency percentiles.
Saves measured outputs to benchmarks/results/http_benchmark_results.json and .md.
"""

import asyncio
import time
import json
import uuid
import os
from pathlib import Path
from typing import List, Dict, Any
import httpx
from api import app


async def run_scenario(
    name: str,
    method: str,
    endpoint: str,
    payload_factory,
    total_requests: int = 1000,
    concurrency: int = 20,
) -> Dict[str, Any]:
    """Runs a concurrent benchmark scenario using httpx ASGI client."""
    print(f"\n[HTTP Benchmark] Starting: {name} ({total_requests} requests, concurrency={concurrency})...")
    
    latencies: List[float] = []
    successes = 0
    failures = 0
    status_codes: Dict[int, int] = {}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        queue = asyncio.Queue()
        for i in range(total_requests):
            queue.put_nowait(i)

        async def worker():
            nonlocal successes, failures
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

                payload = payload_factory()
                t0 = time.perf_counter()
                try:
                    if method == "POST":
                        resp = await client.post(endpoint, json=payload)
                    else:
                        resp = await client.get(endpoint)
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                    latencies.append(elapsed_ms)

                    code = resp.status_code
                    status_codes[code] = status_codes.get(code, 0) + 1
                    if 200 <= code < 300:
                        successes += 1
                    else:
                        failures += 1
                except Exception as ex:
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                    latencies.append(elapsed_ms)
                    failures += 1
                finally:
                    queue.task_done()

        start_time = time.perf_counter()
        workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await queue.join()
        for w in workers:
            w.cancel()
        total_time = time.perf_counter() - start_time

    latencies.sort()
    count = len(latencies)
    throughput = round(count / total_time, 2) if total_time > 0 else 0.0

    p50 = round(latencies[int(count * 0.50)], 3) if count > 0 else 0.0
    p90 = round(latencies[int(count * 0.90)], 3) if count > 0 else 0.0
    p95 = round(latencies[int(count * 0.95)], 3) if count > 0 else 0.0
    p99 = round(latencies[min(int(count * 0.99), count - 1)], 3) if count > 0 else 0.0
    mean_lat = round(sum(latencies) / count, 3) if count > 0 else 0.0
    min_lat = round(latencies[0], 3) if count > 0 else 0.0
    max_lat = round(latencies[-1], 3) if count > 0 else 0.0
    error_rate = round((failures / count) * 100.0, 2) if count > 0 else 0.0

    results = {
        "scenario": name,
        "endpoint": endpoint,
        "method": method,
        "total_requests": count,
        "concurrency": concurrency,
        "duration_seconds": round(total_time, 3),
        "throughput_rps": throughput,
        "successes": successes,
        "failures": failures,
        "error_rate_pct": error_rate,
        "latency_ms": {
            "min": min_lat,
            "mean": mean_lat,
            "p50": p50,
            "p90": p90,
            "p95": p95,
            "p99": p99,
            "max": max_lat
        },
        "status_codes": status_codes
    }

    print(f"  Completed {count} requests in {total_time:.2f}s | Throughput: {throughput:.1f} req/s")
    print(f"  Latency (ms) -> Min: {min_lat} | Mean: {mean_lat} | p50: {p50} | p95: {p95} | p99: {p99} | Max: {max_lat}")
    print(f"  Success: {successes} | Failures: {failures} | Error Rate: {error_rate}%\n")
    return results


async def run_all_http_benchmarks() -> List[Dict[str, Any]]:
    results = []

    # Scenario 1: Routing Decision Endpoint
    sc1 = await run_scenario(
        name="FastAPI /routing/decision",
        method="POST",
        endpoint="/routing/decision",
        payload_factory=lambda: {
            "amount": 1500.0,
            "currency": "INR",
            "payment_method": "upi",
            "customer_id": f"cust_{uuid.uuid4().hex[:6]}",
            "risk_score": 0.12
        },
        total_requests=1000,
        concurrency=25
    )
    results.append(sc1)

    # Scenario 2: ACID Payment Creation Endpoint
    sc2 = await run_scenario(
        name="FastAPI /payment/create (ACID + Idempotency)",
        method="POST",
        endpoint="/payment/create",
        payload_factory=lambda: {
            "amount": 2499.0,
            "currency": "INR",
            "payment_method": "card",
            "customer_id": f"cust_{uuid.uuid4().hex[:6]}",
            "idempotency_key": f"bench_{uuid.uuid4().hex}"
        },
        total_requests=500,
        concurrency=15
    )
    results.append(sc2)

    # Scenario 3: Payment Simulate Endpoint (Full Execution)
    sc3 = await run_scenario(
        name="FastAPI /payment/simulate (End-to-End Orchestration)",
        method="POST",
        endpoint="/payment/simulate",
        payload_factory=lambda: {
            "amount": 999.0,
            "currency": "INR",
            "payment_method": "upi",
            "customer_id": f"cust_{uuid.uuid4().hex[:6]}",
            "risk_score": 0.08
        },
        total_requests=500,
        concurrency=15
    )
    results.append(sc3)

    # Save results
    results_dir = Path("benchmarks/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    json_path = results_dir / "http_benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    md_path = results_dir / "http_benchmark_results.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# PayWeave Measured HTTP Performance Benchmark Results\n\n")
        f.write("Measured using `httpx` ASGI client against actual FastAPI application endpoints.\n\n")
        f.write("| Endpoint | Total Req | Concurrency | Duration (s) | Throughput (RPS) | p50 Latency (ms) | p95 Latency (ms) | p99 Latency (ms) | Error Rate |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results:
            l = r["latency_ms"]
            f.write(
                f"| `{r['endpoint']}` | {r['total_requests']} | {r['concurrency']} | "
                f"{r['duration_seconds']}s | **{r['throughput_rps']} req/s** | "
                f"{l['p50']} ms | {l['p95']} ms | {l['p99']} ms | {r['error_rate_pct']}% |\n"
            )
        f.write("\n*Generated from real benchmark execution on host machine without simulated values.*\n")

    print(f"HTTP benchmark results saved to {json_path} and {md_path}")
    return results


if __name__ == "__main__":
    asyncio.run(run_all_http_benchmarks())
