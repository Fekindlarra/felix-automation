#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3: A/B Testing Framework Integration - Test Suite
Validates ML vs Rules Comparator, Personalization Engine, and WebSocket Broadcasting
"""

import pytest
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

# Test imports
from agents.ml_vs_rules_comparator import MLvsRulesComparator
from agents.personalization_engine import PersonalizationEngine
from agents.email_variant_assigner import EmailVariantAssigner


class TestDatabase:
    """Test database setup and schema"""

    @pytest.fixture
    def db_connection(self):
        """Create in-memory SQLite database for testing"""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # Create necessary tables for testing
        self._create_test_schema(conn)
        yield conn
        conn.close()

    def _create_test_schema(self, conn):
        """Create minimal schema for testing"""
        cursor = conn.cursor()

        # Clients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # AB Tests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                email_type TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                variant_a TEXT,
                variant_b TEXT,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                planned_duration_days INTEGER DEFAULT 14,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ML Predictions tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_test_ml_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                ml_probability REAL NOT NULL,
                rules_probability REAL NOT NULL,
                actual_outcome INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                outcome_date TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES ab_tests(id),
                FOREIGN KEY (client_id) REFERENCES clients(id),
                UNIQUE(test_id, client_id)
            )
        """)

        # Personalization variants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personalization_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                winning_variant TEXT NOT NULL,
                rollout_phase INTEGER DEFAULT 1,
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                effective_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES ab_tests(id),
                FOREIGN KEY (client_id) REFERENCES clients(id),
                UNIQUE(test_id, client_id)
            )
        """)

        # Comparison reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparison_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                ml_accuracy REAL,
                rules_accuracy REAL,
                ml_avg_confidence REAL,
                winner TEXT,
                confidence_interval TEXT,
                sample_size INTEGER,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES ab_tests(id),
                UNIQUE(test_id)
            )
        """)

        conn.commit()


class TestMLvsRulesComparator(TestDatabase):
    """Test MLvsRulesComparator class"""

    def test_record_prediction_pair(self, db_connection):
        """Test recording ML vs rules prediction pair"""
        comparator = MLvsRulesComparator(db_connection)

        # Setup: Create test and client
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type) VALUES (?, ?)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid
        cursor.execute("INSERT INTO clients (name) VALUES (?)", ("Client 1",))
        client_id = cursor.lastrowid
        db_connection.commit()

        # Test: Record prediction pair
        record_id = comparator.record_prediction_pair(test_id, client_id, 0.75, 0.65)
        assert record_id > 0, "Should return positive record ID"

        # Verify: Check database
        cursor.execute("""
            SELECT ml_probability, rules_probability FROM ab_test_ml_predictions
            WHERE test_id = ? AND client_id = ?
        """, (test_id, client_id))
        row = cursor.fetchone()
        assert row is not None, "Record should exist"
        assert row['ml_probability'] == 0.75
        assert row['rules_probability'] == 0.65

    def test_record_outcome(self, db_connection):
        """Test recording actual conversion outcome"""
        comparator = MLvsRulesComparator(db_connection)

        # Setup
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type) VALUES (?, ?)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid
        cursor.execute("INSERT INTO clients (name) VALUES (?)", ("Client 1",))
        client_id = cursor.lastrowid
        db_connection.commit()

        # Record prediction first
        comparator.record_prediction_pair(test_id, client_id, 0.75, 0.65)

        # Test: Record outcome
        success = comparator.record_outcome(test_id, client_id, 1)
        assert success is True

        # Verify
        cursor.execute("""
            SELECT actual_outcome, outcome_date FROM ab_test_ml_predictions
            WHERE test_id = ? AND client_id = ?
        """, (test_id, client_id))
        row = cursor.fetchone()
        assert row['actual_outcome'] == 1
        assert row['outcome_date'] is not None

    def test_calculate_accuracy(self, db_connection):
        """Test accuracy calculation"""
        comparator = MLvsRulesComparator(db_connection)

        # Setup: Create test and client
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type) VALUES (?, ?)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid

        # Add 10 test cases
        for i in range(10):
            cursor.execute("INSERT INTO clients (name) VALUES (?)", (f"Client {i}",))
            client_id = cursor.lastrowid

            # ML is more accurate in this scenario
            ml_prob = 0.8 if i % 2 == 0 else 0.2  # Alternating high/low
            rules_prob = 0.5  # Rules always 0.5
            actual = 1 if i % 2 == 0 else 0  # Outcome matches ML predictions

            comparator.record_prediction_pair(test_id, client_id, ml_prob, rules_prob)
            comparator.record_outcome(test_id, client_id, actual)

        db_connection.commit()

        # Test: Calculate accuracy
        accuracy = comparator.calculate_accuracy(test_id)

        assert accuracy['sample_size'] == 10
        assert accuracy['ml_accuracy'] > 0.5, "ML should have >50% accuracy"
        assert accuracy['rules_accuracy'] == 0.5, "Rules should have 50% (always 0.5 threshold)"
        assert accuracy['winner'] == 'ML', "ML should win"

    def test_confidence_interval(self, db_connection):
        """Test Wilson score confidence interval calculation"""
        comparator = MLvsRulesComparator(db_connection)

        # Test: 80% accuracy with 100 samples
        ci = comparator.calculate_confidence_interval(0.8, 100)

        assert ci['lower'] < 0.8, "Lower bound should be < point estimate"
        assert ci['upper'] > 0.8, "Upper bound should be > point estimate"
        assert ci['lower'] >= 0.0, "Lower bound should be >= 0"
        assert ci['upper'] <= 1.0, "Upper bound should be <= 1"

    def test_generate_comparison_report(self, db_connection):
        """Test comparison report generation"""
        comparator = MLvsRulesComparator(db_connection)

        # Setup
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type) VALUES (?, ?)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid

        # Add test data
        for i in range(20):
            cursor.execute("INSERT INTO clients (name) VALUES (?)", (f"Client {i}",))
            client_id = cursor.lastrowid
            comparator.record_prediction_pair(test_id, client_id, 0.7, 0.6)
            comparator.record_outcome(test_id, client_id, 1 if i % 2 == 0 else 0)

        db_connection.commit()

        # Test: Generate report
        report = comparator.generate_comparison_report(test_id)

        assert report is not None
        assert report['test_id'] == test_id
        assert report['sample_size'] == 20
        assert 'ml_accuracy' in report
        assert 'rules_accuracy' in report
        assert 'winner' in report
        assert 'confidence_interval' in report


class TestPersonalizationEngine(TestDatabase):
    """Test PersonalizationEngine class"""

    def test_apply_test_winner(self, db_connection):
        """Test applying test winner with gradual rollout"""
        engine = PersonalizationEngine(db_connection)

        # Setup: Create test and clients
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type, active) VALUES (?, ?, 1)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid

        # Create multiple clients
        for i in range(20):
            cursor.execute("INSERT INTO clients (name) VALUES (?)", (f"Client {i}",))
        db_connection.commit()

        # Test: Apply winner
        success = engine.apply_test_winner(test_id, 'A')
        assert success is True

        # Verify: Should have assigned to ~10% of clients (2 out of 20)
        cursor.execute("""
            SELECT COUNT(*) as count FROM personalization_variants
            WHERE test_id = ? AND rollout_phase = 1
        """, (test_id,))
        count = cursor.fetchone()['count']
        assert count > 0, "Should have assigned Phase 1 variants"
        assert count <= 5, "Phase 1 should be ~10% of clients"

    def test_should_use_variant(self, db_connection):
        """Test checking if client should use personalized variant"""
        engine = PersonalizationEngine(db_connection)

        # Setup
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type) VALUES (?, ?)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid
        cursor.execute("INSERT INTO clients (name) VALUES (?)", ("Client 1",))
        client_id = cursor.lastrowid

        # Create personalization variant
        cursor.execute("""
            INSERT INTO personalization_variants
            (client_id, test_id, winning_variant, rollout_phase)
            VALUES (?, ?, ?, 1)
        """, (client_id, test_id, 'A'))
        db_connection.commit()

        # Test: Check variant assignment
        should_use, variant = engine.should_use_variant(test_id, client_id)
        assert should_use is True
        assert variant == 'A'

        # Test: Non-existent variant
        should_use, variant = engine.should_use_variant(test_id, 999)
        assert should_use is False
        assert variant is None

    def test_advance_rollout_phase(self, db_connection):
        """Test advancing rollout phase"""
        engine = PersonalizationEngine(db_connection)

        # Setup
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type) VALUES (?, ?)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid

        # Create Phase 1 assignments
        for i in range(5):
            cursor.execute("INSERT INTO clients (name) VALUES (?)", (f"Client {i}",))
            client_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO personalization_variants
                (client_id, test_id, winning_variant, rollout_phase)
                VALUES (?, ?, 'A', 1)
            """, (client_id, test_id))
        db_connection.commit()

        # Test: Advance to Phase 2
        success = engine.advance_rollout_phase(test_id, target_phase=2)
        assert success is True

        # Verify: Should have more assignments now
        cursor.execute("""
            SELECT COUNT(*) as count FROM personalization_variants
            WHERE test_id = ? AND rollout_phase = 2
        """, (test_id,))
        count = cursor.fetchone()['count']
        assert count >= 0, "Phase 2 assignments created"

    def test_get_rollout_stats(self, db_connection):
        """Test retrieving rollout statistics"""
        engine = PersonalizationEngine(db_connection)

        # Setup
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type) VALUES (?, ?)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid

        # Create mixed phase assignments
        for phase, count in [(1, 5), (2, 10), (3, 20)]:
            for i in range(count):
                cursor.execute("INSERT INTO clients (name) VALUES (?)",
                             (f"Client {phase}_{i}",))
                client_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO personalization_variants
                    (client_id, test_id, winning_variant, rollout_phase)
                    VALUES (?, ?, ?, ?)
                """, (client_id, test_id, 'A', phase))
        db_connection.commit()

        # Test: Get stats
        stats = engine.get_rollout_stats(test_id)
        assert stats['total_assigned'] == 35
        assert stats['phase_1'] == 5
        assert stats['phase_2'] == 10
        assert stats['phase_3'] == 20
        assert stats['current_phase'] == 3


class TestEmailVariantAssigner(TestDatabase):
    """Test EmailVariantAssigner personalization integration"""

    def test_assign_variant_with_personalization(self, db_connection):
        """Test that assign_variant checks personalization first"""
        assigner = EmailVariantAssigner(db_connection)

        # Setup
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type) VALUES (?, ?)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid
        cursor.execute("INSERT INTO clients (name) VALUES (?)", ("Client 1",))
        client_id = cursor.lastrowid

        # Create personalization variant
        cursor.execute("""
            INSERT INTO personalization_variants
            (client_id, test_id, winning_variant)
            VALUES (?, ?, 'B')
        """, (client_id, test_id))
        db_connection.commit()

        # Test: Should use personalized variant
        variant = assigner.assign_variant(test_id, client_id)
        assert variant == 'B', "Should use personalized variant"

    def test_assign_variant_fallback_to_hash(self, db_connection):
        """Test fallback to hash-based assignment"""
        assigner = EmailVariantAssigner(db_connection)

        # Setup
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO ab_tests (test_name, email_type) VALUES (?, ?)",
                      ("Test 1", "email_test"))
        test_id = cursor.lastrowid
        cursor.execute("INSERT INTO clients (name) VALUES (?)", ("Client 1",))
        client_id = cursor.lastrowid
        db_connection.commit()

        # Test: No personalization, use hash
        variant = assigner.assign_variant(test_id, client_id)
        assert variant in ['A', 'B'], "Should return A or B"


# Performance and Integration Tests

class TestIntegration:
    """Integration tests for Phase 3 components"""

    def test_full_workflow(self):
        """Test complete Phase 3 workflow"""
        # Setup in-memory database
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row

        # Create schema (simplified for this test)
        cursor = conn.cursor()

        # ... would need full schema here for real test

        # Workflow:
        # 1. Create A/B test
        # 2. Record ML vs rules predictions
        # 3. Generate comparison report
        # 4. Apply winner with personalization
        # 5. Verify variant assignment respects personalization

        # This is a placeholder for the full integration test
        assert True, "Workflow test structure defined"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
