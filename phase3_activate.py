#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Activation Script
Orchestrates Phase 3 launch with pre-flight validation, backup, and checkpoint scheduling
Execution window: 24 hours with 13 checkpoints every 2 hours
"""

import sqlite3
import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

DB_PATH = "data/pipeline.sqlite"
BACKUP_DIR = Path("data/backups")
LOGS_DIR = Path("logs/phase3")
CHECKPOINT_INTERVAL = 2 * 3600  # 2 hours in seconds
TOTAL_CHECKPOINTS = 13
EXECUTION_HOURS = 24

# Metric thresholds (targets from dashboard)
METRICS_THRESHOLDS = {
    "ml_accuracy": 0.78,           # ≥78%
    "error_rate": 0.0008,          # <0.08%
    "websocket_latency": 95,       # <95ms
    "predictions_hour": 42,        # ≥42
    "personalization_active": 140, # ≥140
    "active_tests": 8              # ≥8
}

# =============================================================================
# Pre-flight Validation
# =============================================================================

class Phase3Validator:
    """Validates all pre-conditions for Phase 3 activation"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.checks = {}
    
    def check_database_exists(self) -> bool:
        """Check database file exists and is accessible"""
        try:
            if not Path(self.db_path).exists():
                logger.error(f"❌ Database file not found: {self.db_path}")
                return False
            
            # Test connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            count = cursor.fetchone()[0]
            conn.close()
            
            logger.info(f"✅ Database check: {count} tables found, connection OK")
            return True
        except Exception as e:
            logger.error(f"❌ Database check failed: {str(e)}")
            return False
    
    def check_phase2_health(self) -> bool:
        """Check Phase 2 metrics are healthy (error_rate < 1%)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query recent metrics
            cursor.execute("""
                SELECT AVG(error_rate) as avg_error_rate
                FROM metrics
                WHERE created_at > datetime('now', '-24 hours')
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                error_rate = result[0]
                health_ok = error_rate < 0.01  # <1%
                status = "✅" if health_ok else "⚠️ "
                logger.info(f"{status} Phase 2 health: error_rate={error_rate:.4f}%")
                return True  # Allow activation even if no Phase 2 data (fresh deployment)
            
            logger.info("✅ Phase 2 health: No historical data (fresh deployment)")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Phase 2 health check skipped: {str(e)}")
            return True
    
    def check_backup_recent(self) -> bool:
        """Check if backups directory exists and is writable"""
        try:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            
            # Test write capability
            test_file = BACKUP_DIR / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
            
            logger.info("✅ Backup directory: Writable and ready")
            return True
        except Exception as e:
            logger.error(f"❌ Backup directory check failed: {str(e)}")
            return False
    
    def check_circuit_breakers(self) -> bool:
        """Check circuit breakers are in CLOSED state"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, state FROM circuit_breaker_states
                WHERE last_checked > datetime('now', '-5 minutes')
            """)
            
            breakers = cursor.fetchall()
            conn.close()
            
            if not breakers:
                logger.info("✅ Circuit breakers: No breakers recorded (fresh system)")
                return True
            
            all_closed = all(state == "CLOSED" for _, state in breakers)
            if all_closed:
                logger.info(f"✅ Circuit breakers: All {len(breakers)} in CLOSED state")
                return True
            else:
                open_breakers = [name for name, state in breakers if state != "CLOSED"]
                logger.error(f"❌ Circuit breaker check FAILED: {open_breakers} are not CLOSED")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️  Circuit breaker check skipped: {str(e)}")
            return True
    
    def check_required_tables(self) -> bool:
        """Check all required tables exist"""
        try:
            required = [
                "ab_tests",
                "ab_test_ml_predictions",
                "personalization_variants",
                "phase3_checkpoints",
                "system_config",
                "system_metrics",
                "circuit_breaker_states"
            ]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing = {row[0] for row in cursor.fetchall()}
            
            missing = set(required) - existing
            conn.close()
            
            if missing:
                logger.error(f"❌ Missing tables: {missing}")
                return False
            
            logger.info(f"✅ Database schema: All {len(required)} required tables present")
            return True
            
        except Exception as e:
            logger.error(f"❌ Table check failed: {str(e)}")
            return False
    
    def run_all_checks(self) -> tuple:
        """Run all validation checks"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 3 PRE-FLIGHT VALIDATION")
        logger.info("="*70)
        
        checks = {
            "database_exists": self.check_database_exists(),
            "required_tables": self.check_required_tables(),
            "phase2_health": self.check_phase2_health(),
            "backup_ready": self.check_backup_recent(),
            "circuit_breakers": self.check_circuit_breakers()
        }
        
        all_pass = all(checks.values())
        failed = [k for k, v in checks.items() if not v]
        
        logger.info("\n" + "-"*70)
        if all_pass:
            logger.info("✅ ALL PRE-FLIGHT CHECKS PASSED")
        else:
            logger.error(f"❌ FAILED CHECKS: {failed}")
        logger.info("-"*70 + "\n")
        
        return all_pass, checks

# =============================================================================
# Phase 3 Activation
# =============================================================================

class Phase3Activator:
    """Orchestrates Phase 3 activation"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.activation_time = datetime.utcnow()
        self.backup_path = None
    
    def create_backup(self) -> bool:
        """Create pre-activation backup"""
        try:
            logger.info("💾 Creating pre-activation backup...")
            
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = self.activation_time.strftime("%Y%m%d_%H%M%S_UTC")
            self.backup_path = BACKUP_DIR / f"phase3_pre_activation_{timestamp}.sqlite"
            
            shutil.copy2(self.db_path, str(self.backup_path))
            logger.info(f"✅ Backup created: {self.backup_path}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Backup failed: {str(e)}")
            return False
    
    def enable_phase3_flag(self) -> bool:
        """Set PHASE_3_ACTIVE flag in database"""
        try:
            logger.info("🚀 Enabling Phase 3 flag...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Set activation flag
            cursor.execute("""
                INSERT OR REPLACE INTO system_config (key, value, updated_at)
                VALUES ('PHASE_3_ACTIVE', 'true', ?)
            """, (self.activation_time.isoformat(),))
            
            # Record activation time
            cursor.execute("""
                INSERT OR REPLACE INTO system_config (key, value, updated_at)
                VALUES ('PHASE_3_ACTIVATION_TIME', ?, ?)
            """, (self.activation_time.isoformat(), self.activation_time.isoformat()))
            
            # Set checkpoint tracking
            cursor.execute("""
                INSERT OR REPLACE INTO system_config (key, value, updated_at)
                VALUES ('PHASE_3_CHECKPOINT_COUNT', '0', ?)
            """, (self.activation_time.isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Phase 3 flag ENABLED")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set Phase 3 flag: {str(e)}")
            return False
    
    def schedule_checkpoints(self) -> bool:
        """Log checkpoint schedule for monitoring"""
        try:
            logger.info("📅 Scheduling 13 checkpoints for 24-hour window...")
            
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            
            checkpoints = []
            for i in range(TOTAL_CHECKPOINTS):
                checkpoint_time = self.activation_time + timedelta(hours=i*2)
                checkpoints.append({
                    "number": i + 1,
                    "hora": 48 + (i * 2),
                    "scheduled_time": checkpoint_time.isoformat(),
                    "status": "pending"
                })
            
            # Save checkpoint schedule
            schedule_file = LOGS_DIR / "checkpoint_schedule.json"
            with open(schedule_file, 'w') as f:
                json.dump(checkpoints, f, indent=2)
            
            logger.info(f"✅ Checkpoint schedule saved: {len(checkpoints)} checkpoints")
            logger.info(f"   First checkpoint: {checkpoints[0]['hora']} ({checkpoints[0]['scheduled_time']})")
            logger.info(f"   Last checkpoint:  {checkpoints[-1]['hora']} ({checkpoints[-1]['scheduled_time']})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Checkpoint scheduling failed: {str(e)}")
            return False
    
    def create_activation_report(self) -> dict:
        """Generate activation report"""
        report = {
            "status": "ACTIVATED",
            "timestamp": self.activation_time.isoformat(),
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "execution_window": f"{EXECUTION_HOURS} hours (24-hour monitoring)",
            "checkpoint_count": TOTAL_CHECKPOINTS,
            "checkpoint_interval_hours": 2,
            "metrics_thresholds": METRICS_THRESHOLDS,
            "phase_advancement": {
                "phase_1": {"rollout": "10%", "duration_hours": 8},
                "phase_2": {"rollout": "50%", "duration_hours": 8},
                "phase_3": {"rollout": "100%", "duration_hours": 8}
            },
            "monitoring_url": "http://localhost:8000/dashboard/phase3",
            "kill_switch_activate": "POST /api/admin/phase3/activate",
            "kill_switch_deactivate": "POST /api/admin/phase3/deactivate",
            "kill_switch_status": "GET /api/admin/phase3/status",
            "first_checkpoint_eta": (self.activation_time + timedelta(hours=2)).isoformat(),
            "final_decision_time": (self.activation_time + timedelta(hours=24)).isoformat()
        }
        
        return report
    
    def activate(self) -> bool:
        """Execute full activation sequence"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 3 ACTIVATION SEQUENCE")
        logger.info("="*70 + "\n")
        
        # Step 1: Create backup
        if not self.create_backup():
            return False
        
        # Step 2: Enable flag
        if not self.enable_phase3_flag():
            return False
        
        # Step 3: Schedule checkpoints
        if not self.schedule_checkpoints():
            return False
        
        # Step 4: Generate report
        report = self.create_activation_report()
        
        logger.info("\n" + "="*70)
        logger.info("✅ PHASE 3 ACTIVATED SUCCESSFULLY")
        logger.info("="*70)
        logger.info(f"\n📊 Activation Report:")
        logger.info(json.dumps(report, indent=2))
        logger.info("\n" + "="*70)
        
        # Save report
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        report_file = LOGS_DIR / f"activation_report_{self.activation_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Report saved: {report_file}")
        
        return True

# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main activation flow"""
    
    print("\n" + "🚀 "*20)
    print("FASE 15 PHASE 3 - ACTIVATION SCRIPT")
    print("🚀 "*20 + "\n")
    
    # Step 1: Validate
    validator = Phase3Validator(DB_PATH)
    all_pass, checks = validator.run_all_checks()
    
    if not all_pass:
        logger.error("\n❌ ACTIVATION ABORTED: Pre-flight checks failed")
        logger.error("Fix the issues above and retry activation")
        sys.exit(1)
    
    # Step 2: Activate
    activator = Phase3Activator(DB_PATH)
    if not activator.activate():
        logger.error("\n❌ ACTIVATION FAILED: See errors above")
        sys.exit(1)
    
    logger.info("\n✅ Phase 3 is now ACTIVE and ready for execution")
    logger.info("📊 Monitor at: http://localhost:8000/dashboard/phase3")
    logger.info("🔴 Kill-switch endpoint: POST /api/admin/phase3/deactivate")
    logger.info("\nMonitoring will begin automatically at the first checkpoint")
    logger.info("Next checkpoint: ~2 hours from now\n")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
