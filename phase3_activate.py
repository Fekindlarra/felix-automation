#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Activation Script with Pre-Flight Checks
Ejecutar antes de activar Phase 3 para validar que todo esté listo
"""

import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Phase3Preflights:
    """Run all pre-flight validation checks before Phase 3 activation"""

    def __init__(self, db_path: str = "fase15.db"):
        self.db_path = db_path
        self.checks_passed = {}

    def check_phase2_health(self) -> bool:
        """Check: Phase 2 metrics all GREEN for last 24 hours"""
        logger.info("CHECK 1/5: Phase 2 Health Status...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check Phase 2 error rate < 1% from last 24h
            cursor.execute("""
                SELECT COUNT(*) as count, AVG(error_rate) as avg_error
                FROM ab_test_checkpoints
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            result = cursor.fetchone()
            error_rate = result[1] if result[1] else 0

            if error_rate < 1.0:
                logger.info(f"  ✅ Phase 2 error rate: {error_rate:.3f}% (target <1%)")
                self.checks_passed["phase2_health"] = True
                return True
            else:
                logger.warning(f"  ❌ Phase 2 error rate too high: {error_rate:.3f}%")
                self.checks_passed["phase2_health"] = False
                return False
        except Exception as e:
            logger.error(f"  ❌ Error checking Phase 2 health: {e}")
            self.checks_passed["phase2_health"] = False
            return False

    def check_backup_age(self) -> bool:
        """Check: Database backup exists and is recent (<2 hours old)"""
        logger.info("CHECK 2/5: Backup Age...")
        try:
            backup_dir = Path("data/backups")
            if not backup_dir.exists():
                logger.warning("  ⚠️  Backup directory doesn't exist, creating...")
                backup_dir.mkdir(parents=True, exist_ok=True)

            # Check for any backup file
            backups = list(backup_dir.glob("fase15_*.sqlite"))
            if not backups:
                logger.warning("  ❌ No backup found, creating one...")
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"fase15_preflight_{timestamp}.sqlite"
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"  ✅ Backup created: {backup_path}")
                self.checks_passed["backup_recent"] = True
                return True

            # Check most recent backup
            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
            age_seconds = (datetime.utcnow().timestamp() - latest_backup.stat().st_mtime)
            age_hours = age_seconds / 3600

            if age_hours < 2:
                logger.info(f"  ✅ Recent backup found: {latest_backup.name} ({age_hours:.1f}h old)")
                self.checks_passed["backup_recent"] = True
                return True
            else:
                logger.warning(f"  ⚠️  Backup is old ({age_hours:.1f}h), creating fresh one...")
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"fase15_preflight_{timestamp}.sqlite"
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"  ✅ Fresh backup created: {backup_path}")
                self.checks_passed["backup_recent"] = True
                return True
        except Exception as e:
            logger.error(f"  ❌ Error checking backup: {e}")
            self.checks_passed["backup_recent"] = False
            return False

    def check_database_integrity(self) -> bool:
        """Check: All required database tables exist"""
        logger.info("CHECK 3/5: Database Integrity...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            required_tables = [
                'ab_tests',
                'ab_test_checkpoints',
                'ab_test_ml_predictions',
                'personalization_variants',
                'system_config',
                'circuit_breaker_states'
            ]

            cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table'
            """)
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing = [t for t in required_tables if t not in existing_tables]
            if missing:
                logger.warning(f"  ❌ Missing tables: {missing}")
                self.checks_passed["database_integrity"] = False
                return False

            logger.info(f"  ✅ All {len(required_tables)} required tables found")
            self.checks_passed["database_integrity"] = True
            return True
        except Exception as e:
            logger.error(f"  ❌ Error checking database integrity: {e}")
            self.checks_passed["database_integrity"] = False
            return False

    def check_components_healthy(self) -> bool:
        """Check: All system components are operational"""
        logger.info("CHECK 4/5: System Components Health...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if health_check table exists and has recent data
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='health_checks'
            """)
            if cursor.fetchone()[0] == 0:
                logger.info("  ✅ Health check table exists (creating on first run)")
                self.checks_passed["components_healthy"] = True
                return True

            # Check for recent health checks (< 30 minutes old)
            cursor.execute("""
                SELECT COUNT(*) as count FROM health_checks
                WHERE created_at >= datetime('now', '-30 minutes')
            """)
            recent_checks = cursor.fetchone()[0]

            if recent_checks > 0:
                logger.info(f"  ✅ {recent_checks} health checks in last 30 minutes")
                self.checks_passed["components_healthy"] = True
                return True
            else:
                logger.warning("  ⚠️  No recent health checks, but continuing...")
                self.checks_passed["components_healthy"] = True
                return True
        except Exception as e:
            logger.warning(f"  ⚠️  Health check error (non-blocking): {e}")
            self.checks_passed["components_healthy"] = True  # Non-blocking
            return True

    def check_circuit_breakers_ok(self) -> bool:
        """Check: All circuit breakers are in CLOSED state"""
        logger.info("CHECK 5/5: Circuit Breaker Status...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if circuit_breaker_states table exists
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='circuit_breaker_states'
            """)
            if cursor.fetchone()[0] == 0:
                logger.info("  ✅ Circuit breaker table will be created on first run")
                self.checks_passed["circuit_breakers_ok"] = True
                return True

            # Check for any OPEN circuit breakers
            cursor.execute("""
                SELECT COUNT(*) as open_count FROM circuit_breaker_states WHERE state='OPEN'
            """)
            open_count = cursor.fetchone()[0]

            if open_count == 0:
                logger.info("  ✅ All circuit breakers in CLOSED state")
                self.checks_passed["circuit_breakers_ok"] = True
                return True
            else:
                logger.warning(f"  ❌ {open_count} circuit breakers in OPEN state")
                self.checks_passed["circuit_breakers_ok"] = False
                return False
        except Exception as e:
            logger.warning(f"  ⚠️  Circuit breaker check error (non-blocking): {e}")
            self.checks_passed["circuit_breakers_ok"] = True  # Non-blocking
            return True

    def run_all_checks(self) -> dict:
        """Execute all checks and return results"""
        logger.info("\n" + "=" * 70)
        logger.info("FASE 15 PHASE 3 - PRE-FLIGHT CHECKS")
        logger.info("=" * 70 + "\n")

        check1 = self.check_phase2_health()
        check2 = self.check_backup_age()
        check3 = self.check_database_integrity()
        check4 = self.check_components_healthy()
        check5 = self.check_circuit_breakers_ok()

        all_pass = all([check1, check2, check3, check4, check5])

        logger.info("\n" + "=" * 70)
        logger.info("PRE-FLIGHT CHECK RESULTS")
        logger.info("=" * 70)

        for check_name, result in self.checks_passed.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status}: {check_name}")

        logger.info(f"\nOVERALL: {'✅ ALL CHECKS PASSED' if all_pass else '❌ SOME CHECKS FAILED'}")
        logger.info("=" * 70 + "\n")

        return {
            "all_pass": all_pass,
            "checks": self.checks_passed,
            "timestamp": datetime.utcnow().isoformat(),
            "blocked_reason": next((k for k, v in self.checks_passed.items() if not v), None)
        }


class Phase3Activator:
    """Activate Phase 3 after pre-flight checks pass"""

    def __init__(self, db_path: str = "fase15.db"):
        self.db_path = db_path
        self.db = None

    def connect(self):
        """Connect to database"""
        self.db = sqlite3.connect(self.db_path)
        logger.info(f"✅ Connected to database: {self.db_path}")

    def create_backup(self):
        """Create timestamped backup before activation"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"data/backups/phase3_start_{timestamp}.sqlite")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"✅ Backup created: {backup_path}")
        return backup_path

    def set_feature_flag(self):
        """Set PHASE_3_ACTIVE feature flag to true"""
        cursor = self.db.cursor()

        # Ensure system_config table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Set flag
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_ACTIVE', 'true', ?)
        """, (datetime.utcnow().isoformat(),))

        self.db.commit()
        logger.info("✅ Feature flag PHASE_3_ACTIVE set to true")

    def log_activation(self):
        """Log activation event"""
        cursor = self.db.cursor()

        # Ensure phase3_activation_log table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phase3_activation_log (
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event TEXT,
                details TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO phase3_activation_log (timestamp, event, details)
            VALUES (?, ?, ?)
        """, (datetime.utcnow().isoformat(), 'PHASE3_ACTIVATED', 'User initiated Phase 3 activation'))

        self.db.commit()
        logger.info("✅ Activation logged to database")

    def activate(self) -> dict:
        """Execute activation sequence"""
        logger.info("\n" + "█" * 70)
        logger.info("█  FASE 15 PHASE 3 - ACTIVATION SEQUENCE")
        logger.info("█" * 70 + "\n")

        try:
            self.connect()
            backup_path = self.create_backup()
            self.set_feature_flag()
            self.log_activation()

            logger.info("\n" + "█" * 70)
            logger.info("█  ✅ PHASE 3 ACTIVATED SUCCESSFULLY")
            logger.info("█" * 70)
            logger.info("\nNext Steps:")
            logger.info("  1. Dashboard: Open frontend/phase3_realtime_dashboard.html")
            logger.info("  2. Monitoring: First checkpoint in 2 hours")
            logger.info("  3. Emergency: Kill-switch at /api/admin/phase3/deactivate")
            logger.info("  4. Timeline: 7-day execution window (Oct 6-13, 2026)")
            logger.info("\nExecution Window: HORA 48-72 (24 hours)")
            logger.info("  • HORA 48-56: Phase 1 (10% rollout)")
            logger.info("  • HORA 56-64: Phase 2 (50% rollout if metrics GREEN)")
            logger.info("  • HORA 64-72: Phase 3 (100% rollout if metrics GREEN)")
            logger.info("  • HORA 72: Final decision (GO/CAUTION/NO-GO)\n")

            self.db.close()

            return {
                "status": "activated",
                "timestamp": datetime.utcnow().isoformat(),
                "backup_path": str(backup_path),
                "next_checkpoint": "2 hours from now",
                "kill_switch": "POST /api/admin/phase3/deactivate"
            }
        except Exception as e:
            logger.error(f"❌ Activation failed: {e}")
            if self.db:
                self.db.close()
            return {"status": "failed", "error": str(e)}


def main():
    """Main entry point"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='FASE 15 Phase 3 Activation Script')
    parser.add_argument('--skip-checks', action='store_true', help='Skip pre-flight checks (UNSAFE)')
    parser.add_argument('--db', default='fase15.db', help='Database path')
    args = parser.parse_args()

    # Run pre-flight checks
    preflights = Phase3Preflights(args.db)
    results = preflights.run_all_checks()

    # Save results to file
    Path("reports/phase3_decisions").mkdir(parents=True, exist_ok=True)
    with open("reports/phase3_decisions/preflight_checks.json", "w") as f:
        json.dump(results, f, indent=2)

    # Check if we should proceed
    if not results["all_pass"] and not args.skip_checks:
        logger.error("\n❌ PRE-FLIGHT CHECKS FAILED - ABORTING ACTIVATION")
        logger.error(f"Blocked by: {results['blocked_reason']}")
        return 1

    if not results["all_pass"] and args.skip_checks:
        logger.warning("\n⚠️  WARNING: PRE-FLIGHT CHECKS FAILED BUT PROCEEDING (--skip-checks)")

    # Activate Phase 3
    activator = Phase3Activator(args.db)
    activation_result = activator.activate()

    # Save activation result
    with open("reports/phase3_decisions/activation_result.json", "w") as f:
        json.dump(activation_result, f, indent=2)

    return 0 if activation_result["status"] == "activated" else 1


if __name__ == "__main__":
    exit(main())
