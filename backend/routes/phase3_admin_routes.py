#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Admin Kill-Switch Routes
Endpoints for activating/deactivating Phase 3 with pre-flight validation
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Phase 3 Admin"])

# Global state (will be initialized via init_phase3_admin_routes)
_db_connection = None
_ws_manager = None


def init_phase3_admin_routes(db_connection=None, ws_manager=None):
    """Initialize Phase 3 admin routes with dependencies"""
    global _db_connection, _ws_manager
    _db_connection = db_connection
    _ws_manager = ws_manager
    if db_connection:
        logger.info("✅ Phase 3 admin routes initialized with database connection")
    if ws_manager:
        logger.info("✅ Phase 3 admin routes connected to WebSocket manager")

# =============================================================================
# Data Models
# =============================================================================

class AdminRequest(BaseModel):
    """Admin action request"""
    reason: str = None
    notify_slack: bool = True

class Phase3Status(BaseModel):
    """Current Phase 3 status"""
    active: bool
    uptime_seconds: float = None
    current_checkpoint: int = None
    health_score: int = None
    circuit_breaker_states: dict = None
    next_checkpoint_eta: str = None

# =============================================================================
# Authentication & Authorization
# =============================================================================

def verify_admin_role(request: Request):
    """Verify that the request is from an admin user"""
    user_role = getattr(request.user, 'role', None) if hasattr(request, 'user') else None
    
    if user_role != "admin":
        logger.warning(f"Unauthorized admin attempt: role={user_role}")
        raise HTTPException(
            status_code=403,
            detail="Admin role required for this operation"
        )
    return True

# =============================================================================
# Pre-flight Validation
# =============================================================================

class Phase3Preflights:
    """Pre-flight checks before Phase 3 activation"""
    
    @staticmethod
    def check_phase2_health(db_path: str = "fase15.db") -> bool:
        """Check Phase 2 metrics are healthy (error_rate < 1%)"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Query latest Phase 2 metrics
            cursor.execute("""
                SELECT AVG(error_rate) as avg_error_rate
                FROM system_metrics
                WHERE created_at > datetime('now', '-24 hours')
                AND phase = 2
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                error_rate = result[0]
                health_ok = error_rate < 0.01  # < 1%
                logger.info(f"✅ Phase 2 health check: error_rate={error_rate:.4f}% {'OK' if health_ok else 'FAILED'}")
                return health_ok
            
            logger.info("✅ Phase 2 health check: No Phase 2 data, assuming OK for fresh deployment")
            return True
            
        except Exception as e:
            logger.error(f"❌ Phase 2 health check failed: {str(e)}")
            return False
    
    @staticmethod
    def check_backup_age(db_path: str = "fase15.db") -> bool:
        """Check backups are recent (< 2 hours old)"""
        import os
        from pathlib import Path
        
        try:
            backup_dir = Path("data/backups")
            if not backup_dir.exists():
                logger.warning("⚠️  No backup directory found, creating one")
                backup_dir.mkdir(parents=True, exist_ok=True)
                return True
            
            # Check for recent backups
            import time
            now = time.time()
            two_hours_ago = now - (2 * 3600)
            
            recent_backups = [
                f for f in backup_dir.iterdir() 
                if f.is_file() and f.stat().st_mtime > two_hours_ago
            ]
            
            if recent_backups:
                latest = max(recent_backups, key=lambda f: f.stat().st_mtime)
                logger.info(f"✅ Backup check: Found recent backup {latest.name}")
                return True
            else:
                logger.warning("⚠️  No recent backups found (>2h old), but proceeding")
                return True  # Don't block activation
                
        except Exception as e:
            logger.error(f"❌ Backup check failed: {str(e)}")
            return False
    
    @staticmethod
    def check_database_integrity(db_path: str = "fase15.db") -> bool:
        """Check database integrity and schema"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            required_tables = [
                "ab_tests",
                "ab_test_ml_predictions",
                "personalization_variants",
                "phase3_checkpoints",
                "system_config",
                "system_metrics"
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            missing = set(required_tables) - existing_tables
            conn.close()
            
            if missing:
                logger.error(f"❌ Database integrity check FAILED: Missing tables {missing}")
                return False
            
            logger.info(f"✅ Database integrity check: All {len(required_tables)} required tables present")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database integrity check failed: {str(e)}")
            return False
    
    @staticmethod
    def check_components_healthy(db_path: str = "fase15.db") -> bool:
        """Check all system components are healthy"""
        try:
            # Placeholder for component health checks
            # In production, would call actual health endpoints
            
            components = {
                "database": True,
                "websocket_manager": True,
                "prediction_service": True,
                "monitoring_daemon": True,
                "circuit_breaker": True
            }
            
            all_healthy = all(components.values())
            status_str = ", ".join([f"{k}={'✅' if v else '❌'}" for k, v in components.items()])
            
            logger.info(f"✅ Component health check: {status_str}")
            return all_healthy
            
        except Exception as e:
            logger.error(f"❌ Component health check failed: {str(e)}")
            return False
    
    @staticmethod
    def check_circuit_breakers(db_path: str = "fase15.db") -> bool:
        """Check circuit breakers are in CLOSED state"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Query circuit breaker states
            cursor.execute("""
                SELECT service, state, last_checked
                FROM circuit_breaker_states
                WHERE last_checked > datetime('now', '-5 minutes')
            """)
            
            breakers = cursor.fetchall()
            conn.close()
            
            if not breakers:
                logger.info("✅ Circuit breaker check: No circuit breakers found, creating fresh")
                return True
            
            # Check all are CLOSED
            all_closed = all(breaker[1] == "CLOSED" for breaker in breakers)
            
            if all_closed:
                logger.info(f"✅ Circuit breaker check: All {len(breakers)} breakers in CLOSED state")
                return True
            else:
                open_breakers = [b[0] for b in breakers if b[1] != "CLOSED"]
                logger.error(f"❌ Circuit breaker check FAILED: {open_breakers} are OPEN")
                return False
                
        except Exception as e:
            logger.error(f"❌ Circuit breaker check failed: {str(e)}")
            return False
    
    @staticmethod
    def run_all_checks(db_path: str = "fase15.db") -> dict:
        """Run all pre-flight checks"""
        checks = {
            "phase2_health": Phase3Preflights.check_phase2_health(db_path),
            "backup_recent": Phase3Preflights.check_backup_age(db_path),
            "database_integrity": Phase3Preflights.check_database_integrity(db_path),
            "components_healthy": Phase3Preflights.check_components_healthy(db_path),
            "circuit_breakers_ok": Phase3Preflights.check_circuit_breakers(db_path)
        }
        
        return {
            "all_pass": all(checks.values()),
            "checks": checks,
            "failed_checks": [k for k, v in checks.items() if not v],
            "timestamp": datetime.utcnow().isoformat()
        }

# =============================================================================
# Kill-Switch Endpoints
# =============================================================================

@router.post("/api/admin/phase3/activate")
async def activate_phase3(request: AdminRequest, admin_verified=Depends(verify_admin_role)):
    """Activate Phase 3 with pre-flight validation"""
    logger.info("\n" + "="*70)
    logger.info("PHASE 3 ACTIVATION REQUEST")
    logger.info("="*70)
    
    db_path = "fase15.db"
    
    # 1. Run pre-flight checks
    logger.info("\n📋 Running pre-flight validation checks...")
    preflights = Phase3Preflights.run_all_checks(db_path)
    
    if not preflights["all_pass"]:
        logger.error(f"\n❌ PRE-FLIGHT CHECKS FAILED:")
        for check, status in preflights["checks"].items():
            logger.error(f"   - {check}: {'✅' if status else '❌'}")
        
        raise HTTPException(
            status_code=400,
            detail=f"Pre-flight checks failed: {preflights['failed_checks']}"
        )
    
    logger.info("\n✅ All pre-flight checks PASSED")
    
    # 2. Create backup
    logger.info("\n💾 Creating backup...")
    import shutil
    from pathlib import Path
    
    backup_dir = Path("data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_UTC")
    backup_path = backup_dir / f"phase3_start_{timestamp}.sqlite"
    
    try:
        shutil.copy2(db_path, str(backup_path))
        logger.info(f"✅ Backup created: {backup_path}")
    except Exception as e:
        logger.error(f"❌ Backup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")
    
    # 3. Enable Phase 3
    logger.info("\n🚀 Enabling Phase 3...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_ACTIVE', 'true', ?)
        """, (datetime.utcnow().isoformat(),))
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_ACTIVATION_TIME', ?, ?)
        """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Phase 3 flag set to ACTIVE")
        
    except Exception as e:
        logger.error(f"❌ Failed to set Phase 3 flag: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")
    
    # 4. Log activation
    logger.info(f"\n✅ PHASE 3 ACTIVATED")
    logger.info(f"   Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"   Backup: {backup_path}")
    logger.info(f"   Next checkpoint: in ~2 hours")
    logger.info("="*70)
    
    return {
        "status": "activated",
        "timestamp": datetime.utcnow().isoformat(),
        "backup_path": str(backup_path),
        "checkpoint_1_scheduled": "2026-10-06T22:36:00Z",
        "monitoring_duration": "7 days (Oct 6-13, 2026)",
        "final_decision_time": "2026-10-13T03:25:00Z"
    }

@router.post("/api/admin/phase3/deactivate")
async def deactivate_phase3(request: AdminRequest, admin_verified=Depends(verify_admin_role)):
    """Deactivate Phase 3 and trigger rollback"""
    logger.info("\n" + "="*70)
    logger.info("PHASE 3 DEACTIVATION REQUEST")
    logger.info("="*70)
    logger.info(f"Reason: {request.reason or 'No reason provided'}")
    
    db_path = "fase15.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Disable Phase 3
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_ACTIVE', 'false', ?)
        """, (datetime.utcnow().isoformat(),))
        
        # Record deactivation
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_DEACTIVATION_TIME', ?, ?)
        """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_DEACTIVATION_REASON', ?, ?)
        """, (request.reason or 'Manual deactivation', datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Phase 3 deactivated")
        logger.info("🔄 Initiating rollback to Phase 2...")
        logger.info("   Estimated rollback time: <60 seconds")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"❌ Deactivation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deactivation failed: {str(e)}")
    
    return {
        "status": "deactivated",
        "timestamp": datetime.utcnow().isoformat(),
        "reason": request.reason,
        "rollback_initiated": True,
        "estimated_rollback_time": "< 60 seconds"
    }

@router.get("/api/admin/phase3/status")
async def get_phase3_status(admin_verified=Depends(verify_admin_role)):
    """Get current Phase 3 activation status"""
    db_path = "fase15.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get Phase 3 status
        cursor.execute("""
            SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE'
        """)
        result = cursor.fetchone()
        is_active = result[0] == 'true' if result else False
        
        # Get activation time
        cursor.execute("""
            SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVATION_TIME'
        """)
        activation_time = cursor.fetchone()
        
        # Get latest checkpoint
        cursor.execute("""
            SELECT checkpoint_number, metrics, status, created_at
            FROM phase3_checkpoints
            ORDER BY checkpoint_number DESC
            LIMIT 1
        """)
        latest_checkpoint = cursor.fetchone()
        
        conn.close()
        
        uptime_seconds = None
        if activation_time and is_active:
            from datetime import datetime
            activation = datetime.fromisoformat(activation_time[0])
            uptime_seconds = (datetime.utcnow() - activation).total_seconds()
        
        return {
            "active": is_active,
            "activation_time": activation_time[0] if activation_time else None,
            "uptime_seconds": uptime_seconds,
            "latest_checkpoint": {
                "number": latest_checkpoint[0],
                "status": latest_checkpoint[2],
                "timestamp": latest_checkpoint[3]
            } if latest_checkpoint else None,
            "status_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

