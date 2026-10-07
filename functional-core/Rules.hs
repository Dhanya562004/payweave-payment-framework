-- PayWeave Haskell Functional Core: Pure Business Rules Engine
-- Demonstrates pure functions, pattern matching, and Either monadic error handling

module Rules where

import PaymentTypes

-- | Pure function: Validate request parameters
validateRequest :: MerchantConfig -> PaymentRequest -> Either String PaymentRequest
validateRequest cfg req
  | amount req <= 0 = Left "Amount must be strictly positive."
  | currency req /= "INR" && currency req /= "USD" = Left "Unsupported currency."
  | otherwise = Right req

-- | Pure function: Evaluate fraud risk
evaluateRisk :: MerchantConfig -> PaymentRequest -> Either String RiskDecision
evaluateRisk cfg req
  | riskScore req > maxRiskScore cfg = Left ("Risk score " ++ show (riskScore req) ++ " exceeds threshold.")
  | otherwise = Right (RiskAllowed (riskScore req))

-- | Pure function: Determine 2FA requirement using Pattern Matching
determineAuth :: MerchantConfig -> PaymentRequest -> RiskDecision -> AuthDecision
determineAuth cfg req (RiskAllowed score) = case authMode cfg of
  Always2FA    -> Auth2FARequired "Merchant policy forces 2FA."
  Frictionless -> if amount req > 50000.0
                  then Auth2FARequired "High value transaction step-up."
                  else AuthFrictionless
  Adaptive     -> if score >= stepUpThresh cfg || amount req > 20000.0
                  then Auth2FARequired "Adaptive risk step-up triggered."
                  else AuthFrictionless
determineAuth _ _ (RiskBlocked _ reason) = Auth2FARequired ("Risk blocked: " ++ reason)
