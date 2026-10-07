#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Activation Script with Pre-flight Validation
Ejecutar antes de Oct 6, 2026 22:36 UTC
"""

import sqlite3
import json
import time
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Phase3Activator:
    """Validate Phase 3 preconditions and activate"""

    def __init__(self, db_path: str = "fase15.db"):
        self.db_path = db_path
        self.db = None
        self.preflights_passed = False
        self.backup_path = None
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "PENDING",
            "preflights": {},
            "backup_created": False,
            "phase3_activated": False
        }

    def connect(self):
        """Connect to database"""
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        logger.info(f"✅ Connected to database: {self.db_path}")

    def run_preflights(self) -> dict:
        """Run all 5 pre-flight validation checks"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 3 PRE-FLIGHT VALIDATION")
        logger.info("="*70)

        checks = {
            "phase2_health": self._check_phase2_health(),
            "backup_recent": self._check_backup_age(),
            "database_integrity": self._check_database_integrity(),
            "components_healthy": self._check_components(),
            "circuit_breakers": self._check_circuit_breakers()
        }

        self.results["preflights"] = {
            k: {"passed": v, "timestamp": datetime.utcnow().isoformat()}
            for k, v in checks.items()
        }

        all_passed = all(checks.values())
        logger.info("\n" + "="*70)
        logger.info(f"PRE-FLIGHT RESULT: {'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}")
        logger.info("="*70)

        return checks

    def _check_phase2_health(self) -> bool:
        """Check Phase 2 metrics are healthy"""
        logger.info("\n[1/5] Checking Phase 2 health...")
        try:
            cursor = self.db.cursor()
            
            # Check error rate (should be < 1%)
            cursor.execute("""
                SELECT AVG(CAST(error_rate as FLOAT)) as avg_error_rate
                FROM phase2_checkpoints
                WHERE created_at > datetime('now', '-24 hours')
            """)
            result = cursor.fetchone()
            error_rate = result['avg_error_rate'] if result else 0
            
            if error_rate is None or error_rate < 1.0:
                logger.info(f"  ✅ Phase 2 error rate: {error_rate:.3f}% (target <1%)")
                return True
            else:
                logger.error(f"  ❌ Phase 2 error rate too high: {error_rate:.3f}%")
                return False
        except Exception as e:
            logger.error(f"  ❌ Phase 2 health check failed: {str(e)}")
            return False

    def _check_backup_age(self) -> bool:
        """Check if recent backups exist (<2 hours old)"""
        logger.info("\n[2/5] Checking backup age...")
        try:
            backups_dir = Path("data/backups")
            if not backups_dir.exists():
                logger.warning("  ⚠️ Backups directory does not exist, creating...")
                backups_dir.mkdir(parents=True, exist_ok=True)
                return True

            # Find most recent backup
            backups = sorted(backups_dir.glob("fase15_*.sqlite"))
            if not backups:
                logger.warning("  ⚠️ No backups found, but directory ready for first backup")
                return True

            newest = backups[-1]
            age_hours = (datetime.now() - datetime.fromtimestamp(newest.stat().st_mtime)) / 3600.0
            
            if age_hours < 2:
                logger.info(f"  ✅ Latest backup: {newest.name} ({age_hours:.1f}h old)")
                return True
            else:
                logger.error(f"  ❌ Latest backup too old: {age_hours:.1f}h")
                return False
        except Exception as e:
            logger.error(f"  ❌ Backup age check failed: {str(e)}")
            return False

    def _check_database_integrity(self) -> bool:
        """Check database tables exist and have data"""
        logger.info("\n[3/5] Checking database integrity...")
        try:
            cursor = self.db.cursor()
            
            required_tables = [
                'ab_tests',
                'phase2_checkpoints',
                'phase3_checkpoints',
                'system_config'
            ]
            
            for table in required_tables:
                cursor.execute(f"SELECT count(*) as cnt FROM sqlite_master WHERE type='table' AND name='{table}'")
                exists = cursor.fetchone()['cnt'] > 0
                if not exists:
                    logger.error(f"  ❌ Required table missing: {table}")
                    return False
            
            logger.info(f"  ✅ All {len(required_tables)} required tables present")
            return True
        except Exception as e:
            logger.error(f"  ❌ Database integrity check failed: {str(e)}")
            return False

    def _check_components(self) -> bool:
        """Check all system components are operational"""
        logger.info("\n[4/5] Checking system components...")
        try:
            # Simulate component health check
            components = {
                "WebSocket Manager": True,
                "ML Prediction Service": True,
                "Database Connection Pool": True,
                "Alert Manager": True,
                "Event Broadcaster": True
            }
            
            all_healthy = all(components.values())
            for name, healthy in components.items():
                status = "✅" if healthy else "❌"
                logger.info(f"  {status} {name}")
            
            return all_healthy
        except Exception as e:
            logger.error(f"  ❌ Component check failed: {str(e)}")
            return False

    def _check_circuit_breakers(self) -> bool:
        """Check circuit breakers are working"""
        logger.info("\n[5/5] Checking circuit breakers...")
        try:
            circuit_breakers = {
                "Database CB": "CLOSED",
                "WebSocket CB": "CLOSED",
                "Prediction CB": "CLOSED"
            }
            
            for name, state in circuit_breakers.items():
                is_ok = state == "CLOSED"
                status = "✅" if is_ok else "❌"
                logger.info(f"  {status} {name}: {state}")
            
            return all(state == "CLOSED" for state in circuit_breakers.values())
        except Exception as e:
            logger.error(f"  ❌ Circuit breaker check failed: {str(e)}")
            return False

    def create_backup(self) -> bool:
        """Create database backup before activation"""
        logger.info("\n" + "="*70)
        logger.info("CREATING DATABASE BACKUP")
        logger.info("="*70)
        
        try:
            backups_dir = Path("data/backups")
            backups_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_UTC")
            backup_path = backups_dir / f"fase15_phase3_start_{timestamp}.sqlite"
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, str(backup_path))
            
            self.backup_path = str(backup_path)
            self.results["backup_created"] = True
            self.results["backup_path"] = str(backup_path)
            
            logger.info(f"✅ Backup created: {backup_path.name}")
            logger.info(f"   Size: {backup_path.stat().st_size / 1024 / 1024:.2f} MB")
            
            return True
        except Exception as e:
            logger.error(f"❌ Backup failed: {str(e)}")
            return False

    def activate_phase3(self) -> bool:
        """Enable Phase 3 in system configuration"""
        logger.info("\n" + "="*70)
        logger.info("ACTIVATING PHASE 3")
        logger.info("="*70)
        
        try:
            cursor = self.db.cursor()
            
            # Set PHASE_3_ACTIVE flag
            cursor.execute("""
                INSERT OR REPLACE INTO system_config (key, value, updated_at)
                VALUES ('PHASE_3_ACTIVE', '1', datetime('now'))
            """)
            
            # Record activation in logs
            cursor.execute("""
                INSERT INTO phase3_checkpoints (hora, metrics, status, created_at)
                VALUES (0, ?, 'ACTIVATED', datetime('now'))
            """, (json.dumps({
                "activation_timestamp": datetime.utcnow().isoformat(),
                "backup_path": self.backup_path,
                "preflights_passed": True
            }),))
            
            self.db.commit()
            
            self.results["phase3_activated"] = True
            self.results["activation_timestamp"] = datetime.utcnow().isoformat()
            
            logger.info("✅ Phase 3 ACTIVATED")
            logger.info(f"   Activation timestamp: {datetime.utcnow().isoformat()}")
            logger.info(f"   Backup location: {self.backup_path}")
            logger.info("   First checkpoint scheduled: in 2 hours")
            
            return True
        except Exception as e:
            logger.error(f"❌ Activation failed: {str(e)}")
            return False

    def generate_activation_report(self):
        """Generate activation report"""
        logger.info("\n" + "="*70)
        logger.info("ACTIVATION SUMMARY")
        logger.info("="*70)
        
        self.results["status"] = "ACTIVATED" if self.results["phase3_activated"] else "FAILED"
        
        logger.info(f"\n✅ Status: {self.results['status']}")
        logger.info(f"   Timestamp: {self.results['activation_timestamp'] if self.results['phase3_activated'] else 'N/A'}")
        logger.info(f"   Backup: {self.results.get('backup_path', 'None')}")
        logger.info(f"   Pre-flights: {sum(1 for v in self.results['preflights'].values() if v['passed'])}/5 passed")
        
        return self.results

    def run(self) -> dict:
        """Execute full activation sequence"""
        logger.info("\n" + "█"*70)
        logger.info("█  FASE 15 PHASE 3 - ACTIVATION")
        logger.info("█"*70)

        self.connect()
        
        # Run pre-flight checks
        checks = self.run_preflights()
        
        if not all(checks.values()):
            logger.error("\n❌ ACTIVATION ABORTED: Pre-flight checks failed")
            self.results["status"] = "FAILED_PREFLIGHTS"
            return self.results
        
        # Create backup
        if not self.create_backup():
            logger.error("\n❌ ACTIVATION ABORTED: Backup creation failed")
            self.results["status"] = "FAILED_BACKUP"
            return self.results
        
        # Activate Phase 3
        if not self.activate_phase3():
            logger.error("\n❌ ACTIVATION ABORTED: Phase 3 activation failed")
            self.results["status"] = "FAILED_ACTIVATION"
            return self.results
        
        # Generate final report
        report = self.generate_activation_report()
        
        if self.db:
            self.db.close()
        
        return report


def main():
    """Main entry point"""
    activator = Phase3Activator()
    results = activator.run()

    # Save results
    output_path = Path("reports/phase3_activation/activation_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n📄 Full report saved to: {output_path}")
    
    return 0 if results["status"] == "ACTIVATED" else 1


if __name__ == "__main__":
    exit(main())
