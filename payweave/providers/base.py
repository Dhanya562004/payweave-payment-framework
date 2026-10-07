"""
PayWeave Provider Adapter Base Interface.
Defines abstract contracts for mock PSP integrations and synthetic telemetry data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import uuid
import time
import random


class ProviderStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    DEGRADED = "DEGRADED"


@dataclass
class TransactionResult:
    transaction_id: str
    request_id: str
    provider_id: str
    status: ProviderStatus
    response_code: str
    latency_ms: float
    message: str
    timestamp: float = time.time()


class BasePSPAdapter(ABC):
    """Abstract Base Class for payment service provider integrations."""

    def __init__(self, provider_id: str, name: str, default_success_rate: float,
                 default_latency_ms: float, cost_score: float, capacity_pct: float = 100.0):
        self.provider_id = provider_id
        self.name = name
        self.default_success_rate = default_success_rate
        self.default_latency_ms = default_latency_ms
        self.cost_score = cost_score  # 0.0 (cheapest) to 1.0 (most expensive)
        self.capacity_pct = capacity_pct

        # Dynamic simulation parameters
        self.current_success_rate = default_success_rate
        self.current_latency_ms = default_latency_ms
        self.is_available = True
        self.latency_spike = False

    @abstractmethod
    def process_payment(self, request_id: str, amount: float, currency: str,
                        method: str, force_fail: bool = False) -> TransactionResult:
        pass

    def simulate_degradation(self, latency_multiplier: float = 3.0, success_drop: float = 0.3) -> None:
        """Injects simulated network degradation or provider failure."""
        self.current_latency_ms = self.default_latency_ms * latency_multiplier
        self.current_success_rate = max(0.05, self.default_success_rate - success_drop)
        self.latency_spike = True

    def recover(self) -> None:
        """Restores normal operating health metrics."""
        self.current_success_rate = self.default_success_rate
        self.current_latency_ms = self.default_latency_ms
        self.is_available = True
        self.latency_spike = False
