-- | PayWeave Haskell Functional Core: Pure Payment Business Rules & State Transitions
-- Pure functions, exhaustive pattern matching, and Either monadic error handling.
module PaymentRules where

import PaymentTypes

-- | Pure function: Validate request invariants using Either PaymentError
-- Guarantees invalid amounts, unsupported currencies, or empty customer IDs are rejected.
validatePaymentRequest :: MerchantConfig -> PaymentRequest -> Either PaymentError PaymentRequest
validatePaymentRequest _ req
  | amount req <= 0.0 = Left (InvalidAmount (amount req))
  | currency req /= "INR" && currency req /= "USD" && currency req /= "EUR" = Left (UnsupportedCurrency (currency req))
  | null (customerId req) = Left (InvalidCustomer "Customer ID cannot be empty.")
  | otherwise = Right req

-- | Pure function: Validate merchant configuration invariants
validateMerchantConfig :: MerchantConfig -> Either PaymentError MerchantConfig
validateMerchantConfig cfg
  | maxRiskScore cfg < 0.0 || maxRiskScore cfg > 1.0 =
      Left (InvalidMerchantConfig "maxRiskScore must be in range [0.0, 1.0]")
  | stepUpThresh cfg < 0.0 || stepUpThresh cfg > 1.0 =
      Left (InvalidMerchantConfig "stepUpThresh must be in range [0.0, 1.0]")
  | null (merchantId cfg) =
      Left (InvalidMerchantConfig "merchantId cannot be empty")
  | otherwise = Right cfg

-- | Pure function: Evaluate fraud risk against configured thresholds
evaluateRisk :: MerchantConfig -> PaymentRequest -> Either PaymentError RiskDecision
evaluateRisk cfg req
  | riskScore req > maxRiskScore cfg =
      Left (RiskThresholdExceeded (riskScore req) (maxRiskScore cfg))
  | otherwise =
      Right (RiskAllowed (riskScore req))

-- | Pure function: Decide authentication requirement (Frictionless vs 2FA Step-Up)
decideAuthentication :: MerchantConfig -> PaymentRequest -> RiskDecision -> AuthenticationDecision
decideAuthentication cfg req (RiskAllowed score) = case authMode cfg of
  Always2FA    -> Auth2FARequired "Merchant policy enforces mandatory 2FA."
  Frictionless -> if amount req > 50000.0
                  then Auth2FARequired "High transaction value step-up triggered (> 50,000)."
                  else AuthFrictionless
  Adaptive     -> if score >= stepUpThresh cfg || amount req > 20000.0
                  then Auth2FARequired "Adaptive risk step-up threshold triggered."
                  else AuthFrictionless
decideAuthentication _ _ (RiskBlocked _ reason) =
  Auth2FARequired ("Risk blocked: " ++ reason)

-- | Pure function: State Machine Transition Logic
-- CREATED -> PENDING -> SUCCEEDED / FAILED / UNCERTAIN_TIMEOUT
-- UNCERTAIN_TIMEOUT -> SUCCEEDED / FAILED
-- All invalid transitions return Left (InvalidStateTransition from to)
transitionPaymentState :: PaymentState -> PaymentState -> Either PaymentError PaymentState
transitionPaymentState Created Pending          = Right Pending
transitionPaymentState Pending Succeeded        = Right Succeeded
transitionPaymentState Pending Failed           = Right Failed
transitionPaymentState Pending UncertainTimeout = Right UncertainTimeout
transitionPaymentState UncertainTimeout Succeeded = Right Succeeded
transitionPaymentState UncertainTimeout Failed    = Right Failed
transitionPaymentState from to                  = Left (InvalidStateTransition from to)

-- | Pure function: Retry Eligibility Rule
-- Technical timeouts and circuit errors are retryable; business/validation errors NEVER are.
isRetryEligible :: PaymentError -> Bool
isRetryEligible (CircuitBreakerOpen _) = True
isRetryEligible (SystemError _)        = True
isRetryEligible NoHealthyProvider      = False
isRetryEligible (InvalidAmount _)      = False
isRetryEligible (UnsupportedCurrency _) = False
isRetryEligible (RiskThresholdExceeded _ _) = False
isRetryEligible (InvalidCustomer _)    = False
isRetryEligible (InvalidMerchantConfig _) = False
isRetryEligible (InvalidStateTransition _ _) = False
isRetryEligible (InvalidPaymentMethod _) = False
