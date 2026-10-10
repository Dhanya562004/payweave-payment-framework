# NeuroDB Portfolio Upgrade Guide

Use this guide to upgrade your standalone **NeuroDB** C++ repository to hit the Tier 3 Juspay engineering criteria:
1. GitHub Actions CMake CI with AddressSanitizer and automated tests.
2. Query latency benchmark harness measuring p50, p95, and throughput.

---

## 1. GitHub Actions CI Workflow (`.github/workflows/cmake_ci.yml`)

Save this file in `.github/workflows/cmake_ci.yml` in your NeuroDB repository:

```yaml
name: NeuroDB CMake CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install Build Essentials
        run: |
          sudo apt-get update
          sudo apt-get install -y cmake g++ lcov libgtest-dev

      - name: Configure CMake with ASan
        run: |
          cmake -B build \
            -DCMAKE_BUILD_TYPE=Debug \
            -DENABLE_ASAN=ON \
            -DBUILD_TESTS=ON

      - name: Build NeuroDB Engine & Tests
        run: cmake --build build --config Debug -j $(nproc)

      - name: Run Test Suite
        run: |
          cd build
          ctest --output-on-failure
```

---

## 2. Microsecond Query Latency Benchmark Harness (`benchmark_query.cpp`)

Add this benchmark file to test NeuroDB query performance:

```cpp
#include <iostream>
#include <chrono>
#include <vector>
#include <numeric>
#include <algorithm>

int main() {
    constexpr int NUM_QUERIES = 10000;
    std::vector<double> latencies_us;
    latencies_us.reserve(NUM_QUERIES);

    std::cout << "Starting NeuroDB Query Latency Benchmark (" << NUM_QUERIES << " queries)...\n";

    auto start_total = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < NUM_QUERIES; ++i) {
        auto t0 = std::chrono::high_resolution_clock::now();

        // Call your actual NeuroDB query function here:
        // neuro_db.execute_query("MATCH (n:Node) RETURN n LIMIT 1");

        auto t1 = std::chrono::high_resolution_clock::now();
        double elapsed_us = std::chrono::duration<double, std::micro>(t1 - t0).count();
        latencies_us.push_back(elapsed_us);
    }

    auto end_total = std::chrono::high_resolution_clock::now();
    double total_sec = std::chrono::duration<double>(end_total - start_total).count();

    std::sort(latencies_us.begin(), latencies_us.end());

    double p50 = latencies_us[static_cast<size_t>(NUM_QUERIES * 0.50)];
    double p95 = latencies_us[static_cast<size_us>(NUM_QUERIES * 0.95)];
    double p99 = latencies_us[static_cast<size_t>(NUM_QUERIES * 0.99)];
    double throughput = NUM_QUERIES / total_sec;

    std::cout << "--------------------------------------------------\n";
    std::cout << "NeuroDB Benchmark Results:\n";
    std::cout << "  Throughput: " << throughput << " queries/sec\n";
    std::cout << "  p50 Latency: " << p50 << " us\n";
    std::cout << "  p95 Latency: " << p95 << " us\n";
    std::cout << "  p99 Latency: " << p99 << " us\n";
    std::cout << "--------------------------------------------------\n";

    return 0;
}
```
