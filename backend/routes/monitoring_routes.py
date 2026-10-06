#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 - Monitoring API Routes
FastAPI endpoints for monitoring data exposure and health checks
"""

import logging
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# ============================================================================
# MONITORING INITIALIZATION
# ============================================================================

@router.post("/initialize")
async def initialize_monitoring():
    """
    Initialize monitoring system
    
    Returns:
        - Monitoring system status
        - Enabled components
        - Configuration summary
    """
    try:
        from backend.monitoring_startup import initialize_monitoring
        
        monitoring = initialize_monitoring()
        
        if monitoring:
            return {
                "status": "initialized",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "components": {
                    "metrics_collector": "active",
                    "health_checker": "active",
                    "performance_profiler": "active",
                    "monitoring_dashboard": "active"
                },
                "message": "Monitoring system initialized successfully"
            }
        else:
            return {
                "status": "warning",
                "message": "Monitoring initialization returned None - may be disabled"
            }
            
    except Exception as e:
        logger.error(f"Failed to initialize monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monitoring initialization failed: {str(e)}"
        )


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@router.get("/health")
async def get_health_status():
    """
    Get overall system health status
    
    Returns:
        - Overall status: healthy/degraded/unhealthy
        - Detailed metrics for each health check
        - Active alerts
        - Recommendations for issues
    """
    try:
        from backend.monitoring import get_health_checker
        
        health_checker = get_health_checker()
        health_status = health_checker.evaluate_health()
        
        return {
            "status": "ok",
            "health": health_status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


# ============================================================================
# DASHBOARD ENDPOINT
# ============================================================================

@router.get("/dashboard")
async def get_monitoring_dashboard():
    """
    Get comprehensive monitoring dashboard with all metrics
    
    Returns:
        - All metrics (counters, gauges, timers)
        - Health status summary
        - Active alerts
        - Performance statistics
    """
    try:
        from backend.monitoring import get_monitoring_dashboard
        
        dashboard = get_monitoring_dashboard()
        dashboard_data = dashboard.get_dashboard_data()
        
        return {
            "status": "ok",
            "dashboard": dashboard_data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard retrieval failed: {str(e)}"
        )


# ============================================================================
# INDIVIDUAL METRIC ENDPOINTS
# ============================================================================

@router.get("/metrics/{metric_name}")
async def get_metric(
    metric_name: str,
    minutes: int = Query(60, ge=1, le=1440, description="Time window in minutes")
):
    """
    Get detailed metrics for a specific metric name
    
    Args:
        metric_name: Name of the metric to retrieve
        minutes: Time window in minutes (default: 60, max: 1440 = 24hrs)
        
    Returns:
        - Metric history (data points)
        - Statistical summary (min, max, avg, p95, p99)
        - Latest value
    """
    try:
        from backend.monitoring import get_metrics_collector
        
        collector = get_metrics_collector()
        
        # Get history
        history = collector.get_metric_history(metric_name, minutes)
        
        # Get latest
        latest = collector.get_latest(metric_name)
        
        # Get stats
        stats = collector.get_stats(metric_name, minutes)
        
        if not history and not latest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for metric: {metric_name}"
            )
        
        return {
            "status": "ok",
            "metric_name": metric_name,
            "time_window_minutes": minutes,
            "data_points": len(history),
            "history": [
                {
                    "timestamp": h.timestamp,
                    "value": h.value,
                    "type": h.metric_type.value,
                    "unit": h.unit,
                    "labels": h.labels
                }
                for h in history
            ],
            "latest": {
                "timestamp": latest.timestamp,
                "value": latest.value,
                "type": latest.metric_type.value,
                "unit": latest.unit
            } if latest else None,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric {metric_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metric: {str(e)}"
        )


# ============================================================================
# METRICS LIST ENDPOINT
# ============================================================================

@router.get("/metrics")
async def list_metrics():
    """
    List all available metrics currently being tracked
    
    Returns:
        - List of metric names
        - Metric type for each
        - Latest value
        - Data point count
    """
    try:
        from backend.monitoring import get_metrics_collector
        
        collector = get_metrics_collector()
        
        metrics_list = []
        for metric_name in collector.metrics.keys():
            latest = collector.get_latest(metric_name)
            if latest:
                metrics_list.append({
                    "name": metric_name,
                    "type": latest.metric_type.value,
                    "unit": latest.unit,
                    "latest_value": latest.value,
                    "data_points": len(collector.metrics[metric_name]),
                    "latest_timestamp": latest.timestamp
                })
        
        return {
            "status": "ok",
            "metric_count": len(metrics_list),
            "metrics": sorted(metrics_list, key=lambda x: x['name']),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to list metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list metrics: {str(e)}"
        )


# ============================================================================
# ALERTS ENDPOINT
# ============================================================================

@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: info/warning/critical"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status")
):
    """
    Get current alerts from monitoring system
    
    Args:
        severity: Optional filter by severity level
        resolved: Optional filter by resolution status
        
    Returns:
        - List of active alerts
        - Alert severity and details
        - Timestamp when alert was generated
    """
    try:
        from backend.monitoring import get_health_checker
        
        health_checker = get_health_checker()
        health_status = health_checker.evaluate_health()
        
        alerts = health_status.get('alerts', [])
        
        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a.get('severity') == severity]
        
        # Filter by resolved status if specified
        if resolved is not None:
            alerts = [a for a in alerts if a.get('resolved') == resolved]
        
        return {
            "status": "ok",
            "alert_count": len(alerts),
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alerts: {str(e)}"
        )


# ============================================================================
# PERFORMANCE STATS ENDPOINT
# ============================================================================

@router.get("/performance/{operation_name}")
async def get_operation_performance(
    operation_name: str,
    minutes: int = Query(60, ge=1, le=1440)
):
    """
    Get performance statistics for a specific operation
    
    Args:
        operation_name: Name of the operation (e.g., "database.get_client")
        minutes: Time window in minutes
        
    Returns:
        - Operation timing statistics
        - Min, max, average latencies
        - Percentiles (p50, p95, p99)
    """
    try:
        from backend.monitoring import get_performance_profiler
        
        profiler = get_performance_profiler()
        stats = profiler.get_operation_stats(operation_name)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No performance data for operation: {operation_name}"
            )
        
        return {
            "status": "ok",
            "operation_name": operation_name,
            "time_window_minutes": minutes,
            "performance": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance for {operation_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance data: {str(e)}"
        )


# ============================================================================
# STATUS SUMMARY ENDPOINT
# ============================================================================

@router.get("/status/summary")
async def get_status_summary():
    """
    Quick status summary for health checks and dashboards
    
    Returns:
        - Overall system status in one call
        - Key metrics snapshot
        - Alert count
        - Last updated timestamp
    """
    try:
        from backend.monitoring import (
            get_health_checker,
            get_metrics_collector,
            get_monitoring_dashboard
        )
        
        health = get_health_checker()
        collector = get_metrics_collector()
        dashboard = get_monitoring_dashboard()
        
        health_status = health.evaluate_health()
        dashboard_data = dashboard.get_dashboard_data()
        
        alerts = health_status.get('alerts', [])
        critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
        
        return {
            "status": "ok",
            "overall_health": health_status.get('overall_status'),
            "metrics_count": len(collector.metrics),
            "active_alerts": len(alerts),
            "critical_alerts": len(critical_alerts),
            "recommendations": health_status.get('recommendations', []),
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get status summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate status summary: {str(e)}"
        )


# ============================================================================
# ENDPOINTS REGISTRATION
# ============================================================================

def register_monitoring_routes(app):
    """
    Register monitoring routes to FastAPI application
    
    Usage:
        from backend.routes.monitoring_routes import register_monitoring_routes
        register_monitoring_routes(app)
    """
    app.include_router(router)
    logger.info("✓ Monitoring routes registered")
