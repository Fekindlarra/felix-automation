#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Week 2: Track C - Alert Routing
API routes for managing AlertManager configuration and routing
"""

import logging
from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import requests
import json

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/alerts",
    tags=["alert-routing"],
    responses={404: {"description": "Not found"}}
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SlackConfig(BaseModel):
    """Slack webhook configuration"""
    channel: str = Field(..., description="Slack channel name")
    webhook_url: str = Field(..., description="Slack webhook URL")
    enabled: bool = True
    send_resolved: bool = True

class PagerDutyConfig(BaseModel):
    """PagerDuty integration configuration"""
    service_key: str = Field(..., description="PagerDuty service key")
    enabled: bool = True

class EmailConfig(BaseModel):
    """Email notification configuration"""
    to: List[str] = Field(..., description="Recipient emails")
    enabled: bool = True

class ReceiverConfig(BaseModel):
    """Alert receiver configuration"""
    name: str = Field(..., description="Receiver name")
    slack: Optional[SlackConfig] = None
    pagerduty: Optional[PagerDutyConfig] = None
    email: Optional[EmailConfig] = None
    description: Optional[str] = None

class AlertRoute(BaseModel):
    """Alert routing rule"""
    match_labels: Dict[str, str] = Field(..., description="Labels to match")
    receiver: str = Field(..., description="Receiver name")
    group_by: List[str] = Field(default_factory=lambda: ["alertname", "severity"])
    group_wait: str = "10s"
    group_interval: str = "10s"
    repeat_interval: str = "12h"
    continue_route: bool = False

class AlertRoutingConfig(BaseModel):
    """Complete alert routing configuration"""
    receivers: List[ReceiverConfig]
    routes: List[AlertRoute]
    grouping_wait: str = "10s"
    grouping_interval: str = "10s"
    repeat_interval: str = "12h"

class AlertStatus(BaseModel):
    """Status of an alert"""
    alertname: str
    severity: str
    component: str
    status: str  # 'firing' or 'resolved'
    started_at: str
    resolved_at: Optional[str] = None
    value: Optional[float] = None
    annotations: Dict[str, str] = {}

class AlertGroup(BaseModel):
    """Group of related alerts"""
    group_labels: Dict[str, str]
    group_key: str
    alerts: List[AlertStatus]
    firing_count: int
    resolved_count: int

class WebhookPayload(BaseModel):
    """AlertManager webhook payload"""
    status: str
    alerts: List[Dict[str, Any]]
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str

# ============================================================================
# RECEIVER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/receivers", response_model=List[ReceiverConfig])
async def get_receivers():
    """
    Get all configured alert receivers

    Returns list of Slack, PagerDuty, Email receivers
    """
    try:
        logger.info("📥 Fetching configured receivers")

        # TODO: Load from alertmanager.yml or database
        receivers = [
            ReceiverConfig(
                name="critical-team",
                slack=SlackConfig(
                    channel="#felix-alerts-critical",
                    webhook_url="https://hooks.slack.com/services/..."
                ),
                pagerduty=PagerDutyConfig(service_key="PAGERDUTY_KEY"),
                description="Critical alerts go to critical team"
            ),
            ReceiverConfig(
                name="warning-receiver",
                slack=SlackConfig(
                    channel="#felix-alerts-warnings",
                    webhook_url="https://hooks.slack.com/services/..."
                ),
                description="Warning alerts go to warnings channel"
            )
        ]

        logger.info(f"✅ Returned {len(receivers)} receivers")
        return receivers
    except Exception as e:
        logger.error(f"❌ Error fetching receivers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/receivers", response_model=ReceiverConfig, status_code=status.HTTP_201_CREATED)
async def create_receiver(receiver: ReceiverConfig = Body(...)):
    """
    Create a new alert receiver

    Supports Slack, PagerDuty, and Email receivers
    """
    try:
        logger.info(f"📝 Creating receiver: {receiver.name}")

        # Validate receiver has at least one config
        if not any([receiver.slack, receiver.pagerduty, receiver.email]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receiver must have at least one config (Slack, PagerDuty, or Email)"
            )

        # TODO: Save to alertmanager.yml
        # TODO: Reload AlertManager configuration

        logger.info(f"✅ Receiver created: {receiver.name}")
        return receiver
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating receiver: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/receivers/{receiver_name}", response_model=ReceiverConfig)
async def update_receiver(
    receiver_name: str,
    receiver: ReceiverConfig = Body(...)
):
    """
    Update an existing alert receiver
    """
    try:
        logger.info(f"🔄 Updating receiver: {receiver_name}")

        # TODO: Update in alertmanager.yml
        # TODO: Reload AlertManager configuration

        logger.info(f"✅ Receiver updated: {receiver_name}")
        return receiver
    except Exception as e:
        logger.error(f"❌ Error updating receiver: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/receivers/{receiver_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receiver(receiver_name: str):
    """
    Delete an alert receiver
    """
    try:
        logger.info(f"🗑️ Deleting receiver: {receiver_name}")

        # TODO: Remove from alertmanager.yml
        # TODO: Reload AlertManager configuration

        logger.info(f"✅ Receiver deleted: {receiver_name}")
    except Exception as e:
        logger.error(f"❌ Error deleting receiver: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ============================================================================
# ROUTING RULES ENDPOINTS
# ============================================================================

@router.get("/routes", response_model=List[AlertRoute])
async def get_routes():
    """
    Get all configured alert routing rules
    """
    try:
        logger.info("📥 Fetching alert routes")

        # TODO: Load from alertmanager.yml or database
        routes = [
            AlertRoute(
                match_labels={"severity": "critical"},
                receiver="critical-team",
                group_wait="0s",
                group_interval="5s"
            ),
            AlertRoute(
                match_labels={"component": "websocket"},
                receiver="websocket-team",
                group_wait="5s"
            )
        ]

        logger.info(f"✅ Returned {len(routes)} routes")
        return routes
    except Exception as e:
        logger.error(f"❌ Error fetching routes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/routes", response_model=AlertRoute, status_code=status.HTTP_201_CREATED)
async def create_route(route: AlertRoute = Body(...)):
    """
    Create a new alert routing rule

    Maps label patterns to receivers
    """
    try:
        logger.info(f"📝 Creating route with labels: {route.match_labels}")

        # TODO: Save to alertmanager.yml
        # TODO: Reload AlertManager

        logger.info(f"✅ Route created")
        return route
    except Exception as e:
        logger.error(f"❌ Error creating route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ============================================================================
# ACTIVE ALERTS ENDPOINTS
# ============================================================================

@router.get("/active", response_model=List[AlertGroup])
async def get_active_alerts():
    """
    Get currently active alerts from AlertManager
    """
    try:
        logger.info("📥 Fetching active alerts from AlertManager")

        # Query AlertManager API
        response = requests.get(
            "http://localhost:9093/api/v1/alerts",
            params={"active": "true"},
            timeout=5
        )
        response.raise_for_status()

        alerts_data = response.json().get("data", [])
        logger.info(f"✅ Retrieved {len(alerts_data)} active alerts")

        # Group alerts
        groups = _group_alerts(alerts_data)
        return groups
    except requests.RequestException as e:
        logger.error(f"❌ AlertManager connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AlertManager unavailable"
        )
    except Exception as e:
        logger.error(f"❌ Error fetching active alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/resolved", response_model=List[AlertGroup])
async def get_resolved_alerts():
    """
    Get recently resolved alerts
    """
    try:
        logger.info("📥 Fetching resolved alerts from AlertManager")

        # Query AlertManager API
        response = requests.get(
            "http://localhost:9093/api/v1/alerts",
            params={"active": "false"},
            timeout=5
        )
        response.raise_for_status()

        alerts_data = response.json().get("data", [])
        logger.info(f"✅ Retrieved {len(alerts_data)} resolved alerts")

        # Group alerts
        groups = _group_alerts(alerts_data)
        return groups
    except Exception as e:
        logger.error(f"❌ Error fetching resolved alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@router.post("/webhooks/alertmanager")
async def alertmanager_webhook(payload: WebhookPayload):
    """
    Webhook receiver for AlertManager alerts

    Logs all incoming alerts and routes them
    """
    try:
        logger.info(
            f"🔔 AlertManager webhook: {len(payload.alerts)} alerts, "
            f"status={payload.status}"
        )

        for alert in payload.alerts:
            logger.info(
                f"  - {alert.get('labels', {}).get('alertname')}: "
                f"{alert.get('status')}"
            )

        # TODO: Process alerts (store in DB, forward to integrations, etc.)

        return {"status": "ok", "alerts_processed": len(payload.alerts)}
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/webhooks/slack")
async def slack_webhook_handler(payload: Dict[str, Any]):
    """
    Custom webhook handler for Slack actions

    Handles acknowledgement, escalation, etc.
    """
    try:
        action = payload.get("action")
        alert_id = payload.get("alert_id")

        logger.info(f"🎯 Slack action: {action} for alert {alert_id}")

        # TODO: Handle Slack actions

        return {"status": "ok", "action": action}
    except Exception as e:
        logger.error(f"❌ Error handling Slack webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/webhooks/pagerduty")
async def pagerduty_webhook_handler(payload: Dict[str, Any]):
    """
    Custom webhook handler for PagerDuty actions

    Handles incident status changes
    """
    try:
        incident_id = payload.get("incident_id")
        status = payload.get("status")

        logger.info(f"📱 PagerDuty incident {incident_id}: {status}")

        # TODO: Handle PagerDuty incident updates

        return {"status": "ok", "incident": incident_id}
    except Exception as e:
        logger.error(f"❌ Error handling PagerDuty webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ============================================================================
# ALERT STATISTICS & ANALYTICS
# ============================================================================

@router.get("/stats/summary")
async def get_alert_summary():
    """
    Get summary statistics of alerts
    """
    try:
        logger.info("📊 Calculating alert statistics")

        # Query active alerts
        response = requests.get(
            "http://localhost:9093/api/v1/alerts",
            timeout=5
        )
        response.raise_for_status()

        alerts = response.json().get("data", [])

        # Calculate stats
        stats = {
            "total_alerts": len(alerts),
            "firing": sum(1 for a in alerts if a.get("status") == "firing"),
            "resolved": sum(1 for a in alerts if a.get("status") == "resolved"),
            "by_severity": {},
            "by_component": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Count by severity
        for alert in alerts:
            labels = alert.get("labels", {})
            severity = labels.get("severity", "unknown")
            component = labels.get("component", "unknown")

            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
            stats["by_component"][component] = stats["by_component"].get(component, 0) + 1

        logger.info(f"✅ Stats: {stats['firing']} firing, {stats['resolved']} resolved")
        return stats
    except Exception as e:
        logger.error(f"❌ Error calculating statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _group_alerts(alerts: List[Dict[str, Any]]) -> List[AlertGroup]:
    """
    Group alerts by their labels
    """
    groups_dict = {}

    for alert in alerts:
        labels = alert.get("labels", {})
        group_key = f"{labels.get('alertname')}_{labels.get('severity')}"

        if group_key not in groups_dict:
            groups_dict[group_key] = {
                "group_labels": {
                    "alertname": labels.get("alertname"),
                    "severity": labels.get("severity")
                },
                "group_key": group_key,
                "alerts": [],
                "firing_count": 0,
                "resolved_count": 0
            }

        # Create alert status
        status_obj = AlertStatus(
            alertname=labels.get("alertname", "unknown"),
            severity=labels.get("severity", "unknown"),
            component=labels.get("component", "system"),
            status=alert.get("status", "unknown"),
            started_at=alert.get("startsAt", ""),
            resolved_at=alert.get("endsAt"),
            value=float(alert.get("value", 0)) if alert.get("value") else None,
            annotations=alert.get("annotations", {})
        )

        groups_dict[group_key]["alerts"].append(status_obj)

        if alert.get("status") == "firing":
            groups_dict[group_key]["firing_count"] += 1
        else:
            groups_dict[group_key]["resolved_count"] += 1

    return [AlertGroup(**group) for group in groups_dict.values()]
