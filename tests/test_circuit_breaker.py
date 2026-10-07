#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Circuit Breaker Tests
Unit tests for circuit breaker pattern implementation
"""

import pytest
import time
from backend.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerRegistry,
    get_database_breaker,
    get_websocket_breaker,
    get_prediction_breaker
)


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions"""

    def test_initial_state_closed(self):
        """Circuit breaker should start in CLOSED state"""
        breaker = CircuitBreaker(name="test", failure_threshold=5, timeout=30)
        assert breaker.get_state() == CircuitBreakerState.CLOSED

    def test_transition_closed_to_open(self):
        """Should transition CLOSED → OPEN after threshold failures"""
        breaker = CircuitBreaker(name="test", failure_threshold=3, timeout=30)

        # Record 3 failures
        for i in range(3):
            breaker.record_failure()

        assert breaker.get_state() == CircuitBreakerState.OPEN

    def test_open_state_fail_fast(self):
        """OPEN state should fail fast without calling operation"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, timeout=30)
        breaker.record_failure()  # Move to OPEN

        assert breaker.get_state() == CircuitBreakerState.OPEN
        assert breaker.is_open() == True

    def test_transition_open_to_half_open(self):
        """Should transition OPEN → HALF_OPEN after timeout"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, timeout=1)
        breaker.record_failure()  # Move to OPEN

        assert breaker.get_state() == CircuitBreakerState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Should be in HALF_OPEN now
        assert breaker.get_state() == CircuitBreakerState.HALF_OPEN

    def test_transition_half_open_to_closed(self):
        """Should transition HALF_OPEN → CLOSED on success"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, timeout=1)
        breaker.record_failure()  # Move to OPEN
        time.sleep(1.1)  # Wait for HALF_OPEN

        breaker.record_success()  # Should move to CLOSED

        assert breaker.get_state() == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0

    def test_transition_half_open_to_open(self):
        """Should transition HALF_OPEN → OPEN on failure"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, timeout=1)
        breaker.record_failure()  # Move to OPEN
        time.sleep(1.1)  # Wait for HALF_OPEN

        assert breaker.get_state() == CircuitBreakerState.HALF_OPEN

        breaker.record_failure()  # Should move back to OPEN

        assert breaker.get_state() == CircuitBreakerState.OPEN


class TestCircuitBreakerMetrics:
    """Test circuit breaker metrics tracking"""

    def test_failure_count(self):
        """Should track failure count"""
        breaker = CircuitBreaker(name="test", failure_threshold=5, timeout=30)

        for i in range(3):
            breaker.record_failure()

        assert breaker.failure_count == 3

    def test_success_resets_count(self):
        """Success should reset failure count"""
        breaker = CircuitBreaker(name="test", failure_threshold=5, timeout=30)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 2

        breaker.record_success()
        assert breaker.failure_count == 0

    def test_get_metrics(self):
        """Should return metrics dict"""
        breaker = CircuitBreaker(name="test", failure_threshold=5, timeout=30)
        breaker.record_failure()

        metrics = breaker.get_metrics()

        assert metrics['name'] == "test"
        assert metrics['state'] == CircuitBreakerState.CLOSED
        assert metrics['failure_count'] == 1
        assert metrics['failure_threshold'] == 5
        assert 'last_failure_time' in metrics


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry functionality"""

    def test_register_breaker(self):
        """Should register breakers"""
        registry = CircuitBreakerRegistry()
        breaker = CircuitBreaker(name="test", failure_threshold=5, timeout=30)

        registry.register("test", breaker)
        retrieved = registry.get("test")

        assert retrieved is breaker

    def test_get_all_breakers(self):
        """Should return all registered breakers"""
        registry = CircuitBreakerRegistry()
        breaker1 = CircuitBreaker(name="test1", failure_threshold=5, timeout=30)
        breaker2 = CircuitBreaker(name="test2", failure_threshold=5, timeout=30)

        registry.register("test1", breaker1)
        registry.register("test2", breaker2)

        all_breakers = registry.get_all()

        assert len(all_breakers) == 2
        assert "test1" in all_breakers
        assert "test2" in all_breakers

    def test_get_all_metrics(self):
        """Should return metrics for all breakers"""
        registry = CircuitBreakerRegistry()
        breaker1 = CircuitBreaker(name="test1", failure_threshold=5, timeout=30)
        breaker2 = CircuitBreaker(name="test2", failure_threshold=5, timeout=30)

        breaker1.record_failure()
        breaker2.record_success()

        registry.register("test1", breaker1)
        registry.register("test2", breaker2)

        all_metrics = registry.get_all_metrics()

        assert len(all_metrics) == 2
        assert all_metrics[0]['failure_count'] == 1
        assert all_metrics[1]['failure_count'] == 0


class TestSpecializedBreakers:
    """Test specialized circuit breakers"""

    def test_database_breaker_exists(self):
        """Database circuit breaker should exist"""
        breaker = get_database_breaker()

        assert breaker is not None
        assert breaker.name == "database"
        assert breaker.get_state() in [CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN, CircuitBreakerState.OPEN]

    def test_websocket_breaker_exists(self):
        """WebSocket circuit breaker should exist"""
        breaker = get_websocket_breaker()

        assert breaker is not None
        assert breaker.name == "websocket"

    def test_prediction_breaker_exists(self):
        """Prediction circuit breaker should exist"""
        breaker = get_prediction_breaker()

        assert breaker is not None
        assert breaker.name == "prediction"

    def test_breakers_are_singletons(self):
        """Breakers should return same instance"""
        db1 = get_database_breaker()
        db2 = get_database_breaker()

        assert db1 is db2


class TestCircuitBreakerThreshold:
    """Test failure threshold logic"""

    def test_threshold_boundary(self):
        """Should not open until threshold reached"""
        breaker = CircuitBreaker(name="test", failure_threshold=3, timeout=30)

        breaker.record_failure()
        assert breaker.get_state() == CircuitBreakerState.CLOSED

        breaker.record_failure()
        assert breaker.get_state() == CircuitBreakerState.CLOSED

        breaker.record_failure()
        assert breaker.get_state() == CircuitBreakerState.OPEN

    def test_custom_threshold(self):
        """Should respect custom threshold values"""
        breaker = CircuitBreaker(name="test", failure_threshold=10, timeout=30)

        for i in range(9):
            breaker.record_failure()
            assert breaker.get_state() == CircuitBreakerState.CLOSED

        breaker.record_failure()  # 10th failure
        assert breaker.get_state() == CircuitBreakerState.OPEN


class TestCircuitBreakerTimeout:
    """Test timeout and recovery logic"""

    def test_timeout_duration(self):
        """Should respect timeout duration"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, timeout=2)
        breaker.record_failure()

        assert breaker.get_state() == CircuitBreakerState.OPEN

        # Before timeout expires
        time.sleep(1)
        assert breaker.get_state() == CircuitBreakerState.OPEN

        # After timeout expires
        time.sleep(1.1)
        assert breaker.get_state() == CircuitBreakerState.HALF_OPEN

    def test_short_timeout(self):
        """Should handle very short timeouts"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, timeout=0.5)
        breaker.record_failure()

        assert breaker.get_state() == CircuitBreakerState.OPEN

        time.sleep(0.6)
        assert breaker.get_state() == CircuitBreakerState.HALF_OPEN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
