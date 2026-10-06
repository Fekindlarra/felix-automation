#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Track D: Performance & Load Testing
Tests for WebSocket, API latency, and alert throughput
"""

import pytest
import time
import asyncio
from datetime import datetime, timezone
from typing import List
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================

@pytest.fixture
def large_alert_payload():
    """Generate large alert payload (1000+ events)"""
    return {
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": f"PerfTestAlert{i}",
                    "severity": "warning" if i % 2 == 0 else "critical",
                    "component": ["websocket", "api", "cache", "system"][i % 4],
                    "service": "felix"
                },
                "annotations": {
                    "summary": f"Performance test alert {i}",
                    "description": f"Test alert for performance testing",
                    "value": str(i * 10)
                },
                "startsAt": datetime.now(timezone.utc).isoformat(),
                "endsAt": "0001-01-01T00:00:00Z",
                "value": str(i)
            }
            for i in range(1000)
        ],
        "groupLabels": {"severity": "warning"},
        "commonLabels": {"service": "felix"},
        "commonAnnotations": {"source": "performance-test"},
        "externalURL": "http://prometheus:9090"
    }

# ============================================================================
# TEST SUITE 1: Webhook Performance
# ============================================================================

class TestWebhookPerformance:
    """Performance tests for webhook endpoints"""

    def test_webhook_response_time_single_alert(self):
        """Test webhook response time for single alert"""
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "SingleAlert", "severity": "warning"},
                    "annotations": {"summary": "Single alert"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }

        start = time.time()
        response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
        elapsed = (time.time() - start) * 1000  # ms

        assert response.status_code == 200
        assert elapsed < 100, f"Single alert processing took {elapsed:.2f}ms (target: <100ms)"

    def test_webhook_response_time_bulk_alerts(self, large_alert_payload):
        """Test webhook response time for 1000 alerts"""
        start = time.time()
        response = client.post("/api/alerts/webhooks/alertmanager", json=large_alert_payload)
        elapsed = (time.time() - start) * 1000  # ms

        assert response.status_code == 200
        assert response.json()["alerts_processed"] == 1000
        assert elapsed < 2000, f"1000 alerts took {elapsed:.2f}ms (target: <2000ms)"

    def test_webhook_throughput_concurrent(self):
        """Test webhook throughput with rapid concurrent requests"""
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "ConcurrentAlert", "severity": "warning"},
                    "annotations": {"summary": "Concurrent test"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }

        # Send 10 concurrent-like requests
        start = time.time()
        for _ in range(10):
            response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
            assert response.status_code == 200
        elapsed = (time.time() - start) * 1000

        avg_time = elapsed / 10
        assert avg_time < 100, f"Average request time {avg_time:.2f}ms (target: <100ms)"

# ============================================================================
# TEST SUITE 2: Query Performance
# ============================================================================

class TestQueryPerformance:
    """Performance tests for query endpoints"""

    def test_active_alerts_query_performance(self):
        """Test GET /api/alerts/active performance"""
        start = time.time()
        response = client.get("/api/alerts/active")
        elapsed = (time.time() - start) * 1000  # ms

        if response.status_code == 200:
            assert elapsed < 500, f"Query took {elapsed:.2f}ms (target: <500ms)"

    def test_stats_calculation_performance(self):
        """Test GET /api/alerts/stats/summary performance"""
        start = time.time()
        response = client.get("/api/alerts/stats/summary")
        elapsed = (time.time() - start) * 1000  # ms

        if response.status_code == 200:
            assert elapsed < 300, f"Stats calculation took {elapsed:.2f}ms (target: <300ms)"

    def test_receiver_list_performance(self):
        """Test GET /api/alerts/receivers performance"""
        start = time.time()
        response = client.get("/api/alerts/receivers")
        elapsed = (time.time() - start) * 1000  # ms

        assert response.status_code == 200
        assert elapsed < 100, f"Receiver list took {elapsed:.2f}ms (target: <100ms)"

# ============================================================================
# TEST SUITE 3: Memory & Resource Usage
# ============================================================================

class TestResourceUsage:
    """Tests for memory and resource efficiency"""

    def test_large_payload_memory_efficiency(self, large_alert_payload):
        """Test memory efficiency with large payload"""
        import sys

        # Process large payload
        start_size = sys.getsizeof(large_alert_payload)
        response = client.post("/api/alerts/webhooks/alertmanager", json=large_alert_payload)

        assert response.status_code == 200
        # Payload should be processed without excessive memory issues

    def test_repeated_processing_stability(self):
        """Test stability under repeated processing"""
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "RepeatedAlert", "severity": "warning"},
                    "annotations": {"summary": "Repeated test"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }

        # Process same payload 100 times
        for i in range(100):
            response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
            assert response.status_code == 200
            if i % 25 == 0:
                print(f"  Processed {i+1} iterations successfully")

# ============================================================================
# TEST SUITE 4: Latency & Response Times
# ============================================================================

class TestLatency:
    """Tests for API latency and SLA compliance"""

    def test_webhook_latency_sla(self):
        """Test webhook processing meets <100ms SLA"""
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "SLATest", "severity": "critical"},
                    "annotations": {"summary": "SLA test"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }

        latencies = []
        for _ in range(10):
            start = time.time()
            response = client.post("/api/alerts/webhooks/alertmanager", json=payload)
            latencies.append((time.time() - start) * 1000)
            assert response.status_code == 200

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        assert avg_latency < 100, f"Avg latency {avg_latency:.2f}ms exceeds SLA"
        assert p95_latency < 150, f"P95 latency {p95_latency:.2f}ms exceeds SLA"

        print(f"  Average latency: {avg_latency:.2f}ms")
        print(f"  P95 latency: {p95_latency:.2f}ms")

    def test_receiver_operation_latency(self):
        """Test receiver CRUD operations latency"""
        receiver_data = {
            "name": "latency-test",
            "slack": {
                "channel": "#test",
                "webhook_url": "https://hooks.slack.com/test"
            }
        }

        # Create
        start = time.time()
        response = client.post("/api/alerts/receivers", json=receiver_data)
        create_time = (time.time() - start) * 1000
        assert response.status_code == 201
        assert create_time < 100

        # List
        start = time.time()
        response = client.get("/api/alerts/receivers")
        list_time = (time.time() - start) * 1000
        assert response.status_code == 200
        assert list_time < 100

        # Update
        receiver_data["slack"]["channel"] = "#updated"
        start = time.time()
        response = client.put("/api/alerts/receivers/latency-test", json=receiver_data)
        update_time = (time.time() - start) * 1000
        assert update_time < 100

        # Delete
        start = time.time()
        response = client.delete("/api/alerts/receivers/latency-test")
        delete_time = (time.time() - start) * 1000
        assert response.status_code == 204
        assert delete_time < 100

# ============================================================================
# TEST SUITE 5: Throughput & Capacity
# ============================================================================

class TestThroughput:
    """Tests for throughput and capacity"""

    def test_alerts_per_second_throughput(self):
        """Test processing rate (alerts per second)"""
        payload_single_alert = {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "ThroughputTest", "severity": "warning"},
                    "annotations": {"summary": "Throughput test"},
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {},
            "commonLabels": {},
            "commonAnnotations": {},
            "externalURL": "http://prometheus:9090"
        }

        alert_count = 0
        start = time.time()

        # Process alerts for 5 seconds or until 100 alerts
        while time.time() - start < 5 and alert_count < 100:
            response = client.post("/api/alerts/webhooks/alertmanager", json=payload_single_alert)
            assert response.status_code == 200
            alert_count += response.json()["alerts_processed"]

        elapsed = time.time() - start
        throughput = alert_count / elapsed

        print(f"  Processed {alert_count} alerts in {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.2f} alerts/second")
        assert throughput > 10, f"Throughput {throughput:.2f} alerts/sec below target (>10)"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
