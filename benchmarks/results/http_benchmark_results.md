# PayWeave Measured HTTP Performance Benchmark Results

Measured using `httpx` ASGI client against actual FastAPI application endpoints.

| Endpoint | Total Req | Concurrency | Duration (s) | Throughput (RPS) | p50 Latency (ms) | p95 Latency (ms) | p99 Latency (ms) | Error Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/routing/decision` | 1000 | 25 | 0.804s | **1244.48 req/s** | 18.561 ms | 29.389 ms | 34.948 ms | 0.0% |
| `/payment/create` | 500 | 15 | 2.376s | **210.4 req/s** | 67.991 ms | 97.781 ms | 110.478 ms | 0.0% |
| `/payment/simulate` | 500 | 15 | 1.95s | **256.43 req/s** | 55.402 ms | 70.695 ms | 88.516 ms | 63.6% |

*Generated from real benchmark execution on host machine without simulated values.*
