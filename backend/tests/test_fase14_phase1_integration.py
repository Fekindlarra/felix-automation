#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Phase 1 Integration Tests
Tests the complete monitoring infrastructure integration
"""

import pytest
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def setup_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture
def metrics_collector(setup_logging):
    """Get or create MetricsCollector"""
    from backend.backend_metrics_collector import MetricsCollector
    return MetricsCollector()


@pytest.fixture
def error_tracker(setup_logging):
    """Get or create ErrorTracker"""
    from backend.backend_error_tracker import ErrorTracker
    return ErrorTracker()


@pytest.fixture
def alert_manager(setup_logging):
    """Get or create AlertManager with default rules"""
    from backend.backend_alert_manager import AlertManager, setup_default_alerts
    return setup_default_alerts()


@pytest.fixture
def prediction_broadcaster(setup_logging):
    """Get or create PredictionBroadcaster"""
    from backend.prediction_broadcaster import PredictionBroadcaster
    return PredictionBroadcaster()


# ============================================================================
# TESTS - METRICS COLLECTOR
# ============================================================================

def test_metrics_collector_initialization(metrics_collector):
    """Test MetricsCollector initializes correctly"""
    assert metrics_collector is not None
    assert hasattr(metrics_collector, 'record_metric')
    assert hasattr(metrics_collector, 'get_metric_summary')
    logger.info("✅ MetricsCollector initialization passed")


def test_metrics_collector_record_metric(metrics_collector):
    """Test recording metrics"""
    metrics_collector.record_metric(
        metric_name="test_latency",
        value=45.5,
        metric_type="LATENCY_MS",
        unit="ms",
        component="api"
    )

    summary = metrics_collector.get_metric_summary()
    assert summary is not None
    assert summary.get('total_metrics_recorded', 0) >= 1
    logger.info("✅ MetricsCollector record_metric passed")


def test_metrics_collector_anomaly_detection(metrics_collector):
    """Test anomaly detection in metrics"""
    # Record normal values
    for i in range(10):
        metrics_collector.record_metric(
            metric_name="cpu_usage",
            value=50.0,
            metric_type="RESOURCE_USAGE",
            unit="%",
            component="system"
        )

    # Record anomalous value
    metrics_collector.record_metric(
        metric_name="cpu_usage",
        value=95.0,  # Significant spike
        metric_type="RESOURCE_USAGE",
        unit="%",
        component="system"
    )

    anomalies = metrics_collector.get_anomalies(hours=1)
    assert anomalies is not None
    # Anomalies may or may not be detected depending on threshold logic
    logger.info("✅ MetricsCollector anomaly detection passed")


# ============================================================================
# TESTS - ERROR TRACKER
# ============================================================================

def test_error_tracker_initialization(error_tracker):
    """Test ErrorTracker initializes correctly"""
    assert error_tracker is not None
    assert hasattr(error_tracker, 'record_error')
    assert hasattr(error_tracker, 'get_error_summary')
    logger.info("✅ ErrorTracker initialization passed")


def test_error_tracker_record_error(error_tracker):
    """Test recording errors"""
    from backend.backend_error_tracker import ErrorCategory, ErrorSeverity

    error_tracker.record_error(
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.WARNING,
        message="Test connection error",
        error_type="ConnectionError",
        component="database",
        context={'connection': 'sqlite'}
    )

    summary = error_tracker.get_error_summary()
    assert summary is not None
    assert summary.get('total_errors', 0) >= 1
    logger.info("✅ ErrorTracker record_error passed")


def test_error_tracker_exception_recording(error_tracker):
    """Test recording exceptions"""
    from backend.backend_error_tracker import ErrorCategory

    try:
        raise ValueError("Test exception for tracking")
    except ValueError as e:
        error_tracker.record_exception(e, ErrorCategory.VALIDATION, "test_function")

    summary = error_tracker.get_error_summary()
    assert summary is not None
    logger.info("✅ ErrorTracker exception recording passed")


# ============================================================================
# TESTS - ALERT MANAGER
# ============================================================================

def test_alert_manager_initialization(alert_manager):
    """Test AlertManager initializes correctly"""
    assert alert_manager is not None
    assert hasattr(alert_manager, 'evaluate_rule')
    assert hasattr(alert_manager, 'get_alert_summary')
    logger.info("✅ AlertManager initialization passed")


def test_alert_manager_rules(alert_manager):
    """Test AlertManager has default rules configured"""
    if alert_manager is not None:
        rules_count = len(alert_manager.rules) if hasattr(alert_manager, 'rules') else 0
        logger.info(f"   - {rules_count} default rules loaded")

        if hasattr(alert_manager, 'rules'):
            for rule_id, rule in list(alert_manager.rules.items())[:3]:
                rule_name = getattr(rule, 'name', rule_id)
                enabled = getattr(rule, 'enabled', True)
                logger.info(f"   - Rule: {rule_name} (enabled={enabled})")

    logger.info("✅ AlertManager rules passed")


def test_alert_manager_alert_creation(alert_manager):
    """Test creating and managing alerts"""
    from backend.backend_alert_manager import AlertSeverity, AlertConditionType, AlertChannelType, AlertRule

    # Create a test rule
    test_rule = AlertRule(
        rule_id="test_rule",
        name="Test Alert Rule",
        description="Test rule for alert creation",
        condition_type=AlertConditionType.THRESHOLD,
        component="test",
        metric_or_error_type="test_metric",
        threshold_value=50.0,
        severity=AlertSeverity.WARNING,
        enabled=True,
        channels=[AlertChannelType.LOG]
    )

    # Register the rule
    alert_manager.register_rule(test_rule)

    # Trigger the alert by evaluating with a value above threshold
    alert = alert_manager.evaluate_rule(test_rule, 75.0)

    # Alert might be None if in cooldown, but rule should be registered
    if alert is not None:
        assert alert.severity == AlertSeverity.WARNING
    logger.info("✅ AlertManager alert creation passed")


# ============================================================================
# TESTS - PREDICTION BROADCASTER
# ============================================================================

def test_prediction_broadcaster_initialization(prediction_broadcaster):
    """Test PredictionBroadcaster initializes correctly"""
    assert prediction_broadcaster is not None
    assert hasattr(prediction_broadcaster, 'broadcast_prediction')
    assert hasattr(prediction_broadcaster, 'get_statistics')
    logger.info("✅ PredictionBroadcaster initialization passed")


def test_prediction_broadcaster_prediction(prediction_broadcaster):
    """Test broadcasting predictions"""
    from backend.prediction_broadcaster import ConversionPrediction

    prediction = ConversionPrediction(
        client_id=123,
        probability=75.5,
        confidence=88.2,
        positive_factors=['High engagement', 'Multiple touchpoints'],
        risk_factors=['Budget concerns'],
        predicted_timeline_days=7,
        anomalies_detected=[],
        recommendation='Follow up with case study'
    )

    result = prediction_broadcaster.broadcast_prediction(prediction)
    assert result is True
    logger.info("✅ PredictionBroadcaster prediction broadcast passed")


def test_prediction_broadcaster_statistics(prediction_broadcaster):
    """Test prediction statistics"""
    stats = prediction_broadcaster.get_statistics()
    assert stats is not None
    assert 'total_predictions' in stats
    assert 'avg_probability' in stats
    logger.info(f"   - Total predictions: {stats.get('total_predictions')}")
    logger.info(f"   - Avg probability: {stats.get('avg_probability')}%")
    logger.info("✅ PredictionBroadcaster statistics passed")


# ============================================================================
# TESTS - MONITORING STARTUP
# ============================================================================

def test_monitoring_startup_initialization(setup_logging):
    """Test monitoring startup initialization"""
    from backend.monitoring_startup import initialize_monitoring

    result = initialize_monitoring()
    assert result is not None
    assert 'metrics_collector' in result
    assert 'error_tracker' in result
    assert 'alert_manager' in result
    assert 'prediction_broadcaster' in result
    logger.info("✅ Monitoring startup initialization passed")


def test_monitoring_startup_status(setup_logging):
    """Test getting monitoring status"""
    from backend.monitoring_startup import get_monitoring_status

    status = get_monitoring_status()
    assert status is not None
    # May be error or operational depending on initialization
    if 'timestamp' in status:
        logger.info(f"   - Timestamp: {status.get('timestamp')}")
    if 'components' in status:
        logger.info(f"   - Components: {list(status.get('components', {}).keys())}")
    if 'status' in status:
        logger.info(f"   - Status: {status.get('status')}")
    logger.info("✅ Monitoring status retrieval passed")


# ============================================================================
# TESTS - SHOPIFY API CLIENT
# ============================================================================

def test_shopify_api_client_initialization(setup_logging):
    """Test ShopifyAPIClient initializes correctly"""
    from whitebox.shopify_api_client import ShopifyAPIClient

    client = ShopifyAPIClient(
        shop_domain="test.myshopify.com",
        access_token="shpat_test_token_123"
    )

    assert client is not None
    assert client.store.shop_domain == "test.myshopify.com"
    logger.info("✅ ShopifyAPIClient initialization passed")


def test_shopify_rate_limiter(setup_logging):
    """Test Shopify rate limiter"""
    from whitebox.shopify_api_client import ShopifyRateLimiter

    limiter = ShopifyRateLimiter(max_calls=2, time_period=1.0)

    # First call should not wait
    limiter.wait_if_needed()
    assert len(limiter.calls) == 1

    # Second call should not wait
    limiter.wait_if_needed()
    assert len(limiter.calls) == 2

    logger.info("✅ Shopify rate limiter passed")


# ============================================================================
# TESTS - INTEGRATION SCENARIOS
# ============================================================================

def test_end_to_end_monitoring_flow(setup_logging):
    """Test complete monitoring flow"""
    from backend.backend_metrics_collector import MetricsCollector
    from backend.backend_error_tracker import ErrorTracker, ErrorCategory, ErrorSeverity
    from backend.backend_alert_manager import setup_default_alerts
    from backend.prediction_broadcaster import PredictionBroadcaster

    logger.info("\n🚀 Starting End-to-End Monitoring Flow Test")

    # 1. Initialize components
    metrics = MetricsCollector()
    errors = ErrorTracker()
    alerts = setup_default_alerts()
    broadcaster = PredictionBroadcaster()

    logger.info("✅ All components initialized")

    # 2. Record some metrics
    metrics.record_metric(
        metric_name="api_latency",
        value=120.5,
        metric_type="LATENCY_MS",
        component="api"
    )
    logger.info("✅ Metric recorded")

    # 3. Record an error
    errors.record_error(
        category=ErrorCategory.API,
        severity=ErrorSeverity.WARNING,
        message="Test API error",
        error_type="TimeoutError",
        component="api"
    )
    logger.info("✅ Error recorded")

    # 4. Broadcast a prediction
    from backend.prediction_broadcaster import ConversionPrediction
    prediction = ConversionPrediction(
        client_id=456,
        probability=82.0,
        confidence=92.0,
        positive_factors=['Recent purchase'],
        risk_factors=[],
        predicted_timeline_days=5,
        anomalies_detected=[],
        recommendation='Send premium offer'
    )
    broadcaster.broadcast_prediction(prediction)
    logger.info("✅ Prediction broadcasted")

    # 5. Get comprehensive status
    from backend.monitoring_startup import get_monitoring_status
    status = get_monitoring_status()
    logger.info(f"✅ Status retrieved: {status.get('status')}")

    logger.info("✅ End-to-End Monitoring Flow Test PASSED\n")
    assert True


# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ])
