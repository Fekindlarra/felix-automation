#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Admin Kill-Switch Routes
Management endpoints for activation, deactivation, and status monitoring
Protected with admin-only access control
"""

import logging
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, Field
from auth import verify_request_admin_role

logger = logging.getLogger(__name__)

# Module-level database and WebSocket manager (injected by main app)
database = None
websocket_manager = None

# Module-level router
router = APIRouter(prefix="/api/admin/phase3", tags=["Phase 3 Admin"])


# ==================== REQUEST/RESPONSE MODELS ====================

class AdminRequest(BaseModel):
    """Base request for admin operations"""
    reason: Optional[str] = Field(None, description="Reason for the action")


class Phase3StatusResponse(BaseModel):
    """Response with Phase 3 status"""
    active: bool = Field(..., description="Whether Phase 3 is currently active")
    uptime_hours: float = Field(..., description="Hours Phase 3 has been running")
    current_checkpoint: Optional[int] = Field(..., description="Current checkpoint number (1-13)")
    health_score: Optional[int] = Field(..., description="Health score 0-6")
    last_checkpoint_timestamp: Optional[str] = Field(..., description="When last checkpoint was taken")
    next_checkpoint_eta: Optional[str] = Field(..., description="When next checkpoint is scheduled")
    circuit_breaker_states: Dict[str, str] = Field(default_factory=dict, description="State of each circuit breaker")
    last_checkpoint_decision: Optional[str] = Field(None, description="Last decision: CONTINUE/CAUTION/ROLLBACK")


class Phase3ActionResponse(BaseModel):
    """Response from activation/deactivation"""
    status: str = Field(..., description="Operation status")
    timestamp: str = Field(..., description="When operation occurred")
    message: str = Field(..., description="Detailed message")


# ==================== ADMIN VERIFICATION ====================

# Admin role verification is provided by auth.verify_request_admin_role()


# ==================== HELPER FUNCTIONS ====================

def set_phase3_active(active: bool) -> None:
    """Set Phase 3 active status in database"""
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    try:
        cursor = database.cursor()

        # Ensure system_config table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Update or insert PHASE_3_ACTIVE flag
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_ACTIVE', ?, CURRENT_TIMESTAMP)
        """, ('true' if active else 'false',))

        database.commit()
        logger.info(f"✅ Phase 3 active status set to: {active}")
    except Exception as e:
        logger.error(f"❌ Failed to set Phase 3 active status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


def get_phase3_active() -> bool:
    """Get Phase 3 active status from database"""
    if database is None:
        return False

    try:
        cursor = database.cursor()
        cursor.execute("""
            SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE'
        """)
        result = cursor.fetchone()
        return result[0] == 'true' if result else False
    except Exception as e:
        logger.error(f"❌ Failed to get Phase 3 active status: {e}")
        return False


def create_backup() -> str:
    """Create database backup before Phase 3 activation"""
    import shutil
    import os
    from pathlib import Path

    try:
        # Create backups directory if it doesn't exist
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Get database path
        db_path = "fase15.db"  # Adjust based on actual database location

        if not os.path.exists(db_path):
            logger.warning(f"Database file not found at {db_path}, skipping backup")
            return None

        # Create timestamped backup
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"phase3_start_{timestamp}.sqlite"

        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ Database backup created at {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"❌ Backup creation failed: {e}")
        return None


def get_current_checkpoint() -> Optional[int]:
    """Get current checkpoint number from monitoring daemon"""
    if database is None:
        return None

    try:
        cursor = database.cursor()
        cursor.execute("""
            SELECT checkpoint_number FROM system_config
            WHERE key = 'CURRENT_CHECKPOINT' LIMIT 1
        """)
        result = cursor.fetchone()
        return int(result[0]) if result else None
    except Exception:
        return None


def get_last_checkpoint_data() -> Optional[Dict[str, Any]]:
    """Get data from last checkpoint"""
    if database is None:
        return None

    try:
        cursor = database.cursor()
        cursor.execute("""
            SELECT value FROM system_config
            WHERE key LIKE 'CHECKPOINT_%'
            ORDER BY key DESC LIMIT 1
        """)
        result = cursor.fetchone()

        if result:
            import json
            return json.loads(result[0])
        return None
    except Exception:
        return None


def trigger_rollback() -> None:
    """Trigger immediate rollback via RollbackManager"""
    from rollback_manager import RollbackManager, RollbackTrigger

    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    try:
        rollback_mgr = RollbackManager(database)
        # Set Phase 3 as inactive
        set_phase3_active(False)
        # Trigger rollback with MANUAL trigger
        rollback_mgr.trigger_rollback(
            trigger_type=RollbackTrigger.MANUAL,
            reason="Manual kill-switch activation"
        )
        logger.info("✅ Manual rollback triggered")
    except Exception as e:
        logger.error(f"❌ Rollback trigger failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback trigger failed: {str(e)}"
        )


# ==================== ROUTES ====================

@router.post("/activate", response_model=Phase3ActionResponse, tags=["Phase 3 Admin"])
async def activate_phase3(request: Request, body: AdminRequest) -> Phase3ActionResponse:
    """
    Activate Phase 3 for 24-hour production test (HORA 48-72)

    Pre-flight checks required:
    - Phase 2 metrics all healthy
    - Database backups recent (<2h)
    - All system components responding
    - Circuit breakers functional

    Returns:
    - Activation timestamp
    - First checkpoint scheduled time (HORA 50, ~2 hours later)
    """
    # Verify admin role
    verify_request_admin_role(request)

    # Check if already active
    if get_phase3_active():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phase 3 is already active"
        )

    try:
        # Run pre-flight checks
        from phase3_preflights import Phase3Preflights
        preflights = Phase3Preflights(database)
        preflight_result = preflights.run_all_checks()

        if not preflight_result["all_pass"]:
            logger.warning(f"❌ Pre-flight checks failed: {preflight_result['blocked_reason']}")
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"Pre-flight check failed: {preflight_result['blocked_reason']}"
            )

        # Create backup
        backup_path = create_backup()

        # Activate Phase 3
        set_phase3_active(True)

        # Broadcast activation event
        if websocket_manager:
            await websocket_manager.broadcast(
                {
                    "event": "phase3:activated",
                    "timestamp": datetime.utcnow().isoformat(),
                    "backup_location": backup_path,
                    "reason": body.reason or "Manual activation"
                },
                role="admin"
            )

        logger.info(f"✅ Phase 3 activated successfully. Backup: {backup_path}")

        return Phase3ActionResponse(
            status="activated",
            timestamp=datetime.utcnow().isoformat(),
            message=f"Phase 3 activated. First checkpoint in ~2 hours. Backup: {backup_path}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Phase 3 activation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Activation failed: {str(e)}"
        )


@router.post("/deactivate", response_model=Phase3ActionResponse, tags=["Phase 3 Admin"])
async def deactivate_phase3(request: Request, body: AdminRequest) -> Phase3ActionResponse:
    """
    Deactivate Phase 3 and trigger immediate rollback

    This is the kill-switch endpoint:
    - Disables Phase 3 immediately
    - Triggers automatic rollback
    - Reverts traffic to Phase 2
    - Restores database from backup
    - Sends critical alerts
    """
    # Verify admin role
    verify_request_admin_role(request)

    # Check if already inactive
    if not get_phase3_active():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Phase 3 is already inactive"
        )

    try:
        # Trigger rollback
        trigger_rollback()

        # Broadcast deactivation event
        if websocket_manager:
            await websocket_manager.broadcast(
                {
                    "event": "phase3:deactivated",
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": body.reason or "Manual deactivation",
                    "rollback_status": "initiated"
                },
                role="admin"
            )

        logger.info(f"✅ Phase 3 deactivated and rollback triggered. Reason: {body.reason}")

        return Phase3ActionResponse(
            status="deactivated",
            timestamp=datetime.utcnow().isoformat(),
            message="Phase 3 deactivated. Rollback in progress. Traffic reverted to Phase 2."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Phase 3 deactivation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deactivation failed: {str(e)}"
        )


@router.get("/status", response_model=Phase3StatusResponse, tags=["Phase 3 Admin"])
async def get_phase3_status(request: Request) -> Phase3StatusResponse:
    """
    Get current Phase 3 status and health metrics

    Returns:
    - Active status
    - Uptime (if active)
    - Current checkpoint number (1-13)
    - Health score (0-6 metrics passing)
    - Circuit breaker states
    - Last decision (CONTINUE/CAUTION/ROLLBACK)
    """
    # Verify admin role
    verify_request_admin_role(request)

    try:
        active = get_phase3_active()

        # Get activation timestamp
        uptime_hours = 0.0
        if active:
            if database:
                try:
                    cursor = database.cursor()
                    cursor.execute("""
                        SELECT value FROM system_config
                        WHERE key = 'PHASE_3_ACTIVATED_AT'
                    """)
                    result = cursor.fetchone()
                    if result:
                        from datetime import datetime as dt
                        activated_at = dt.fromisoformat(result[0])
                        uptime_hours = (dt.utcnow() - activated_at).total_seconds() / 3600
                except Exception as e:
                    logger.warning(f"Could not calculate uptime: {e}")

        # Get current checkpoint and health data
        current_checkpoint = get_current_checkpoint()
        last_checkpoint = get_last_checkpoint_data()

        # Get circuit breaker states
        from circuit_breaker import CircuitBreakerRegistry
        registry = CircuitBreakerRegistry()
        cb_states = {name: breaker.state.name for name, breaker in registry.breakers.items()}

        # Extract health score from checkpoint
        health_score = None
        last_decision = None
        if last_checkpoint:
            health_score = last_checkpoint.get("health_score", 0)
            last_decision = last_checkpoint.get("decision", "UNKNOWN")

        # Calculate next checkpoint ETA
        next_checkpoint_eta = None
        if active and current_checkpoint:
            # Checkpoint every 2 hours
            from datetime import timedelta
            next_checkpoint_time = datetime.utcnow() + timedelta(hours=2)
            next_checkpoint_eta = next_checkpoint_time.isoformat()

        return Phase3StatusResponse(
            active=active,
            uptime_hours=uptime_hours,
            current_checkpoint=current_checkpoint,
            health_score=health_score,
            last_checkpoint_timestamp=last_checkpoint.get("timestamp") if last_checkpoint else None,
            next_checkpoint_eta=next_checkpoint_eta,
            circuit_breaker_states=cb_states,
            last_checkpoint_decision=last_decision
        )

    except Exception as e:
        logger.error(f"❌ Failed to get Phase 3 status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status retrieval failed: {str(e)}"
        )


def init_phase3_admin_routes(db_connection, ws_manager):
    """Initialize module-level dependencies for phase3_admin_routes"""
    global database, websocket_manager
    database = db_connection
    websocket_manager = ws_manager
    logger.info("✅ Phase 3 Admin Routes initialized")
