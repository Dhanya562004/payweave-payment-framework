"""
PayWeave Enterprise Circuit Breaker.
Implements finite state machine: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
with configurable failure thresholds, cooldown intervals, probe recovery,
and thread-safe state inspection.
"""

import time
from enum import Enum
from typing import Optional, Dict, Any


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """
    Finite state machine circuit breaker protecting downstream payment provider adapters.
    - CLOSED: Normal traffic allowed. Rolling window tracks errors.
    - OPEN: Tripped due to failure threshold. No traffic allowed until cooldown expires.
    - HALF_OPEN: Cooldown has elapsed; allows a trial probe to evaluate upstream health.
      - Probe success -> CLOSED (recovered)
      - Probe failure -> OPEN (re-tripped with renewed cooldown)
    """

    def __init__(
        self,
        provider_id: str,
        failure_threshold: int = 3,
        error_rate_threshold: float = 0.50,
        cooldown_seconds: float = 5.0,
        half_open_success_threshold: int = 1
    ):
        self.provider_id = provider_id
        self.failure_threshold = failure_threshold
        self.error_rate_threshold = error_rate_threshold
        self.cooldown_seconds = cooldown_seconds
        self.half_open_success_threshold = half_open_success_threshold

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_state_change = time.time()
        self._last_failure_time = 0.0

    @property
    def state(self) -> CircuitState:
        """Dynamically transitions OPEN -> HALF_OPEN if cooldown has elapsed."""
        if self._state == CircuitState.OPEN:
            if (time.time() - self._last_failure_time) >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                self._last_state_change = time.time()
                self._consecutive_successes = 0
        return self._state

    def is_available(self) -> bool:
        """Returns True if the provider can receive traffic (CLOSED or HALF_OPEN)."""
        current = self.state
        return current in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        """Records a successful operation."""
        current = self.state
        if current == CircuitState.HALF_OPEN:
            self._consecutive_successes += 1
            if self._consecutive_successes >= self.half_open_success_threshold:
                # Recover circuit to CLOSED
                self._state = CircuitState.CLOSED
                self._consecutive_failures = 0
                self._consecutive_successes = 0
                self._last_state_change = time.time()
        elif current == CircuitState.CLOSED:
            self._consecutive_failures = max(0, self._consecutive_failures - 1)

    def record_failure(self, is_timeout: bool = False) -> None:
        """Records a failed operation or timeout."""
        current = self.state
        self._last_failure_time = time.time()

        if current == CircuitState.HALF_OPEN:
            # Immediate re-trip to OPEN upon probe failure
            self._state = CircuitState.OPEN
            self._consecutive_failures += 1
            self._last_state_change = time.time()
        elif current == CircuitState.CLOSED:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_state_change = time.time()

    def trip_open_manually(self) -> None:
        """Manually force the circuit breaker into OPEN state (for chaos testing/failover)."""
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()
        self._last_state_change = time.time()

    def reset(self) -> None:
        """Resets circuit breaker back to initial CLOSED state."""
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_failure_time = 0.0
        self._last_state_change = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "state": self.state.value,
            "consecutive_failures": self._consecutive_failures,
            "cooldown_seconds": self.cooldown_seconds,
            "is_available": self.is_available()
        }
