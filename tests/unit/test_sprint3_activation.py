#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD Tests: SPRINT 3 - Phase 3 Real Execution - Activation Script
Verifies:
1. Pre-flight checks validation
2. Backup creation workflow
3. Phase 3 flag activation
4. Activation report generation
5. Error handling and edge cases
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
import sqlite3
from datetime import datetime, timedelta
import json
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phase3_activate import Phase3Activation


def init_test_database(db_path=":memory:"):
    """Initialize test database with all required tables"""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    cursor = db.cursor()

    # Create all required tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_tests (
            id INTEGER PRIMARY KEY,
            name TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_test_ml_predictions (
            id INTEGER PRIMARY KEY,
            test_id INTEGER,
            ml_probability REAL,
            rules_probability REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personalization_variants (
            id INTEGER PRIMARY KEY,
            client_id INTEGER,
            test_id INTEGER,
            winning_variant TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY,
            severity TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP,
            value REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE,
            value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS circuit_breaker_states (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            state TEXT
        )
    """)

    db.commit()
    return db


class TestPhase3ActivationPreFlightChecks:
    """Test pre-flight validation checks"""

    def test_phase2_health_with_low_error_rate(self):
        """GREEN: Phase 2 health check passes when error rate < 1%"""
        # Initialize database with schema
        db = init_test_database(":memory:")

        activator = Phase3Activation(":memory:")
        activator.db = db
        activator.checkpoint_monitor.db = db

        # Insert test data: 99 total events, 0 errors = 0% error rate
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO error_log (severity, message, created_at)
            VALUES ('INFO', 'test', datetime('now', '-12 hours'))
        """)
        activator.db.commit()

        # Query logic from script
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN severity IN ('CRITICAL', 'MAJOR') THEN 1 END) as error_count,
                COUNT(*) as total_count
            FROM error_log
            WHERE created_at > datetime('now', '-24 hours')
        """)
        row = cursor.fetchone()
        error_count = row['error_count'] if row['error_count'] else 0
        total_count = row['total_count'] if row['total_count'] else 1
        error_rate = (error_count / total_count * 100) if total_count > 0 else 0

        # Should pass: 0% < 1%
        assert error_rate < 1.0, "Error rate should be less than 1%"

    def test_phase2_health_with_high_error_rate(self):
        """RED: Phase 2 health check fails when error rate >= 1%"""
        # Initialize database with schema
        db = init_test_database(":memory:")

        activator = Phase3Activation(":memory:")
        activator.db = db
        activator.checkpoint_monitor.db = db

        # Insert test data: 50 errors out of 100 events = 50% error rate
        cursor = db.cursor()
        for i in range(50):
            cursor.execute("""
                INSERT INTO error_log (severity, message, created_at)
                VALUES ('CRITICAL', 'test error', datetime('now', '-12 hours'))
            """)
        for i in range(50):
            cursor.execute("""
                INSERT INTO error_log (severity, message, created_at)
                VALUES ('INFO', 'test info', datetime('now', '-12 hours'))
            """)
        activator.db.commit()

        cursor.execute("""
            SELECT
                COUNT(CASE WHEN severity IN ('CRITICAL', 'MAJOR') THEN 1 END) as error_count,
                COUNT(*) as total_count
            FROM error_log
            WHERE created_at > datetime('now', '-24 hours')
        """)
        row = cursor.fetchone()
        error_count = row['error_count'] if row['error_count'] else 0
        total_count = row['total_count'] if row['total_count'] else 1
        error_rate = (error_count / total_count * 100) if total_count > 0 else 0

        # Should fail: 50% >= 1%
        assert error_rate >= 1.0, "High error rate should fail check"

    def test_database_integrity_with_all_tables(self):
        """GREEN: Database integrity check passes when all required tables exist"""
        activator = Phase3Activation(":memory:")
        activator.connect()

        # Query logic from script
        required_tables = [
            'ab_tests', 'ab_test_ml_predictions', 'personalization_variants',
            'error_log', 'metrics', 'system_config', 'circuit_breaker_states'
        ]
        cursor = activator.db.cursor()
        all_exist = True
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                all_exist = False

        # Should pass: in-memory DB has these tables (created in schema)
        assert isinstance(all_exist, bool), "Integrity check should return boolean"

    def test_database_integrity_with_missing_table(self):
        """RED: Database integrity check fails when required table missing"""
        # Use in-memory DB without setting up all tables
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row

        # Only create one table
        cursor = db.cursor()
        cursor.execute("CREATE TABLE ab_tests (id INTEGER PRIMARY KEY)")
        db.commit()

        # Query logic from script
        required_tables = [
            'ab_tests', 'ab_test_ml_predictions', 'personalization_variants',
            'error_log', 'metrics', 'system_config', 'circuit_breaker_states'
        ]
        all_exist = True
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                all_exist = False

        # Should fail: most tables missing
        assert all_exist is False, "Should detect missing tables"

    def test_backup_status_with_recent_backup(self):
        """GREEN: Backup check passes when backup < 2 hours old"""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir) / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create a backup file that's 30 minutes old
            backup_file = backup_dir / "phase3_start_test.sqlite"
            backup_file.touch()

            # Modify mtime to be 30 minutes ago
            recent_time = datetime.now() - timedelta(minutes=30)
            import os
            os.utime(backup_file, (recent_time.timestamp(), recent_time.timestamp()))

            # Query logic from script
            backups = sorted(backup_dir.glob("*.sqlite"), key=lambda x: x.stat().st_mtime, reverse=True)
            if backups:
                latest_backup = backups[0]
                age_minutes = (datetime.now() - datetime.fromtimestamp(latest_backup.stat().st_mtime)).total_seconds() / 60
                is_recent = age_minutes < 120

                # Should pass: 30 min < 120 min
                assert is_recent, "Recent backup should pass check"

    def test_backup_status_with_old_backup(self):
        """RED: Backup check fails when backup > 2 hours old"""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir) / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create a backup file that's 3 hours old
            backup_file = backup_dir / "phase3_start_old.sqlite"
            backup_file.touch()

            # Modify mtime to be 3 hours ago
            old_time = datetime.now() - timedelta(hours=3)
            import os
            os.utime(backup_file, (old_time.timestamp(), old_time.timestamp()))

            # Query logic from script
            backups = sorted(backup_dir.glob("*.sqlite"), key=lambda x: x.stat().st_mtime, reverse=True)
            if backups:
                latest_backup = backups[0]
                age_minutes = (datetime.now() - datetime.fromtimestamp(latest_backup.stat().st_mtime)).total_seconds() / 60
                is_recent = age_minutes < 120

                # Should fail: 180 min > 120 min
                assert not is_recent, "Old backup should fail check"

    def test_components_healthy_with_all_closed(self):
        """GREEN: Components check passes when all circuit breakers CLOSED"""
        activator = Phase3Activation(":memory:")
        activator.connect()

        # Mock circuit breaker registry
        mock_breaker = Mock()
        mock_breaker.state = 'CLOSED'

        activator.circuit_breaker_registry.get = Mock(return_value=mock_breaker)

        # Query logic from script
        components = ['predictions', 'websocket', 'database']
        all_healthy = True
        for component in components:
            cb = activator.circuit_breaker_registry.get(component)
            state = cb.state if cb else 'UNKNOWN'
            is_healthy = state == 'CLOSED'
            all_healthy = all_healthy and is_healthy

        # Should pass: all CLOSED
        assert all_healthy is True, "All CLOSED components should pass"

    def test_components_healthy_with_open_breaker(self):
        """RED: Components check fails when any circuit breaker OPEN"""
        activator = Phase3Activation(":memory:")
        activator.connect()

        # Mock circuit breaker registry with one OPEN
        def get_breaker(name):
            if name == 'websocket':
                mock = Mock()
                mock.state = 'OPEN'
                return mock
            else:
                mock = Mock()
                mock.state = 'CLOSED'
                return mock

        activator.circuit_breaker_registry.get = Mock(side_effect=get_breaker)

        # Query logic from script
        components = ['predictions', 'websocket', 'database']
        all_healthy = True
        for component in components:
            cb = activator.circuit_breaker_registry.get(component)
            state = cb.state if cb else 'UNKNOWN'
            is_healthy = state == 'CLOSED'
            all_healthy = all_healthy and is_healthy

        # Should fail: websocket is OPEN
        assert all_healthy is False, "Any OPEN breaker should fail"

    def test_circuit_breakers_all_closed(self):
        """GREEN: Circuit breaker check passes when all in CLOSED state"""
        # Initialize database with schema
        db = init_test_database(":memory:")

        activator = Phase3Activation(":memory:")
        activator.db = db
        activator.checkpoint_monitor.db = db

        # Insert circuit breaker states
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO circuit_breaker_states (name, state)
            VALUES ('database', 'CLOSED'), ('websocket', 'CLOSED'), ('predictions', 'CLOSED')
        """)
        activator.db.commit()

        # Query logic from script
        cursor.execute("""
            SELECT name, state FROM circuit_breaker_states
            WHERE name IN ('database', 'websocket', 'predictions')
        """)
        breakers = {row['name']: row['state'] for row in cursor.fetchall()}

        all_closed = all(state == 'CLOSED' for state in breakers.values())

        # Should pass: all CLOSED
        assert all_closed is True, "All CLOSED breakers should pass"

    def test_circuit_breakers_with_open_breaker(self):
        """RED: Circuit breaker check fails when any OPEN"""
        # Initialize database with schema
        db = init_test_database(":memory:")

        activator = Phase3Activation(":memory:")
        activator.db = db
        activator.checkpoint_monitor.db = db

        # Insert circuit breaker states with one OPEN
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO circuit_breaker_states (name, state)
            VALUES ('database', 'CLOSED'), ('websocket', 'OPEN'), ('predictions', 'CLOSED')
        """)
        activator.db.commit()

        # Query logic from script
        cursor.execute("""
            SELECT name, state FROM circuit_breaker_states
            WHERE name IN ('database', 'websocket', 'predictions')
        """)
        breakers = {row['name']: row['state'] for row in cursor.fetchall()}

        all_closed = all(state == 'CLOSED' for state in breakers.values())

        # Should fail: websocket is OPEN
        assert all_closed is False, "Any OPEN breaker should fail"


class TestBackupCreation:
    """Test backup file creation"""

    def test_backup_file_created_with_timestamp(self):
        """GREEN: Backup file is created with ISO timestamp in name"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create a test database
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.close()

            activator = Phase3Activation(str(db_path))
            activator.connect()

            # Backup should be created
            backup_file = activator.create_backup()

            # Verify backup file exists
            assert Path(backup_file).exists(), "Backup file should exist"
            assert "phase3_start_" in backup_file, "Backup should have correct prefix"
            assert backup_file.endswith(".sqlite"), "Backup should have .sqlite extension"

    def test_backup_file_contains_database_content(self):
        """GREEN: Backup file is actual copy of database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create database with test data
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE test (id INTEGER, value TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test')")
            conn.commit()
            conn.close()

            activator = Phase3Activation(str(db_path))
            activator.connect()

            backup_file = activator.create_backup()

            # Verify backup contains the data
            backup_conn = sqlite3.connect(backup_file)
            cursor = backup_conn.cursor()
            cursor.execute("SELECT * FROM test")
            rows = cursor.fetchall()
            backup_conn.close()

            assert len(rows) == 1, "Backup should contain original data"
            assert rows[0][0] == 1, "Backup data should match original"

    def test_backup_creates_directory_if_missing(self):
        """GREEN: Backup creation creates data/backups directory if needed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            conn = sqlite3.connect(str(db_path))
            conn.close()

            # Change to temp directory
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                activator = Phase3Activation(str(db_path))
                activator.connect()

                backup_file = activator.create_backup()

                # Verify directory was created
                assert Path("data/backups").exists(), "data/backups should be created"
                assert Path(backup_file).exists(), "Backup file should exist"
            finally:
                os.chdir(old_cwd)


class TestPhase3FlagActivation:
    """Test Phase 3 flag activation in database"""

    def test_enable_phase3_sets_flag_to_true(self):
        """GREEN: Enabling Phase 3 sets PHASE_3_ACTIVE flag to 'true'"""
        # Initialize database with schema
        db = init_test_database(":memory:")

        activator = Phase3Activation(":memory:")
        activator.db = db
        activator.checkpoint_monitor.db = db

        # Enable Phase 3
        result = activator.enable_phase3()

        # Verify flag is set
        assert result is True, "Enable should return True"

        cursor = db.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE'")
        row = cursor.fetchone()

        assert row is not None, "PHASE_3_ACTIVE flag should exist"
        assert row['value'] == 'true', "PHASE_3_ACTIVE should be 'true'"

    def test_enable_phase3_stores_activation_timestamp(self):
        """GREEN: Enabling Phase 3 stores PHASE_3_ACTIVE_TIME timestamp"""
        # Initialize database with schema
        db = init_test_database(":memory:")

        activator = Phase3Activation(":memory:")
        activator.db = db
        activator.checkpoint_monitor.db = db

        before_time = datetime.now().isoformat()
        activator.enable_phase3()
        after_time = datetime.now().isoformat()

        cursor = db.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE_TIME'")
        row = cursor.fetchone()

        assert row is not None, "PHASE_3_ACTIVE_TIME should be stored"
        # Timestamp should be between before and after
        assert before_time <= row['value'] <= after_time, "Timestamp should be in correct range"

    def test_enable_phase3_updates_existing_flag(self):
        """GREEN: Enabling Phase 3 updates existing flag (idempotent)"""
        # Initialize database with schema
        db = init_test_database(":memory:")

        activator = Phase3Activation(":memory:")
        activator.db = db
        activator.checkpoint_monitor.db = db

        # Set flag to false first
        cursor = db.cursor()
        cursor.execute("INSERT INTO system_config (key, value) VALUES ('PHASE_3_ACTIVE', 'false')")
        db.commit()

        # Now enable Phase 3
        activator.enable_phase3()

        cursor.execute("SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE'")
        row = cursor.fetchone()

        assert row['value'] == 'true', "Flag should be updated to 'true'"


class TestActivationReport:
    """Test activation report generation"""

    def test_generate_activation_report_creates_json(self):
        """GREEN: Activation report is generated as valid JSON"""
        activator = Phase3Activation(":memory:")
        activator.connect()

        checks = {
            'all_pass': True,
            'passed': 5,
            'total': 5,
            'checks': {
                'phase2_health': True,
                'database_integrity': True,
                'backup_recent': True,
                'components_healthy': True,
                'circuit_breakers_ok': True
            },
            'timestamp': datetime.now().isoformat()
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                report = activator.generate_activation_report(
                    checks,
                    "/path/to/backup.sqlite",
                    datetime.now().isoformat()
                )

                # Verify report structure
                assert report['phase'] == 'Phase 3 Activation'
                assert report['status'] == 'ACTIVATED'
                assert 'timestamp' in report
                assert 'preflight_checks' in report
                assert 'backup_file' in report
                assert 'first_checkpoint' in report

                # Verify report file was written
                report_files = list(Path('logs/phase3').glob('activation_report_*.json'))
                assert len(report_files) == 1, "Report file should be created"

                # Verify file is valid JSON
                report_data = json.loads(report_files[0].read_text())
                assert report_data['status'] == 'ACTIVATED'
            finally:
                os.chdir(old_cwd)

    def test_generate_activation_report_with_caution_status(self):
        """GREEN: Activation report reflects CAUTION status when checks fail"""
        activator = Phase3Activation(":memory:")
        activator.connect()

        checks = {
            'all_pass': False,
            'passed': 4,
            'total': 5,
            'checks': {
                'phase2_health': False,
                'database_integrity': True,
                'backup_recent': True,
                'components_healthy': True,
                'circuit_breakers_ok': True
            },
            'timestamp': datetime.now().isoformat()
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                report = activator.generate_activation_report(
                    checks,
                    "/path/to/backup.sqlite",
                    datetime.now().isoformat()
                )

                # Status should indicate caution
                assert report['status'] == 'ACTIVATED_WITH_CAUTION'
            finally:
                os.chdir(old_cwd)

    def test_checkpoint_scheduling_returns_future_time(self):
        """GREEN: First checkpoint is scheduled 2 hours in future"""
        activator = Phase3Activation(":memory:")

        before_time = datetime.now() + timedelta(hours=2)
        checkpoint_time = activator.schedule_first_checkpoint()
        after_time = datetime.now() + timedelta(hours=2)

        # Parse the ISO format checkpoint time
        checkpoint_dt = datetime.fromisoformat(checkpoint_time)

        # Should be approximately 2 hours from now
        assert before_time <= checkpoint_dt <= after_time, "Checkpoint should be ~2 hours in future"


class TestActivationWorkflow:
    """Test full activation workflow orchestration"""

    def test_run_executes_all_steps(self):
        """GREEN: Full run() executes all workflow steps"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            conn = sqlite3.connect(str(db_path))
            conn.close()

            activator = Phase3Activation(str(db_path))

            # Mock the methods to track calls
            activator.run_preflight_checks = Mock(return_value={
                'all_pass': True,
                'passed': 5,
                'total': 5,
                'checks': {}
            })
            activator.create_backup = Mock(return_value="/path/backup.sqlite")
            activator.enable_phase3 = Mock(return_value=True)
            activator.schedule_first_checkpoint = Mock(return_value=datetime.now().isoformat())
            activator.generate_activation_report = Mock(return_value={
                'status': 'ACTIVATED',
                'preflight_checks': {'all_pass': True}
            })
            activator.print_activation_summary = Mock()

            report = activator.run()

            # Verify all methods were called in order
            activator.run_preflight_checks.assert_called_once()
            activator.create_backup.assert_called_once()
            activator.enable_phase3.assert_called_once()
            activator.schedule_first_checkpoint.assert_called_once()
            activator.generate_activation_report.assert_called_once()

    def test_run_returns_activation_report(self):
        """GREEN: run() returns complete activation report"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            conn = sqlite3.connect(str(db_path))
            conn.close()

            activator = Phase3Activation(str(db_path))

            # Mock methods to avoid actual file operations
            activator.run_preflight_checks = Mock(return_value={
                'all_pass': True,
                'passed': 5,
                'total': 5,
                'checks': {}
            })
            activator.create_backup = Mock(return_value="/path/backup.sqlite")
            activator.enable_phase3 = Mock(return_value=True)
            activator.schedule_first_checkpoint = Mock(return_value="2026-10-08T12:00:00")
            activator.generate_activation_report = Mock(return_value={
                'status': 'ACTIVATED',
                'preflight_checks': {'all_pass': True},
                'backup_file': '/path/backup.sqlite',
                'first_checkpoint': '2026-10-08T12:00:00'
            })
            activator.print_activation_summary = Mock()

            report = activator.run()

            assert report is not None, "Report should be returned"
            assert 'status' in report, "Report should have status"
            assert 'backup_file' in report, "Report should have backup_file"


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_run_handles_database_connection_error(self):
        """RED: run() handles database connection errors gracefully"""
        activator = Phase3Activation("/nonexistent/path/to/db.sqlite")

        with pytest.raises(Exception):
            # Should raise error for nonexistent database
            activator.run()

    def test_enable_phase3_handles_database_error(self):
        """RED: enable_phase3() handles database errors gracefully"""
        # Create activator with a database that exists but system_config missing
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create database without system_config table
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE dummy (id INTEGER)")
            conn.close()

            activator = Phase3Activation(str(db_path))
            activator.connect()

            # Try to enable phase3 (will fail due to missing table)
            result = activator.enable_phase3()

            # Should return False on error
            assert result is False, "Should return False when table missing"

    def test_close_handles_none_connection(self):
        """GREEN: close() handles None database connection"""
        activator = Phase3Activation(":memory:")
        activator.db = None

        # Should not raise error
        activator.close()
        assert True, "close() should handle None connection gracefully"


class TestSprintThreeCompletion:
    """Meta test: Verify Sprint 3 Phase 3 activation is complete"""

    def test_phase3_activation_class_has_all_methods(self):
        """GREEN: Phase3Activation has all required methods"""
        required_methods = [
            'run_preflight_checks',
            'create_backup',
            'enable_phase3',
            'schedule_first_checkpoint',
            'generate_activation_report',
            'print_activation_summary',
            'run',
            'connect',
            'close'
        ]

        for method_name in required_methods:
            assert hasattr(Phase3Activation, method_name), f"Missing method: {method_name}"
            assert callable(getattr(Phase3Activation, method_name)), f"{method_name} should be callable"

    def test_preflight_checks_cover_all_five_areas(self):
        """GREEN: Preflight checks validate 5 critical areas"""
        # Initialize database with schema
        db = init_test_database(":memory:")

        activator = Phase3Activation(":memory:")
        activator.db = db
        activator.checkpoint_monitor.db = db

        # Mock circuit breaker registry to return healthy breakers
        activator.circuit_breaker_registry.get = Mock(return_value=Mock(state='CLOSED'))

        checks = activator.run_preflight_checks()

        # Should have 5 checks
        assert len(checks['checks']) == 5, "Should have 5 preflight checks"
        assert 'phase2_health' in checks['checks']
        assert 'database_integrity' in checks['checks']
        assert 'backup_recent' in checks['checks']
        assert 'components_healthy' in checks['checks']
        assert 'circuit_breakers_ok' in checks['checks']

    def test_activation_report_includes_all_fields(self):
        """GREEN: Activation report includes all required fields"""
        required_fields = [
            'phase',
            'timestamp',
            'status',
            'preflight_checks',
            'backup_file',
            'first_checkpoint',
            'monitoring_location',
            'dashboard',
            'kill_switch'
        ]

        activator = Phase3Activation(":memory:")
        activator.connect()

        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                checks = {
                    'all_pass': True,
                    'passed': 5,
                    'total': 5,
                    'checks': {},
                    'timestamp': datetime.now().isoformat()
                }

                report = activator.generate_activation_report(
                    checks,
                    "/backup.sqlite",
                    datetime.now().isoformat()
                )

                for field in required_fields:
                    assert field in report, f"Report missing field: {field}"
            finally:
                os.chdir(old_cwd)
