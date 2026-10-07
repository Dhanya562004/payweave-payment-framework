-- PayWeave Haskell Functional Core: Monadic Pipeline Composition
-- Demonstrates monadic composition via Either PaymentError monad >>= (bind) operators

module PayWeave where

import PaymentTypes
import PaymentRules
import Routing

-- | Pure Functional Pipeline: Request -> ExecutionPlan
buildPlan :: MerchantConfig -> [ProviderHealth] -> PaymentRequest -> Either PaymentError PaymentExecutionPlan
buildPlan cfg providers req = do
  validReq <- validatePaymentRequest cfg req
  riskDec  <- evaluateRisk cfg validReq
  routing  <- chooseProvider providers
  let authDec = decideAuthentication cfg validReq riskDec
  let req2FA  = case authDec of
                  Auth2FARequired _ -> True
                  AuthFrictionless  -> False
  return ExecutionPlan
    { planReqId          = requestId req
    , planTargetProvider = selectedProvider routing
    , planRequires2FA    = req2FA
    , planFallbackChain  = fallbackChain routing
    , planEstimatedLat   = 120.0
    , planRationale      = rationale routing
    }
