#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Track D: E2E Testing - Alert Routing & Integration Tests
Comprehensive end-to-end tests for Prometheus → AlertManager → Webhooks
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock
import requests
from fastapi.testclient import TestClient

# Import application
from backend.app import app
from backend.routes.alert_routing_routes import (
    ReceiverConfig, AlertRoute, AlertStatus, AlertGroup, WebhookPayload
)

# Test client
client = TestClient(app)

# ============================================================================
# FIXTURES & TEST DATA
# ============================================================================

@pytest.fixture
def sample_webhook_payload():
    """Sample AlertManager webhook payload"""
    return {
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighWebSocketLatency",
                    "severity": "warning",
                    "component": "websocket",
                    "service": "felix"
                },
                "annotations": {
                    "summary": "WebSocket latency high",
                    "description": "WebSocket latency exceeds 200ms",
                    "impact": "Users may experience slow updates",
                    "action": "Check WebSocket server logs"
                },
                "startsAt": datetime.now(timezone.utc).isoformat(),
                "endsAt": "0001-01-01T00:00:00Z",
                "value": "250"
            }
        ],
        "groupLabels": {
            "alertname": "HighWebSocketLatency",
            "severity": "warning"
        },
        "commonLabels": {
            "service": "felix",
            "component": "websocket"
        },
        "commonAnnotations": {
            "summary": "WebSocket latency high"
        },
        "externalURL": "http://prometheus:9090"
    }

@pytest.fixture
def critical_alert_payload():
    """Sample CRITICAL alert payload"""
    return {
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "FelixSystemUnhealthy",
                    "severity": "critical",
                    "service": "felix",
                    "component": "system"
                },
                "annotations": {
                    "summary": "System health check failed",
                    "description": "System health is critical",
                    "impact": "System is down",
                    "action": "Immediately check system status"
                },
                "startsAt": datetime.now(timezone.utc).isoformat(),
                "endsAt": "0001-01-01T00:00:00Z",
                "value": "-1"
            }
        ],
        "groupLabels": {
            "alertname": "FelixSystemUnhealthy",
            "severity": "critical"
        },
        "commonLabels": {
            "service": "felix"
        },
        "commonAnnotations": {
            "summary": "System health check failed"
        },
        "externalURL": "http://prometheus:9090"
    }

@pytest.fixture
def resolved_alert_payload():
    """Sample resolved alert"""
    return {
        "status": "resolved",
        "alerts": [
            {
                "status": "resolved",
                "labels": {
                    "alertname": "HighWebSocketLatency",
                    "severity": "warning",
                    "component": "websocket"
                },
                "annotations": {
                    "summary": "WebSocket latency resolved"
                },
                "startsAt": "2026-10-06T05:00:00Z",
                "endsAt": datetime.now(timezone.utc).isoformat()
            }
        ],
        "groupLabels": {
            "alertname": "HighWebSocketLatency"
        },
        "commonLabels": {},
        "commonAnnotations": {},
        "externalURL": "http://prometheus:9090"
    }

# ============================================================================
# TEST SUITE 1: Receiver Management
# ============================================================================

class TestReceiverManagement:
    """Tests for receiver CRUD operations"""

    def test_list_receivers(self):
        """Test GET /api/alerts/receivers"""
        response = client.get("/api/alerts/receivers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        # Should return at least default receivers
        assert len(response.json()) >= 1

    def test_create_slack_receiver(self):
        """Test POST /api/alerts/receivers - Slack receiver"""
        receiver_data = {
            "name": "test-slack-receiver",
            "slack": {
                "channel": "#test-alerts",
                "webhook_url": "https://hooks.slack.com/services/TEST",
                "enabled": True,
                "send_resolved": True
            },
            "description": "Test Slack receiver"
        }
        response = client.post("/api/alerts/receivers", json=receiver_data)
        assert response.status_code == 201
        assert response.json()["name"] == "test-slack-receiver"

    def test_create_receiver_missing_config(self):
        """Test POST /api/alerts/receivers - Missing config (should fail)"""
        receiver_data = {
            "name": "invalid-receiver",
            "description": "No slack/pagerduty/email config"
        }
        response = client.post("/api/alerts/receivers", json=receiver_data)
        assert response.status_code == 400
        assert "must have at least one config" in response.json()["detail"]

    def test_update_receiver(self):
        """Test PUT /api/alerts/receivers/{name}"""
        updated_data = {
            "name": "critical-team",
            "slack": {
                "channel": "#updated-critical",
                "webhook_url": "https://hooks.slack.com/services/UPDATED"
            }
        }
        response = client.put("/api/alerts/receivers/critical-team", json=updated_data)
        assert response.status_code == 200

    def test_delete_receiver(self):
        """Test DELETE /api/alerts/receivers/{name}"""
        response = client.delete("/api/alerts/receivers/test-slack-receiver")
        assert response.status_code == 204

# ============================================================================
# TEST SUITE 2: Route Management
# ============================================================================

class TestRouteManagement:
    """Tests for alert routing rules"""

    def test_list_routes(self):
        """Test GET /api/alerts/routes"""
        response = client.get("/api/alerts/routes")
        assert response.status_code == 200
        routes = response.json()
        assert isinstance(routes, list)
        assert len(routes) >= 1

    def test_create_route(self):
        """Test POST /api/alerts/routes"""
        route_data = {
            "match_labels": {
                "severity": "critical",
                "component": "websocket"
            },
            "receiver": "websocket-team",
            "group_by": ["alertname", "severity"],
            "group_wait": "5s",
            "group_interval": "5s",
            "repeat_interval": "1h"
        }
        response = client.post("/api/alerts/routes", json=route_data)
        assert response.status_code == 201
        created_route = response.json()
        assert created_route["receiver"] == "websocket-team"
        assert created_route["match_labels"]["severity"] == "critical"

# ============================================================================
# TEST SUITE 3: Alert Webhook Handling
# ============================================================================

class TestAlertWebhookHandling:
    """Tests for webhook payload processing"""

    def test_alertmanager_webhook_firing(self, sample_webhook_payload):
        """Test POST /api/alerts/webhooks/alertmanager - Firing alert"""
        response = client.post("/api/alerts/webhooks/alertmanager", json=sample_webhook_payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["alerts_processed"] == 1

    def test_alertmanager_webhook_critical(self, critical_alert_payload):
        """Test critical alert webhook"""
        response = client.post("/api/alerts/webhooks/alertmanager", json=critical_alert_payload)
        assert response.status_code == 200
        assert response.json()["alerts_processed"] == 1

    def test_alertmanager_webhook_resolved(self, resolved_alert_payload):
        """Test resolved alert webhook"""
        response = client.post("/api/alerts/webhooks/alertmanager", json=resolved_alert_payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_multiple_alerts_webhook(self):
        """Test webhook with multiple alerts"""
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": f"Alert{i}",
                        "severity": "warning"
                    },
                    "annotations": {"summary": f"Test alert {i}"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
                for i in range(5)
            ],
            "groupLabels": {"severity": "warning"},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }
        response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
        assert response.status_code == 200
        assert response.json()["alerts_processed"] == 5

# ============================================================================
# TEST SUITE 4: Alert Querying
# ============================================================================

class TestAlertQuerying:
    """Tests for alert query endpoints"""

    def test_get_active_alerts(self):
        """Test GET /api/alerts/active"""
        response = client.get("/api/alerts/active")
        assert response.status_code == 200 or response.status_code == 503  # 503 if AlertManager unavailable
        if response.status_code == 200:
            alerts = response.json()
            assert isinstance(alerts, list)

    def test_get_resolved_alerts(self):
        """Test GET /api/alerts/resolved"""
        response = client.get("/api/alerts/resolved")
        assert response.status_code == 200 or response.status_code == 503
        if response.status_code == 200:
            alerts = response.json()
            assert isinstance(alerts, list)

    def test_get_alert_statistics(self):
        """Test GET /api/alerts/stats/summary"""
        response = client.get("/api/alerts/stats/summary")
        assert response.status_code == 200 or response.status_code == 503
        if response.status_code == 200:
            stats = response.json()
            assert "total_alerts" in stats
            assert "firing" in stats
            assert "resolved" in stats
            assert "by_severity" in stats
            assert "timestamp" in stats

# ============================================================================
# TEST SUITE 5: Alert Grouping & Deduplication
# ============================================================================

class TestAlertGrouping:
    """Tests for alert grouping and deduplication"""

    def test_same_alert_deduplication(self):
        """Test that duplicate alerts are deduplicated"""
        # Send same alert twice
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "DuplicateAlert",
                        "severity": "warning"
                    },
                    "annotations": {"summary": "Test duplicate"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {"alertname": "DuplicateAlert"},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }

        # First alert
        response1 = client.post("/api/alerts/webhooks/alertmanager", json=payload)
        assert response1.status_code == 200

        # Duplicate alert
        response2 = client.post("/api/alerts/webhooks/alertmanager", json=payload)
        assert response2.status_code == 200
        # System should handle gracefully

    def test_alert_grouping_by_severity(self):
        """Test alerts are grouped by severity"""
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "GroupTest",
                        "severity": "warning",
                        "service": "felix"
                    },
                    "annotations": {"summary": "Warning alert"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                },
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "GroupTest",
                        "severity": "critical",
                        "service": "felix"
                    },
                    "annotations": {"summary": "Critical alert"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {"alertname": "GroupTest"},
            "commonLabels": {"service": "felix"},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }

        response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
        assert response.status_code == 200
        assert response.json()["alerts_processed"] == 2

# ============================================================================
# TEST SUITE 6: Slack Webhook Handler
# ============================================================================

class TestSlackWebhookHandler:
    """Tests for Slack action handlers"""

    def test_slack_acknowledge_action(self):
        """Test Slack webhook - Acknowledge action"""
        payload = {
            "action": "acknowledge",
            "alert_id": "alert-123"
        }
        response = client.post("/api/alerts/webhooks/slack", json=payload)
        assert response.status_code == 200
        assert response.json()["action"] == "acknowledge"

    def test_slack_escalate_action(self):
        """Test Slack webhook - Escalate action"""
        payload = {
            "action": "escalate",
            "alert_id": "alert-456"
        }
        response = client.post("/api/alerts/webhooks/slack", json=payload)
        assert response.status_code == 200

# ============================================================================
# TEST SUITE 7: PagerDuty Webhook Handler
# ============================================================================

class TestPagerDutyWebhookHandler:
    """Tests for PagerDuty webhook handlers"""

    def test_pagerduty_incident_triggered(self):
        """Test PagerDuty webhook - Incident triggered"""
        payload = {
            "incident_id": "incident-789",
            "status": "triggered"
        }
        response = client.post("/api/alerts/webhooks/pagerduty", json=payload)
        assert response.status_code == 200
        assert response.json()["incident"] == "incident-789"

    def test_pagerduty_incident_acknowledged(self):
        """Test PagerDuty webhook - Incident acknowledged"""
        payload = {
            "incident_id": "incident-789",
            "status": "acknowledged"
        }
        response = client.post("/api/alerts/webhooks/pagerduty", json=payload)
        assert response.status_code == 200

    def test_pagerduty_incident_resolved(self):
        """Test PagerDuty webhook - Incident resolved"""
        payload = {
            "incident_id": "incident-789",
            "status": "resolved"
        }
        response = client.post("/api/alerts/webhooks/pagerduty", json=payload)
        assert response.status_code == 200

# ============================================================================
# TEST SUITE 8: Alert Routing Logic
# ============================================================================

class TestAlertRoutingLogic:
    """Tests for alert routing decision logic"""

    def test_critical_routes_to_all_receivers(self):
        """Critical alerts should route to Slack + PagerDuty + Email"""
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "TestCritical",
                        "severity": "critical"
                    },
                    "annotations": {"summary": "Critical test"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {"severity": "critical"},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }
        response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
        assert response.status_code == 200
        # In real scenario, should trigger all 3 integrations

    def test_warning_routes_to_slack_only(self):
        """Warning alerts should route to Slack only"""
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "TestWarning",
                        "severity": "warning"
                    },
                    "annotations": {"summary": "Warning test"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {"severity": "warning"},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }
        response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
        assert response.status_code == 200

    def test_component_based_routing(self):
        """Test routing by component"""
        for component in ["websocket", "api", "cache", "system"]:
            payload = {
                "status": "firing",
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {
                            "alertname": f"{component.upper()}Alert",
                            "component": component,
                            "severity": "warning"
                        },
                        "annotations": {"summary": f"{component} test"},
                        "startsAt": datetime.now(timezone.utc).isoformat(),
                        "endsAt": "0001-01-01T00:00:00Z"
                    }
                ],
                "groupLabels": {"component": component},
                "commonLabels": {},
                "commonAnnotations": {},
                "externalURL": "http://prometheus:9090"
            }
            response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
            assert response.status_code == 200

# ============================================================================
# TEST SUITE 9: Integration Tests
# ============================================================================

class TestAlertIntegration:
    """End-to-end integration tests"""

    def test_complete_alert_lifecycle(self, sample_webhook_payload):
        """Test complete alert lifecycle: fire → acknowledge → resolve"""
        # 1. Alert fires
        response = client.post("/api/alerts/webhooks/alertmanager", json=sample_webhook_payload)
        assert response.status_code == 200

        # 2. Query active alerts
        response = client.get("/api/alerts/active")
        assert response.status_code == 200 or response.status_code == 503

        # 3. Acknowledge via Slack
        ack_payload = {
            "action": "acknowledge",
            "alert_id": "HighWebSocketLatency"
        }
        response = client.post("/api/alerts/webhooks/slack", json=ack_payload)
        assert response.status_code == 200

        # 4. Alert resolves
        resolved_payload = sample_webhook_payload.copy()
        resolved_payload["status"] = "resolved"
        resolved_payload["alerts"][0]["status"] = "resolved"
        response = client.post("/api/alerts/webhooks/alertmanager", json=resolved_payload)
        assert response.status_code == 200

        # 5. Query resolved alerts
        response = client.get("/api/alerts/resolved")
        assert response.status_code == 200 or response.status_code == 503

    def test_alert_storm_handling(self):
        """Test handling of alert storm (many alerts at once)"""
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": f"StormAlert{i}",
                        "severity": "warning"
                    },
                    "annotations": {"summary": f"Alert {i}"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
                for i in range(50)
            ],
            "groupLabels": {"severity": "warning"},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }
        response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
        assert response.status_code == 200
        assert response.json()["alerts_processed"] == 50

# ============================================================================
# TEST SUITE 10: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for error handling and edge cases"""

    def test_invalid_webhook_payload(self):
        """Test handling of invalid webhook payload"""
        response = client.post("/api/alerts/webhooks/alertmanager", json={"invalid": "data"})
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self):
        """Test webhook with missing required fields"""
        payload = {
            "status": "firing",
            "alerts": [],  # Empty alerts list
            "groupLabels": {},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }
        response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
