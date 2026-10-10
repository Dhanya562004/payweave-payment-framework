# PayWeave Functional Core (Haskell Architecture Specification)

This directory contains the formal pure Haskell functional implementation of the PayWeave Functional Core Engine.

## Architectural Rationale & Design

Payment routing and business decision logic are inherently domain-heavy, policy-driven workflows where side-effects, mutable state, and unhandled runtime exceptions create serious financial risk.

### Why Pure Functions for Payment Logic?
1. **Referential Transparency**: Given the same `PaymentRequest`, `MerchantConfig`, and `[ProviderHealth]`, a pure decision function returns the identical `RoutingDecision` or `PaymentExecutionPlan`.
2. **Zero Side-Effect Replay**: Pure decision rules can be unit tested, audited, or replayed against historical payment logs without risk of double-charging or calling live external APIs.
3. **Formal Verification & Determinism**: Pure functions enable strict mathematical reasoning and property-based testing via QuickCheck.

### Explicit Error Representation (`Either PaymentError a`)
Domain failure modes and state transitions are modeled explicitly using Algebraic Data Types (ADTs):
- `InvalidAmount Double`
- `UnsupportedCurrency String`
- `InvalidPaymentMethod String`
- `RiskThresholdExceeded Double Double`
- `InvalidCustomer String`
- `NoHealthyProvider`
- `InvalidMerchantConfig String`
- `InvalidStateTransition PaymentState PaymentState`
- `CircuitBreakerOpen Provider`
- `SystemError String`

Every step of the pipeline returns `Either PaymentError Result`. Monadic binding forces callers to handle failure explicitly at compile-time.

---

## Code Base Structure

| File | Purpose |
| :--- | :--- |
| `PaymentTypes.hs` | Defines Algebraic Data Types (`PaymentMethod`, `PaymentState`, `CircuitBreakerState`, `PaymentError`, `AuthMode`, `PaymentRequest`, `ProviderHealth`, `MerchantConfig`, `RiskDecision`, `AuthenticationDecision`, `RoutingDecision`, `PaymentExecutionPlan`). |
| `PaymentRules.hs` | Implements pure validation (`validatePaymentRequest`, `validateMerchantConfig`), fraud risk evaluation (`evaluateRisk`), adaptive authentication (`decideAuthentication`), finite state machine (`transitionPaymentState`), and retry eligibility (`isRetryEligible`). |
| `Routing.hs` | Implements pure provider multi-factor scoring (`computeProviderScore`) with circuit breaker awareness, and deterministic tie-breaking provider ranking (`chooseProvider`). Guarantees no unhealthy provider is selected and returns `Left NoHealthyProvider` if none are available. |
| `PayWeave.hs` | Orchestrates the end-to-end monadic pipeline (`buildPlan :: MerchantConfig -> [ProviderHealth] -> PaymentRequest -> Either PaymentError PaymentExecutionPlan`). |
| `Main.hs` | Standalone executable demonstrating successful plans, boundary error handling, and state transitions. |
| `TestMain.hs` | QuickCheck property-based test runner validating mathematical invariants, deterministic state transitions, and unhealthy provider exclusion. |
| `payweave-core.cabal` | Cabal package specification, pinned to GHC 9.6.6 with QuickCheck test suite. |
| `stack.yaml` | Stack configuration pinning `lts-22.28` (GHC 9.6.6). |
| `cabal.project` | Cabal project configuration pinning compiler version. |

---

## Reproducible Build & Test Instructions

### Cabal (Pinned GHC 9.6.6)
```bash
cabal update
cabal build
cabal test --test-show-details=always
```

### Stack (LTS 22.28 / GHC 9.6.6)
```bash
stack setup
stack build
stack test
```

### Standalone with `runhaskell`
```bash
runhaskell Main.hs
```

*Note: In environments where GHC is not installed locally (e.g. standard local Windows developer laptops without Haskell toolchains), GitHub Actions runs the full Cabal build and QuickCheck suite on Ubuntu CI. The Python reference runtime (`payweave/runtime/functional_core.py`) executes the identical verified logic and is verified by differential tests.*
