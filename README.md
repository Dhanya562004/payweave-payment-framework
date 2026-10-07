# PayWeave — Declarative Payment Application & Intelligent Infrastructure Framework

<div align="center">

# ⚡ PAYWEAVE

**Declarative Payment Application & Intelligent Infrastructure Framework**

[![Live Streamlit App](https://img.shields.io/badge/🚀_Live_Demo-Streamlit_Cloud-FF4B4B?style=for-the-badge&logo=streamlit)](https://payweave-payment-framework-pxtcmxmheexmcuyul6lkmy.streamlit.app/)
[![GitHub CI](https://img.shields.io/github/actions/workflow/status/Dhanya562004/payweave-payment-framework/ci.yml?branch=main&style=for-the-badge&logo=github)](https://github.com/Dhanya562004/payweave-payment-framework/actions)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.style=for-the-badge)](LICENSE)

[🌐 **Explore Live Application Demo**](https://payweave-payment-framework-pxtcmxmheexmcuyul6lkmy.streamlit.app/) • [📖 **API Docs**](#-api-endpoints-reference) • [🧪 **Test Suite**](#-running-automated-test-suite) • [⚡ **React SDK**](#-react-merchant-checkout-sdk)

</div>

---

## 🌟 What is PayWeave?

**PayWeave** is a declarative payment application and intelligent infrastructure framework. Instead of writing complex, hardcoded payment orchestration logic, PayWeave empowers merchants to define end-to-end payment flows, adaptive authentication security, dynamic provider routing, risk limits, and multi-datacenter topologies declaratively using **Declarative YAML DSL**.

### 🎨 Key Engineering Highlights
* 📜 **Declarative Business Logic DSL**: Configure payment rules, fraud thresholds, and fallback policies without code modification.
* 🧮 **Functional Programming Core**: Monadic (`Result` / `Either`) payment execution pipelines. Exposes formal **Haskell Functional Core** specification alongside a portable Python reference runtime.
* 🧠 **Intelligent Payment Router**: Multi-factor dynamic PSP scoring algorithm balancing success rates, latency SLAs, provider health, cost efficiency, and capacity.
* 🛡️ **Automated Self-Healing System**: Real-time provider circuit breaking that detects network degradation, shifts live traffic to healthy fallbacks, and logs recovery audit timelines.
* 📈 **Automatic Anomaly Detector**: Statistical Z-score telemetry monitoring identifying latency spikes, success drops, and error rate bursts.
* 🧩 **Visual Low-Code Flow Builder**: Drag-and-drop workflow builder supporting bidirectional conversion between visual node graphs and YAML DSL specs.
* 🌐 **Multi-Data-Center & Edge Simulation**: Simulates primary/failover datacenters (DC-1 Mumbai / DC-2 Bengaluru) and edge node worker pre-filtering.
* 🤖 **AI Payment Operations (PayWeave Assist)**: Natural language query engine powered by Gemini / Groq / Together AI with a **100% deterministic offline fallback engine**.
* ⚛️ **React Merchant Checkout SDK**: Pure TypeScript + React `<PayWeaveCheckout />` SDK for web integration.

---

## 🏗️ System Architecture Topology

```mermaid
graph TD
    DSL[Declarative YAML DSL] --> Parser[DSL Parser & Validator]
    Parser --> Core[Functional Execution Core]
    Core --> Plan[Payment Execution Plan]
    Plan --> Router[Intelligent Payment Router]
    
    subgraph Intelligent Routing & Self-Healing
        Router --> Score[Multi-Factor Scoring Engine]
        Score --> Health[Provider Health Tracker]
        Health --> Heal[Self-Healing Recovery Engine]
    end

    Router --> PSPs[Mock PSP Adapters]
    PSPs --> PSPA[PSP-A Enterprise Gateway]
    PSPs --> PSPB[PSP-B SpeedPay Express]
    PSPs --> PSPC[PSP-C ValuePay Direct]

    PSPs --> Telemetry[Telemetry Stream & Feature Extractor]
    Telemetry --> Anomaly[Z-Score Anomaly Detector]
    Telemetry --> Storage[(SQLite Database Persistence)]

    subgraph Infrastructure Layer
        Edge[Edge Nodes] --> MultiDC[Multi-DC Controller: DC1 / DC2]
        MultiDC --> PSPs
    end

    subgraph AI Operations
        AIOps[PayWeave Assist Query Engine] --> LLM[LLM Client / Offline Fallback]
    end
```

---

## 📜 Declarative YAML DSL Specification

```yaml
merchant:
  id: merchant_demo
  name: Demo Store Inc.
  environment: simulation

payment:
  methods:
    - upi
    - card
  currencies:
    - INR
    - USD
  default_method: upi

routing:
  strategy: intelligent
  prefer:
    - lowest_latency
    - highest_success_rate
  weights:
    success_rate: 0.40
    latency: 0.30
    health: 0.15
    cost: 0.10
    capacity: 0.05
  fallback:
    enabled: true
    max_retries: 2
    fallback_providers:
      - psp-b
      - psp-c

authentication:
  mode: adaptive
  step_up_threshold: 0.75
  require_2fa_above_amount: 10000.0

risk:
  max_score: 0.80
  block_high_risk: true

anomaly:
  enabled: true
  threshold: 0.65

infrastructure:
  primary_dc: dc1
  failover_dc: dc2
  edge_enabled: true
```

---

## 🧠 Intelligent Provider Routing Algorithm

The Intelligent Router calculates a composite score for each candidate provider:

$$\text{Score} = w_{\text{succ}} \cdot S + w_{\text{lat}} \cdot \left(1 - \frac{L}{L_{\text{ref}}}\right) + w_{\text{health}} \cdot H + w_{\text{cost}} \cdot (1 - C) + w_{\text{cap}} \cdot \frac{\text{Cap}}{100}$$

### Supported Routing Strategies
1. `intelligent`: Dynamic multi-weighted decision balancing all factors.
2. `highest_success_rate`: Prioritizes provider with highest rolling success rate.
3. `lowest_latency`: Prioritizes ultra-low latency providers.
4. `lowest_cost`: Minimizes transaction processing interchange fees.
5. `balanced`: Equal weight distribution across factors.

---

## 🛡️ Self-Healing System & Recovery Timeline

When network latency spikes or provider success rates fall below configured SLAs:
1. **Detection**: `DEGRADATION_DETECTED` event logged.
2. **Circuit Breaking**: Provider health score reduced to zero.
3. **Traffic Shift**: Active payment traffic automatically rerouted to secondary fallback providers.
4. **Recovery**: Once telemetry stabilizes, `RECOVERY_CONFIRMED` event is logged and provider is restored to primary pool.

```text
10:32:04 [WARNING] DEGRADATION_DETECTED: Latency spike (420ms) on PSP-A.
10:32:05 [CRITICAL] HEALTH_SCORE_REDUCED: PSP-A health score set to 0.
10:32:05 [INFO] TRAFFIC_REROUTED: Rerouted active traffic to PSP-B fallback.
10:32:06 [INFO] RECOVERY_CONFIRMED: PSP-A telemetry restored to baseline.
```

---

## 🤖 AI Payment Operations & Seamless Fallback

**PayWeave Assist** answers natural language questions regarding system performance, outage root causes, and cost optimization.
- **LLM Integration**: Supports Gemini, Groq, and Together AI API keys.
- **100% Deterministic Fallback**: If no API key is provided or if an API rate limit occurs, PayWeave utilizes a built-in deterministic response engine. The application **never** breaks due to a missing API key.

---

## ⚛️ React Merchant Checkout SDK

Located in `sdk/react/`:
- Configurable `<PayWeaveCheckout />` component.
- Interactive UPI Intent, VPA validation, Card tokenization simulation, and One-Click checkout.
- Dynamic theme (`dark_glass`, `vibrant_fintech`) and layout modes (`compact`, `standard`).

```bash
# Run React SDK Demo locally
cd sdk/react
npm install
npm run dev
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ *(optional, for React SDK)*

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/Dhanya562004/payweave-payment-framework.git
cd payweave-payment-framework

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Launch Streamlit Application UI
```bash
streamlit run app.py
```
Open browser at `http://localhost:8501`.

### 3. Launch FastAPI REST API Server
```bash
uvicorn api:app --reload --port 8000
```
Interactive API Documentation available at `http://localhost:8000/docs`.

---

## 🧪 Running Automated Test Suite

PayWeave contains **43 automated unit & API test cases** covering DSL parsing, semantic validation, functional rules, routing algorithms, self-healing, anomaly detection, infrastructure simulation, and REST endpoints.

```bash
python -m pytest
```

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Framework health status check |
| `POST` | `/validate-config` | Validates YAML DSL configuration syntax & rules |
| `POST` | `/routing/decision` | Computes intelligent routing decision & rationale |
| `POST` | `/payment/simulate` | Executes simulated payment request & fallback |
| `POST` | `/payment/flow` | Generates visual graph flow nodes |
| `POST` | `/anomaly/detect` | Runs statistical Z-score anomaly detector |
| `POST` | `/infrastructure/simulate` | Simulates multi-DC outage & failover |
| `GET` | `/metrics` | Fetches live telemetry summary & provider health |
| `GET` | `/providers` | Returns list of configured mock PSP adapters |
| `GET` / `POST` | `/merchant/config` | Get or update active merchant DSL configuration |

---

## 🌐 Live Application Link

- **Live Streamlit App**: [https://payweave-payment-framework-pxtcmxmheexmcuyul6lkmy.streamlit.app/](https://payweave-payment-framework-pxtcmxmheexmcuyul6lkmy.streamlit.app/)

---

## ⚠️ Portfolio Simulation Limitations

1. **Simulated Payment Gateway**: PayWeave is an architectural simulation framework designed for software architecture demonstration.
2. **Synthetic Telemetry**: Telemetry streams, provider latencies, and success rates are synthetic workload simulations.
3. **No Real Money / Bank Integration**: PayWeave does **NOT** connect to real bank networks, process real financial currency, or handle real payment credentials.
4. **Portable Functional Core**: Streamlit deployment utilizes the Python reference runtime to ensure reliable deployment without requiring GHC compilers on cloud hosts.

---

## 📄 License
Licensed under the [MIT License](LICENSE).
