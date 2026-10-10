# PayWeave Distributed Infrastructure & Shared State Topology

## 1. Multi-Datacenter Architecture

PayWeave is architected for active-passive regional redundancy across two primary Indian data centers:

| Tier | Region / Zone | Baseline Internal Latency | Role | Default Capacity |
|---|---|---|---|---|
| **DC1** | Mumbai (`ap-south-1a`) | **15.0ms** | **Primary Active** | 1,000 req/sec |
| **DC2** | Bengaluru (`ap-south-1b`) | **42.0ms** | **Standby Failover** | 1,000 req/sec (scales to 1,800 req/sec during failover) |

### Automatic Failover Protocol
1. **Health Check Probing**: Edge gateways monitor DC1 with 200ms heartbeat probes.
2. **Failure Threshold**: 3 consecutive probe timeouts or an unhandled circuit trip triggers automated traffic re-routing.
3. **Capacity Shifting**: DC2 dynamic autoscaling expands provisioned capacity from 1,000 to 1,800 req/sec to absorb redirected traffic without queue buildup.
4. **Graceful Primary Recovery**: When DC1 passes 5 consecutive health checks, traffic is seamlessly drained from DC2 back to DC1 to minimize regional latency.

---

## 2. Distributed State Coordination (`SharedStateManager`)

Payment gateways running across distributed worker nodes require synchronized views of provider health and circuit breaker trips to avoid split-brain routing decisions.

### Redis-Backed Shared State
- **Key Namespace**:
  - `payweave:health:{provider_id}`: Rolling window success rate, average latency, and health flags.
  - `payweave:circuit_breaker:{provider_id}`: Circuit state (`CLOSED`, `OPEN`, `HALF_OPEN`), failure counts, cooldown timestamps.
- **Resilient Fallback**:
  If Redis is unavailable or unconfigured, `SharedStateManager` gracefully and automatically falls back to an internal thread-safe in-memory store without interrupting transaction processing.

---

## 3. Docker Compose Generator (`DockerComposeGenerator`)

PayWeave generates reproducible, multi-service Docker configurations directly from the merchant's declarative DSL (`MerchantConfig`):

- **`payweave-api`**: FastAPI high-throughput routing engine and ACID payment lifecycle service.
- **`payweave-ui`**: Real-time Streamlit operations console and observability dashboard.
- **`redis`**: Distributed caching layer for provider health and circuit-breaker telemetry (`redis:7-alpine`).
- **`mock-psp-*`**: Isolated mock payment gateway containers representing configured PSP adapters.
