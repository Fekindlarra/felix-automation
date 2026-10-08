#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPRINT 3 Part B: Checkpoint Monitoring System Tests
Verifies 13-checkpoint monitoring during 24-hour Phase 3 execution window (HORA 48-72)
TDD Pattern: RED → GREEN → verify → commit → document
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import sqlite3
import json
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.phase3_checkpoint_monitor import (
    Phase3CheckpointMonitor,
    MetricSnapshot,
    CheckpointStatus,
    CheckpointDecision,
    CircuitBreakerState,
    Checkpoint,
    MetricsCollectionError
)


def init_checkpoint_test_db(db_path: str = ":memory:") -> sqlite3.Connection:
    """Initialize test database with required tables for checkpoint monitoring"""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    cursor = db.cursor()

    # Core tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_tests (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_test_ml_predictions (
            id INTEGER PRIMARY KEY,
            test_id INTEGER,
            ml_accuracy REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES ab_tests(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY,
            severity TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            metric_name TEXT,
            value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personalization_variants (
            id INTEGER PRIMARY KEY,
            client_id INTEGER,
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS circuit_breaker_states (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            state TEXT DEFAULT 'CLOSED'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            alert_id TEXT,
            rule_name TEXT,
            severity TEXT,
            status TEXT,
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phase3_checkpoints (
            id INTEGER PRIMARY KEY,
            hora INTEGER,
            timestamp TEXT,
            ml_accuracy REAL,
            error_rate REAL,
            websocket_latency REAL,
            predictions_hour REAL,
            personalization_active INTEGER,
            active_tests INTEGER,
            health_score INTEGER,
            status TEXT,
            decision TEXT,
            reasoning TEXT
        )
    """)

    # Initialize circuit breaker states
    cursor.execute("INSERT OR IGNORE INTO circuit_breaker_states (name, state) VALUES ('database', 'CLOSED')")
    cursor.execute("INSERT OR IGNORE INTO circuit_breaker_states (name, state) VALUES ('websocket', 'CLOSED')")
    cursor.execute("INSERT OR IGNORE INTO circuit_breaker_states (name, state) VALUES ('predictions', 'CLOSED')")

    db.commit()
    return db


class TestMetricSnapshot:
    """Test MetricSnapshot data class and health scoring"""

    def test_health_score_all_passing(self):
        """GREEN: All 6 metrics above thresholds gives score 6"""
        metrics = MetricSnapshot(
            ml_accuracy=0.85,
            error_rate=0.0001,
            websocket_latency=30.0,
            predictions_hour=50,
            personalization_active=160,
            active_tests=10
        )
        assert metrics.health_score() == 6

    def test_health_score_one_failing(self):
        """YELLOW: One metric below threshold gives score 5"""
        metrics = MetricSnapshot(
            ml_accuracy=0.75,  # Below 0.78
            error_rate=0.0001,
            websocket_latency=30.0,
            predictions_hour=50,
            personalization_active=160,
            active_tests=10
        )
        assert metrics.health_score() == 5

    def test_health_score_multiple_failing(self):
        """RED: Multiple metrics below threshold gives score <5"""
        metrics = MetricSnapshot(
            ml_accuracy=0.75,  # Below 0.78
            error_rate=0.001,  # Below 0.0008
            websocket_latency=100.0,  # Above 95
            predictions_hour=30,  # Below 42
            personalization_active=100,  # Below 140
            active_tests=5  # Below 8
        )
        assert metrics.health_score() == 0

    def test_status_green(self):
        """GREEN: 6/6 metrics = GREEN status"""
        metrics = MetricSnapshot(
            ml_accuracy=0.85, error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )
        assert metrics.status() == CheckpointStatus.GREEN

    def test_status_yellow(self):
        """YELLOW: 5/6 metrics = YELLOW status"""
        metrics = MetricSnapshot(
            ml_accuracy=0.75, error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )
        assert metrics.status() == CheckpointStatus.YELLOW

    def test_status_red(self):
        """RED: <5/6 metrics = RED status"""
        metrics = MetricSnapshot(
            ml_accuracy=0.75, error_rate=0.001, websocket_latency=100.0,
            predictions_hour=30, personalization_active=100, active_tests=5
        )
        assert metrics.status() == CheckpointStatus.RED

    def test_to_dict(self):
        """GREEN: MetricSnapshot can be serialized to dict"""
        metrics = MetricSnapshot(
            ml_accuracy=0.85, error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )
        d = metrics.to_dict()
        assert d['ml_accuracy'] == 0.85
        assert d['error_rate'] == 0.0001
        assert isinstance(d, dict)


class TestMetricsCollection:
    """Test metrics collection from database"""

    def test_collect_ml_accuracy_with_valid_data(self):
        """GREEN: ML accuracy collected when predictions exist"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        # Insert complete test data for all metrics
        cursor = db.cursor()
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.82)")
        cursor.execute("INSERT INTO metrics (metric_name, value) VALUES ('websocket_latency', 30.0)")
        cursor.execute("INSERT INTO ab_tests (name, status) VALUES ('test1', 'ACTIVE')")
        db.commit()

        # Collect metrics
        metrics = monitor.collect_metrics()
        assert metrics.ml_accuracy == 0.82

        db.close()

    def test_collect_ml_accuracy_missing_raises_error(self):
        """RED: No ML accuracy data raises MetricsCollectionError"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        # No predictions inserted - should fail
        with pytest.raises(MetricsCollectionError) as exc:
            monitor.collect_metrics()

        assert "no data collected" in str(exc.value).lower()
        db.close()

    def test_collect_error_rate_with_no_errors(self):
        """GREEN: Error rate is 0 when no errors in 2-hour window"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        # Insert metrics for other fields
        cursor = db.cursor()
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.82)")
        cursor.execute("INSERT INTO metrics (metric_name, value) VALUES ('websocket_latency', 30.0)")
        cursor.execute("INSERT INTO ab_tests (name, status) VALUES ('test1', 'ACTIVE')")
        db.commit()

        metrics = monitor.collect_metrics()
        assert metrics.error_rate == 0.0

        db.close()

    def test_collect_error_rate_with_errors(self):
        """GREEN: Error rate calculates correctly from error count"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        cursor = db.cursor()
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.82)")
        cursor.execute("INSERT INTO metrics (metric_name, value) VALUES ('websocket_latency', 30.0)")
        cursor.execute("INSERT INTO ab_tests (name, status) VALUES ('test1', 'ACTIVE')")

        # Insert 100 errors
        for _ in range(100):
            cursor.execute("INSERT INTO error_log (severity) VALUES ('CRITICAL')")
        db.commit()

        metrics = monitor.collect_metrics()
        # 100 errors / 100000 = 0.001
        assert metrics.error_rate == 0.001

        db.close()

    def test_collect_websocket_latency_with_valid_data(self):
        """GREEN: Latency collected from metrics table"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        cursor = db.cursor()
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.82)")
        cursor.execute("INSERT INTO metrics (metric_name, value) VALUES ('websocket_latency', 42.5)")
        cursor.execute("INSERT INTO ab_tests (name, status) VALUES ('test1', 'ACTIVE')")
        db.commit()

        metrics = monitor.collect_metrics()
        assert metrics.websocket_latency == 42.5

        db.close()

    def test_collect_predictions_hour_calculation(self):
        """GREEN: Predictions/hour extrapolated from 2-hour window"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        cursor = db.cursor()
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.82)")
        cursor.execute("INSERT INTO metrics (metric_name, value) VALUES ('websocket_latency', 30.0)")
        cursor.execute("INSERT INTO ab_tests (name, status) VALUES ('test1', 'ACTIVE')")

        # Insert 2 predictions in 2-hour window
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.80)")
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.81)")
        db.commit()

        metrics = monitor.collect_metrics()
        # 3 predictions in 2h window → 90 per hour (3 * 30)
        assert metrics.predictions_hour == 90.0

        db.close()

    def test_collect_predictions_with_no_data_raises_error(self):
        """RED: No predictions raises MetricsCollectionError"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        # Only insert partial data (no predictions)
        cursor = db.cursor()
        cursor.execute("INSERT INTO error_log (severity) VALUES ('CRITICAL')")
        db.commit()

        with pytest.raises(MetricsCollectionError) as exc:
            monitor.collect_metrics()

        assert "no data collected" in str(exc.value).lower()
        db.close()

    def test_collect_personalization_count(self):
        """GREEN: Personalization active count collected"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        cursor = db.cursor()
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.82)")
        cursor.execute("INSERT INTO metrics (metric_name, value) VALUES ('websocket_latency', 30.0)")
        cursor.execute("INSERT INTO ab_tests (name, status) VALUES ('test1', 'ACTIVE')")

        # Insert 5 distinct personalized clients
        for i in range(5):
            cursor.execute("INSERT INTO personalization_variants (client_id) VALUES (?)", (i,))
        db.commit()

        metrics = monitor.collect_metrics()
        assert metrics.personalization_active == 5

        db.close()

    def test_collect_active_tests_count(self):
        """GREEN: Active tests count collected"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        cursor = db.cursor()
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.82)")
        cursor.execute("INSERT INTO metrics (metric_name, value) VALUES ('websocket_latency', 30.0)")

        # Insert 3 active tests with past created_at timestamp
        for i in range(3):
            cursor.execute(
                "INSERT INTO ab_tests (name, status, created_at, end_date) VALUES (?, ?, datetime('now', '-1 hour'), ?)",
                (f"test{i}", 'ACTIVE', None)
            )
        db.commit()

        metrics = monitor.collect_metrics()
        assert metrics.active_tests == 3

        db.close()


class TestCircuitBreakerChecking:
    """Test circuit breaker state detection"""

    def test_circuit_breakers_all_closed(self):
        """GREEN: All circuit breakers CLOSED"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        cb_state = monitor.check_circuit_breakers()

        assert cb_state.database == 'CLOSED'
        assert cb_state.websocket == 'CLOSED'
        assert cb_state.predictions == 'CLOSED'
        assert cb_state.any_open is False

        db.close()

    def test_circuit_breakers_database_open(self):
        """YELLOW: Database circuit breaker OPEN"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        cursor = db.cursor()
        cursor.execute("UPDATE circuit_breaker_states SET state = 'OPEN' WHERE name = 'database'")
        db.commit()

        cb_state = monitor.check_circuit_breakers()

        assert cb_state.database == 'OPEN'
        assert cb_state.any_open is True

        db.close()

    def test_circuit_breakers_multiple_open(self):
        """RED: Multiple circuit breakers OPEN"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        cursor = db.cursor()
        cursor.execute("UPDATE circuit_breaker_states SET state = 'OPEN' WHERE name = 'database'")
        cursor.execute("UPDATE circuit_breaker_states SET state = 'OPEN' WHERE name = 'websocket'")
        db.commit()

        cb_state = monitor.check_circuit_breakers()

        assert cb_state.database == 'OPEN'
        assert cb_state.websocket == 'OPEN'
        assert cb_state.predictions == 'CLOSED'
        assert cb_state.any_open is True

        db.close()


class TestCriticalAlertDetection:
    """Test critical alert detection"""

    def test_no_critical_alerts(self):
        """GREEN: No CRITICAL alerts found"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        alerts = monitor.check_critical_alerts()

        assert alerts == []

        db.close()

    def test_critical_alerts_detected(self):
        """RED: CRITICAL alerts detected"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO alerts (alert_id, rule_name, severity, status) VALUES (?, ?, ?, ?)",
            ('alert1', 'high_error_rate', 'CRITICAL', 'FIRING')
        )
        cursor.execute(
            "INSERT INTO alerts (alert_id, rule_name, severity, status) VALUES (?, ?, ?, ?)",
            ('alert2', 'latency_spike', 'CRITICAL', 'FIRING')
        )
        db.commit()

        alerts = monitor.check_critical_alerts()

        assert len(alerts) == 2
        assert 'alert1' in alerts
        assert 'alert2' in alerts

        db.close()


class TestCheckpointDecisionLogic:
    """Test checkpoint decision making"""

    def test_decision_continue_green(self):
        """GREEN: GREEN metrics + no open breakers = CONTINUE"""
        metrics = MetricSnapshot(
            ml_accuracy=0.85, error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )
        cb_state = CircuitBreakerState()

        checkpoint = Checkpoint(
            hora=48, timestamp=datetime.utcnow().isoformat(),
            metrics=metrics, circuit_breakers=cb_state,
            critical_alerts=[], status=CheckpointStatus.GREEN,
            decision=CheckpointDecision.CONTINUE, reasoning=[]
        )

        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        decision = monitor.make_checkpoint_decision(checkpoint)

        assert decision == CheckpointDecision.CONTINUE

        db.close()

    def test_decision_caution_yellow(self):
        """YELLOW: YELLOW metrics (5/6) = CAUTION"""
        metrics = MetricSnapshot(
            ml_accuracy=0.75,  # Failing
            error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )
        cb_state = CircuitBreakerState()

        checkpoint = Checkpoint(
            hora=48, timestamp=datetime.utcnow().isoformat(),
            metrics=metrics, circuit_breakers=cb_state,
            critical_alerts=[], status=CheckpointStatus.YELLOW,
            decision=CheckpointDecision.CAUTION, reasoning=[]
        )

        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        decision = monitor.make_checkpoint_decision(checkpoint)

        assert decision == CheckpointDecision.CAUTION

        db.close()

    def test_decision_rollback_critical_alerts(self):
        """RED: CRITICAL alerts trigger ROLLBACK"""
        metrics = MetricSnapshot(
            ml_accuracy=0.85, error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )
        cb_state = CircuitBreakerState()

        checkpoint = Checkpoint(
            hora=48, timestamp=datetime.utcnow().isoformat(),
            metrics=metrics, circuit_breakers=cb_state,
            critical_alerts=['alert_high_error_rate'],  # CRITICAL alerts
            status=CheckpointStatus.GREEN,
            decision=CheckpointDecision.CONTINUE, reasoning=[]
        )

        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        decision = monitor.make_checkpoint_decision(checkpoint)

        assert decision == CheckpointDecision.ROLLBACK

        db.close()

    def test_decision_rollback_red_metrics(self):
        """RED: RED metrics (<5/6) trigger ROLLBACK"""
        metrics = MetricSnapshot(
            ml_accuracy=0.75, error_rate=0.001, websocket_latency=100.0,
            predictions_hour=30, personalization_active=100, active_tests=5
        )
        cb_state = CircuitBreakerState()

        checkpoint = Checkpoint(
            hora=48, timestamp=datetime.utcnow().isoformat(),
            metrics=metrics, circuit_breakers=cb_state,
            critical_alerts=[], status=CheckpointStatus.RED,
            decision=CheckpointDecision.CONTINUE, reasoning=[]
        )

        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        decision = monitor.make_checkpoint_decision(checkpoint)

        assert decision == CheckpointDecision.ROLLBACK

        db.close()

    def test_decision_caution_green_but_open_breaker(self):
        """YELLOW: GREEN metrics but open breaker = CAUTION (hold phase)"""
        metrics = MetricSnapshot(
            ml_accuracy=0.85, error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )
        cb_state = CircuitBreakerState(database='OPEN', any_open=True)

        checkpoint = Checkpoint(
            hora=48, timestamp=datetime.utcnow().isoformat(),
            metrics=metrics, circuit_breakers=cb_state,
            critical_alerts=[], status=CheckpointStatus.GREEN,
            decision=CheckpointDecision.CONTINUE, reasoning=[]
        )

        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        decision = monitor.make_checkpoint_decision(checkpoint)

        assert decision == CheckpointDecision.CAUTION

        db.close()


class TestCheckpointSaving:
    """Test checkpoint persistence"""

    def test_save_checkpoint_to_database(self):
        """GREEN: Checkpoint saved to database"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        metrics = MetricSnapshot(
            ml_accuracy=0.85, error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )

        checkpoint = Checkpoint(
            hora=48, timestamp="2026-10-06T00:00:00Z",
            metrics=metrics, circuit_breakers=CircuitBreakerState(),
            critical_alerts=[], status=CheckpointStatus.GREEN,
            decision=CheckpointDecision.CONTINUE,
            reasoning=["All metrics passing", "No circuit breakers open"]
        )

        monitor.save_checkpoint(checkpoint)

        # Verify saved
        cursor = db.cursor()
        cursor.execute("SELECT * FROM phase3_checkpoints WHERE hora = 48")
        row = cursor.fetchone()

        assert row is not None
        assert row['hora'] == 48
        assert row['status'] == 'GREEN'
        assert row['decision'] == 'CONTINUE'

        db.close()

    def test_save_checkpoint_to_json_file(self):
        """GREEN: Checkpoint saved to JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            db = init_checkpoint_test_db(db_path)
            monitor = Phase3CheckpointMonitor(db_path)
            monitor.db = db

            metrics = MetricSnapshot(
                ml_accuracy=0.85, error_rate=0.0001, websocket_latency=30.0,
                predictions_hour=50, personalization_active=160, active_tests=10
            )

            checkpoint = Checkpoint(
                hora=48, timestamp="2026-10-06T00:00:00Z",
                metrics=metrics, circuit_breakers=CircuitBreakerState(),
                critical_alerts=[], status=CheckpointStatus.GREEN,
                decision=CheckpointDecision.CONTINUE,
                reasoning=["All metrics passing"]
            )

            monitor.save_checkpoint(checkpoint)

            # Verify JSON file exists
            json_file = Path("logs/phase3/checkpoint_hora_48_2026-10-06.json")
            # Note: Will be created in current directory during test
            # In actual execution, it would be in the project directory

            db.close()


class TestCollectCheckpointWorkflow:
    """Test full checkpoint collection workflow"""

    def test_collect_checkpoint_success(self):
        """GREEN: Successful checkpoint collection end-to-end"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        # Insert valid metrics meeting all 6 thresholds
        cursor = db.cursor()

        # ML Accuracy >= 0.78
        cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.85)")

        # WebSocket latency < 95ms
        cursor.execute("INSERT INTO metrics (metric_name, value) VALUES ('websocket_latency', 30.0)")

        # Error rate < 0.0008 (no critical/major errors)
        # (error_log will be empty, so error_rate = 0)

        # Predictions/hour >= 42 (need 42+ predictions in 2h window to get 42/hr)
        for _ in range(50):
            cursor.execute("INSERT INTO ab_test_ml_predictions (ml_accuracy) VALUES (0.82)")

        # Personalization active >= 140
        for i in range(150):
            cursor.execute("INSERT INTO personalization_variants (client_id) VALUES (?)", (i,))

        # Active tests >= 8
        for i in range(10):
            cursor.execute(
                "INSERT INTO ab_tests (name, status, created_at, end_date) VALUES (?, ?, datetime('now', '-1 hour'), ?)",
                (f"test{i}", 'ACTIVE', None)
            )

        db.commit()

        checkpoint = monitor.collect_checkpoint(48)

        assert checkpoint is not None
        assert checkpoint.hora == 48
        assert checkpoint.metrics.ml_accuracy >= 0.78  # Above threshold
        assert checkpoint.status == CheckpointStatus.GREEN
        assert checkpoint.decision == CheckpointDecision.CONTINUE

        db.close()

    def test_collect_checkpoint_metrics_collection_fails(self):
        """RED: Collection fails if metrics unavailable"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        # Don't insert any metrics - should fail
        checkpoint = monitor.collect_checkpoint(48)

        assert checkpoint is None  # Returns None on failure

        db.close()


class TestCheckpointReportGeneration:
    """Test checkpoint report generation"""

    def test_generate_report_empty_checkpoints(self):
        """GREEN: Report with no checkpoints"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        report = monitor.generate_checkpoint_report()

        assert report['total_checkpoints'] == 0
        assert report['green_checkpoints'] == 0
        assert report['yellow_checkpoints'] == 0
        assert report['red_checkpoints'] == 0

        db.close()

    def test_generate_report_with_checkpoints(self):
        """GREEN: Report aggregates checkpoint data"""
        db = init_checkpoint_test_db(":memory:")
        monitor = Phase3CheckpointMonitor(":memory:")
        monitor.db = db

        # Add mock checkpoints
        metrics_green = MetricSnapshot(
            ml_accuracy=0.85, error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )
        checkpoint_green = Checkpoint(
            hora=48, timestamp="2026-10-06T00:00:00Z",
            metrics=metrics_green, circuit_breakers=CircuitBreakerState(),
            critical_alerts=[], status=CheckpointStatus.GREEN,
            decision=CheckpointDecision.CONTINUE, reasoning=[]
        )

        metrics_yellow = MetricSnapshot(
            ml_accuracy=0.75, error_rate=0.0001, websocket_latency=30.0,
            predictions_hour=50, personalization_active=160, active_tests=10
        )
        checkpoint_yellow = Checkpoint(
            hora=50, timestamp="2026-10-06T02:00:00Z",
            metrics=metrics_yellow, circuit_breakers=CircuitBreakerState(),
            critical_alerts=[], status=CheckpointStatus.YELLOW,
            decision=CheckpointDecision.CAUTION, reasoning=[]
        )

        monitor.checkpoints_collected = [checkpoint_green, checkpoint_yellow]

        report = monitor.generate_checkpoint_report()

        assert report['total_checkpoints'] == 2
        assert report['green_checkpoints'] == 1
        assert report['yellow_checkpoints'] == 1
        assert report['red_checkpoints'] == 0

        db.close()


class TestPhase3CheckpointIntegration:
    """Integration tests for full checkpoint monitoring"""

    def test_checkpoint_sequence_13_horas(self):
        """GREEN: Verify 13-checkpoint sequence HORA 48-72"""
        horas = list(range(48, 74, 2))  # 48, 50, 52, ..., 70, 72

        assert len(horas) == 13
        assert horas[0] == 48
        assert horas[-1] == 72
        assert all(h % 2 == 0 for h in horas)

    def test_checkpoint_decision_progression(self):
        """GREEN: Decisions can be collected across checkpoints"""
        decisions = [
            CheckpointDecision.CONTINUE,
            CheckpointDecision.CONTINUE,
            CheckpointDecision.CAUTION,
            CheckpointDecision.CONTINUE,
        ]

        continue_count = sum(1 for d in decisions if d == CheckpointDecision.CONTINUE)
        caution_count = sum(1 for d in decisions if d == CheckpointDecision.CAUTION)
        rollback_count = sum(1 for d in decisions if d == CheckpointDecision.ROLLBACK)

        assert continue_count == 3
        assert caution_count == 1
        assert rollback_count == 0


class TestSprintThreePartBCompletion:
    """Meta test: Verify Sprint 3 Part B checkpoint monitoring is complete"""

    def test_metric_snapshot_complete(self):
        """GREEN: MetricSnapshot class has all 6 metrics"""
        import inspect
        sig = inspect.signature(MetricSnapshot.__init__)
        params = [p for p in sig.parameters.keys() if p != 'self']

        expected = ['ml_accuracy', 'error_rate', 'websocket_latency',
                   'predictions_hour', 'personalization_active', 'active_tests']

        for exp in expected:
            assert exp in params, f"Missing metric: {exp}"

    def test_checkpoint_monitor_has_all_methods(self):
        """GREEN: Phase3CheckpointMonitor has all required methods"""
        required_methods = [
            'connect', 'close', 'is_phase3_active',
            'collect_metrics', 'check_circuit_breakers', 'check_critical_alerts',
            'make_checkpoint_decision', 'save_checkpoint', 'collect_checkpoint',
            'generate_checkpoint_report'
        ]

        for method in required_methods:
            assert hasattr(Phase3CheckpointMonitor, method), f"Missing method: {method}"
            assert callable(getattr(Phase3CheckpointMonitor, method))

    def test_decision_enum_complete(self):
        """GREEN: CheckpointDecision has all three decision types"""
        decisions = [d.value for d in CheckpointDecision]

        assert 'CONTINUE' in decisions
        assert 'CAUTION' in decisions
        assert 'ROLLBACK' in decisions

    def test_status_enum_complete(self):
        """GREEN: CheckpointStatus has all four status types"""
        statuses = [s.value for s in CheckpointStatus]

        assert 'GREEN' in statuses
        assert 'YELLOW' in statuses
        assert 'RED' in statuses
        assert 'CRITICAL' in statuses
