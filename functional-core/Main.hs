-- | PayWeave Haskell Functional Core: Standalone Executable Demonstration
module Main where

import PaymentTypes
import PaymentRules
import Routing
import PayWeave

main :: IO ()
main = do
  putStrLn "=================================================="
  putStrLn "PayWeave Haskell Functional Core Engine"
  putStrLn "=================================================="
  
  let merchantCfg = MerchantConfig
        { merchantId   = "merch_demo"
        , maxRiskScore = 0.70
        , authMode     = Adaptive
        , stepUpThresh = 0.40
        , primaryDC    = "dc1"
        , fallbackDC   = "dc2"
        }

  let providers =
        [ ProviderHealth "psp-a" 0.985 120.0 0.70 90.0 True Closed
        , ProviderHealth "psp-b" 0.990  85.0 0.85 95.0 True Closed
        , ProviderHealth "psp-c" 0.965 210.0 0.30 70.0 False Closed  -- Unhealthy
        ]

  let validReq = PaymentRequest
        { requestId  = "req_haskell_101"
        , amount     = 1500.0
        , currency   = "INR"
        , method     = UPI
        , customerId = "cust_hs_01"
        , riskScore  = 0.15
        }

  putStrLn "\n[Test 1] Processing Valid Payment Request:"
  case buildPlan merchantCfg providers validReq of
    Right plan -> do
      putStrLn "  RESULT: Success (Right PaymentExecutionPlan)"
      putStrLn ("  Target Provider: " ++ planTargetProvider plan)
      putStrLn ("  Requires 2FA:    " ++ show (planRequires2FA plan))
      putStrLn ("  Fallback Chain:  " ++ show (planFallbackChain plan))
      putStrLn ("  Rationale:       " ++ planRationale plan)
    Left err ->
      putStrLn ("  FAILURE: Unexpected error - " ++ show err)

  let invalidAmountReq = validReq { amount = -50.0 }
  putStrLn "\n[Test 2] Processing Invalid Negative Amount:"
  case buildPlan merchantCfg providers invalidAmountReq of
    Right _  -> putStrLn "  FAILURE: Expected error for negative amount, got Right."
    Left err -> putStrLn ("  RESULT: Caught Expected Error -> " ++ show err)

  let highRiskReq = validReq { riskScore = 0.95 }
  putStrLn "\n[Test 3] Processing High Risk Request:"
  case buildPlan merchantCfg providers highRiskReq of
    Right _  -> putStrLn "  FAILURE: Expected risk error, got Right."
    Left err -> putStrLn ("  RESULT: Caught Expected Error -> " ++ show err)

  putStrLn "\n[Test 4] State Transition: Pending -> Succeeded:"
  case transitionPaymentState Pending Succeeded of
    Right s  -> putStrLn ("  RESULT: Transitioned to " ++ show s)
    Left err -> putStrLn ("  FAILURE: " ++ show err)

  putStrLn "\n[Test 5] Invalid State Transition: Created -> Succeeded:"
  case transitionPaymentState Created Succeeded of
    Right s  -> putStrLn ("  FAILURE: Illegal transition accepted -> " ++ show s)
    Left err -> putStrLn ("  RESULT: Caught Expected Transition Error -> " ++ show err)

  putStrLn "\n=================================================="
  putStrLn "Haskell Functional Core Demonstration Complete."
  putStrLn "=================================================="
