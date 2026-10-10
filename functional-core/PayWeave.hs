-- | PayWeave Haskell Functional Core: Monadic Pipeline Composition
-- Composes validation, fraud risk, provider routing, and authentication via Either monad.
module PayWeave where

import PaymentTypes
import PaymentRules
import Routing

-- | Pure Functional Pipeline: MerchantConfig -> [ProviderHealth] -> PaymentRequest -> Either PaymentError PaymentExecutionPlan
buildPlan :: MerchantConfig -> [ProviderHealth] -> PaymentRequest -> Either PaymentError PaymentExecutionPlan
buildPlan cfg providers req = do
  validCfg <- validateMerchantConfig cfg
  validReq <- validatePaymentRequest validCfg req
  riskDec  <- evaluateRisk validCfg validReq
  routing  <- chooseProvider providers
  let authDec = decideAuthentication validCfg validReq riskDec
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
