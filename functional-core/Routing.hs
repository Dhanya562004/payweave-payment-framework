-- PayWeave Haskell Functional Core: Multi-Factor Scoring & Provider Routing
-- Demonstrates higher-order functions, list transformations, and pure immutable scoring

module Routing where

import PaymentTypes
import Data.List (sortOn)

-- | Pure function: Compute weighted score for a single provider
computeProviderScore :: ProviderHealth -> Double
computeProviderScore p
  | not (isHealthy p) = 0.0
  | otherwise = (0.40 * successRate p)
              + (0.30 * max 0.0 (1.0 - (latencyMs p / 500.0)))
              + (0.15 * (if isHealthy p then 1.0 else 0.0))
              + (0.10 * max 0.0 (1.0 - costScore p))
              + (0.05 * max 0.0 (min 1.0 (capacityPct p / 100.0)))

-- | Pure function: Rank providers and select best routing decision
chooseProvider :: [ProviderHealth] -> Either PaymentError RoutingDecision
chooseProvider providers =
  let healthyOnly = filter isHealthy providers
      scored = map (\p -> (providerId p, computeProviderScore p, p)) healthyOnly
      sorted = reverse (sortOn (\(_, s, _) -> s) scored)
  in case sorted of
    [] -> Left NoHealthyProvider
    ((bestId, score, p):rest) ->
      let fallbacks = map (\(pid, _, _) -> pid) rest
          desc = "Selected " ++ bestId ++ " with routing score " ++ show (roundTo3 score)
      in Right (SelectedPSP bestId score fallbacks desc)

roundTo3 :: Double -> Double
roundTo3 f = fromInteger (round (f * 1000.0)) / 1000.0
