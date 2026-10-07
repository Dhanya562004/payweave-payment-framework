-- PayWeave Haskell Functional Core: Main Pipeline Composition
-- Demonstrates monadic composition via Either monad >>= (bind) operators

module PayWeave where

import PaymentTypes
import Rules
import Routing

-- | Pure Functional Pipeline: Request -> ExecutionPlan
buildPlan :: MerchantConfig -> [ProviderHealth] -> PaymentRequest -> Either String PaymentExecutionPlan
buildPlan cfg providers req = do
  validReq <- validateRequest cfg req
  riskDec  <- evaluateRisk cfg validReq
  let authDec  = determineAuth cfg validReq riskDec
  let (SelectedPSP target score fallbacks rationale) = selectBestProvider providers
  let req2FA   = case authDec of
                   Auth2FARequired _ -> True
                   AuthFrictionless  -> False
  Right $ ExecutionPlan
    { planReqId          = requestId req
    , planTargetProvider = target
    , planRequires2FA    = req2FA
    , planFallbackChain  = fallbacks
    , planEstimatedLat   = 120.0
    , planRationale      = rationale
    }
