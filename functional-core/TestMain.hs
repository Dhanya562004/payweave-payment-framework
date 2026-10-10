-- | PayWeave Haskell Functional Core: Property-Based & Invariant Test Suite
module Main where

import System.Exit (exitFailure, exitSuccess)
import Control.Monad (unless)
import Test.QuickCheck

import PaymentTypes
import PaymentRules
import Routing
import PayWeave

-- | Sample valid test configuration
sampleConfig :: MerchantConfig
sampleConfig = MerchantConfig
  { merchantId   = "merch_prop_test"
  , maxRiskScore = 0.50
  , authMode     = Adaptive
  , stepUpThresh = 0.25
  , primaryDC    = "dc-mumbai"
  , fallbackDC   = "dc-bengaluru"
  }

-- | Sample valid base request
sampleReq :: PaymentRequest
sampleReq = PaymentRequest
  { requestId  = "req_test_01"
  , amount     = 1000.0
  , currency   = "INR"
  , method     = UPI
  , customerId = "cust_valid"
  , riskScore  = 0.10
  }

-- | QuickCheck Property 1: Non-positive amount always fails with InvalidAmount
prop_nonPositiveAmountRejected :: Double -> Property
prop_nonPositiveAmountRejected amt =
  amt <= 0 ==>
    case validatePaymentRequest sampleConfig (sampleReq { amount = amt }) of
      Left (InvalidAmount a) -> a <= 0
      _                      -> False

-- | QuickCheck Property 2: Routing never selects an unhealthy or open-circuit provider
prop_routingNeverSelectsUnhealthy :: [Bool] -> [Bool] -> Property
prop_routingNeverSelectsUnhealthy healthFlags circuitFlags =
  let count = min (length healthFlags) (length circuitFlags)
      pids  = ["psp-" ++ show i | i <- [1..count]]
      providers = zipWith3 (\pid h isOp ->
                    ProviderHealth pid 0.95 100.0 0.50 80.0 h (if isOp then Open else Closed)
                  ) pids (take count healthFlags) (take count circuitFlags)
  in case chooseProvider providers of
    Left NoHealthyProvider -> property True
    Right (SelectedPSP chosen _ _ _) ->
      property $ any (\p -> providerId p == chosen && isHealthy p && circuitBreaker p /= Open) providers
    Left _ -> property False

-- | QuickCheck Property 3: If all providers are unhealthy, routing must return Left NoHealthyProvider
prop_allUnhealthyYieldsNoHealthyProvider :: [Double] -> Property
prop_allUnhealthyYieldsNoHealthyProvider latencies =
  let providers = [ ProviderHealth ("psp-" ++ show i) 0.90 lat 0.5 80.0 False Closed
                  | (i, lat) <- zip ([1..5] :: [Int]) latencies ]
  in property $ chooseProvider providers == Left NoHealthyProvider

-- | QuickCheck Property 4: Determinism: Identical inputs produce identical execution plans
prop_pureDeterminism :: Double -> Double -> Property
prop_pureDeterminism amt rScore =
  amt > 0 && rScore >= 0.0 && rScore <= 1.0 ==>
    let req = sampleReq { amount = amt, riskScore = rScore }
        ps  = [ ProviderHealth "psp-a" 0.98 120.0 0.6 90.0 True Closed
              , ProviderHealth "psp-b" 0.99  90.0 0.8 95.0 True Closed ]
    in buildPlan sampleConfig ps req == buildPlan sampleConfig ps req

-- | QuickCheck Property 5: Retry eligibility consistency
prop_retryEligibilityInvariants :: Property
prop_retryEligibilityInvariants = property $
  isRetryEligible (CircuitBreakerOpen "psp-a") == True &&
  isRetryEligible (SystemError "timeout") == True &&
  isRetryEligible (InvalidAmount (-10.0)) == False &&
  isRetryEligible (UnsupportedCurrency "XYZ") == False &&
  isRetryEligible (RiskThresholdExceeded 0.9 0.3) == False &&
  isRetryEligible NoHealthyProvider == False

-- | Deterministic State Machine Transition Invariant Checks
testStateTransitions :: Bool
testStateTransitions =
  -- Valid transitions
  transitionPaymentState Created Pending == Right Pending &&
  transitionPaymentState Pending Succeeded == Right Succeeded &&
  transitionPaymentState Pending Failed == Right Failed &&
  transitionPaymentState Pending UncertainTimeout == Right UncertainTimeout &&
  transitionPaymentState UncertainTimeout Succeeded == Right Succeeded &&
  transitionPaymentState UncertainTimeout Failed == Right Failed &&
  -- Invalid transitions
  transitionPaymentState Created Succeeded == Left (InvalidStateTransition Created Succeeded) &&
  transitionPaymentState Succeeded Pending == Left (InvalidStateTransition Succeeded Pending) &&
  transitionPaymentState Failed Pending == Left (InvalidStateTransition Failed Pending)

-- | Deterministic Currency & Validation Checks
testValidationBoundaries :: Bool
testValidationBoundaries =
  case validatePaymentRequest sampleConfig (sampleReq { currency = "JPY" }) of
    Left (UnsupportedCurrency "JPY") -> True
    _                                -> False

main :: IO ()
main = do
  putStrLn "=================================================="
  putStrLn "Running PayWeave Functional Core QuickCheck Suite"
  putStrLn "=================================================="

  r1 <- quickCheckResult (withMaxSuccess 100 prop_nonPositiveAmountRejected)
  r2 <- quickCheckResult (withMaxSuccess 100 prop_routingNeverSelectsUnhealthy)
  r3 <- quickCheckResult (withMaxSuccess 100 prop_allUnhealthyYieldsNoHealthyProvider)
  r4 <- quickCheckResult (withMaxSuccess 100 prop_pureDeterminism)
  r5 <- quickCheckResult (withMaxSuccess 100 prop_retryEligibilityInvariants)

  putStrLn "\nRunning Deterministic Invariant Checks..."
  let stOk = testStateTransitions
  let valOk = testValidationBoundaries
  putStrLn $ "  State machine transitions: " ++ if stOk then "PASSED" else "FAILED"
  putStrLn $ "  Validation boundaries:     " ++ if valOk then "PASSED" else "FAILED"

  let allSuccess = isSuccess r1 && isSuccess r2 && isSuccess r3 && isSuccess r4 && isSuccess r5 && stOk && valOk
  if allSuccess
    then do
      putStrLn "\nAll 7 QuickCheck and Deterministic Invariant Suites Passed!"
      exitSuccess
    else do
      putStrLn "\nFunctional Core Test Failures Detected!"
      exitFailure
