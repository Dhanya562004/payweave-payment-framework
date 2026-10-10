-- | PayWeave Haskell Functional Core: Multi-Factor Scoring & Resilient Provider Routing
-- Pure immutable scoring, deterministic tie-breaking, and circuit-breaker awareness.
module Routing where

import PaymentTypes
import Data.List (sortBy)

-- | Pure function: Multi-factor weighted score calculation for an operational provider
-- Returns 0.0 if provider is unhealthy or its circuit breaker is OPEN.
computeProviderScore :: ProviderHealth -> Double
computeProviderScore p
  | not (isHealthy p) = 0.0
  | circuitBreaker p == Open = 0.0
  | otherwise =
      let succScore = 0.40 * successRate p
          latScore  = 0.30 * max 0.0 (1.0 - (latencyMs p / 500.0))
          hlthScore = 0.15 * (if isHealthy p && circuitBreaker p /= Open then 1.0 else 0.0)
          costScore = 0.10 * max 0.0 (1.0 - costScore p)
          capScore  = 0.05 * max 0.0 (min 1.0 (capacityPct p / 100.0))
      in succScore + latScore + hlthScore + costScore + capScore

-- | Deterministic comparator: Higher score wins. On identical score, alphabetical providerId breaks tie.
compareProviders :: (Provider, Double, ProviderHealth) -> (Provider, Double, ProviderHealth) -> Ordering
compareProviders (idA, scoreA, _) (idB, scoreB, _)
  | abs (scoreA - scoreB) > 1e-6 = if scoreA > scoreB then LT else GT
  | otherwise = compare idA idB

-- | Pure function: Rank providers and select best candidate
-- Guarantees that:
-- 1. Unhealthy or Open-circuit providers are strictly excluded.
-- 2. If no candidate is healthy, returns Left NoHealthyProvider.
-- 3. Identical inputs yield deterministic decisions with consistent tie-breaking.
chooseProvider :: [ProviderHealth] -> Either PaymentError RoutingDecision
chooseProvider providers =
  let eligible = filter (\p -> isHealthy p && circuitBreaker p /= Open) providers
      scored   = map (\p -> (providerId p, computeProviderScore p, p)) eligible
      sorted   = sortBy compareProviders scored
  in case sorted of
    [] -> Left NoHealthyProvider
    ((bestId, score, _):rest) ->
      let fallbacks = map (\(pid, _, _) -> pid) rest
          desc      = "Selected " ++ bestId ++ " with routing score " ++ show (roundTo3 score)
      in Right (SelectedPSP bestId (roundTo3 score) fallbacks desc)

roundTo3 :: Double -> Double
roundTo3 f = fromInteger (round (f * 1000.0)) / 1000.0
