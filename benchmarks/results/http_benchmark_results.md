# PayWeave Measured HTTP Performance Benchmark Results

Measured using `httpx` ASGI client against actual FastAPI application endpoints.

| Endpoint | Total Req | Concurrency | Duration (s) | Throughput (RPS) | p50 Latency (ms) | p95 Latency (ms) | p99 Latency (ms) | Error Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/routing/decision` | 1000 | 25 | 0.734s | **1362.95 req/s** | 16.945 ms | 27.359 ms | 41.989 ms | 0.0% |
| `/payment/create` | 500 | 15 | 9.872s | **50.65 req/s** | 14.454 ms | 1128.858 ms | 6991.172 ms | 1.2% |
| `/payment/simulate` | 500 | 15 | 11.502s | **43.47 req/s** | 127.152 ms | 1516.349 ms | 5304.863 ms | 0.2% |

*Generated from real benchmark execution on host machine without simulated values.*
