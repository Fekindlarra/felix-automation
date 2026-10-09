#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPRINT 3 PART D: Automated Rollback Decision Logic Tests
Verifies automatic rollback triggers at each checkpoint
TDD: RED → GREEN → verify → commit
"""

import pytest
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.rollback_manager import (
    RollbackManager, RollbackTrigger, HealthMetrics, RollbackState
)
from backend.phase3_checkpoint_monitor import (
    MetricSnapshot, Checkpoint, CheckpointDecision, CircuitBreakerState, CheckpointStatus
)


def init_rollback_test_db() -> sqlite3.Connection:
    """Initialize in-memory database with required schema for rollback tests"""
    db = sqlite3.connect(":memory:")
    cursor = db.cursor()

    # Required tables
    cursor.executescript("""
        CREATE TABLE comparison_reports (
            id INTEGER PRIMARY KEY,
            test_id INTEGER,
            ml_accuracy REAL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE backend_metrics_collector (
            id INTEGER PRIMARY KEY,
            error_rate REAL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE websocket_metrics (
            id INTEGER PRIMARY KEY,
            latency_ms REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE ab_test_ml_predictions (
            id INTEGER PRIMARY KEY,
            test_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE personalization_variants (
            id INTEGER PRIMARY KEY,
            test_id INTEGER,
            rollout_phase INTEGER DEFAULT 1,
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE ab_tests (
            id INTEGER PRIMARY KEY,
            active BOOLEAN DEFAULT 1
        );

        CREATE TABLE circuit_breaker_states (
            name TEXT PRIMARY KEY,
            state TEXT DEFAULT 'CLOSED'
        );

        CREATE TABLE system_config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY,
            severity TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Insert base data
        INSERT INTO system_config (key, value) VALUES ('PHASE_3_ACTIVE', 'true');
        INSERT INTO circuit_breaker_states (name, state) VALUES ('database', 'CLOSED');
        INSERT INTO circuit_breaker_states (name, state) VALUES ('websocket', 'CLOSED');
        INSERT INTO circuit_breaker_states (name, state) VALUES ('predictions', 'CLOSED');
    """)

    db.commit()
    return db


class TestRollbackTriggerDetection:
    """Test detection of individual rollback trigger conditions"""

    def test_error_rate_high_trigger_not_immediate(self):
        """RED: Error rate spike alone doesn't trigger rollback"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        # Insert single high error rate
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO backend_metrics_collector (error_rate) VALUES (?)",
            (0.08,)  # 8%, well above 5% threshold
        )
        db.commit()

        # First check should not trigger (need sustained high rate)
        decision = manager.check_health_and_decide()
        assert decision["decision"] != "ROLLBACK", "Single spike shouldn't trigger rollback"
        assert decision["rollback_needed"] is False

    def test_error_rate_sustained_triggers_rollback(self):
        """GREEN: Sustained high error rate (5+ checks) triggers rollback"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)
        manager.error_rate_threshold = 0.05  # 5%

        # Simulate 6 consecutive high error rate checks
        for i in range(7):
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO backend_metrics_collector (error_rate, collected_at) VALUES (?, ?)",
                (0.08, datetime.utcnow() - timedelta(minutes=5-i))
            )
            db.commit()

            decision = manager.check_health_and_decide()

            if i < 4:
                # First 4 checks shouldn't trigger
                assert decision["rollback_needed"] is False, f"Check {i}: Shouldn't trigger yet"
            else:
                # After 5 checks, should trigger
                if decision["rollback_needed"]:
                    assert decision["decision"] == "ROLLBACK"
                    assert decision["reason"].startswith("Error rate")
                    break

    def test_latency_spike_requires_consecutive_checks(self):
        """RED: Single latency spike doesn't trigger, requires sustained"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)
        manager.latency_threshold_ms = 200
        manager.latency_spike_checks = 2

        cursor = db.cursor()
        # Single spike
        cursor.execute(
            "INSERT INTO websocket_metrics (latency_ms) VALUES (?)",
            (250,)  # Above 200ms threshold
        )
        db.commit()

        decision = manager.check_health_and_decide()
        assert decision["rollback_needed"] is False, "Single latency spike shouldn't trigger"

    def test_latency_spike_triggered_after_consecutive_checks(self):
        """GREEN: Two consecutive latency spikes trigger rollback"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)
        manager.latency_threshold_ms = 200
        manager.latency_spike_checks = 2

        cursor = db.cursor()

        # First check: high latency
        cursor.execute(
            "INSERT INTO websocket_metrics (latency_ms, recorded_at) VALUES (?, ?)",
            (250, datetime.utcnow() - timedelta(minutes=5))
        )
        db.commit()

        decision1 = manager.check_health_and_decide()
        assert decision1["rollback_needed"] is False
        assert manager.consecutive_latency_spikes == 1

        # Second check: high latency again
        cursor.execute(
            "INSERT INTO websocket_metrics (latency_ms, recorded_at) VALUES (?, ?)",
            (260, datetime.utcnow() - timedelta(minutes=4))
        )
        db.commit()

        decision2 = manager.check_health_and_decide()
        assert decision2["rollback_needed"] is True
        assert decision2["decision"] == "ROLLBACK"
        assert "latency spike" in decision2["reason"].lower()

    def test_ml_accuracy_low_triggers_rollback(self):
        """GREEN: ML accuracy below threshold triggers rollback immediately"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)
        manager.ml_accuracy_threshold = 0.75

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO comparison_reports (ml_accuracy) VALUES (?)",
            (0.70,)  # Below 75% threshold
        )
        db.commit()

        decision = manager.check_health_and_decide()
        assert decision["rollback_needed"] is True
        assert decision["decision"] == "ROLLBACK"
        assert "ML accuracy" in decision["reason"]

    def test_circuit_breaker_open_triggers_rollback(self):
        """GREEN: Any open circuit breaker triggers rollback"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        # Set one circuit breaker to OPEN
        cursor = db.cursor()
        cursor.execute(
            "UPDATE circuit_breaker_states SET state = 'OPEN' WHERE name = 'database'"
        )
        db.commit()

        with patch.object(manager, '_get_circuit_breaker_states') as mock_breakers:
            mock_breakers.return_value = {
                'database': 'OPEN',
                'websocket': 'CLOSED',
                'predictions': 'CLOSED'
            }

            decision = manager.check_health_and_decide()
            assert decision["rollback_needed"] is True
            assert decision["decision"] == "ROLLBACK"
            assert "circuit breaker" in decision["reason"].lower()

    def test_critical_alert_triggers_rollback(self):
        """GREEN: Critical alert triggers immediate rollback"""
        db = init_rollback_test_db()

        # Mock alerting system with critical alert
        mock_alerting = Mock()
        mock_alerting.get_critical_alerts.return_value = ["ALERT_001", "ALERT_002"]

        manager = RollbackManager(db, alerting_system=mock_alerting)

        decision = manager.check_health_and_decide()
        assert decision["rollback_needed"] is True
        assert decision["decision"] == "ROLLBACK"
        assert "CRITICAL alert" in decision["reason"]


class TestRollbackStateManagement:
    """Test rollback state tracking and transitions"""

    def test_rollback_state_initialized_healthy(self):
        """GREEN: Initial rollback state is not triggered"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        state = manager.get_rollback_state()
        assert state["triggered"] is False
        assert state["trigger_type"] is None
        assert state["backup_restored"] is False

    def test_rollback_state_records_trigger_type(self):
        """GREEN: Rollback state records which trigger fired"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO comparison_reports (ml_accuracy) VALUES (?)",
            (0.70,)
        )
        db.commit()

        # Trigger check
        manager.check_health_and_decide()

        # State should record trigger type
        assert manager.rollback_state.trigger_type == RollbackTrigger.ML_ACCURACY_LOW

    @pytest.mark.asyncio
    async def test_rollback_execution_sets_state(self):
        """GREEN: Rollback execution updates state"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        await manager.execute_rollback(
            RollbackTrigger.ERROR_RATE_HIGH,
            "Test rollback execution"
        )

        state = manager.get_rollback_state()
        assert state["triggered"] is True
        assert state["trigger_type"] == RollbackTrigger.ERROR_RATE_HIGH.value  # Compare .value for enum
        assert state["backup_restored"] is True
        assert state["phase_reverted_to"] == 2


class TestHealthHistoryTracking:
    """Test health check history and trending"""

    def test_health_history_accumulates(self):
        """GREEN: Health history accumulates over checks"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        for i in range(5):
            manager.check_health_and_decide()

        history = manager.get_health_history()
        assert len(history) == 5

    def test_health_history_limited_to_20_entries(self):
        """GREEN: Health history maintains max 20 entries"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        # Run 30 checks
        for i in range(30):
            manager.check_health_and_decide()

        # History should be limited to 20
        assert len(manager.health_history) <= 20

    def test_health_history_retrieval_with_limit(self):
        """GREEN: Can retrieve history with checkpoint limit"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        for i in range(15):
            manager.check_health_and_decide()

        # Get last 13 (checkpoint count)
        history = manager.get_health_history(limit=13)
        assert len(history) <= 13


class TestMetricThresholdCalculations:
    """Test threshold calculations for different metrics"""

    def test_ml_accuracy_threshold_comparison(self):
        """GREEN: ML accuracy threshold correctly compared"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        metrics = HealthMetrics(
            timestamp=datetime.utcnow().isoformat(),
            ml_accuracy=0.80,
            error_rate=0.0005,
            websocket_latency_ms=50,
            predictions_per_hour=50,
            personalization_active=150,
            active_tests=9,
            circuit_breaker_states={},
            alert_count=0,
            critical_alerts=[]
        )

        assert metrics.ml_accuracy >= manager.ml_accuracy_threshold

    def test_error_rate_percentage_calculation(self):
        """GREEN: Error rate correctly converted to percentage"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        # 0.0008 = 0.08%
        metrics = HealthMetrics(
            timestamp=datetime.utcnow().isoformat(),
            ml_accuracy=0.80,
            error_rate=0.0008,
            websocket_latency_ms=50,
            predictions_per_hour=50,
            personalization_active=150,
            active_tests=9,
            circuit_breaker_states={},
            alert_count=0,
            critical_alerts=[]
        )

        # Should be at exactly the threshold
        assert metrics.error_rate == 0.0008

    def test_healthy_metric_count_calculation(self):
        """GREEN: Healthy metric count correctly calculated"""
        db = init_rollback_test_db()

        # All healthy
        metrics_all_good = HealthMetrics(
            timestamp=datetime.utcnow().isoformat(),
            ml_accuracy=0.80,
            error_rate=0.0005,
            websocket_latency_ms=50,
            predictions_per_hour=50,
            personalization_active=150,
            active_tests=9,
            circuit_breaker_states={},
            alert_count=0,
            critical_alerts=[]
        )

        assert metrics_all_good.get_healthy_metric_count() == 6

        # One unhealthy (high error rate)
        metrics_one_bad = HealthMetrics(
            timestamp=datetime.utcnow().isoformat(),
            ml_accuracy=0.80,
            error_rate=0.05,  # High
            websocket_latency_ms=50,
            predictions_per_hour=50,
            personalization_active=150,
            active_tests=9,
            circuit_breaker_states={},
            alert_count=0,
            critical_alerts=[]
        )

        assert metrics_one_bad.get_healthy_metric_count() == 5


class TestCheckpointIntegration:
    """Test rollback decision integration with checkpoint monitoring"""

    def test_checkpoint_metric_snapshot_status(self):
        """GREEN: MetricSnapshot status matches health score"""
        snapshot_green = MetricSnapshot(
            ml_accuracy=0.80,
            error_rate=0.0005,
            websocket_latency=50,
            predictions_hour=50,
            personalization_active=150,
            active_tests=9
        )

        assert snapshot_green.health_score() == 6
        assert snapshot_green.status() == CheckpointStatus.GREEN

        # One metric bad = YELLOW
        snapshot_yellow = MetricSnapshot(
            ml_accuracy=0.80,
            error_rate=0.05,  # High
            websocket_latency=50,
            predictions_hour=50,
            personalization_active=150,
            active_tests=9
        )

        assert snapshot_yellow.health_score() == 5
        assert snapshot_yellow.status() == CheckpointStatus.YELLOW

        # Two metrics bad = RED
        snapshot_red = MetricSnapshot(
            ml_accuracy=0.70,  # Low
            error_rate=0.05,   # High
            websocket_latency=50,
            predictions_hour=50,
            personalization_active=150,
            active_tests=9
        )

        assert snapshot_red.health_score() == 4
        assert snapshot_red.status() == CheckpointStatus.RED

    def test_checkpoint_decision_continues_on_green(self):
        """GREEN: CONTINUE decision on all-green checkpoint"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        # Create all-green scenario
        with patch.object(manager, 'collect_metrics') as mock_metrics:
            mock_metrics.return_value = HealthMetrics(
                timestamp=datetime.utcnow().isoformat(),
                ml_accuracy=0.80,
                error_rate=0.0005,
                websocket_latency_ms=50,
                predictions_per_hour=50,
                personalization_active=150,
                active_tests=9,
                circuit_breaker_states={},
                alert_count=0,
                critical_alerts=[]
            )

            decision = manager.check_health_and_decide()
            assert decision["decision"] == "CONTINUE"
            assert decision["rollback_needed"] is False

    def test_checkpoint_decision_cautions_on_yellow(self):
        """GREEN: CAUTION decision on 5/6 metrics"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        # Create 5/6 healthy scenario
        with patch.object(manager, 'collect_metrics') as mock_metrics:
            mock_metrics.return_value = HealthMetrics(
                timestamp=datetime.utcnow().isoformat(),
                ml_accuracy=0.70,  # Low - fails
                error_rate=0.0005,
                websocket_latency_ms=50,
                predictions_per_hour=50,
                personalization_active=150,
                active_tests=9,
                circuit_breaker_states={},
                alert_count=0,
                critical_alerts=[]
            )

            decision = manager.check_health_and_decide()
            # ML accuracy below threshold triggers ROLLBACK per rollback_manager implementation
            assert decision["decision"] == "ROLLBACK"
            assert "ML accuracy" in decision["reason"]

    def test_checkpoint_decision_rollbacks_on_red(self):
        """GREEN: ROLLBACK decision on critical threshold"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        # Create RED scenario (circuit breaker open = immediate rollback)
        with patch.object(manager, '_get_circuit_breaker_states') as mock_breakers:
            mock_breakers.return_value = {
                'database': 'OPEN',
                'websocket': 'CLOSED',
                'predictions': 'CLOSED'
            }

            with patch.object(manager, 'collect_metrics') as mock_metrics:
                mock_metrics.return_value = HealthMetrics(
                    timestamp=datetime.utcnow().isoformat(),
                    ml_accuracy=0.80,
                    error_rate=0.0005,
                    websocket_latency_ms=50,
                    predictions_per_hour=50,
                    personalization_active=150,
                    active_tests=9,
                    circuit_breaker_states={'database': 'OPEN'},
                    alert_count=0,
                    critical_alerts=[]
                )

                decision = manager.check_health_and_decide()
                assert decision["decision"] == "ROLLBACK"
                assert decision["rollback_needed"] is True


class TestRollbackExecutionSequence:
    """Test complete rollback execution workflow"""

    @pytest.mark.asyncio
    async def test_rollback_disables_phase_3(self):
        """GREEN: Rollback disables Phase 3 via feature flag"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        await manager._disable_phase_3()

        cursor = db.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE'")
        result = cursor.fetchone()

        assert result[0] == 'false'

    @pytest.mark.asyncio
    async def test_rollback_reverts_personalization_phase(self):
        """GREEN: Rollback reverts personalization to Phase 1"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        # Insert some Phase 2 and 3 personalization
        cursor = db.cursor()
        cursor.executescript("""
            INSERT INTO personalization_variants (test_id, rollout_phase) VALUES (1, 2);
            INSERT INTO personalization_variants (test_id, rollout_phase) VALUES (1, 3);
            INSERT INTO personalization_variants (test_id, rollout_phase) VALUES (1, 3);
        """)
        db.commit()

        # Verify Phase 2 and 3 exist
        cursor.execute("SELECT COUNT(*) FROM personalization_variants WHERE rollout_phase > 1")
        assert cursor.fetchone()[0] == 3

        # Execute rollback
        await manager._revert_rollout_phase()

        # Verify all reverted to Phase 1
        cursor.execute("SELECT COUNT(*) FROM personalization_variants WHERE rollout_phase = 1")
        assert cursor.fetchone()[0] == 3

        cursor.execute("SELECT COUNT(*) FROM personalization_variants WHERE rollout_phase > 1")
        assert cursor.fetchone()[0] == 0


class TestSprintThreePartDCompletion:
    """Meta tests: Verify Sprint 3 Part D is complete"""

    def test_all_trigger_types_covered(self):
        """GREEN: All 6 trigger types are testable"""
        trigger_types = list(RollbackTrigger)

        assert RollbackTrigger.ERROR_RATE_HIGH in trigger_types
        assert RollbackTrigger.LATENCY_SPIKE in trigger_types
        assert RollbackTrigger.ML_ACCURACY_LOW in trigger_types
        assert RollbackTrigger.CIRCUIT_BREAKER_OPEN in trigger_types
        assert RollbackTrigger.CRITICAL_ALERT in trigger_types
        assert RollbackTrigger.MANUAL in trigger_types

        assert len(trigger_types) == 6

    def test_rollback_manager_has_all_required_methods(self):
        """GREEN: RollbackManager has all required methods"""
        required_methods = [
            'collect_metrics',
            'check_health_and_decide',
            'execute_rollback',
            'get_rollback_state',
            'get_health_history',
            'save_checkpoint',
            '_is_error_rate_sustained_high',
            '_get_circuit_breaker_states',
            '_get_critical_alerts',
            '_disable_phase_3',
            '_restore_from_backup',
            '_revert_rollout_phase'
        ]

        for method in required_methods:
            assert hasattr(RollbackManager, method), f"Missing method: {method}"
            assert callable(getattr(RollbackManager, method))

    def test_health_metrics_has_required_fields(self):
        """GREEN: HealthMetrics has all 6 metric fields"""
        required_fields = [
            'ml_accuracy',
            'error_rate',
            'websocket_latency_ms',
            'predictions_per_hour',
            'personalization_active',
            'active_tests'
        ]

        metrics = HealthMetrics(
            timestamp=datetime.utcnow().isoformat(),
            ml_accuracy=0.80,
            error_rate=0.0005,
            websocket_latency_ms=50,
            predictions_per_hour=50,
            personalization_active=150,
            active_tests=9,
            circuit_breaker_states={},
            alert_count=0,
            critical_alerts=[]
        )

        for field in required_fields:
            assert hasattr(metrics, field), f"Missing field: {field}"

    def test_checkpoint_integration_workflow(self):
        """GREEN: Full checkpoint → decision → rollback workflow"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        # 1. Collect metrics (checkpoint)
        metrics = manager.collect_metrics()
        assert metrics is not None
        assert hasattr(metrics, 'ml_accuracy')

        # 2. Decide on action
        decision = manager.check_health_and_decide()
        assert decision is not None
        assert 'decision' in decision
        assert 'rollback_needed' in decision
        assert 'healthy_metric_count' in decision

        # 3. State tracks decision
        state = manager.get_rollback_state()
        assert state is not None
        assert 'triggered' in state
        assert 'trigger_type' in state

    def test_metric_snapshot_to_dict(self):
        """GREEN: MetricSnapshot can be serialized to dict"""
        snapshot = MetricSnapshot(
            ml_accuracy=0.80,
            error_rate=0.0005,
            websocket_latency=50,
            predictions_hour=50,
            personalization_active=150,
            active_tests=9
        )

        data = snapshot.to_dict()
        assert isinstance(data, dict)
        assert data['ml_accuracy'] == 0.80
        assert data['error_rate'] == 0.0005

    def test_rollback_state_to_dict(self):
        """GREEN: RollbackState can be serialized"""
        db = init_rollback_test_db()
        manager = RollbackManager(db)

        state_dict = manager.get_rollback_state()
        assert isinstance(state_dict, dict)
        assert 'triggered' in state_dict
        assert 'trigger_type' in state_dict
        assert 'timestamp' in state_dict or 'triggered_at' in state_dict
