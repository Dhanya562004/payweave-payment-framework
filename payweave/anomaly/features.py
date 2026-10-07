"""
PayWeave Anomaly Telemetry Feature Extractor.
Calculates rolling statistical features (mean, std dev, z-scores) over payment telemetry streams.
"""

import math
from typing import List, Dict, Any


class FeatureExtractor:
    """Computes statistical metrics over telemetry batches."""

    @staticmethod
    def calculate_stats(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"mean": 0.0, "std": 0.0, "count": 0}
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / (n if n > 1 else 1)
        std = math.sqrt(variance)
        return {"mean": mean, "std": std, "count": n}

    @staticmethod
    def calculate_z_score(val: float, mean: float, std: float) -> float:
        if std == 0.0:
            return 0.0
        return (val - mean) / std
