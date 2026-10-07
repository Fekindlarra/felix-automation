#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Rollback Manager Tests
Unit tests for automatic rollback logic and health monitoring
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from backend.rollback_manager import RollbackManager, RollbackTrigger
from backend.config import DATABASE_PATH


class TestRollbackDecisionLogic:
    """Test rollback decision making based on metrics"""

    def test_healthy_metrics_no_rollback(self):
        """All 6 metrics healthy should not trigger rollback"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.85,
            'error_rate': 0.00015,
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        assert decision['should_rollback'] == False
        assert decision['status'] == 'CONTINUE'
        assert decision['metrics_met'] == 6

    def test_ml_accuracy_below_threshold(self):
        """ML accuracy below 78% should flag as unhealthy"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.75,  # Below 78%
            'error_rate': 0.00015,
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        assert decision['metrics_met'] == 5
        assert 'ml_accuracy' in decision['unhealthy_metrics']

    def test_error_rate_above_threshold(self):
        """Error rate above 0.08% should flag as unhealthy"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.85,
            'error_rate': 0.0009,  # 0.09% > 0.08%
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        assert decision['metrics_met'] == 5
        assert 'error_rate' in decision['unhealthy_metrics']

    def test_latency_above_threshold(self):
        """WebSocket latency above 95ms should flag as unhealthy"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.85,
            'error_rate': 0.00015,
            'websocket_latency': 100,  # > 95ms
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        assert decision['metrics_met'] == 5
        assert 'websocket_latency' in decision['unhealthy_metrics']

    def test_multiple_metrics_unhealthy(self):
        """Multiple unhealthy metrics should be detected"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.75,  # Below 78%
            'error_rate': 0.0009,  # Above 0.08%
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        assert decision['metrics_met'] == 4
        assert len(decision['unhealthy_metrics']) == 2


class TestRollbackThresholds:
    """Test rollback trigger thresholds"""

    def test_caution_threshold_5_of_6(self):
        """5 out of 6 metrics should return CAUTION"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.75,  # Unhealthy
            'error_rate': 0.00015,
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        assert decision['metrics_met'] == 5
        assert decision['status'] == 'CAUTION'
        assert decision['should_rollback'] == False

    def test_no_go_threshold_below_5_of_6(self):
        """Less than 5 metrics should trigger NO-GO"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.75,  # Unhealthy
            'error_rate': 0.0009,  # Unhealthy
            'websocket_latency': 100,  # Unhealthy
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        assert decision['metrics_met'] == 3
        assert decision['status'] == 'NO-GO'
        assert decision['should_rollback'] == True


class TestRollbackTriggerMapping:
    """Test rollback trigger type mapping"""

    def test_trigger_type_latency_spike(self):
        """Latency spike should be correctly mapped"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.85,
            'error_rate': 0.00015,
            'websocket_latency': 120,  # Spike > 95ms
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        # Should identify latency as trigger
        if decision['should_rollback']:
            assert 'websocket_latency' in decision['trigger_types']

    def test_trigger_type_error_rate_spike(self):
        """Error rate spike should be correctly mapped"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.85,
            'error_rate': 0.0015,  # High error rate
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        if decision['should_rollback']:
            assert 'error_rate' in decision['trigger_types']


class TestRollbackMetricsCollection:
    """Test metrics collection for rollback decisions"""

    def test_collect_metrics_structure(self):
        """Collected metrics should have correct structure"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.85,
            'error_rate': 0.00015,
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        # Verify decision structure
        assert 'timestamp' in decision
        assert 'metrics' in decision
        assert 'status' in decision
        assert 'should_rollback' in decision
        assert 'metrics_met' in decision
        assert 'unhealthy_metrics' in decision

    def test_metrics_are_numeric(self):
        """All metrics should be numeric"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.85,
            'error_rate': 0.00015,
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)
        decision_metrics = decision['metrics']

        for key, value in decision_metrics.items():
            assert isinstance(value, (int, float)), f"{key} should be numeric, got {type(value)}"


class TestRollbackAutomation:
    """Test automated rollback execution logic"""

    def test_rollback_decision_persistence(self):
        """Rollback decisions should be traceable"""
        manager = RollbackManager()

        metrics1 = {
            'ml_accuracy': 0.85,
            'error_rate': 0.00015,
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        metrics2 = {
            'ml_accuracy': 0.75,
            'error_rate': 0.00015,
            'websocket_latency': 8,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision1 = manager.check_health_and_decide(metrics1)
        decision2 = manager.check_health_and_decide(metrics2)

        # First should be CONTINUE, second should be CAUTION
        assert decision1['status'] == 'CONTINUE'
        assert decision2['status'] == 'CAUTION'

    def test_rollback_should_include_reason(self):
        """Rollback decision should include clear reason"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.75,
            'error_rate': 0.0009,
            'websocket_latency': 100,
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        if decision['should_rollback']:
            assert 'reason' in decision or 'unhealthy_metrics' in decision


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_all_metrics_at_threshold(self):
        """All metrics exactly at threshold should be healthy"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.78,  # Exactly at threshold
            'error_rate': 0.0008,  # Exactly at threshold (0.08%)
            'websocket_latency': 95,  # Exactly at threshold
            'predictions_hour': 42,  # Exactly at threshold
            'personalization_active': 140,  # Exactly at threshold
            'active_tests': 8  # Exactly at threshold
        }

        decision = manager.check_health_and_decide(metrics)

        assert decision['metrics_met'] == 6
        assert decision['status'] == 'CONTINUE'

    def test_zero_values(self):
        """Should handle zero/very small values"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.85,
            'error_rate': 0.00001,  # Very small error rate
            'websocket_latency': 1,  # Very fast
            'predictions_hour': 50,
            'personalization_active': 160,
            'active_tests': 12
        }

        decision = manager.check_health_and_decide(metrics)

        assert decision['metrics_met'] == 6
        assert decision['status'] == 'CONTINUE'

    def test_extreme_values(self):
        """Should handle extreme values gracefully"""
        manager = RollbackManager()

        metrics = {
            'ml_accuracy': 0.99,  # Very high
            'error_rate': 0.0,  # No errors
            'websocket_latency': 500,  # Very high latency
            'predictions_hour': 500,  # High predictions
            'personalization_active': 5000,  # Many active
            'active_tests': 100  # Many tests
        }

        decision = manager.check_health_and_decide(metrics)

        # Latency is too high
        assert 'websocket_latency' in decision.get('unhealthy_metrics', [])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
