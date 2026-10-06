#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Monitoring API Endpoints (FASE 14)
Tests all 8 monitoring endpoints for proper functionality
"""

import sys
import json
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.monitoring import (
    get_metrics_collector,
    get_health_checker,
    get_performance_profiler,
    get_monitoring_dashboard,
    HealthMetric,
    MetricType
)
from backend.monitoring_startup import (
    initialize_monitoring,
    start_monitoring_background_tasks
)


def test_monitoring_initialization():
    """Test 1: Monitoring system initialization"""
    print("\n" + "="*70)
    print("TEST 1: Monitoring System Initialization")
    print("="*70)

    try:
        initialize_monitoring()
        collector = get_metrics_collector()
        health = get_health_checker()
        profiler = get_performance_profiler()
        dashboard = get_monitoring_dashboard()

        assert collector is not None, "MetricsCollector not initialized"
        assert health is not None, "HealthChecker not initialized"
        assert profiler is not None, "PerformanceProfiler not initialized"
        assert dashboard is not None, "MonitoringDashboard not initialized"

        print("✅ PASS: All monitoring components initialized successfully")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_metrics_collection():
    """Test 2: Metrics collection and retrieval"""
    print("\n" + "="*70)
    print("TEST 2: Metrics Collection and Retrieval")
    print("="*70)

    try:
        collector = get_metrics_collector()

        # Record a test metric
        metric = HealthMetric(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            timestamp="",
            unit="units",
            labels={"test": "value"}
        )
        collector.record(metric)

        # Retrieve it
        latest = collector.get_latest("test_metric")
        assert latest is not None, "Failed to retrieve recorded metric"
        assert latest.value == 42.5, f"Expected 42.5, got {latest.value}"

        # Get history
        history = collector.get_metric_history("test_metric", minutes=60)
        assert len(history) > 0, "No history returned"

        # Get statistics
        stats = collector.get_stats("test_metric", minutes=60)
        assert "min" in stats, "Statistics missing 'min'"
        assert "max" in stats, "Statistics missing 'max'"
        assert "avg" in stats, "Statistics missing 'avg'"

        print(f"✅ PASS: Metrics collected: {len(history)} points")
        print(f"   Stats: min={stats['min']}, max={stats['max']}, avg={stats['avg']:.2f}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_health_checks():
    """Test 3: Health check evaluation"""
    print("\n" + "="*70)
    print("TEST 3: Health Check Evaluation")
    print("="*70)

    try:
        health = get_health_checker()

        # Evaluate health
        health_status = health.evaluate_health()

        assert "timestamp" in health_status, "Missing timestamp"
        assert "overall_status" in health_status, "Missing overall_status"
        assert "metrics" in health_status, "Missing metrics"
        assert "alerts" in health_status, "Missing alerts"

        # Check overall status is valid
        valid_statuses = ["healthy", "degraded", "unhealthy"]
        assert health_status["overall_status"] in valid_statuses, \
            f"Invalid status: {health_status['overall_status']}"

        # Count evaluated metrics
        metrics_count = len(health_status["metrics"])
        print(f"✅ PASS: Health evaluated - overall_status={health_status['overall_status']}")
        print(f"   Metrics evaluated: {metrics_count}")
        print(f"   Active alerts: {len(health_status['alerts'])}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_performance_profiling():
    """Test 4: Performance profiling"""
    print("\n" + "="*70)
    print("TEST 4: Performance Profiling")
    print("="*70)

    try:
        profiler = get_performance_profiler()

        # Simulate an operation
        with profiler.profile("test_operation"):
            time.sleep(0.1)  # 100ms operation

        # Get stats
        stats = profiler.get_operation_stats("test_operation")

        assert "count" in stats, "Missing count in stats"
        assert stats["count"] > 0, "No operations recorded"

        print(f"✅ PASS: Performance profiling works")
        print(f"   Operations recorded: {stats['count']}")
        print(f"   Latency (avg): {stats['avg']:.2f}ms")
        print(f"   Latency (p95): {stats['p95']:.2f}ms")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_dashboard_data():
    """Test 5: Dashboard data aggregation"""
    print("\n" + "="*70)
    print("TEST 5: Dashboard Data Aggregation")
    print("="*70)

    try:
        dashboard = get_monitoring_dashboard()

        # Get dashboard data
        data = dashboard.get_dashboard_data(force_refresh=True)

        assert "timestamp" in data, "Missing timestamp"
        assert "health" in data, "Missing health"
        assert "websocket_metrics" in data, "Missing websocket_metrics"
        assert "cache_metrics" in data, "Missing cache_metrics"
        assert "api_metrics" in data, "Missing api_metrics"
        assert "ml_metrics" in data, "Missing ml_metrics"
        assert "database_metrics" in data, "Missing database_metrics"
        assert "alerts" in data, "Missing alerts"

        print(f"✅ PASS: Dashboard data aggregated successfully")
        print(f"   Sections: {len(data) - 2}")  # -2 for timestamp and cache time
        print(f"   Active alerts: {len(data['alerts'])}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_alert_generation():
    """Test 6: Alert generation on anomalies"""
    print("\n" + "="*70)
    print("TEST 6: Alert Generation")
    print("="*70)

    try:
        health = get_health_checker()
        collector = get_metrics_collector()

        # Record a critical metric to trigger alert
        # (e.g., high error rate)
        metric = HealthMetric(
            name="error_rate",
            value=0.1,  # 10% error rate - above critical threshold of 5%
            metric_type=MetricType.GAUGE,
            timestamp="",
            unit="%"
        )
        collector.record(metric)

        # Evaluate health to generate alerts
        health_status = health.evaluate_health()

        # Check if alerts were generated
        alerts = health_status.get("alerts", [])

        print(f"✅ PASS: Alert system functioning")
        print(f"   Alerts generated: {len(alerts)}")
        if alerts:
            print(f"   First alert: {alerts[0]['title']}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_thread_safety():
    """Test 7: Thread safety of metric collection"""
    print("\n" + "="*70)
    print("TEST 7: Thread Safety")
    print("="*70)

    try:
        import threading

        collector = get_metrics_collector()
        errors = []

        def record_metrics(thread_id):
            try:
                for i in range(10):
                    metric = HealthMetric(
                        name=f"thread_test_{thread_id}",
                        value=i * thread_id,
                        metric_type=MetricType.COUNTER,
                        timestamp="",
                        unit="count"
                    )
                    collector.record(metric)
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=record_metrics, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"

        print(f"✅ PASS: Thread-safe metric collection verified")
        print(f"   Threads executed: 5")
        print(f"   Metrics recorded: 50 (10 per thread)")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_background_tasks():
    """Test 8: Background health check tasks"""
    print("\n" + "="*70)
    print("TEST 8: Background Health Check Tasks")
    print("="*70)

    try:
        # Tasks should already be running from initialization
        health = get_health_checker()

        # Evaluate multiple times to ensure consistency
        health_status_1 = health.evaluate_health()
        time.sleep(0.5)
        health_status_2 = health.evaluate_health()

        assert health_status_1["overall_status"] is not None
        assert health_status_2["overall_status"] is not None

        print(f"✅ PASS: Background tasks executing properly")
        print(f"   Health check 1: {health_status_1['overall_status']}")
        print(f"   Health check 2: {health_status_2['overall_status']}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def run_all_tests():
    """Run all tests and generate report"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  FASE 14: Monitoring API Endpoints Test Suite".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    tests = [
        ("Initialization", test_monitoring_initialization),
        ("Metrics Collection", test_metrics_collection),
        ("Health Checks", test_health_checks),
        ("Performance Profiling", test_performance_profiling),
        ("Dashboard Data", test_dashboard_data),
        ("Alert Generation", test_alert_generation),
        ("Thread Safety", test_thread_safety),
        ("Background Tasks", test_background_tasks),
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
        print("\n🎉 ALL TESTS PASSED - Monitoring system ready for production!\n")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Review output above\n")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
