-- PayWeave Haskell Functional Core: Pure Payment Business Rules
-- Demonstrates pure functions, pattern matching, and Either monadic error handling

module PaymentRules where

import PaymentTypes

-- | Pure function: Validate request invariants using Either PaymentError
validatePaymentRequest :: MerchantConfig -> PaymentRequest -> Either PaymentError PaymentRequest
validatePaymentRequest cfg req
  | amount req <= 0.0 = Left (InvalidAmount (amount req))
  | currency req /= "INR" && currency req /= "USD" = Left (UnsupportedCurrency (currency req))
  | null (customerId req) = Left (InvalidCustomer "Customer ID cannot be empty.")
  | otherwise = Right req

-- | Pure function: Evaluate fraud risk using explicit error type
evaluateRisk :: MerchantConfig -> PaymentRequest -> Either PaymentError RiskDecision
evaluateRisk cfg req
  | riskScore req > maxRiskScore cfg = Left (RiskThresholdExceeded (riskScore req) (maxRiskScore cfg))
  | otherwise = Right (RiskAllowed (riskScore req))

-- | Pure function: Decide authentication mode (Frictionless vs 2FA Step-Up)
decideAuthentication :: MerchantConfig -> PaymentRequest -> RiskDecision -> AuthenticationDecision
decideAuthentication cfg req (RiskAllowed score) = case authMode cfg of
  Always2FA    -> Auth2FARequired "Merchant policy requires mandatory 2FA."
  Frictionless -> if amount req > 50000.0
                  then Auth2FARequired "High transaction value step-up triggered (> 50,000)."
                  else AuthFrictionless
  Adaptive     -> if score >= stepUpThresh cfg || amount req > 20000.0
                  then Auth2FARequired "Adaptive risk step-up threshold triggered."
                  else AuthFrictionless
decideAuthentication _ _ (RiskBlocked _ reason) = Auth2FARequired ("Risk blocked: " ++ reason)
