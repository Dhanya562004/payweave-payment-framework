"""
PayWeave Shared State Manager.
Coordinates provider health metrics and circuit-breaker states across distributed workers.
Supports Redis-backed synchronization with automatic graceful fallback to thread-safe in-memory storage.
"""

import os
import json
import time
import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class SharedStateManager:
    """
    Distributed coordination store for routing decisions and circuit breakers.
    Uses Redis when available, falling back seamlessly to an in-memory thread-safe store.
    """

    def __init__(self, redis_url: Optional[str] = None, client: Any = None):
        self._lock = threading.Lock()
        self._memory_health: Dict[str, Dict[str, Any]] = {}
        self._memory_circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self._client = client
        self._use_redis = False

        if client is not None:
            self._client = client
            self._use_redis = True
        elif REDIS_AVAILABLE:
            url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                c = redis.from_url(
                    url,
                    socket_connect_timeout=0.2,
                    socket_timeout=0.2,
                    decode_responses=True
                )
                c.ping()
                self._client = c
                self._use_redis = True
                logger.info("Connected to Redis shared state store at %s", url)
            except Exception as e:
                self._use_redis = False
                logger.info("Redis unreachable (%s). Using thread-safe in-memory fallback.", str(e))
        else:
            self._use_redis = False

    @property
    def is_using_redis(self) -> bool:
        """Returns True if backed by active Redis connection, False if in-memory fallback."""
        return self._use_redis

    def set_provider_health(self, provider_id: str, health_data: Dict[str, Any], ttl_seconds: int = 3600) -> None:
        """Saves provider health telemetry."""
        payload = {**health_data, "last_updated": time.time()}
        if self._use_redis and self._client:
            try:
                key = f"payweave:health:{provider_id}"
                self._client.set(key, json.dumps(payload), ex=ttl_seconds)
                return
            except Exception as e:
                logger.warning("Redis write error: %s; falling back to in-memory store.", e)

        with self._lock:
            self._memory_health[provider_id] = payload

    def get_provider_health(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves provider health telemetry."""
        if self._use_redis and self._client:
            try:
                key = f"payweave:health:{provider_id}"
                data = self._client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning("Redis read error: %s; falling back to in-memory store.", e)

        with self._lock:
            val = self._memory_health.get(provider_id)
            return dict(val) if val else None

    def set_circuit_breaker_state(self, provider_id: str, cb_data: Dict[str, Any], ttl_seconds: int = 3600) -> None:
        """Persists circuit breaker status (state, failure_count, last_state_change)."""
        payload = {**cb_data, "updated_at": time.time()}
        if self._use_redis and self._client:
            try:
                key = f"payweave:circuit_breaker:{provider_id}"
                self._client.set(key, json.dumps(payload), ex=ttl_seconds)
                return
            except Exception as e:
                logger.warning("Redis write error: %s; falling back to in-memory store.", e)

        with self._lock:
            self._memory_circuit_breakers[provider_id] = payload

    def get_circuit_breaker_state(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves circuit breaker status for provider."""
        if self._use_redis and self._client:
            try:
                key = f"payweave:circuit_breaker:{provider_id}"
                data = self._client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning("Redis read error: %s; falling back to in-memory store.", e)

        with self._lock:
            val = self._memory_circuit_breakers.get(provider_id)
            return dict(val) if val else None

    def reset_state(self) -> None:
        """Clears memory state (and flush matching keys in Redis if active)."""
        with self._lock:
            self._memory_health.clear()
            self._memory_circuit_breakers.clear()

        if self._use_redis and self._client:
            try:
                keys = self._client.keys("payweave:*")
                if keys:
                    self._client.delete(*keys)
            except Exception as e:
                logger.warning("Redis reset error: %s", e)
