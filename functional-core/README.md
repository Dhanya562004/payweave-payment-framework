# PayWeave Functional Core (Haskell Architecture Specification)

This directory contains the formal pure Haskell functional implementation of the PayWeave Functional Core Engine.

## Architectural Rationale & Design

Payment routing and business decision logic are inherently domain-heavy, policy-driven workflows where side-effects, mutable state, and unhandled runtime exceptions create serious financial risk.

### Why Pure Functions for Payment Logic?
1. **Referential Transparency**: Given the same `PaymentRequest`, `MerchantConfig`, and `[ProviderHealth]`, a pure decision function returns the identical `RoutingDecision` or `PaymentExecutionPlan`.
2. **Zero Side-Effect Replay**: pure decision rules can be unit tested, audited, or replayed against historical payment logs without risk of double-charging or calling live external APIs.
3. **Formal Verification & Determinism**: Pure functions enable strict mathematical reasoning and property-based testing.

### Why `Either PaymentError a` over Exception Throwing?
In standard procedural programming, unexpected conditions (e.g. invalid currency, exceeded risk limits, degraded providers) often throw runtime exceptions (`throw new Exception(...)`) that bubble up through stack frames uncontrolled.

In PayWeave's functional architecture:
- Domain failure modes are modeled explicitly using the `PaymentError` Algebraic Data Type (ADT):
  - `InvalidAmount Double`
  - `UnsupportedCurrency String`
  - `RiskThresholdExceeded Double Double`
  - `InvalidCustomer String`
  - `NoHealthyProvider`
  - `SystemError String`
- Every step of the pipeline returns `Either PaymentError Result`.
- Monadic binding (`do` notation / `>>=`) forces callers to handle failure explicitly at compile-time.

---

## Code Base Structure

| File | Purpose |
| :--- | :--- |
| `PaymentTypes.hs` | Defines Algebraic Data Types (`PaymentMethod`, `PaymentError`, `AuthMode`, `PaymentRequest`, `ProviderHealth`, `MerchantConfig`, `RiskDecision`, `AuthenticationDecision`, `RoutingDecision`, `PaymentExecutionPlan`). |
| `PaymentRules.hs` | Implements pure validation (`validatePaymentRequest`), fraud risk evaluation (`evaluateRisk`), and adaptive authentication step-up (`decideAuthentication`). |
| `Routing.hs` | Implements pure provider scoring (`computeProviderScore`) and ranking (`chooseProvider`). |
| `PayWeave.hs` | Orchestrates the end-to-end monadic pipeline (`buildPlan :: MerchantConfig -> [ProviderHealth] -> PaymentRequest -> Either PaymentError PaymentExecutionPlan`). |
| `Main.hs` | Standalone executable test suite validating successful plans and explicit `Left PaymentError` returns. |

---

## Compilation & Local Run Instructions

If the Glasgow Haskell Compiler (`ghc`) or `runhaskell` is installed on your machine:

### Option A: Run directly with `runhaskell`
```bash
cd functional-core
runhaskell Main.hs
```

### Option B: Compile to binary with `ghc`
```bash
cd functional-core
ghc -O2 Main.hs -o run_core
./run_core
```

*Note: If GHC is not installed in your local environment, the Python reference runtime (`payweave/runtime/functional_core.py`) executes the identical monadic logic for Streamlit cloud portable deployment.*
