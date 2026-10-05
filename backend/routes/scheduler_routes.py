#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 2: Scheduler Routes
FastAPI endpoints for managing analytics scheduler
"""

import logging
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, Dict, List
from analytics.analytics_scheduler import AnalyticsScheduler
from backend.auth import verify_admin_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])

# Global scheduler instance
_scheduler_instance = None


def get_scheduler(orchestrator) -> AnalyticsScheduler:
    """Get or create scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AnalyticsScheduler(orchestrator)
        _scheduler_instance.start()
    return _scheduler_instance


# ============================================================================
# SCHEDULER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/status")
async def get_scheduler_status(token: str):
    """Get current scheduler status and running jobs"""
    verify_admin_token(token)

    try:
        # Import here to avoid circular dependencies
        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)

        status_info = scheduler.get_scheduler_status()

        return {
            "status": "ok",
            "scheduler": status_info,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Failed to get scheduler status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving scheduler status"
        )


@router.post("/run-now")
async def trigger_analysis_run(
    token: str,
    analysis_type: str = Query("full", regex="^(full|quick|custom)$")
):
    """
    Trigger immediate analysis run

    Args:
        analysis_type: 'full', 'quick', or 'custom'

    Returns:
        Job result with status and metadata
    """
    verify_admin_token(token)

    try:
        logger.info(f"🚀 Triggering {analysis_type} analysis run via API")

        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)

        result = scheduler.run_analysis_now(analysis_type)

        return {
            "status": "success" if result.get('status') == 'success' else "failed",
            "job": result,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Failed to trigger analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error triggering analysis run"
        )


@router.get("/jobs")
async def list_scheduled_jobs(token: str):
    """Get list of all scheduled jobs"""
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)

        status_info = scheduler.get_scheduler_status()

        return {
            "total_jobs": status_info.get('jobs_count', 0),
            "running": status_info.get('running', False),
            "jobs": status_info.get('jobs', [])
        }

    except Exception as e:
        logger.error(f"❌ Failed to list jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving job list"
        )


@router.get("/history")
async def get_job_history(
    token: str,
    limit: int = Query(50, ge=1, le=500),
    status_filter: Optional[str] = Query(None, regex="^(success|failed)$")
):
    """
    Get analysis run history

    Args:
        limit: Maximum records to return (1-500)
        status_filter: Optional filter by status ('success' or 'failed')

    Returns:
        List of job history records
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)

        history = scheduler.get_job_history(limit)

        # Apply status filter if provided
        if status_filter:
            history = [j for j in history if j.get('status') == status_filter]

        return {
            "total": len(history),
            "limit": limit,
            "status_filter": status_filter,
            "history": history
        }

    except Exception as e:
        logger.error(f"❌ Failed to retrieve history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving job history"
        )


@router.post("/configure")
async def configure_scheduler(
    token: str,
    daily_enabled: bool = True,
    daily_hour: int = Query(8, ge=0, le=23),
    daily_minute: int = Query(0, ge=0, le=59),
    weekly_enabled: bool = True,
    weekly_day: int = Query(0, ge=0, le=6),  # 0=Monday, 6=Sunday
    weekly_hour: int = Query(8, ge=0, le=23)
):
    """
    Configure scheduler settings

    Args:
        daily_enabled: Enable daily runs
        daily_hour: Hour for daily run (0-23)
        daily_minute: Minute for daily run (0-59)
        weekly_enabled: Enable weekly runs
        weekly_day: Day of week for weekly run (0=Monday)
        weekly_hour: Hour for weekly run (0-23)

    Returns:
        Updated scheduler status
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)

        # Configure daily runs
        if daily_enabled:
            scheduler.add_daily_analysis(hour=daily_hour, minute=daily_minute)
            logger.info(f"✅ Daily analysis configured for {daily_hour:02d}:{daily_minute:02d}")

        # Configure weekly runs
        if weekly_enabled:
            scheduler.add_weekly_analysis(day_of_week=weekly_day, hour=weekly_hour)
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            logger.info(f"✅ Weekly analysis configured for {days[weekly_day]} at {weekly_hour:02d}:00")

        status_info = scheduler.get_scheduler_status()

        return {
            "status": "configured",
            "configuration": {
                "daily_enabled": daily_enabled,
                "daily_time": f"{daily_hour:02d}:{daily_minute:02d}",
                "weekly_enabled": weekly_enabled,
                "weekly_day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekly_day],
                "weekly_time": f"{weekly_hour:02d}:00"
            },
            "scheduler_jobs": status_info.get('jobs', [])
        }

    except Exception as e:
        logger.error(f"❌ Failed to configure scheduler: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error configuring scheduler"
        )


@router.post("/notifications/configure")
async def configure_notifications(
    token: str,
    notify_critical: bool = True,
    notify_high: bool = True,
    notify_medium: bool = False,
    notify_low: bool = False
):
    """
    Configure notification thresholds

    Args:
        notify_critical: Send emails for CRITICAL anomalies
        notify_high: Send emails for HIGH anomalies
        notify_medium: Send emails for MEDIUM anomalies
        notify_low: Send emails for LOW anomalies

    Returns:
        Updated notification configuration
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)

        thresholds = {
            'CRITICAL': notify_critical,
            'HIGH': notify_high,
            'MEDIUM': notify_medium,
            'LOW': notify_low
        }

        scheduler.configure_notifications(thresholds)
        logger.info(f"✅ Notification thresholds updated")

        return {
            "status": "configured",
            "notification_config": thresholds
        }

    except Exception as e:
        logger.error(f"❌ Failed to configure notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error configuring notifications"
        )


@router.get("/trends")
async def get_trend_analysis(
    token: str,
    days: int = Query(7, ge=1, le=90)
):
    """
    Get trend analysis over time period

    Args:
        days: Number of days to analyze (1-90)

    Returns:
        Trend analysis with daily stats and week-over-week changes
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)

        trends = scheduler.get_trend_analysis(days)

        return {
            "status": "ok",
            "trends": trends
        }

    except Exception as e:
        logger.error(f"❌ Failed to retrieve trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving trend analysis"
        )
