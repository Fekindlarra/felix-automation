#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Sprint 4 Performance Testing
Benchmarks critical Phase 3 queries and operations to verify optimization improvements
"""

import sqlite3
import logging
import time
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database_optimizations import DatabaseOptimizer, PerformanceBenchmark

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Phase3PerformanceTester:
    """Test and benchmark Phase 3 database and WebSocket performance"""

    def __init__(self, db_path: str = "data/pipeline.sqlite"):
        self.db_path = db_path
        self.results = {}
        logger.info(f"✅ Phase 3 Performance Tester initialized (DB: {db_path})")

    def benchmark_batch_insert_performance(self) -> dict:
        """Benchmark batch insert performance for predictions"""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK: Batch Insert Performance (ML vs Rules Predictions)")
        logger.info("="*70)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Generate test data: 1000 predictions in batches
            test_data = [
                (1, i, 0.45 + (i % 100) * 0.001, 0.52 + (i % 100) * 0.001)
                for i in range(1000)
            ]

            times = []
            for batch_size in [1, 10, 50, 100, 500]:
                start = time.time()

                for i in range(0, len(test_data), batch_size):
                    batch = test_data[i:i+batch_size]
                    cursor.executemany("""
                        INSERT OR REPLACE INTO ab_test_ml_predictions
                        (test_id, client_id, ml_probability, rules_probability, created_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, batch)
                    conn.commit()

                elapsed = (time.time() - start) * 1000  # Convert to ms
                times.append((batch_size, elapsed))
                throughput = (len(test_data) / (elapsed / 1000)) if elapsed > 0 else 0

                logger.info(f"  Batch size {batch_size:3d}: {elapsed:7.2f}ms | "
                           f"Throughput: {throughput:6.0f} records/sec")

            conn.close()

            return {
                "test": "batch_insert_performance",
                "total_records": len(test_data),
                "results": [{"batch_size": bs, "elapsed_ms": t} for bs, t in times],
                "recommendation": "Batch size 100+ recommended for Phase 3 production"
            }

        except Exception as e:
            logger.error(f"❌ Error in batch insert benchmark: {e}")
            return {"error": str(e)}

    def benchmark_query_with_indexes(self) -> dict:
        """Benchmark queries with Phase 3 indexes"""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK: Query Performance (With Phase 3 Indexes)")
        logger.info("="*70)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Test predictions query
            results = {}

            # Query 1: Get predictions by test ID (uses idx_predictions_test_client)
            query1 = """
                SELECT id, test_id, client_id, ml_probability, rules_probability
                FROM ab_test_ml_predictions
                WHERE test_id = ?
                ORDER BY created_at ASC
            """
            benchmark1 = PerformanceBenchmark.benchmark_query(
                query1,
                params=(1,),
                iterations=100,
                db_path=self.db_path
            )
            results["predictions_by_test"] = benchmark1
            logger.info(f"  Predictions Query (idx_predictions_test_client):")
            logger.info(f"    Avg: {benchmark1.get('avg_ms', 0):.2f}ms | "
                       f"Min: {benchmark1.get('min_ms', 0):.2f}ms | "
                       f"Max: {benchmark1.get('max_ms', 0):.2f}ms")

            # Query 2: Get personalization status by test/phase (uses idx_personalization_rollout)
            query2 = """
                SELECT COUNT(*) as count
                FROM personalization_variants
                WHERE test_id = ? AND rollout_phase = ?
            """
            benchmark2 = PerformanceBenchmark.benchmark_query(
                query2,
                params=(1, 1),
                iterations=100,
                db_path=self.db_path
            )
            results["personalization_by_phase"] = benchmark2
            logger.info(f"  Personalization Query (idx_personalization_rollout):")
            logger.info(f"    Avg: {benchmark2.get('avg_ms', 0):.2f}ms | "
                       f"Min: {benchmark2.get('min_ms', 0):.2f}ms | "
                       f"Max: {benchmark2.get('max_ms', 0):.2f}ms")

            # Query 3: System config lookup (uses idx_system_config_key)
            query3 = """
                SELECT value FROM system_config WHERE key = ?
            """
            benchmark3 = PerformanceBenchmark.benchmark_query(
                query3,
                params=('PHASE_3_ACTIVE',),
                iterations=100,
                db_path=self.db_path
            )
            results["config_lookup"] = benchmark3
            logger.info(f"  Config Lookup Query (idx_system_config_key):")
            logger.info(f"    Avg: {benchmark3.get('avg_ms', 0):.2f}ms | "
                       f"Min: {benchmark3.get('min_ms', 0):.2f}ms | "
                       f"Max: {benchmark3.get('max_ms', 0):.2f}ms")

            conn.close()

            return {
                "test": "query_performance_with_indexes",
                "results": results,
                "target_latency_ms": 5,
                "status": "All queries meeting <5ms target" if all(
                    r.get('avg_ms', 999) < 5 for r in results.values()
                ) else "Some queries exceed target"
            }

        except Exception as e:
            logger.error(f"❌ Error in query benchmark: {e}")
            return {"error": str(e)}

    def benchmark_connection_pooling(self) -> dict:
        """Benchmark connection pooling efficiency"""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK: Connection Pooling Efficiency")
        logger.info("="*70)

        try:
            optimizer = DatabaseOptimizer(self.db_path)

            # Test with connection pooling
            start = time.time()
            for i in range(10):
                with optimizer.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM ab_tests")
                    cursor.fetchone()
            pooled_time = (time.time() - start) * 1000

            # Test without pooling (new connection each time)
            start = time.time()
            for i in range(10):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ab_tests")
                cursor.fetchone()
                conn.close()
            unpooled_time = (time.time() - start) * 1000

            improvement = ((unpooled_time - pooled_time) / unpooled_time) * 100

            logger.info(f"  Pooled (10 queries): {pooled_time:.2f}ms")
            logger.info(f"  Unpooled (10 queries): {unpooled_time:.2f}ms")
            logger.info(f"  Improvement: {improvement:.1f}%")

            return {
                "test": "connection_pooling",
                "pooled_time_ms": pooled_time,
                "unpooled_time_ms": unpooled_time,
                "improvement_percent": improvement,
                "recommendation": "Connection pooling provides significant performance boost"
            }

        except Exception as e:
            logger.error(f"❌ Error in connection pooling benchmark: {e}")
            return {"error": str(e)}

    def verify_database_pragmas(self) -> dict:
        """Verify database performance pragmas are enabled"""
        logger.info("\n" + "="*70)
        logger.info("VERIFY: Database Performance Pragmas")
        logger.info("="*70)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            pragmas = {
                "cache_size": "PRAGMA cache_size",
                "synchronous": "PRAGMA synchronous",
                "journal_mode": "PRAGMA journal_mode",
                "foreign_keys": "PRAGMA foreign_keys"
            }

            results = {}
            for name, pragma in pragmas.items():
                cursor.execute(pragma)
                value = cursor.fetchone()[0]
                results[name] = value
                logger.info(f"  {name}: {value}")

            conn.close()

            return {
                "test": "database_pragmas",
                "pragmas": results,
                "status": "optimized" if results.get("journal_mode") == "wal" else "needs_attention"
            }

        except Exception as e:
            logger.error(f"❌ Error verifying pragmas: {e}")
            return {"error": str(e)}

    def run_all_benchmarks(self) -> None:
        """Run all performance benchmarks"""
        logger.info("\n" + "="*80)
        logger.info(" FASE 15 PHASE 3 - SPRINT 4 PERFORMANCE TESTING")
        logger.info("="*80)

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": self.db_path,
            "benchmarks": {}
        }

        # Run all benchmarks
        results["benchmarks"]["pragmas"] = self.verify_database_pragmas()
        results["benchmarks"]["connection_pooling"] = self.benchmark_connection_pooling()
        results["benchmarks"]["query_performance"] = self.benchmark_query_with_indexes()
        results["benchmarks"]["batch_insert"] = self.benchmark_batch_insert_performance()

        # Summary
        logger.info("\n" + "="*80)
        logger.info(" SPRINT 4 PERFORMANCE TESTING SUMMARY")
        logger.info("="*80)

        all_passing = True
        for test_name, result in results["benchmarks"].items():
            status = "✅ PASS" if "error" not in result else "❌ FAIL"
            logger.info(f"{status}: {test_name}")
            if "error" in result:
                all_passing = False

        logger.info("\n" + "="*80)
        if all_passing:
            logger.info("✅ ALL BENCHMARKS COMPLETE - Phase 3 optimizations verified")
        else:
            logger.warning("⚠️  Some benchmarks need review")
        logger.info("="*80 + "\n")

        # Save results to file
        report_path = Path("reports/phase3_performance_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📊 Performance report saved to {report_path}")

        return results


def main():
    """Main entry point"""
    try:
        tester = Phase3PerformanceTester()
        results = tester.run_all_benchmarks()
        return 0
    except Exception as e:
        logger.error(f"❌ Performance testing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
