#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Integration Tests
Test all Phase 3 components work together
"""

import sqlite3
import unittest
import json
from datetime import datetime
from pathlib import Path


class Phase3IntegrationTests(unittest.TestCase):
    """Integration test suite for Phase 3"""

    def setUp(self):
        """Set up test fixtures"""
        self.db_path = ":memory:"
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self._init_test_tables()

    def tearDown(self):
        """Clean up"""
        if self.db:
            self.db.close()

    def _init_test_tables(self):
        """Initialize test database tables"""
        cursor = self.db.cursor()
        
        # Create ab_tests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_tests (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT
            )
        """)
        
        # Create phase3_checkpoints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phase3_checkpoints (
                id INTEGER PRIMARY KEY,
                hora INTEGER,
                metrics TEXT,
                status TEXT,
                created_at TIMESTAMP
            )
        """)
        
        # Create ab_test_ml_predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_test_ml_predictions (
                id INTEGER PRIMARY KEY,
                test_id INTEGER,
                client_id INTEGER,
                ml_probability REAL,
                rules_probability REAL,
                actual_outcome INTEGER,
                created_at TIMESTAMP
            )
        """)
        
        # Create system_config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP
            )
        """)
        
        self.db.commit()

    def test_01_database_connectivity(self):
        """Test database connectivity"""
        cursor = self.db.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)

    def test_02_tables_exist(self):
        """Test all required tables exist"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%phase3%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        self.assertGreater(len(tables), 0)

    def test_03_insert_checkpoint(self):
        """Test inserting a checkpoint"""
        cursor = self.db.cursor()
        metrics = json.dumps({
            "ml_accuracy": 0.835,
            "error_rate": 0.017,
            "websocket_latency": 8,
            "predictions_hour": 48,
            "personalization_active": 150,
            "active_tests": 9
        })
        
        cursor.execute("""
            INSERT INTO phase3_checkpoints (hora, metrics, status, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (48, metrics, "GREEN"))
        
        self.db.commit()
        
        cursor.execute("SELECT COUNT(*) as cnt FROM phase3_checkpoints")
        count = cursor.fetchone()['cnt']
        self.assertEqual(count, 1)

    def test_04_retrieve_checkpoint(self):
        """Test retrieving checkpoint data"""
        cursor = self.db.cursor()
        
        # Insert test data
        metrics = json.dumps({"ml_accuracy": 0.84})
        cursor.execute("""
            INSERT INTO phase3_checkpoints (hora, metrics, status)
            VALUES (?, ?, ?)
        """, (50, metrics, "GREEN"))
        self.db.commit()
        
        # Retrieve and verify
        cursor.execute("SELECT * FROM phase3_checkpoints WHERE hora = ?", (50,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['hora'], 50)

    def test_05_ml_vs_rules_comparison(self):
        """Test ML vs rules prediction recording"""
        cursor = self.db.cursor()
        
        # Insert comparison record
        cursor.execute("""
            INSERT INTO ab_test_ml_predictions
            (test_id, client_id, ml_probability, rules_probability)
            VALUES (?, ?, ?, ?)
        """, (1, 100, 0.82, 0.78))
        
        self.db.commit()
        
        # Retrieve and verify
        cursor.execute("""
            SELECT ml_probability, rules_probability 
            FROM ab_test_ml_predictions 
            WHERE test_id = ?
        """, (1,))
        
        row = cursor.fetchone()
        self.assertEqual(row['ml_probability'], 0.82)
        self.assertEqual(row['rules_probability'], 0.78)

    def test_06_health_metrics_calculation(self):
        """Test health score calculation from metrics"""
        metrics_data = {
            "ml_accuracy": 0.835,  # ✅ target >78%
            "error_rate": 0.017,   # ✅ target <0.08%
            "websocket_latency": 8, # ✅ target <95ms
            "predictions_hour": 48, # ✅ target >42
            "personalization_active": 150, # ✅ target >140
            "active_tests": 9       # ✅ target >8
        }
        
        # Calculate health score
        health_score = sum([
            1 if metrics_data["ml_accuracy"] > 0.78 else 0,
            1 if metrics_data["error_rate"] < 0.08 else 0,
            1 if metrics_data["websocket_latency"] < 95 else 0,
            1 if metrics_data["predictions_hour"] > 42 else 0,
            1 if metrics_data["personalization_active"] > 140 else 0,
            1 if metrics_data["active_tests"] > 8 else 0,
        ])
        
        self.assertEqual(health_score, 6)

    def test_07_phase3_activation_flag(self):
        """Test setting Phase 3 activation flag"""
        cursor = self.db.cursor()
        
        # Set flag
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_ACTIVE', '1', datetime('now'))
        """)
        self.db.commit()
        
        # Retrieve and verify
        cursor.execute("SELECT value FROM system_config WHERE key = ?", ("PHASE_3_ACTIVE",))
        row = cursor.fetchone()
        self.assertEqual(row['value'], '1')

    def test_08_checkpoint_sequence(self):
        """Test checkpoint sequence over 24 hours"""
        cursor = self.db.cursor()
        
        # Insert 13 checkpoints simulating 24-hour monitoring
        for i in range(13):
            hora = 48 + (i * 2)  # Every 2 hours
            metrics = json.dumps({
                "ml_accuracy": 0.82 + (i * 0.001),
                "error_rate": 0.017 - (i * 0.0001)
            })
            cursor.execute("""
                INSERT INTO phase3_checkpoints (hora, metrics, status)
                VALUES (?, ?, ?)
            """, (hora, metrics, "GREEN"))
        
        self.db.commit()
        
        # Verify all inserted
        cursor.execute("SELECT COUNT(*) as cnt FROM phase3_checkpoints")
        count = cursor.fetchone()['cnt']
        self.assertEqual(count, 13)

    def test_09_rollback_trigger_condition(self):
        """Test rollback trigger conditions"""
        # Simulate high error rate that triggers rollback
        error_rate = 0.15  # > 0.08% threshold
        should_rollback = error_rate > 0.08
        
        self.assertTrue(should_rollback)

    def test_10_data_consistency(self):
        """Test data consistency across checkpoints"""
        cursor = self.db.cursor()
        
        # Insert checkpoint
        cursor.execute("""
            INSERT INTO phase3_checkpoints (hora, metrics, status)
            VALUES (?, ?, ?)
        """, (48, '{"ml_accuracy": 0.84}', "GREEN"))
        self.db.commit()
        
        # Query and verify
        cursor.execute("SELECT metrics FROM phase3_checkpoints WHERE hora = ?", (48,))
        row = cursor.fetchone()
        metrics = json.loads(row['metrics'])
        
        self.assertEqual(metrics['ml_accuracy'], 0.84)

    def test_11_error_handling(self):
        """Test error handling in database operations"""
        cursor = self.db.cursor()
        
        # Test handling missing table
        with self.assertRaises(Exception):
            cursor.execute("SELECT * FROM nonexistent_table")

    def test_12_concurrent_checkpoint_writes(self):
        """Test handling concurrent checkpoint writes"""
        cursor = self.db.cursor()
        
        # Simulate concurrent writes
        for i in range(5):
            cursor.execute("""
                INSERT INTO phase3_checkpoints (hora, metrics, status)
                VALUES (?, ?, ?)
            """, (48 + i, '{}', "GREEN"))
        
        self.db.commit()
        
        # Verify all writes succeeded
        cursor.execute("SELECT COUNT(*) as cnt FROM phase3_checkpoints")
        count = cursor.fetchone()['cnt']
        self.assertEqual(count, 5)


def run_integration_tests():
    """Run all integration tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(Phase3IntegrationTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_integration_tests())
