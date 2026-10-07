-- PayWeave Haskell Functional Core: Intelligent Provider Scoring & Routing
-- Demonstrates higher-order functions, list transformations, and pure immutable scoring

module Routing where

import PaymentTypes
import Data.List (sortOn)

-- | Pure function: Compute routing score for a single provider
computeProviderScore :: ProviderHealth -> Double
computeProviderScore p
  | not (isHealthy p) = 0.0
  | otherwise = (0.5 * successRate p) + (0.3 * (1.0 - (latencyMs p / 500.0))) + (0.2 * (1.0 - costScore p))

-- | Pure function: Rank providers and construct RoutingDecision
selectBestProvider :: [ProviderHealth] -> RoutingDecision
selectBestProvider providers =
  let scored = map (\p -> (providerId p, computeProviderScore p, p)) providers
      sorted = reverse (sortOn (\(_, s, _) -> s) scored)
  in case sorted of
    [] -> SelectedPSP "psp-b" 0.0 [] "No providers available."
    ((bestId, score, p):rest) ->
      let fallbacks = map (\(pid, _, _) -> pid) rest
          rationale = "Selected " ++ bestId ++ " with score " ++ show score
      in SelectedPSP bestId score fallbacks rationale
