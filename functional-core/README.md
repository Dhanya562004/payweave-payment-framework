# PayWeave Functional Core (Haskell Architecture Specification)

This directory contains the pure Haskell implementation of the PayWeave Functional Core Engine.

## Architectural Purpose
PayWeave demonstrates a declarative, functional-first approach to payment application engineering.
The Haskell implementation models:

1. **Algebraic Data Types (ADTs)** (`PaymentTypes.hs`) representing immutable domain models (`PaymentRequest`, `ProviderHealth`, `MerchantConfig`, `AuthDecision`, `RoutingDecision`, `PaymentExecutionPlan`).
2. **Pure Composable Functions & Monads** (`Rules.hs`, `Routing.hs`) evaluating fraud risk, adaptive step-up authentication, and multi-factor provider scoring without side effects.
3. **Monadic Composition** (`PayWeave.hs`) binding pipeline stages together via `Either String PaymentExecutionPlan`.

## Deployment Architecture Disclaimer
- **Streamlit Cloud Portable Runtime**: The deployed Streamlit web application executes an equivalent Python reference runtime (`payweave/runtime/functional_core.py`) to guarantee zero-dependency portable deployment on cloud servers without requiring GHC/Haskell compilers.
- **Haskell Codebase**: The Haskell files in this directory serve as the formal reference specification for technical review and interview evaluation of the functional programming architecture.
