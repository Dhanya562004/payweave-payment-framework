-- PayWeave Haskell Functional Core: Type Definitions & Domain ADTs
-- Demonstrates pure functional architecture, immutable data models, and explicit domain errors.

module PaymentTypes where

-- | Supported Payment Methods ADT
data PaymentMethod = UPI | Card | NetBanking | Wallet
  deriving (Eq, Show, Read)

-- | Provider Identification Type Alias
type Provider = String

-- | Explicit Domain Failure Types ADT
-- Prefers type-safe error structures over uncontrolled exception throwing
data PaymentError
  = InvalidAmount Double
  | UnsupportedCurrency String
  | RiskThresholdExceeded Double Double
  | InvalidCustomer String
  | NoHealthyProvider
  | SystemError String
  deriving (Eq, Show)

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

-- | Provider Operational Metrics Record
data ProviderHealth = ProviderHealth
  { providerId    :: Provider
  , successRate   :: Double
  , latencyMs     :: Double
  , costScore     :: Double
  , capacityPct   :: Double
  , isHealthy     :: Bool
  } deriving (Eq, Show)

-- | Merchant Configuration Record
data MerchantConfig = MerchantConfig
  { merchantId    :: String
  , maxRiskScore  :: Double
  , authMode      :: AuthMode
  , stepUpThresh  :: Double
  , primaryDC     :: String
  , fallbackDC    :: String
  } deriving (Eq, Show)

-- | Domain Decision ADTs
data RiskDecision = RiskAllowed Double | RiskBlocked Double String
  deriving (Eq, Show)

data AuthenticationDecision
  = Auth2FARequired String
  | AuthFrictionless
  deriving (Eq, Show)

data RoutingDecision = SelectedPSP
  { selectedProvider :: Provider
  , routingScore     :: Double
  , fallbackChain    :: [Provider]
  , rationale        :: String
  } deriving (Eq, Show)

-- | Immutable Payment Execution Plan Record
data PaymentExecutionPlan = ExecutionPlan
  { planReqId           :: String
  , planTargetProvider  :: Provider
  , planRequires2FA     :: Bool
  , planFallbackChain   :: [Provider]
  , planEstimatedLat    :: Double
  , planRationale       :: String
  } deriving (Eq, Show)
