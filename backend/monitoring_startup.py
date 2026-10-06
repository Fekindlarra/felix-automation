"""
Monitoring Initialization - FASE 14 Production Infrastructure
Setup Phase 1 monitoring infrastructure at application startup
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Global instances - initialized once at startup
_monitoring_daemon = None
_metrics_collector = None
_error_tracker = None
_alert_manager = None
_prediction_broadcaster = None


def get_monitoring_daemon():
    """Get or create the monitoring daemon singleton"""
    global _monitoring_daemon
    if _monitoring_daemon is None:
        try:
            from backend.monitoring_daemon import MonitoringDaemon
            _monitoring_daemon = MonitoringDaemon()
        except Exception as e:
            logger.error(f"Failed to initialize MonitoringDaemon: {e}")
    return _monitoring_daemon


def get_metrics_collector():
    """Get or create metrics collector singleton"""
    global _metrics_collector
    if _metrics_collector is None:
        try:
            from backend.backend_metrics_collector import MetricsCollector
            _metrics_collector = MetricsCollector()
        except Exception as e:
            logger.error(f"Failed to initialize MetricsCollector: {e}")
    return _metrics_collector


def get_error_tracker():
    """Get or create error tracker singleton"""
    global _error_tracker
    if _error_tracker is None:
        try:
            from backend.backend_error_tracker import ErrorTracker
            _error_tracker = ErrorTracker()
        except Exception as e:
            logger.error(f"Failed to initialize ErrorTracker: {e}")
    return _error_tracker


def get_alert_manager():
    """Get or create alert manager singleton"""
    global _alert_manager
    if _alert_manager is None:
        try:
            from backend.backend_alert_manager import AlertManager, setup_default_alerts
            _alert_manager = setup_default_alerts()
        except Exception as e:
            logger.error(f"Failed to initialize AlertManager: {e}")
    return _alert_manager


def get_prediction_broadcaster():
    """Get or create prediction broadcaster singleton"""
    global _prediction_broadcaster
    if _prediction_broadcaster is None:
        try:
            from backend.prediction_broadcaster import PredictionBroadcaster
            _prediction_broadcaster = PredictionBroadcaster()
        except Exception as e:
            logger.error(f"Failed to initialize PredictionBroadcaster: {e}")
    return _prediction_broadcaster


def initialize_monitoring() -> Dict:
    """
    Initialize all Phase 1 monitoring infrastructure components.
    Call this once in your main application entry point.

    Returns:
        Dictionary with all initialized monitoring components

    Example:
        from backend.monitoring_startup import initialize_monitoring

        if __name__ == "__main__":
            monitoring = initialize_monitoring()
            # ... rest of your application code
    """
    try:
        logger.info("🚀 FASE 14 Phase 1 Monitoring System - Initializing...")

        # Initialize all core components
        metrics_collector = get_metrics_collector()
        error_tracker = get_error_tracker()
        alert_manager = get_alert_manager()
        prediction_broadcaster = get_prediction_broadcaster()

        logger.info("✅ Phase 1 Monitoring Components Initialized:")
        logger.info(f"   - MetricsCollector: {type(metrics_collector).__name__}")
        logger.info(f"   - ErrorTracker: {type(error_tracker).__name__}")
        logger.info(f"   - AlertManager: {type(alert_manager).__name__}")
        logger.info(f"   - PredictionBroadcaster: {type(prediction_broadcaster).__name__}")

        return {
            'metrics_collector': metrics_collector,
            'error_tracker': error_tracker,
            'alert_manager': alert_manager,
            'prediction_broadcaster': prediction_broadcaster
        }

    except Exception as e:
        logger.error(f"❌ Failed to initialize monitoring: {e}", exc_info=True)
        logger.warning("⚠️  Monitoring disabled - continuing without monitoring infrastructure")
        return None


def start_monitoring_background_tasks() -> Optional[object]:
    """
    Start the Phase 1 Monitoring Daemon in background thread.
    Call this after initialize_monitoring() to start real-time monitoring.

    Returns:
        The monitoring daemon thread, or None on failure
    """
    try:
        import threading

        daemon = get_monitoring_daemon()

        if daemon is None:
            logger.warning("⚠️  Monitoring daemon not available, skipping background tasks")
            return None

        def run_daemon():
            """Run the monitoring daemon"""
            try:
                daemon.start()
            except Exception as e:
                logger.error(f"❌ Monitoring daemon error: {e}", exc_info=True)

        # Start daemon in background thread
        thread = threading.Thread(target=run_daemon, daemon=True, name="MonitoringDaemon")
        thread.start()

        logger.info("✅ Monitoring Daemon started in background thread")
        return thread

    except Exception as e:
        logger.error(f"⚠️  Failed to start monitoring background tasks: {e}", exc_info=True)
        return None


def get_monitoring_status() -> Dict:
    """
    Get current monitoring status from all Phase 1 components.
    Returns comprehensive status report for dashboards.
    """
    try:
        status = {
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'components': {}
        }

        # Get metrics collector status
        metrics = get_metrics_collector()
        if metrics:
            stats = metrics.get_metric_summary()
            status['components']['metrics'] = {
                'status': 'healthy',
                'total_metrics': stats.get('total_metrics_recorded', 0),
                'anomalies_detected': stats.get('anomalies_in_period', 0)
            }

        # Get error tracker status
        errors = get_error_tracker()
        if errors:
            summary = errors.get_error_summary()
            status['components']['errors'] = {
                'status': 'healthy',
                'total_errors': summary.get('total_count', 0),
                'critical_errors': summary.get('critical_count', 0),
                'error_rate': summary.get('error_rate', 0)
            }

        # Get alert manager status
        alerts = get_alert_manager()
        if alerts:
            active_alerts = alerts.get_active_alerts() if hasattr(alerts, 'get_active_alerts') else []
            status['components']['alerts'] = {
                'status': 'healthy',
                'active_alerts': len(active_alerts),
                'total_rules': len(alerts.rules) if hasattr(alerts, 'rules') else 0,
                'enabled_rules': len([r for r in alerts.rules.values() if r.enabled]) if hasattr(alerts, 'rules') else 0
            }

        # Get prediction broadcaster status
        broadcaster = get_prediction_broadcaster()
        if broadcaster:
            stats = broadcaster.get_statistics()
            status['components']['predictions'] = {
                'status': 'healthy',
                'total_predictions': stats.get('total_predictions', 0),
                'broadcast_count': stats.get('broadcast_count', 0),
                'avg_probability': stats.get('avg_probability', 0)
            }

        status['status'] = 'operational'
        return status

    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}", exc_info=True)
        return {
            'status': 'error',
            'message': f'Failed to get monitoring status: {e}',
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
