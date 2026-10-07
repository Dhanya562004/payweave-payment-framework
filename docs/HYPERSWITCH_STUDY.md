# Engineering Study: Juspay Hyperswitch vs. PayWeave Framework

> [!NOTE]
> **Independent Portfolio Study Disclaimer**: This document is an independent technical study and comparative analysis of Juspay's open-source **Hyperswitch** payment router versus the **PayWeave** declarative framework. PayWeave is an independent educational/portfolio project inspired by backend SDE problems and does not claim official affiliation with or contribution to Juspay.

---

## Executive Summary & Comparison Matrix

| Architectural Dimension | Juspay Hyperswitch | PayWeave Framework |
| :--- | :--- | :--- |
| **Primary Language / Stack** | Rust (High-concurrency async runtime) | Python 3.13 (Engine/API/UI) & Haskell (Functional Core Specification) |
| **Core Architecture** | Distributed payment router & connector engine | Declarative payment framework & intelligent infrastructure simulator |
| **Connector Integration** | 50+ Real PSP Connectors (Stripe, Adyen, Razorpay, Paypal, etc.) | Mock PSP Adapters (`psp-a`, `psp-b`, `psp-c`) with simulated latency/failure |
| **Configuration Model** | Dynamic Database Routing Rules & Merchant Dashboard | Declarative YAML DSL schema with low-code visual flow builder |
| **Error Handling Paradigm** | Rust `Result<T, StorageError/ConnectorError>` | Python `Result[T, E]` / Haskell `Either PaymentError a` Monads |
| **Telemetry & Observability** | OpenTelemetry, Prometheus metrics, distributed tracing | Statistical Z-score detector, IsolationForest, and Plotly evidence charts |
| **Data Persistence** | PostgreSQL, Redis Cluster, PCI-DSS Compliant Vault | SQLite local database with in-memory rolling window health tracker |

---

## Deep Technical Analysis

### A. What Hyperswitch Actually Does
**Hyperswitch** is Juspay's high-performance, open-source payment switch written in **Rust**. Key production capabilities include:
1. **Unified Payments Interface**: Single unified REST/GraphQL API encapsulating dozens of payment processors.
2. **Dynamic Smart Routing**: Rule-based and ML-driven routing engine evaluating cost, currency conversion fees, success rates, and volume commitments.
3. **PCI-DSS Vaulting**: Tokenization vault for card details ensuring merchants remain out of PCI scope.
4. **Resilience & Failure Management**: Automated retries, cascading fallbacks, and smart refund processing.

### B. What PayWeave Does
**PayWeave** models the core algorithmic and architectural challenges of payment orchestration:
1. **Functional Decision Core**: Separates side-effect-free payment decision logic (`validate_request`, `evaluate_risk`, `decide_authentication`, `choose_provider`) into monadic pipelines.
2. **Multi-Factor Provider Scoring**: Scores providers using weighted formulas ($40\%$ success rate, $30\%$ latency, $15\%$ health, $10\%$ cost, $5\%$ capacity).
3. **Intelligent Self-Healing & Circuit Breaking**: Automatically trips provider status when latency or error thresholds breach limits and reroutes active traffic.
4. **Multi-DC Infrastructure Simulation**: Simulates DC-1 primary and DC-2 failover capacity shifting and edge validation.

### C. What PayWeave Intentionally Simplifies
- **Mock PSP Connectors**: Replaces external network socket calls with simulated latency distributions for deterministic benchmarking.
- **In-Memory Rolling Telemetry**: Stores metric history in rolling deques rather than a distributed Kafka/ClickHouse cluster.

### D. Architectural Inspiration
PayWeave was directly inspired by Hyperswitch's core design principles:
- **Connector Abstraction**: Abstract base adapter pattern (`BasePSPAdapter`) enforcing uniform `process_payment` signatures across diverse PSPs.
- **Declarative Policy Control**: Business logic and security rules isolated from infrastructure code.

### E. Technical Roadmap: Moving PayWeave Toward Production
To evolve PayWeave into a production-grade payment router like Hyperswitch:
1. **Rust Core Engine Rewrite**: Migrate the Python reference runtime to Rust/Actix for sub-millisecond execution.
2. **Real PSP SDK Integrations**: Implement live REST API connector adapters for Stripe, Adyen, and Razorpay.
3. **PCI-DSS Vaulting Service**: Add a dedicated tokenization service backed by HSM / HashiCorp Vault.
4. **Distributed Telemetry Pipeline**: Replace SQLite and in-memory deques with Redis Cluster, Kafka streams, and ClickHouse OLAP.
