#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Monitoring REST API Endpoints (FASE 14)
Tests all 8 monitoring endpoints with FastAPI test client
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.app import app
from backend.monitoring import (
    get_metrics_collector,
    HealthMetric,
    MetricType
)
from backend.monitoring_startup import initialize_monitoring


# Initialize monitoring before tests
initialize_monitoring()

# Create test client
client = TestClient(app)


def test_health_check_endpoint():
    """Test 1: GET /health endpoint"""
    print("\n" + "="*70)
    print("TEST 1: GET /health")
    print("="*70)

    try:
        response = client.get("/health")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "status" in data, "Missing 'status' field"
        assert data["status"] == "🟢 OK", f"Expected '🟢 OK', got {data['status']}"

        print(f"✅ PASS: Basic health check works")
        print(f"   Response: {data}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_monitoring_initialize_endpoint():
    """Test 2: POST /api/monitoring/initialize"""
    print("\n" + "="*70)
    print("TEST 2: POST /api/monitoring/initialize")
    print("="*70)

    try:
        response = client.post("/api/monitoring/initialize")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "status" in data, "Missing 'status' field"
        assert data["status"] in ["initialized", "warning"], f"Unexpected status: {data['status']}"
        assert "components" in data, "Missing 'components' field"

        print(f"✅ PASS: Monitoring initialization endpoint works")
        print(f"   Status: {data['status']}")
        print(f"   Components: {', '.join(data['components'].keys())}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_monitoring_health_endpoint():
    """Test 3: GET /api/monitoring/health"""
    print("\n" + "="*70)
    print("TEST 3: GET /api/monitoring/health")
    print("="*70)

    try:
        response = client.get("/api/monitoring/health")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data["status"] == "ok", f"Expected status 'ok', got {data['status']}"
        assert "health" in data, "Missing 'health' field"
        assert "timestamp" in data, "Missing 'timestamp' field"

        health = data["health"]
        assert "overall_status" in health, "Missing 'overall_status'"
        assert "metrics" in health, "Missing 'metrics'"
        assert "alerts" in health, "Missing 'alerts'"

        print(f"✅ PASS: Health check endpoint works")
        print(f"   Overall status: {health['overall_status']}")
        print(f"   Metrics: {len(health['metrics'])} health checks")
        print(f"   Active alerts: {len(health['alerts'])}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_monitoring_dashboard_endpoint():
    """Test 4: GET /api/monitoring/dashboard"""
    print("\n" + "="*70)
    print("TEST 4: GET /api/monitoring/dashboard")
    print("="*70)

    try:
        response = client.get("/api/monitoring/dashboard")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data["status"] == "ok", f"Expected status 'ok'"
        assert "dashboard" in data, "Missing 'dashboard' field"
        assert "timestamp" in data, "Missing 'timestamp' field"

        dashboard = data["dashboard"]
        assert "health" in dashboard, "Missing 'health' in dashboard"
        assert "websocket_metrics" in dashboard, "Missing 'websocket_metrics'"
        assert "cache_metrics" in dashboard, "Missing 'cache_metrics'"
        assert "api_metrics" in dashboard, "Missing 'api_metrics'"
        assert "ml_metrics" in dashboard, "Missing 'ml_metrics'"
        assert "database_metrics" in dashboard, "Missing 'database_metrics'"

        print(f"✅ PASS: Dashboard endpoint works")
        print(f"   Sections: {len(dashboard) - 1} (excluding timestamp)")
        print(f"   Health status: {dashboard['health']['overall_status']}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_metrics_list_endpoint():
    """Test 5: GET /api/monitoring/metrics"""
    print("\n" + "="*70)
    print("TEST 5: GET /api/monitoring/metrics")
    print("="*70)

    try:
        # First record a test metric
        collector = get_metrics_collector()
        metric = HealthMetric(
            name="test_api_metric",
            value=100,
            metric_type=MetricType.GAUGE,
            timestamp="",
            unit="units"
        )
        collector.record(metric)

        response = client.get("/api/monitoring/metrics")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data["status"] == "ok", "Expected status 'ok'"
        assert "metrics" in data, "Missing 'metrics' field"
        assert "metric_count" in data, "Missing 'metric_count' field"

        # Check if our test metric is in the list
        metrics = data["metrics"]
        test_metric = next((m for m in metrics if m["name"] == "test_api_metric"), None)
        assert test_metric is not None, "Test metric not found in list"

        print(f"✅ PASS: Metrics list endpoint works")
        print(f"   Total metrics: {data['metric_count']}")
        print(f"   Test metric found: {test_metric['name']}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_individual_metric_endpoint():
    """Test 6: GET /api/monitoring/metrics/{metric_name}"""
    print("\n" + "="*70)
    print("TEST 6: GET /api/monitoring/metrics/{metric_name}")
    print("="*70)

    try:
        # Record multiple test metrics
        collector = get_metrics_collector()
        for i in range(5):
            metric = HealthMetric(
                name="test_individual_metric",
                value=10 * (i + 1),
                metric_type=MetricType.GAUGE,
                timestamp="",
                unit="units"
            )
            collector.record(metric)

        response = client.get("/api/monitoring/metrics/test_individual_metric?minutes=60")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data["status"] == "ok", "Expected status 'ok'"
        assert "metric_name" in data, "Missing 'metric_name'"
        assert "history" in data, "Missing 'history'"
        assert "statistics" in data, "Missing 'statistics'"
        assert "latest" in data, "Missing 'latest'"

        # Verify history
        history = data["history"]
        assert len(history) >= 5, f"Expected at least 5 data points, got {len(history)}"

        # Verify statistics
        stats = data["statistics"]
        assert "min" in stats, "Missing 'min' in stats"
        assert "max" in stats, "Missing 'max' in stats"
        assert "avg" in stats, "Missing 'avg' in stats"

        print(f"✅ PASS: Individual metric endpoint works")
        print(f"   Data points: {len(history)}")
        print(f"   Latest value: {data['latest']['value']}")
        print(f"   Min: {stats['min']}, Max: {stats['max']}, Avg: {stats['avg']:.2f}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_alerts_endpoint():
    """Test 7: GET /api/monitoring/alerts"""
    print("\n" + "="*70)
    print("TEST 7: GET /api/monitoring/alerts")
    print("="*70)

    try:
        response = client.get("/api/monitoring/alerts")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data["status"] == "ok", "Expected status 'ok'"
        assert "alerts" in data, "Missing 'alerts' field"
        assert "alert_count" in data, "Missing 'alert_count' field"

        print(f"✅ PASS: Alerts endpoint works")
        print(f"   Active alerts: {data['alert_count']}")

        # Test filtering by severity
        response_filtered = client.get("/api/monitoring/alerts?severity=critical")
        assert response_filtered.status_code == 200

        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_performance_endpoint():
    """Test 8: GET /api/monitoring/performance/{operation_name}"""
    print("\n" + "="*70)
    print("TEST 8: GET /api/monitoring/performance/{operation_name}")
    print("="*70)

    try:
        # Record some performance data
        profiler = get_metrics_collector()  # profiler is actually metrics_collector
        from backend.monitoring import get_performance_profiler
        profiler = get_performance_profiler()

        with profiler.profile("test_operation"):
            import time
            time.sleep(0.05)

        response = client.get("/api/monitoring/performance/test_operation")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data["status"] == "ok", "Expected status 'ok'"
        assert "operation_name" in data, "Missing 'operation_name'"
        assert "performance" in data, "Missing 'performance'"

        perf = data["performance"]
        assert "avg" in perf, "Missing 'avg' in performance stats"

        print(f"✅ PASS: Performance endpoint works")
        print(f"   Operation: {data['operation_name']}")
        print(f"   Avg latency: {perf['avg']:.2f}ms")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_status_summary_endpoint():
    """Test 9: GET /api/monitoring/status/summary"""
    print("\n" + "="*70)
    print("TEST 9: GET /api/monitoring/status/summary")
    print("="*70)

    try:
        response = client.get("/api/monitoring/status/summary")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data["status"] == "ok", "Expected status 'ok'"
        assert "overall_health" in data, "Missing 'overall_health'"
        assert "metrics_count" in data, "Missing 'metrics_count'"
        assert "active_alerts" in data, "Missing 'active_alerts'"
        assert "critical_alerts" in data, "Missing 'critical_alerts'"

        print(f"✅ PASS: Status summary endpoint works")
        print(f"   Overall health: {data['overall_health']}")
        print(f"   Metrics tracked: {data['metrics_count']}")
        print(f"   Active alerts: {data['active_alerts']}")
        print(f"   Critical alerts: {data['critical_alerts']}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def run_all_tests():
    """Run all tests and generate report"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  FASE 14: Monitoring REST API Endpoints Test Suite".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    tests = [
        ("Basic Health Check", test_health_check_endpoint),
        ("Initialize Monitoring", test_monitoring_initialize_endpoint),
        ("Health Check API", test_monitoring_health_endpoint),
        ("Dashboard API", test_monitoring_dashboard_endpoint),
        ("Metrics List", test_metrics_list_endpoint),
        ("Individual Metric", test_individual_metric_endpoint),
        ("Alerts API", test_alerts_endpoint),
        ("Performance API", test_performance_endpoint),
        ("Status Summary", test_status_summary_endpoint),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ ERROR in {name}: {str(e)}")
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print("="*70)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL REST API TESTS PASSED - Monitoring API ready for production!\n")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Review output above\n")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
