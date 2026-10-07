# PayWeave Engineering Design Rationale & Architectural Trade-offs

This document outlines the core technical decisions, design trade-offs, and algorithmic choices governing the **PayWeave** payment orchestration and infrastructure framework.

---

## 1. Multi-Dimensional Provider Scoring & Routing Weights

PayWeave evaluates providers dynamically using a normalized scoring formula:

$$\text{Score} = (w_{\text{succ}} \cdot S) + (w_{\text{lat}} \cdot L) + (w_{\text{health}} \cdot H) + (w_{\text{cost}} \cdot C) + (w_{\text{cap}} \cdot K)$$

### Actual Production Weight Allocations
In the `INTELLIGENT` routing strategy, PayWeave enforces the following default weight distribution:

```python
{
    "success_rate": 0.40, # Weight 40% - Primary Reliability Vector
    "latency":      0.30, # Weight 30% - Customer Checkout Experience Vector
    "health":       0.15, # Weight 15% - Circuit Breaker Operational Availability
    "cost":         0.10, # Weight 10% - Merchant Interchange Cost Score
    "capacity":     0.05  # Weight 5%  - Provider Load Balancer Capacity
}
```

### Engineering Trade-offs
- **High Success-Rate Weight ($0.40$) vs. Merchant Interchange Cost ($0.10$)**:
  - *Trade-off*: Prioritizing success rate guarantees checkout completion and minimizes customer drop-offs. However, routing traffic away from low-cost providers (e.g., PSP-C with cost factor $0.30$) toward premium providers (e.g., PSP-B with cost factor $0.85$) increases per-transaction processing fees for merchants.
- **Latency Normalization ($L = 1 - \frac{\text{latency}}{\text{max\_latency}}$)**:
  - Latency is normalized relative to a reference threshold ($500\text{ms}$). A provider with $80\text{ms}$ latency receives a latency score of $0.84$, while a provider with $400\text{ms}$ receives $0.20$.

---

## 2. Dynamic Routing Strategies

PayWeave provides 5 discrete strategy profiles:

1. **`intelligent`** (Default): Uses the full weighted scoring formula above ($40\%$ success, $30\%$ latency, $15\%$ health, $10\%$ cost, $5\%$ capacity). Balanced for general production checkout.
2. **`highest_success_rate`**: Re-allocates weights ($80\%$ success, $20\%$ health). Minimizes transaction failures during high-traffic flash sales.
3. **`lowest_latency`**: Re-allocates weights ($80\%$ latency, $20\%$ health). Optimizes micro-checkout flows (e.g., instant subscriptions or food delivery).
4. **`lowest_cost`**: Re-allocates weights ($80\%$ cost, $10\%$ success, $10\%$ health). Routes traffic to low-interchange PSPs when financial margin is critical.
5. **`balanced`**: Equalized weighting ($30\%$ success, $30\%$ latency, $20\%$ cost, $10\%$ health, $10\%$ capacity).

---

## 3. Telemetry Anomaly Detection Architecture

PayWeave combines statistical Z-score analysis with machine-learning Isolation Forests:

### Z-Score Methodology
For rolling window metric $x$ (e.g. latency, success rate), the Z-score is computed as:

$$Z = \frac{x - \mu}{\sigma}$$

- **Threshold ($Z > 2.50$)**: Anomalies are flagged when telemetry deviates by more than $2.5$ standard deviations from the rolling mean $\mu$.
- **Why Z-Score?**: Z-score is computationally lightweight ($\mathcal{O}(1)$ update time per telemetry sample), deterministic, and requires zero offline model training, making it ideal for real-time streaming telemetry analysis.
- **ML IsolationForest Fallback**: For complex multi-variate anomaly patterns (e.g. simultaneous micro-spikes in error rate and transaction volume), PayWeave leverages `sklearn.ensemble.IsolationForest`.

---

## 4. Circuit Breaker & Self-Healing Engine

To prevent catastrophic failure cascading during provider outages, PayWeave implements an automated circuit breaker state machine:

```
    [ HEALTHY ] --- (Success Rate < 60% OR Latency > 700ms) ---> [ DEGRADED ]
         ^                                                            |
         |                                                            |
    (Reset / Manual Recovery) <---------------------------------------+
```

### Self-Healing Lifecycle:
1. **Detection**: `ProviderHealthTracker` continuously evaluates rolling transaction outcomes ($50$-sample window).
2. **Tripping**: If success rate drops below $60\%$ or mean latency exceeds $700\text{ms}$, `is_healthy` flips to `False`.
3. **Rerouting**: `IntelligentRouter` filters out unhealthy providers (score forced to $0.0$) and immediately routes traffic to the fallback chain.
4. **Automated Recovery**: When health parameters normalize, the self-healing engine restores the provider to active routing.

---

## 5. Multi-Data-Center Infrastructure Architecture

PayWeave models a distributed multi-region infrastructure topology:

- **Primary DC (`DC-1` Mumbai)**: Handles active primary traffic with $1,000\text{ TPS}$ capacity.
- **Failover DC (`DC-2` Bengaluru)**: Standby failover data center with capacity auto-scaling to $1,800\text{ TPS}$ upon DC-1 outage injection.
- **Edge Layer**: Simulates edge-node evaluation for regional validation and sub-millisecond static routing checks.

---

## 6. Functional Architecture (`Result` / `Either` Monad)

Payment application execution logic relies on pure functional composition:

- **Explicit Errors**: Avoids unchecked runtime exceptions by returning `Result[T, E]` (in Python) or `Either PaymentError a` (in Haskell).
- **Pure Functions**: Pipeline stages (`validate_request`, `evaluate_risk`, `decide_authentication`, `choose_provider`) are deterministic, pure, and free of global side-effects.

---

## 7. Declarative DSL Configuration

PayWeave decouples business policy from engine execution:
- Merchants configure routing weights, payment methods, 2FA step-up thresholds, and multi-DC targets in a single declarative YAML DSL.
- `DSLParser` and `DSLValidator` validate configurations against formal schemas before applying runtime reloads.

---

## 8. Low-Code Flow Graph Builder

Visual nodes in the Streamlit UI map 1-to-1 with the underlying declarative DSL nodes (`MerchantConfig` -> `FlowGraphNodes`). Changes in the visual low-code editor update the validated DSL runtime seamlessly.

---

## 9. Architectural Trade-offs & Limitations

1. **In-Memory Telemetry State**: Telemetry and provider health metrics are currently maintained in in-memory rolling windows. A production implementation would back this with Redis Cluster or Apache Flink.
2. **Synthetic Telemetry**: Telemetry streams are generated programmatically for reproducible portfolio benchmarking.
