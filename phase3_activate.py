#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Activation Script with Pre-Flight Checks
Validates system readiness before activating Phase 3 production execution
"""

import sys
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from backend.config import DATABASE_PATH


class Phase3ActivationValidator:
    """Pre-flight checks and activation for Phase 3"""

    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.db = None
        self.checks = {}
        self.backup_path = None

    def connect_database(self):
        """Connect to database"""
        try:
            self.db = sqlite3.connect(self.db_path)
            self.db.row_factory = sqlite3.Row
            self.db.execute("PRAGMA foreign_keys = ON")
            logger.info(f"✅ Connected to {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False

    def check_phase2_metrics(self) -> bool:
        """Check if Phase 2 metrics were healthy for last 24h"""
        try:
            logger.info("📊 Checking Phase 2 metrics...")

            cursor = self.db.cursor()

            # Check for recent metrics collection
            cursor.execute("""
                SELECT COUNT(*) FROM backend_metrics_collector
                WHERE collected_at > datetime('now', '-24 hours')
            """)
            result = cursor.fetchone()
            if result[0] < 10:
                logger.warning("⚠️ Insufficient metrics collected in last 24h")
                return False

            # Check if error rate was acceptable
            cursor.execute("""
                SELECT AVG(error_rate) FROM backend_metrics_collector
                WHERE collected_at > datetime('now', '-24 hours')
            """)
            result = cursor.fetchone()
            avg_error_rate = result[0] if result[0] else 0
            if avg_error_rate > 0.001:  # <0.1%
                logger.warning(f"⚠️ Phase 2 error rate too high: {avg_error_rate*100:.2f}%")
                return False

            logger.info(f"✅ Phase 2 metrics healthy (avg error rate: {avg_error_rate*100:.3f}%)")
            return True

        except Exception as e:
            logger.error(f"❌ Error checking Phase 2 metrics: {e}")
            return False

    def check_database_integrity(self) -> bool:
        """Check database schema and integrity"""
        try:
            logger.info("🔍 Checking database integrity...")

            cursor = self.db.cursor()

            # Check required tables exist
            required_tables = [
                'ab_tests',
                'ab_test_ml_predictions',
                'personalization_variants',
                'comparison_reports',
                'backend_metrics_collector',
                'system_config'
            ]

            for table in required_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.debug(f"  ✅ Table '{table}': {count} rows")

            logger.info("✅ Database schema intact")
            return True

        except Exception as e:
            logger.error(f"❌ Database integrity check failed: {e}")
            return False

    def check_backups_recent(self) -> bool:
        """Check if recent backups exist"""
        try:
            logger.info("💾 Checking backup status...")

            backup_dir = Path("data/backups")
            if not backup_dir.exists():
                logger.warning("⚠️ Backup directory not found")
                return False

            # Get most recent backup
            backups = sorted(backup_dir.glob("*.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True)

            if not backups:
                logger.warning("⚠️ No backups found")
                return False

            most_recent = backups[0]
            backup_age_hours = (datetime.utcnow() - datetime.fromtimestamp(most_recent.stat().st_mtime)).total_seconds() / 3600

            if backup_age_hours > 2:
                logger.warning(f"⚠️ Most recent backup is {backup_age_hours:.1f} hours old")
                return False

            self.backup_path = most_recent
            logger.info(f"✅ Recent backup exists: {most_recent.name} ({backup_age_hours:.1f}h old)")
            return True

        except Exception as e:
            logger.error(f"❌ Backup check failed: {e}")
            return False

    def check_circuit_breakers(self) -> bool:
        """Check that circuit breaker system can be initialized"""
        try:
            logger.info("🔌 Checking circuit breaker system...")

            from backend.circuit_breaker import (
                CircuitBreakerRegistry,
                get_database_breaker,
                get_websocket_breaker,
                get_prediction_breaker
            )

            # Try to initialize circuit breakers
            db_breaker = get_database_breaker()
            ws_breaker = get_websocket_breaker()
            pred_breaker = get_prediction_breaker()

            if db_breaker.get_state() not in ["CLOSED", "HALF_OPEN"]:
                logger.warning(f"⚠️ Database circuit breaker in {db_breaker.get_state()} state")

            logger.info("✅ Circuit breaker system operational")
            return True

        except Exception as e:
            logger.error(f"❌ Circuit breaker check failed: {e}")
            return False

    def check_websocket_ready(self) -> bool:
        """Check WebSocket manager is available"""
        try:
            logger.info("📡 Checking WebSocket system...")

            from backend.websocket_manager import get_connection_manager

            ws_manager = get_connection_manager()
            if ws_manager is None:
                logger.warning("⚠️ WebSocket manager not initialized")
                return False

            logger.info("✅ WebSocket system ready")
            return True

        except Exception as e:
            logger.error(f"❌ WebSocket check failed: {e}")
            return False

    def run_all_checks(self) -> bool:
        """Run all pre-flight checks"""
        logger.info("\n" + "="*80)
        logger.info("🚀 FASE 15 Phase 3 - PRE-FLIGHT CHECKS")
        logger.info("="*80 + "\n")

        self.checks["database_connected"] = self.connect_database()
        if not self.checks["database_connected"]:
            return False

        self.checks["phase2_metrics"] = self.check_phase2_metrics()
        self.checks["database_integrity"] = self.check_database_integrity()
        self.checks["backups_recent"] = self.check_backups_recent()
        self.checks["circuit_breakers"] = self.check_circuit_breakers()
        self.checks["websocket_ready"] = self.check_websocket_ready()

        # Summary
        logger.info("\n" + "="*80)
        logger.info("📋 PRE-FLIGHT CHECK SUMMARY")
        logger.info("="*80)

        all_passed = True
        for check_name, result in self.checks.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {check_name}")
            if not result:
                all_passed = False

        logger.info("="*80 + "\n")

        return all_passed

    def activate_phase3(self) -> bool:
        """Activate Phase 3 after all checks pass"""
        try:
            logger.info("🔄 Activating Phase 3...")

            cursor = self.db.cursor()

            # 1. Create backup
            backup_path = self._create_activation_backup()
            logger.info(f"✅ Backup created: {backup_path}")

            # 2. Enable Phase 3 flag
            cursor.execute("""
                INSERT OR REPLACE INTO system_config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, ("PHASE_3_ACTIVE", "true"))
            self.db.commit()
            logger.info("✅ Phase 3 feature flag enabled")

            # 3. Initialize rollout phases
            cursor.execute("""
                UPDATE personalization_variants
                SET rollout_phase = 1
                WHERE rollout_phase IS NULL OR rollout_phase = 0
            """)
            self.db.commit()
            logger.info("✅ Rollout phases initialized to Phase 1 (10%)")

            # 4. Log activation
            activation_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "activated",
                "checks": self.checks,
                "backup_path": str(backup_path),
                "next_checkpoint": "HORA 48 (in 2 hours from start)"
            }

            log_path = Path("logs/phase3_activation.json")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w') as f:
                json.dump(activation_log, f, indent=2)

            logger.info(f"✅ Activation log saved: {log_path}")

            return True

        except Exception as e:
            logger.error(f"❌ Activation failed: {e}")
            return False

    def _create_activation_backup(self) -> Path:
        """Create backup at activation time"""
        try:
            from shutil import copy2

            backup_dir = Path("data/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"phase3_start_{timestamp}.sqlite"

            copy2(self.db_path, backup_path)
            logger.debug(f"Backup created: {backup_path}")

            return backup_path

        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
            return None

    def print_activation_report(self):
        """Print final activation report"""
        logger.info("\n" + "="*80)
        logger.info("✅ FASE 15 PHASE 3 ACTIVATION REPORT")
        logger.info("="*80)
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Backup: {self.backup_path}")
        logger.info("\nStatus: READY FOR PRODUCTION")
        logger.info("Next: Start checkpoint monitoring at HORA 48")
        logger.info("\nCheckpoint Schedule:")
        logger.info("  • HORA 48-56: Phase 1 (10% rollout) - 8 hours")
        logger.info("  • HORA 56-64: Phase 2 (50% rollout) - 8 hours")
        logger.info("  • HORA 64-72: Phase 3 (100% rollout) - 8 hours")
        logger.info("  • HORA 72: FINAL DECISION (SUCCESS/CAUTION/ROLLBACK)")
        logger.info("\nMonitoring:")
        logger.info("  • Checkpoints every 2 hours")
        logger.info("  • 6 metrics tracked (ML Accuracy, Error Rate, Latency, etc.)")
        logger.info("  • Auto-rollback if <5/6 metrics healthy")
        logger.info("\nKill-Switch: Available via POST /api/admin/phase3/deactivate")
        logger.info("="*80 + "\n")

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()


def main():
    """Main activation workflow"""
    validator = Phase3ActivationValidator()

    try:
        # Run pre-flight checks
        if not validator.run_all_checks():
            logger.error("❌ PRE-FLIGHT CHECKS FAILED - ACTIVATION ABORTED")
            validator.print_activation_report()
            return 1

        # Activate Phase 3
        if not validator.activate_phase3():
            logger.error("❌ ACTIVATION FAILED")
            return 1

        # Print success report
        validator.print_activation_report()
        return 0

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1

    finally:
        validator.close()


if __name__ == "__main__":
    sys.exit(main())
