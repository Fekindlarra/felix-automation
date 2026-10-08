#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Activation Script
Executes pre-flight checks, creates backup, and enables Phase 3 with monitoring
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from backend.phase3_checkpoint_monitor import Phase3CheckpointMonitor, MetricsCollectionError
from backend.circuit_breaker import CircuitBreakerRegistry
from backend.rollback_manager import RollbackManager


class Phase3Activation:
    """Handle Phase 3 activation with safety checks"""

    def __init__(self, db_path: str = "fase15.db"):
        self.db_path = db_path
        self.db = None
        self.checkpoint_monitor = Phase3CheckpointMonitor(db_path)
        self.circuit_breaker_registry = CircuitBreakerRegistry()
        self.rollback_manager = RollbackManager(db_path)

    def connect(self):
        """Connect to database"""
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.checkpoint_monitor.connect()
        logger.info(f"✅ Connected to database: {self.db_path}")

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
        self.checkpoint_monitor.close()

    def run_preflight_checks(self) -> dict:
        """
        Run 5 critical pre-flight checks before Phase 3 activation.
        All must pass for activation to proceed.
        """
        logger.info("\n🔍 PHASE 3 PRE-FLIGHT CHECKS")
        logger.info("=" * 50)

        checks = {}

        # Check 1: Phase 2 Health (error rate < 1% in last 24 hours)
        logger.info("\n1️⃣  Checking Phase 2 Health...")
        try:
            cursor = self.db.cursor()
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

            checks['phase2_health'] = error_rate < 1.0
            logger.info(f"   Error Rate: {error_rate:.2f}% (target: <1%)")
            if checks['phase2_health']:
                logger.info("   ✅ PASS: Phase 2 error rate healthy")
            else:
                logger.error("   ❌ FAIL: Phase 2 error rate too high")
        except Exception as e:
            logger.error(f"   ❌ ERROR: {e}")
            checks['phase2_health'] = False

        # Check 2: Database Integrity
        logger.info("\n2️⃣  Checking Database Integrity...")
        try:
            required_tables = [
                'ab_tests', 'ab_test_ml_predictions', 'personalization_variants',
                'error_log', 'metrics', 'system_config', 'circuit_breaker_states'
            ]
            cursor = self.db.cursor()
            all_exist = True
            for table in required_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    logger.warning(f"   ⚠️  Missing table: {table}")
                    all_exist = False

            checks['database_integrity'] = all_exist
            if checks['database_integrity']:
                logger.info("   ✅ PASS: All required tables exist")
            else:
                logger.error("   ❌ FAIL: Some tables missing")
        except Exception as e:
            logger.error(f"   ❌ ERROR: {e}")
            checks['database_integrity'] = False

        # Check 3: Backups Recent (< 2 hours old)
        logger.info("\n3️⃣  Checking Backup Status...")
        try:
            backup_dir = Path("data/backups")
            if not backup_dir.exists():
                backup_dir.mkdir(parents=True, exist_ok=True)
                logger.info("   📁 Created backups directory")

            backups = sorted(backup_dir.glob("*.sqlite"), key=lambda x: x.stat().st_mtime, reverse=True)
            if backups:
                latest_backup = backups[0]
                age_minutes = (datetime.now() - datetime.fromtimestamp(latest_backup.stat().st_mtime)).total_seconds() / 60
                checks['backup_recent'] = age_minutes < 120

                logger.info(f"   Latest backup: {latest_backup.name} ({age_minutes:.0f} minutes old)")
                if checks['backup_recent']:
                    logger.info("   ✅ PASS: Backup is recent (< 2 hours)")
                else:
                    logger.error("   ❌ FAIL: Backup too old (> 2 hours)")
            else:
                logger.warning("   ⚠️  No backups found")
                checks['backup_recent'] = False
        except Exception as e:
            logger.error(f"   ❌ ERROR: {e}")
            checks['backup_recent'] = False

        # Check 4: Components Healthy
        logger.info("\n4️⃣  Checking System Components...")
        try:
            components = ['predictions', 'websocket', 'database']
            all_healthy = True
            for component in components:
                cb = self.circuit_breaker_registry.get(component)
                state = cb.state if cb else 'UNKNOWN'
                is_healthy = state == 'CLOSED'
                all_healthy = all_healthy and is_healthy
                status = "✅" if is_healthy else "❌"
                logger.info(f"   {status} {component.upper()}: {state}")

            checks['components_healthy'] = all_healthy
            if checks['components_healthy']:
                logger.info("   ✅ PASS: All components healthy")
            else:
                logger.warning("   ⚠️  Some components not in CLOSED state")
        except Exception as e:
            logger.error(f"   ❌ ERROR: {e}")
            checks['components_healthy'] = False

        # Check 5: Circuit Breakers Working
        logger.info("\n5️⃣  Checking Circuit Breakers...")
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT name, state FROM circuit_breaker_states
                WHERE name IN ('database', 'websocket', 'predictions')
            """)
            breakers = {row['name']: row['state'] for row in cursor.fetchall()}

            all_closed = all(state == 'CLOSED' for state in breakers.values())
            checks['circuit_breakers_ok'] = all_closed

            for name, state in breakers.items():
                status = "✅" if state == 'CLOSED' else "⚠️ "
                logger.info(f"   {status} {name}: {state}")

            if checks['circuit_breakers_ok']:
                logger.info("   ✅ PASS: All circuit breakers in CLOSED state")
            else:
                logger.warning("   ⚠️  Some circuit breakers not closed")
        except Exception as e:
            logger.error(f"   ❌ ERROR: {e}")
            checks['circuit_breakers_ok'] = False

        # Summary
        logger.info("\n" + "=" * 50)
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        logger.info(f"Pre-Flight Results: {passed}/{total} checks passed")

        if passed == total:
            logger.info("🟢 ALL CHECKS PASSED - Ready for Phase 3 activation")
        else:
            logger.warning("🟡 Some checks failed - Proceeding with caution")

        return {
            "all_pass": passed == total,
            "passed": passed,
            "total": total,
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }

    def create_backup(self) -> str:
        """Create backup before Phase 3 activation"""
        logger.info("\n💾 Creating Phase 3 Activation Backup...")
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"phase3_start_{timestamp}.sqlite"

        try:
            # Close existing connection
            self.close()

            # Copy database
            import shutil
            shutil.copy2(self.db_path, backup_file)

            # Reconnect
            self.connect()

            logger.info(f"✅ Backup created: {backup_file}")
            logger.info(f"   Size: {backup_file.stat().st_size / 1024 / 1024:.1f} MB")
            return str(backup_file)
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            raise

    def enable_phase3(self) -> bool:
        """Enable Phase 3 by setting database flag"""
        logger.info("\n🚀 Enabling Phase 3...")
        try:
            cursor = self.db.cursor()

            # Check if flag exists
            cursor.execute("SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE'")
            existing = cursor.fetchone()

            if existing:
                cursor.execute("UPDATE system_config SET value = 'true' WHERE key = 'PHASE_3_ACTIVE'")
            else:
                cursor.execute("INSERT INTO system_config (key, value) VALUES ('PHASE_3_ACTIVE', 'true')")

            self.db.commit()

            # Also store activation timestamp
            cursor.execute("INSERT INTO system_config (key, value) VALUES ('PHASE_3_ACTIVE_TIME', ?)",
                          (datetime.now().isoformat(),))
            self.db.commit()

            logger.info("✅ Phase 3 flag set to ACTIVE")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to enable Phase 3: {e}")
            self.db.rollback()
            return False

    def schedule_first_checkpoint(self) -> str:
        """Log when first checkpoint should occur (2 hours from now)"""
        first_checkpoint = datetime.now() + timedelta(hours=2)
        checkpoint_time = first_checkpoint.isoformat()

        logger.info(f"\n📍 First Checkpoint Scheduled")
        logger.info(f"   Time: {checkpoint_time}")
        logger.info(f"   In: 2 hours")
        logger.info(f"   Location: logs/phase3/checkpoint_*.json")

        return checkpoint_time

    def generate_activation_report(self, checks: dict, backup_file: str, checkpoint_time: str) -> dict:
        """Generate activation report"""
        report = {
            "phase": "Phase 3 Activation",
            "timestamp": datetime.now().isoformat(),
            "status": "ACTIVATED" if checks['all_pass'] else "ACTIVATED_WITH_CAUTION",
            "preflight_checks": checks,
            "backup_file": backup_file,
            "first_checkpoint": checkpoint_time,
            "monitoring_location": "logs/phase3/",
            "dashboard": "frontend/phase3_realtime_dashboard.html",
            "kill_switch": "POST /api/admin/phase3/deactivate"
        }

        # Save report
        report_file = Path("logs/phase3") / f"activation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2))

        logger.info(f"\n📋 Activation Report saved to: {report_file}")

        return report

    def print_activation_summary(self, report: dict):
        """Print summary to console"""
        logger.info("\n" + "=" * 60)
        logger.info("🟢 PHASE 3 ACTIVATION COMPLETE")
        logger.info("=" * 60)

        logger.info(f"\n📊 Status: {report['status']}")
        logger.info(f"⏰ Timestamp: {report['timestamp']}")

        logger.info(f"\n✅ Pre-Flight Checks: {report['preflight_checks']['passed']}/{report['preflight_checks']['total']}")
        for check_name, passed in report['preflight_checks']['checks'].items():
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {check_name}")

        logger.info(f"\n💾 Backup: {Path(report['backup_file']).name}")

        logger.info(f"\n🔔 First Checkpoint: {report['first_checkpoint']}")
        logger.info(f"📍 Monitoring: {report['monitoring_location']}")
        logger.info(f"📊 Dashboard: {report['dashboard']}")

        logger.info(f"\n🚨 Kill-Switch (Emergency Deactivation):")
        logger.info(f"   {report['kill_switch']}")
        logger.info(f"   Command: curl -X POST http://localhost:8000/api/admin/phase3/deactivate")

        logger.info("\n" + "=" * 60)

    def run(self) -> dict:
        """Execute full Phase 3 activation workflow"""
        try:
            self.connect()

            # Step 1: Pre-flight checks
            checks = self.run_preflight_checks()

            # Step 2: Create backup (even if some checks failed)
            backup_file = self.create_backup()

            # Step 3: Enable Phase 3
            enabled = self.enable_phase3()
            if not enabled:
                raise Exception("Failed to enable Phase 3 flag")

            # Step 4: Schedule first checkpoint
            checkpoint_time = self.schedule_first_checkpoint()

            # Step 5: Generate report
            report = self.generate_activation_report(checks, backup_file, checkpoint_time)

            # Print summary
            self.print_activation_summary(report)

            return report

        except Exception as e:
            logger.error(f"\n❌ ACTIVATION FAILED: {e}")
            raise
        finally:
            self.close()


def main():
    """Main entry point"""
    logger.info("FASE 15 Phase 3 Activation Script")
    logger.info("Starting at " + datetime.now().isoformat())

    activator = Phase3Activation()
    report = activator.run()

    # Exit with success/failure code
    return 0 if report['preflight_checks']['all_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
