#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Track D: Pytest Configuration & Fixtures
Common fixtures and configuration for E2E testing
"""

import pytest
import os
from datetime import datetime, timezone
from typing import Generator
from fastapi.testclient import TestClient
from backend.app import app

# ============================================================================
# SESSION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """Provide FastAPI test client for entire session"""
    return TestClient(app)

@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "alertmanager_url": os.getenv("ALERTMANAGER_URL", "http://localhost:9093"),
        "prometheus_url": os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
        "webhook_timeout": 30,
        "performance_targets": {
            "webhook_latency_ms": 100,
            "query_latency_ms": 500,
            "throughput_alerts_per_sec": 10
        }
    }

# ============================================================================
# ALERT FIXTURES
# ============================================================================

@pytest.fixture
def alert_timestamp():
    """Current timestamp for alerts"""
    return datetime.now(timezone.utc).isoformat()

@pytest.fixture
def base_alert_labels():
    """Common alert labels"""
    return {
        "service": "felix",
        "environment": "test",
        "region": "us-west-2"
    }

@pytest.fixture
def critical_alert(alert_timestamp, base_alert_labels):
    """Critical alert template"""
    return {
        "status": "firing",
        "labels": {
            **base_alert_labels,
            "alertname": "CriticalAlert",
            "severity": "critical"
        },
        "annotations": {
            "summary": "Critical system alert",
            "description": "System health check failed",
            "impact": "Service is down",
            "action": "Immediately check system status"
        },
        "startsAt": alert_timestamp,
        "endsAt": "0001-01-01T00:00:00Z",
        "value": "-1"
    }

# ============================================================================
# WEBHOOK PAYLOAD FIXTURES
# ============================================================================

@pytest.fixture
def webhook_payload_single_alert(critical_alert):
    """Webhook payload with single alert"""
    return {
        "status": "firing",
        "alerts": [critical_alert],
        "groupLabels": {
            "alertname": "CriticalAlert",
            "severity": "critical"
        },
        "commonLabels": {
            "service": "felix"
        },
        "commonAnnotations": {
            "dashboard": "http://localhost:3000"
        },
        "externalURL": "http://prometheus:9090"
    }

# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )

# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def alert_factory():
    """Factory for creating alerts"""
    class AlertFactory:
        @staticmethod
        def create_alert(
            name: str = "TestAlert",
            severity: str = "warning",
            status: str = "firing",
            component: str = "system",
            value: str = "1"
        ) -> dict:
            """Create alert with given parameters"""
            return {
                "status": status,
                "labels": {
                    "alertname": name,
                    "severity": severity,
                    "component": component,
                    "service": "felix"
                },
                "annotations": {
                    "summary": f"{name} triggered",
                    "description": f"Test alert: {name}"
                },
                "startsAt": datetime.now(timezone.utc).isoformat(),
                "endsAt": "0001-01-01T00:00:00Z" if status == "firing" else datetime.now(timezone.utc).isoformat(),
                "value": value
            }
    
    return AlertFactory()

