#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Circuit Breaker Pattern Implementation
Provides resilience to system failures by preventing cascading failures
States: CLOSED (normal) → OPEN (fail fast) → HALF_OPEN (retry testing) → CLOSED
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, Dict
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"          # Normal operation
    OPEN = "OPEN"              # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"    # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5         # Failures to trigger OPEN
    recovery_timeout: int = 30         # Seconds to wait before HALF_OPEN
    success_threshold: int = 2         # Successes in HALF_OPEN to close
    time_window: int = 60              # Time window for counting failures (seconds)
    service_name: str = "service"      # Name for logging


@dataclass
class CircuitBreakerMetrics:
    """Track circuit breaker metrics"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    total_failures: int = 0
    total_successes: int = 0
    total_calls: int = 0
    failures_in_window: Dict[float, int] = field(default_factory=dict)


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation
    Prevents cascading failures by failing fast when service is unavailable
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.metrics = CircuitBreakerMetrics()
        self._lock = {}  # Simple in-memory lock tracking

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result of function call

        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: Original exception from func if it fails
        """
        if self.metrics.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.metrics.state = CircuitState.HALF_OPEN
                self.metrics.success_count = 0
                logger.info(
                    f"🔄 {self.config.service_name}: Circuit HALF_OPEN, attempting recovery"
                )
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker OPEN for {self.config.service_name}. "
                    f"Opened at {self.metrics.opened_at}"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        self.metrics.total_calls += 1
        self.metrics.total_successes += 1

        if self.metrics.state == CircuitState.HALF_OPEN:
            self.metrics.success_count += 1
            if self.metrics.success_count >= self.config.success_threshold:
                self._close()
        elif self.metrics.state == CircuitState.CLOSED:
            # Reset failure count on success in CLOSED state
            self.metrics.failure_count = 0

        logger.debug(
            f"✅ {self.config.service_name}: Success. State={self.metrics.state.value}, "
            f"Successes={self.metrics.success_count}"
        )

    def _on_failure(self):
        """Handle failed call"""
        self.metrics.total_calls += 1
        self.metrics.total_failures += 1
        self.metrics.failure_count += 1
        self.metrics.last_failure_time = datetime.utcnow()

        # Add to time window tracking
        current_time = time.time()
        self.metrics.failures_in_window[current_time] = 1

        # Clean old entries from window
        cutoff = current_time - self.config.time_window
        self.metrics.failures_in_window = {
            t: count for t, count in self.metrics.failures_in_window.items()
            if t > cutoff
        }

        logger.warning(
            f"❌ {self.config.service_name}: Failure #{self.metrics.failure_count}. "
            f"State={self.metrics.state.value}, "
            f"Failures in window={len(self.metrics.failures_in_window)}"
        )

        if self.metrics.state == CircuitState.CLOSED:
            if len(self.metrics.failures_in_window) >= self.config.failure_threshold:
                self._open()
        elif self.metrics.state == CircuitState.HALF_OPEN:
            # Any failure in HALF_OPEN goes back to OPEN
            self._open()

    def _open(self):
        """Open circuit breaker"""
        self.metrics.state = CircuitState.OPEN
        self.metrics.opened_at = datetime.utcnow()
        self.metrics.failure_count = 0
        logger.error(
            f"🚨 {self.config.service_name}: Circuit OPEN! "
            f"Failure threshold reached ({self.config.failure_threshold} failures in "
            f"{self.config.time_window}s)"
        )

    def _close(self):
        """Close circuit breaker"""
        self.metrics.state = CircuitState.CLOSED
        self.metrics.failure_count = 0
        self.metrics.success_count = 0
        self.metrics.failures_in_window = {}
        logger.info(f"✅ {self.config.service_name}: Circuit CLOSED. Service recovered!")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.metrics.opened_at is None:
            return False

        elapsed = datetime.utcnow() - self.metrics.opened_at
        return elapsed.total_seconds() >= self.config.recovery_timeout

    def get_state(self) -> str:
        """Get current circuit state"""
        return self.metrics.state.value

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        return {
            "service": self.config.service_name,
            "state": self.metrics.state.value,
            "total_calls": self.metrics.total_calls,
            "total_successes": self.metrics.total_successes,
            "total_failures": self.metrics.total_failures,
            "failure_rate": (
                self.metrics.total_failures / self.metrics.total_calls
                if self.metrics.total_calls > 0 else 0
            ),
            "failures_in_window": len(self.metrics.failures_in_window),
            "last_failure": (
                self.metrics.last_failure_time.isoformat()
                if self.metrics.last_failure_time else None
            ),
            "opened_at": (
                self.metrics.opened_at.isoformat()
                if self.metrics.opened_at else None
            ),
        }

    def reset(self):
        """Reset circuit breaker to CLOSED state (admin override)"""
        self.metrics.state = CircuitState.CLOSED
        self.metrics.failure_count = 0
        self.metrics.success_count = 0
        self.metrics.failures_in_window = {}
        self.metrics.opened_at = None
        logger.warning(f"🔄 {self.config.service_name}: Circuit manually reset to CLOSED")


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is OPEN"""
    pass


# ==================== PREDEFINED CIRCUIT BREAKERS ====================

class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    _breakers: Dict[str, CircuitBreaker] = {}

    @property
    def breakers(self) -> Dict[str, CircuitBreaker]:
        """Access the breakers dictionary"""
        return self._breakers

    @classmethod
    def get_or_create(cls, service_name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get existing circuit breaker or create new one"""
        if service_name not in cls._breakers:
            if config is None:
                config = CircuitBreakerConfig(service_name=service_name)
            else:
                config.service_name = service_name

            cls._breakers[service_name] = CircuitBreaker(config)
            logger.info(f"📌 Created circuit breaker for {service_name}")

        return cls._breakers[service_name]

    @classmethod
    def get_all_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers"""
        return {
            name: breaker.get_metrics()
            for name, breaker in cls._breakers.items()
        }

    @classmethod
    def reset_all(cls):
        """Reset all circuit breakers (admin override)"""
        for breaker in cls._breakers.values():
            breaker.reset()
        logger.warning("🔄 All circuit breakers manually reset to CLOSED")


# ==================== SERVICE-SPECIFIC CIRCUIT BREAKERS ====================

def get_database_breaker() -> CircuitBreaker:
    """Get circuit breaker for database operations"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30,
        service_name="database"
    )
    return CircuitBreakerRegistry.get_or_create("database", config)


def get_websocket_breaker() -> CircuitBreaker:
    """Get circuit breaker for WebSocket broadcasting"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30,
        service_name="websocket"
    )
    return CircuitBreakerRegistry.get_or_create("websocket", config)


def get_prediction_breaker() -> CircuitBreaker:
    """Get circuit breaker for ML prediction service"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30,
        service_name="prediction"
    )
    return CircuitBreakerRegistry.get_or_create("prediction", config)


# Backward compatibility alias
CircuitBreakerState = CircuitState


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create a simple test function
    call_count = 0

    def failing_service():
        global call_count
        call_count += 1
        if call_count <= 6:  # First 6 calls fail
            raise Exception("Service unavailable")
        return "Success!"

    # Test circuit breaker
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=2,
        service_name="test_service"
    ))

    for i in range(15):
        try:
            result = breaker.call(failing_service)
            print(f"Call {i+1}: {result}")
        except CircuitBreakerOpen as e:
            print(f"Call {i+1}: Circuit breaker open - {e}")
        except Exception as e:
            print(f"Call {i+1}: Error - {e}")

        time.sleep(0.5)

    print("\nFinal metrics:", breaker.get_metrics())
