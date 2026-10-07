#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Database Query Optimizations
Sprint 4: Indexes, query optimization, and connection pooling
"""

import sqlite3
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

# Thread-local storage for database connections (for connection pooling)
_thread_local = threading.local()

# Query optimization hints
QUERY_OPTIMIZATION_HINTS = {
    "ab_tests_by_phase": "Use index idx_ab_tests_phase3",
    "predictions_by_test": "Use index idx_predictions_test_client",
    "predictions_by_accuracy": "Use index idx_predictions_accuracy",
    "personalization_by_rollout": "Use index idx_personalization_rollout",
    "personalization_by_client": "Use index idx_personalization_client",
    "system_config_lookup": "Use index idx_system_config_key",
    "api_logs_by_time": "Use index idx_api_logs_timestamp"
}


class DatabaseOptimizer:
    """Database query optimization and connection management"""

    def __init__(self, db_path: str = "fase15.db"):
        self.db_path = db_path
        self.connection_pool_size = 5
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes

        logger.info(f"✅ DatabaseOptimizer initialized for {db_path}")

    @staticmethod
    def enable_performance_pragmas(db: sqlite3.Connection):
        """Enable SQLite performance optimizations"""
        try:
            cursor = db.cursor()

            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            # Increase cache size (default is 2000 pages)
            cursor.execute("PRAGMA cache_size = 10000")

            # Enable synchronous mode OFF for faster writes (with journaling)
            cursor.execute("PRAGMA synchronous = NORMAL")

            # Set journal mode to WAL for better concurrency
            cursor.execute("PRAGMA journal_mode = WAL")

            # Enable query optimization
            cursor.execute("PRAGMA optimize")

            db.commit()
            logger.info("✅ Performance pragmas enabled: cache_size=10000, sync=NORMAL, journal=WAL")

        except sqlite3.Error as e:
            logger.warning(f"Could not enable all pragmas: {e}")

    @staticmethod
    def create_phase3_indexes(db_path: str = "fase15.db") -> bool:
        """Create all Phase 3 optimization indexes"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            indexes = [
                # ab_tests table indexes
                ("idx_ab_tests_phase3",
                 "CREATE INDEX IF NOT EXISTS idx_ab_tests_phase3 ON ab_tests(phase, active, created_at)"),

                # ab_test_ml_predictions indexes
                ("idx_predictions_test_client",
                 "CREATE INDEX IF NOT EXISTS idx_predictions_test_client ON ab_test_ml_predictions(test_id, client_id)"),

                ("idx_predictions_accuracy",
                 "CREATE INDEX IF NOT EXISTS idx_predictions_accuracy ON ab_test_ml_predictions(test_id, actual_outcome)"),

                # personalization_variants indexes
                ("idx_personalization_rollout",
                 "CREATE INDEX IF NOT EXISTS idx_personalization_rollout ON personalization_variants(test_id, rollout_phase)"),

                ("idx_personalization_client",
                 "CREATE INDEX IF NOT EXISTS idx_personalization_client ON personalization_variants(client_id, effective_until)"),

                # system_config indexes
                ("idx_system_config_key",
                 "CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(key)"),

                # api_logs indexes for monitoring
                ("idx_api_logs_timestamp",
                 "CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_logs(timestamp, status_code)"),
            ]

            created_count = 0
            for index_name, index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    created_count += 1
                    logger.info(f"✅ Index created: {index_name}")
                except sqlite3.OperationalError as e:
                    if "already exists" in str(e):
                        logger.debug(f"⏭️  Index {index_name} already exists")
                    else:
                        logger.warning(f"⚠️  Could not create index {index_name}: {e}")

            conn.commit()
            conn.close()

            logger.info(f"✅ Phase 3 database optimization complete ({created_count} indexes)")
            return True

        except Exception as e:
            logger.error(f"❌ Database optimization failed: {e}")
            return False

    @staticmethod
    def optimize_predictions_query(test_id: int, db_path: str = "fase15.db") -> Optional[list]:
        """
        Optimized query to get predictions for a test.
        Uses index idx_predictions_test_client for fast lookup.
        """
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Query uses index idx_predictions_test_client
            cursor.execute("""
                SELECT
                    id, test_id, client_id, ml_probability, rules_probability,
                    actual_outcome, created_at
                FROM ab_test_ml_predictions
                WHERE test_id = ?
                ORDER BY created_at ASC
            """, (test_id,))

            results = cursor.fetchall()
            conn.close()

            return results

        except sqlite3.Error as e:
            logger.error(f"❌ Error querying predictions: {e}")
            return None

    @staticmethod
    def get_personalization_status(test_id: int, rollout_phase: int,
                                  db_path: str = "fase15.db") -> Dict[str, Any]:
        """
        Get personalization rollout status for a test.
        Uses index idx_personalization_rollout for fast lookup.
        """
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Query uses index idx_personalization_rollout
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM personalization_variants
                WHERE test_id = ? AND rollout_phase = ?
            """, (test_id, rollout_phase))

            result = cursor.fetchone()
            total = result['count'] if result else 0

            conn.close()

            return {
                'test_id': test_id,
                'rollout_phase': rollout_phase,
                'users_affected': total
            }

        except sqlite3.Error as e:
            logger.error(f"❌ Error querying personalization status: {e}")
            return {'test_id': test_id, 'rollout_phase': rollout_phase, 'users_affected': 0}

    @staticmethod
    def batch_insert_predictions(predictions: list, db_path: str = "fase15.db") -> int:
        """
        Batch insert predictions for better performance.
        Sprint 4 optimization: Use executemany with single commit.

        Args:
            predictions: List of (test_id, client_id, ml_prob, rules_prob) tuples
            db_path: Database path

        Returns:
            Number of records inserted
        """
        if not predictions:
            return 0

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Batch insert with single commit
            cursor.executemany("""
                INSERT OR REPLACE INTO ab_test_ml_predictions
                (test_id, client_id, ml_probability, rules_probability, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, predictions)

            conn.commit()
            inserted = len(predictions)
            conn.close()

            logger.info(f"✅ Batch inserted {inserted} predictions")
            return inserted

        except sqlite3.Error as e:
            logger.error(f"❌ Error in batch insert: {e}")
            return 0

    @staticmethod
    def analyze_query_performance(query: str, db_path: str = "fase15.db") -> Dict[str, Any]:
        """
        Analyze query performance using EXPLAIN QUERY PLAN.
        Sprint 4 optimization: Identify missing indexes.

        Args:
            query: SQL query to analyze
            db_path: Database path

        Returns:
            Query plan analysis
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get query plan
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()

            conn.close()

            analysis = {
                'query': query,
                'plan': [dict(row) if hasattr(row, 'keys') else str(row) for row in plan],
                'uses_index': any('INDEX' in str(row) for row in plan),
                'uses_full_scan': any('SCAN' in str(row) for row in plan),
                'recommendation': None
            }

            # Generate recommendation
            if analysis['uses_full_scan']:
                analysis['recommendation'] = "Consider adding an index to avoid full table scans"
            elif not analysis['uses_index']:
                analysis['recommendation'] = "Query could benefit from indexed lookups"

            return analysis

        except sqlite3.Error as e:
            logger.error(f"❌ Error analyzing query: {e}")
            return {'query': query, 'error': str(e)}

    @contextmanager
    def get_connection(self, read_only: bool = False):
        """
        Get a database connection (connection pooling).
        Sprint 4 optimization: Reuse connections from pool.

        Args:
            read_only: Open in read-only mode

        Yields:
            sqlite3.Connection
        """
        try:
            # Check thread-local storage for existing connection
            if not hasattr(_thread_local, 'connection') or _thread_local.connection is None:
                uri = f"file:{self.db_path}?mode={'ro' if read_only else 'rwc'}"
                conn = sqlite3.connect(uri, uri=True)
                self.enable_performance_pragmas(conn)
                _thread_local.connection = conn
            else:
                conn = _thread_local.connection

            yield conn

        except Exception as e:
            logger.error(f"❌ Error getting connection: {e}")
            if hasattr(_thread_local, 'connection'):
                _thread_local.connection = None
            raise

    def close_connections(self):
        """Close all thread-local connections"""
        if hasattr(_thread_local, 'connection') and _thread_local.connection:
            try:
                _thread_local.connection.close()
            except:
                pass
            _thread_local.connection = None


# Performance benchmarking utilities
class PerformanceBenchmark:
    """Benchmark database query performance"""

    @staticmethod
    def benchmark_query(query: str, params: tuple = (), iterations: int = 100,
                       db_path: str = "fase15.db") -> Dict[str, float]:
        """
        Benchmark a query over multiple iterations.
        Sprint 4 optimization: Identify slow queries.

        Args:
            query: SQL query
            params: Query parameters
            iterations: Number of iterations
            db_path: Database path

        Returns:
            Benchmark results with timing statistics
        """
        import time

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            times = []
            for _ in range(iterations):
                start = time.time()
                cursor.execute(query, params)
                cursor.fetchall()
                elapsed = time.time() - start
                times.append(elapsed * 1000)  # Convert to ms

            conn.close()

            total_ms = sum(times)
            avg_ms = total_ms / len(times)
            min_ms = min(times)
            max_ms = max(times)
            median_ms = sorted(times)[len(times) // 2]

            return {
                'query': query,
                'iterations': iterations,
                'total_ms': round(total_ms, 2),
                'avg_ms': round(avg_ms, 2),
                'min_ms': round(min_ms, 2),
                'max_ms': round(max_ms, 2),
                'median_ms': round(median_ms, 2),
                'throughput_per_sec': round(iterations / (total_ms / 1000), 2)
            }

        except Exception as e:
            logger.error(f"❌ Error in benchmark: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*70)
    print("FASE 15 Phase 3 - Database Optimization Utility")
    print("="*70 + "\n")

    optimizer = DatabaseOptimizer()

    # Enable pragmas
    print("📊 Enabling performance pragmas...")
    try:
        conn = sqlite3.connect("fase15.db")
        DatabaseOptimizer.enable_performance_pragmas(conn)
        conn.close()
    except:
        pass

    # Create indexes
    print("\n📑 Creating Phase 3 optimization indexes...")
    DatabaseOptimizer.create_phase3_indexes()

    print("\n✅ Database optimization complete!")
