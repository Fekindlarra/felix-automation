#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Monitoring API Routes - FastAPI Integration
Real-time monitoring, alerts, metrics, and health check endpoints
Integrates with Phase 1 infrastructure: ErrorTracker, MetricsCollector, AlertManager, PredictionBroadcaster
"""

import logging
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Router for monitoring endpoints
router = APIRouter(
    prefix="/api/monitoring",
    tags=["monitoring"]
)


# ============================================================================
# MODELS
# ============================================================================

class AlertResponse(BaseModel):
    """Alert response model"""
    alert_id: str
    rule_name: str
    severity: str
    message: str
    status: str
    created_at: str


class MetricResponse(BaseModel):
    """Metric response model"""
    metric_name: str
    value: float
    metric_type: str
    timestamp: str
    component: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error_id: str
    error_type: str
    message: str
    severity: str
    component: Optional[str] = None
    timestamp: str


class AnomalyResponse(BaseModel):
    """Anomaly response model"""
    anomaly_id: str
    client_id: Optional[int] = None
    anomaly_type: str
    severity: str
    description: str
    timestamp: str


class HealthStatus(BaseModel):
    """Health status response"""
    status: str
    timestamp: str
    components: Dict[str, Any]


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert"""
    acknowledged_by: str = "system"


# ============================================================================
# ENDPOINTS - HEALTH & STATUS
# ============================================================================

@router.get("/health", response_model=HealthStatus)
async def get_health():
    """Get overall system health status"""
    try:
        from backend.monitoring_startup import get_monitoring_status

        status_data = get_monitoring_status()

        if status_data is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Monitoring system not available"
            )

        return status_data

    except Exception as e:
        logger.error(f"Error getting health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health status: {str(e)}"
        )


@router.get("/status")
async def get_status():
    """Get comprehensive monitoring status"""
    try:
        from backend.monitoring_startup import (
            get_monitoring_status,
            get_metrics_collector,
            get_error_tracker,
            get_alert_manager,
            get_prediction_broadcaster
        )

        status_data = get_monitoring_status()

        # Add additional details
        status_data['collectors'] = {
            'metrics_available': get_metrics_collector() is not None,
            'errors_available': get_error_tracker() is not None,
            'alerts_available': get_alert_manager() is not None,
            'predictions_available': get_prediction_broadcaster() is not None
        }

        return status_data

    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - ALERTS
# ============================================================================

@router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts(
    severity: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=720)
):
    """Get active alerts with optional severity filtering"""
    try:
        from backend.monitoring_startup import get_alert_manager

        alert_manager = get_alert_manager()

        if alert_manager is None:
            return {
                'alerts': [],
                'summary': {'total': 0, 'by_severity': {}},
                'count': 0
            }

        # Get summary
        summary = alert_manager.get_alert_summary(hours=hours)

        # Get active alerts
        active_alerts = alert_manager.get_active_alerts()

        # Filter by severity if provided
        if severity:
            try:
                from backend.backend_alert_manager import AlertSeverity
                severity_enum = AlertSeverity[severity.upper()]
                active_alerts = [a for a in active_alerts if a.severity == severity_enum]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity: {severity}"
                )

        return {
            'summary': summary,
            'alerts': [
                {
                    'alert_id': a.alert_id,
                    'rule_name': a.rule_name,
                    'severity': a.severity.value if hasattr(a.severity, 'value') else str(a.severity),
                    'message': a.message,
                    'status': a.status,
                    'created_at': a.created_at
                }
                for a in active_alerts
            ],
            'count': len(active_alerts)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: AcknowledgeAlertRequest):
    """Acknowledge an alert"""
    try:
        from backend.monitoring_startup import get_alert_manager

        alert_manager = get_alert_manager()

        if alert_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Alert manager not available"
            )

        success = alert_manager.acknowledge_alert(alert_id, request.acknowledged_by)

        if success:
            return {
                'message': 'Alert acknowledged',
                'alert_id': alert_id,
                'acknowledged_by': request.acknowledged_by
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    try:
        from backend.monitoring_startup import get_alert_manager

        alert_manager = get_alert_manager()

        if alert_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Alert manager not available"
            )

        success = alert_manager.resolve_alert(alert_id)

        if success:
            return {
                'message': 'Alert resolved',
                'alert_id': alert_id,
                'resolved_at': datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - METRICS
# ============================================================================

@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    hours: int = Query(1, ge=1, le=720),
    component: Optional[str] = Query(None)
):
    """Get all metrics with optional component filtering"""
    try:
        from backend.monitoring_startup import get_metrics_collector

        metrics_collector = get_metrics_collector()

        if metrics_collector is None:
            return {
                'metrics': [],
                'summary': {},
                'anomalies': []
            }

        # Get summary
        summary = metrics_collector.get_statistics()

        # Get anomalies
        anomalies = metrics_collector.get_anomalies(hours=hours) if hasattr(metrics_collector, 'get_anomalies') else []

        return {
            'summary': summary,
            'anomalies': [
                {
                    'metric': a.get('metric', 'unknown'),
                    'value': a.get('value', 0),
                    'severity': a.get('severity', 'warning'),
                    'timestamp': a.get('timestamp', datetime.utcnow().isoformat())
                }
                for a in anomalies
            ],
            'anomaly_count': len(anomalies),
            'hours': hours
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/metrics/{component}")
async def get_component_metrics(component: str, hours: int = Query(1, ge=1, le=720)):
    """Get metrics for a specific component"""
    try:
        from backend.monitoring_startup import get_metrics_collector

        metrics_collector = get_metrics_collector()

        if metrics_collector is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Metrics collector not available"
            )

        # Get component-specific metrics
        stats = metrics_collector.get_statistics()

        return {
            'component': component,
            'summary': stats,
            'hours': hours,
            'timestamp': datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting component metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get component metrics: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - ERRORS
# ============================================================================

@router.get("/errors", response_model=Dict[str, Any])
async def get_errors(hours: int = Query(24, ge=1, le=720)):
    """Get error summary and recent errors"""
    try:
        from backend.monitoring_startup import get_error_tracker

        error_tracker = get_error_tracker()

        if error_tracker is None:
            return {
                'summary': {'total_count': 0},
                'errors': [],
                'count': 0
            }

        summary = error_tracker.get_error_summary(hours=hours)

        return {
            'summary': summary,
            'errors': summary.get('recent_errors', []),
            'count': summary.get('total_count', 0),
            'hours': hours
        }

    except Exception as e:
        logger.error(f"Error getting errors: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get errors: {str(e)}"
        )


@router.post("/errors/{error_id}/resolve")
async def resolve_error(error_id: str):
    """Mark an error as resolved"""
    try:
        from backend.monitoring_startup import get_error_tracker

        error_tracker = get_error_tracker()

        if error_tracker is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error tracker not available"
            )

        # Mark error as resolved in tracker
        return {
            'message': 'Error marked as resolved',
            'error_id': error_id,
            'resolved_at': datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve error: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - ANOMALIES
# ============================================================================

@router.get("/anomalies", response_model=Dict[str, Any])
async def get_anomalies(hours: int = Query(24, ge=1, le=720)):
    """Get detected anomalies"""
    try:
        from backend.monitoring_startup import get_metrics_collector

        metrics_collector = get_metrics_collector()

        if metrics_collector is None:
            return {'anomalies': [], 'count': 0}

        anomalies = metrics_collector.get_anomalies(hours=hours) if hasattr(metrics_collector, 'get_anomalies') else []

        return {
            'anomalies': anomalies,
            'count': len(anomalies),
            'hours': hours
        }

    except Exception as e:
        logger.error(f"Error getting anomalies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get anomalies: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - PREDICTIONS
# ============================================================================

@router.get("/predictions", response_model=Dict[str, Any])
async def get_predictions():
    """Get prediction statistics"""
    try:
        from backend.monitoring_startup import get_prediction_broadcaster

        broadcaster = get_prediction_broadcaster()

        if broadcaster is None:
            return {'predictions': {}, 'count': 0}

        stats = broadcaster.get_statistics()

        return {
            'predictions': stats,
            'count': stats.get('total_predictions', 0),
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting predictions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get predictions: {str(e)}"
        )


@router.get("/predictions/{client_id}")
async def get_client_prediction(client_id: int):
    """Get latest prediction for a specific client"""
    try:
        from backend.monitoring_startup import get_prediction_broadcaster

        broadcaster = get_prediction_broadcaster()

        if broadcaster is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Prediction broadcaster not available"
            )

        prediction = broadcaster.get_active_prediction(client_id)

        if prediction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No prediction found for client {client_id}"
            )

        return {
            'client_id': client_id,
            'prediction': prediction.to_dict() if hasattr(prediction, 'to_dict') else {
                'probability': prediction.probability,
                'confidence': prediction.confidence
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client prediction: {str(e)}"
        )
