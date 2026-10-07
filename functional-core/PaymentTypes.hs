-- PayWeave Haskell Functional Core: Type Definitions
-- Demonstrates Pure Functional Architecture using Algebraic Data Types (ADTs)

module PaymentTypes where

import Data.Time (UTCTime)

-- | Payment Methods ADT
data PaymentMethod = UPI | Card | NetBanking
  deriving (Eq, Show, Read)

-- | Authentication Security Mode ADT
data AuthMode = Frictionless | Adaptive | Always2FA
  deriving (Eq, Show, Read)

-- | Incoming Payment Request Record
data PaymentRequest = PaymentRequest
  { requestId     :: String
  , amount        :: Double
  , currency      :: String
  , method        :: PaymentMethod
  , customerId    :: String
  , riskScore     :: Double
  } deriving (Eq, Show)

-- | Provider Operational Metrics ADT
data ProviderHealth = ProviderHealth
  { providerId    :: String
  , successRate   :: Double
  , latencyMs     :: Double
  , costScore     :: Double
  , isHealthy     :: Bool
  } deriving (Eq, Show)

-- | Merchant Declarative Configuration Record
data MerchantConfig = MerchantConfig
  { merchantId    :: String
  , maxRiskScore  :: Double
  , authMode      :: AuthMode
  , stepUpThresh  :: Double
  , primaryDC     :: String
  , fallbackDC    :: String
  } deriving (Eq, Show)

-- | Decisions ADTs
data RiskDecision = RiskAllowed Double | RiskBlocked Double String
  deriving (Eq, Show)

data AuthDecision = Auth2FARequired String | AuthFrictionless
  deriving (Eq, Show)

data RoutingDecision = SelectedPSP String Double [String] String
  deriving (Eq, Show)

-- | Immutable Payment Execution Plan ADT
data PaymentExecutionPlan = ExecutionPlan
  { planReqId           :: String
  , planTargetProvider  :: String
  , planRequires2FA     :: Bool
  , planFallbackChain   :: [String]
  , planEstimatedLat    :: Double
  , planRationale       :: String
  } deriving (Eq, Show)
