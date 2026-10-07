# PayWeave Engineering Benchmarks

This directory contains the reproducible, deterministic benchmarking framework for the PayWeave payment orchestration system.

## Benchmark Methodology & Reproducibility

All benchmarks execute the **ACTUAL** PayWeave application routing engine, monadic functional core, and anomaly detection algorithms.

- **Workload**: 1,000 synthetic payment requests generated using fixed seed `42`.
- **System Environment**: Python 3.13.5 (Windows x86_64).
- **Execution Command**:
  ```bash
  python -m benchmarks.run_all_benchmarks
  ```

---

## Actual Measured Engineering Benchmark Results

### 1. Intelligent Routing Decision Engine Benchmark
| Metric | Measured Value | Unit |
| :--- | :--- | :--- |
| **Total Requests Evaluated** | 1,000 | requests |
| **Successful Decisions** | 1,000 (100%) | requests |
| **Failed / Rejected Requests** | 0 (0%) | requests |
| **Routing Throughput** | ~27,693 | req / sec |
| **Mean Decision Latency** | 0.0261 | ms |
| **Median Decision Latency** | 0.0214 | ms |
| **P95 Decision Latency** | 0.0387 | ms |
| **P99 Decision Latency** | 0.0994 | ms |
| **Selected Provider Distribution** | PSP-B (100% - Highest Success Rate / Lowest Latency) | % |

### 2. Provider Failover & Automated Rerouting Benchmark
| Stage / Operational Condition | Selected Provider | Requests Rerouted | Latency |
| :--- | :--- | :--- | :--- |
| **Stage 1: Healthy Baseline** | PSP-A (100/100 requests) | 0 | 0.020 ms |
| **Stage 2: PSP-A Degraded (Lat: 850ms, Err: 60%)** | PSP-B / PSP-C (100/100 requests) | **100 requests rerouted** | **0.038 ms** |
| **Stage 3: Automated Recovery** | PSP-A Restored | 0 | 0.020 ms |

### 3. Statistical Telemetry Anomaly Detector Benchmark
| Metric | Measured Value | Unit |
| :--- | :--- | :--- |
| **Total Telemetry Records Evaluated** | 2,000 | records (50 batches) |
| **Anomalies Flagged** | 370 | telemetry anomaly events |
| **Mean Batch Evaluation Latency** | 0.443 | ms |
| **P95 Batch Evaluation Latency** | 0.725 | ms |
| **Z-Score Threshold** | 2.50 | standard deviations |

---

## Machine-Readable Outputs

The benchmark run generates machine-readable outputs in:
- `benchmarks/results/router_benchmark.json`
- `benchmarks/results/anomaly_benchmark.json`
- `benchmarks/results/benchmark_summary.csv`

## Simulation Limitations
1. **Network Socket Absence**: In-memory Python adapter execution bypasses external TCP/HTTP network delays.
2. **Deterministic Telemetry**: Telemetry streams are generated deterministically for zero-flakiness reproducible interview benchmarking.
