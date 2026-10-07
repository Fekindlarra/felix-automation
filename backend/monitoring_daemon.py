"""
Monitoring Daemon - FASE 14 Production Monitoring
Background process that continuously monitors system health and metrics
"""

import logging
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime
import signal
import sys

# Import monitoring components
try:
    from backend_health_check import HealthChecker, HealthStatus
    from backend_error_tracker import ErrorTracker, ErrorCategory, ErrorSeverity, log_exception
    from backend_metrics_collector import MetricsCollector, MetricType, record_latency, record_error_rate
    from backend_alert_manager import AlertManager, AlertRuleLibrary, setup_default_alerts
except ImportError:
    # Graceful fallback if modules not available
    HealthChecker = None
    ErrorTracker = None
    MetricsCollector = None
    AlertManager = None

logger = logging.getLogger(__name__)


class MonitoringDaemon:
    """Background monitoring daemon"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize monitoring daemon

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.running = False
        self.threads: Dict[str, threading.Thread] = {}

        # Initialize components
        self.health_checker = HealthChecker(config=self.config) if HealthChecker else None
        self.error_tracker = ErrorTracker(config=self.config) if ErrorTracker else None
        self.metrics_collector = MetricsCollector(config=self.config) if MetricsCollector else None
        self.alert_manager = setup_default_alerts() if AlertManager else None

        # Configuration
        self.health_check_interval = self.config.get('health_check_interval', 30)  # seconds
        self.metrics_collection_interval = self.config.get('metrics_collection_interval', 10)
        self.error_flush_interval = self.config.get('error_flush_interval', 60)
        self.metrics_flush_interval = self.config.get('metrics_flush_interval', 300)
        self.alert_evaluation_interval = self.config.get('alert_evaluation_interval', 30)

    def start(self):
        """Start monitoring daemon"""
        logger.info("Starting monitoring daemon...")
        self.running = True

        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Start monitoring threads
        self._start_thread('health_checks', self._health_check_loop)
        self._start_thread('metrics', self._metrics_collection_loop)
        self._start_thread('error_tracking', self._error_tracking_loop)
        self._start_thread('alert_evaluation', self._alert_evaluation_loop)

        # Start Phase 3 checkpoint monitoring (FASE 15 Phase 3)
        self._start_thread('phase3_checkpoints', self._phase3_checkpoint_loop)

        logger.info("Monitoring daemon started successfully")

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop monitoring daemon"""
        logger.info("Stopping monitoring daemon...")
        self.running = False

        # Wait for threads
        for name, thread in self.threads.items():
            if thread.is_alive():
                logger.info(f"Waiting for {name} thread...")
                thread.join(timeout=5)

        # Final flush
        if self.error_tracker:
            self.error_tracker.flush_to_database()
        if self.metrics_collector:
            self.metrics_collector.flush_to_database()

        logger.info("Monitoring daemon stopped")

    def _start_thread(self, name: str, target, daemon: bool = True):
        """Start a monitoring thread"""
        thread = threading.Thread(target=target, name=f"Monitor-{name}", daemon=daemon)
        thread.start()
        self.threads[name] = thread
        logger.info(f"Started {name} thread")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)

    def _health_check_loop(self):
        """Continuous health checking loop"""
        if not self.health_checker:
            return

        logger.info("Health check loop started")

        while self.running:
            try:
                start_time = time.time()

                # Run all health checks
                health = self.health_checker.check_all()

                # Record metrics from health check
                if self.metrics_collector:
                    # Component health statuses
                    for check in health.checks:
                        if check.component not in ['websocket', 'memory', 'disk']:
                            self.metrics_collector.record_metric(
                                metric_name=f"{check.component}_response_time",
                                value=check.response_time_ms,
                                metric_type=MetricType.LATENCY_MS,
                                unit="ms",
                                component=check.component
                            )

                # Record error if health is not healthy
                if health.status != HealthStatus.HEALTHY and self.error_tracker:
                    critical_components = [c for c in health.checks if c.status == HealthStatus.CRITICAL]
                    if critical_components:
                        for comp in critical_components:
                            self.error_tracker.record_error(
                                category=ErrorCategory.UNKNOWN,
                                severity=ErrorSeverity.CRITICAL,
                                message=f"Component unhealthy: {comp.message}",
                                error_type="HealthCheckFailure",
                                component=comp.component,
                                context={'status': comp.status.value}
                            )

                elapsed = time.time() - start_time
                logger.debug(f"Health check completed in {elapsed:.2f}s: {health.status.value}")

                time.sleep(max(0, self.health_check_interval - elapsed))

            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)
                if self.error_tracker:
                    self.error_tracker.record_exception(e, ErrorCategory.UNKNOWN, "health_check_loop")
                time.sleep(self.health_check_interval)

    def _metrics_collection_loop(self):
        """Continuous metrics collection loop"""
        if not self.metrics_collector:
            return

        logger.info("Metrics collection loop started")

        while self.running:
            try:
                start_time = time.time()

                # Collect system metrics
                self._collect_system_metrics()

                # Collect API metrics (would be populated by actual API middleware)
                self._collect_api_metrics()

                # Collect database metrics
                self._collect_database_metrics()

                elapsed = time.time() - start_time
                logger.debug(f"Metrics collection completed in {elapsed:.2f}s")

                time.sleep(max(0, self.metrics_collection_interval - elapsed))

            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}", exc_info=True)
                if self.error_tracker:
                    self.error_tracker.record_exception(e, ErrorCategory.UNKNOWN, "metrics_collection_loop")
                time.sleep(self.metrics_collection_interval)

    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            import psutil
            import shutil

            # Memory
            mem = psutil.virtual_memory()
            self.metrics_collector.record_metric(
                metric_name="memory_usage",
                value=mem.percent,
                metric_type=MetricType.RESOURCE_USAGE,
                unit="%",
                component="system"
            )

            # Disk
            disk = shutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            self.metrics_collector.record_metric(
                metric_name="disk_usage",
                value=disk_percent,
                metric_type=MetricType.RESOURCE_USAGE,
                unit="%",
                component="system"
            )

        except ImportError:
            logger.debug("psutil not available, skipping system metrics")
        except Exception as e:
            logger.warning(f"Error collecting system metrics: {e}")

    def _collect_api_metrics(self):
        """Collect API metrics"""
        # These would normally be populated by middleware
        # This is a placeholder for demonstration
        pass

    def _collect_database_metrics(self):
        """Collect database metrics"""
        # These would normally be populated by database wrappers
        # This is a placeholder for demonstration
        pass

    def _error_tracking_loop(self):
        """Continuous error tracking loop"""
        if not self.error_tracker:
            return

        logger.info("Error tracking loop started")

        while self.running:
            try:
                start_time = time.time()

                # Periodically flush errors
                flushed = self.error_tracker.flush_to_database()
                if flushed > 0:
                    logger.debug(f"Flushed {flushed} errors")

                # Get error summary and log concerning patterns
                summary = self.error_tracker.get_error_summary(hours=1)
                if summary['critical_count'] > 0:
                    logger.warning(f"Critical errors detected: {summary['critical_count']}")

                # Get recurring errors
                aggregates = self.error_tracker.get_aggregates(hours=1)
                for agg in aggregates[:5]:  # Log top 5
                    if agg.trend == "increasing":
                        logger.warning(
                            f"Increasing error trend: {agg.error_type} in {agg.component} "
                            f"({agg.count} in last hour, trend: {agg.trend})"
                        )

                elapsed = time.time() - start_time
                time.sleep(max(0, self.error_flush_interval - elapsed))

            except Exception as e:
                logger.error(f"Error in error tracking loop: {e}", exc_info=True)
                time.sleep(self.error_flush_interval)

    def _alert_evaluation_loop(self):
        """Continuous alert evaluation loop"""
        if not self.alert_manager or not self.metrics_collector:
            return

        logger.info("Alert evaluation loop started")

        while self.running:
            try:
                start_time = time.time()

                # Evaluate all enabled rules
                for rule_id, rule in self.alert_manager.rules.items():
                    if not rule.enabled:
                        continue

                    try:
                        # Get latest metric value
                        agg = self.metrics_collector.get_aggregate(
                            rule.metric_or_error_type,
                            rule.component,
                            seconds=rule.window_seconds
                        )

                        if agg:
                            # Evaluate rule
                            current_value = agg.avg_value
                            alert = self.alert_manager.evaluate_rule(rule, current_value)

                            if alert:
                                logger.warning(f"Alert triggered: {alert.rule_name}")

                    except Exception as e:
                        logger.error(f"Error evaluating rule {rule_id}: {e}")

                # Periodically flush metrics
                flushed = self.metrics_collector.flush_to_database()
                if flushed > 0:
                    logger.debug(f"Flushed {flushed} metrics")

                elapsed = time.time() - start_time
                time.sleep(max(0, self.alert_evaluation_interval - elapsed))

            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}", exc_info=True)
                time.sleep(self.alert_evaluation_interval)

    def _phase3_checkpoint_loop(self):
        """Phase 3 checkpoint monitoring loop - runs every 2 hours during 24h execution window"""
        try:
            from backend.rollback_manager import RollbackManager, RollbackTrigger
            from agents.personalization_engine import PersonalizationEngine
        except ImportError as e:
            logger.warning(f"Required modules not available for Phase 3 monitoring: {e}")
            return

        logger.info("Phase 3 checkpoint loop started")

        # Try to import database connection for rollback manager
        try:
            import sqlite3
            from backend.config import DATABASE_PATH
            db = sqlite3.connect(DATABASE_PATH)
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
        except Exception as e:
            logger.error(f"Failed to connect to database for Phase 3 monitoring: {e}")
            return

        rollback_mgr = RollbackManager(db)
        personalization_engine = PersonalizationEngine(db)

        checkpoint_number = 48  # HORA 48 is first checkpoint
        checkpoint_interval = 7200  # 2 hours in seconds
        successful_checkpoints = 0  # Track consecutive healthy checkpoints

        # Phase advancement thresholds
        phase_advance_checkpoints = {
            1: 2,  # Advance from Phase 1 to Phase 2 after 2 healthy checkpoints (~4 hours)
            2: 2   # Advance from Phase 2 to Phase 3 after 2 healthy checkpoints (~4 hours)
        }

        while self.running:
            try:
                start_time = time.time()

                # Check if Phase 3 is active
                try:
                    cursor = db.cursor()
                    cursor.execute("""
                        SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE'
                    """)
                    result = cursor.fetchone()
                    is_active = result[0] == 'true' if result else False

                    if not is_active:
                        logger.debug("Phase 3 not active, skipping checkpoint")
                        time.sleep(checkpoint_interval)
                        continue
                except Exception as e:
                    logger.error(f"Error checking Phase 3 status: {e}")
                    time.sleep(checkpoint_interval)
                    continue

                # Collect health metrics and make decision
                decision = rollback_mgr.check_health_and_decide()

                # Save checkpoint
                rollback_mgr.save_checkpoint(checkpoint_number)

                # Log checkpoint decision
                healthy_count = decision.get('healthy_metric_count', 0)
                decision_status = decision.get('decision', 'UNKNOWN')

                logger.info(
                    f"✅ HORA {checkpoint_number}: {healthy_count}/6 GREEN - Decision: {decision_status}"
                )

                # Handle rollback if needed
                if decision.get('rollback_needed', False):
                    logger.error(f"🚨 ROLLBACK TRIGGERED at HORA {checkpoint_number}: {decision.get('reason', 'unknown')}")

                    trigger_type = RollbackTrigger.CRITICAL_ALERT
                    if decision.get('reason'):
                        # Map reason to trigger type
                        reason = decision['reason']
                        if 'Error rate' in reason:
                            trigger_type = RollbackTrigger.ERROR_RATE_HIGH
                        elif 'latency' in reason.lower():
                            trigger_type = RollbackTrigger.LATENCY_SPIKE
                        elif 'accuracy' in reason.lower():
                            trigger_type = RollbackTrigger.ML_ACCURACY_LOW
                        elif 'circuit' in reason.lower():
                            trigger_type = RollbackTrigger.CIRCUIT_BREAKER_OPEN

                    # Execute async rollback
                    import asyncio
                    try:
                        asyncio.run(rollback_mgr.execute_rollback(
                            trigger_type,
                            decision.get('reason', 'Automatic rollback triggered')
                        ))
                        # Stop checkpoint monitoring on rollback
                        break
                    except Exception as e:
                        logger.error(f"Error executing rollback: {e}")

                # Track successful checkpoints for phase advancement
                elif decision_status == 'CONTINUE':
                    successful_checkpoints += 1

                    # Attempt phase advancement based on consecutive healthy checkpoints
                    try:
                        # Get current personalization status
                        active_tests = []
                        cursor.execute("""
                            SELECT DISTINCT test_id FROM personalization_variants
                            WHERE rollout_phase IS NOT NULL
                        """)
                        for row in cursor.fetchall():
                            active_tests.append(row[0])

                        # Advance phases if thresholds met
                        for test_id in active_tests:
                            stats = personalization_engine.get_rollout_stats(test_id)
                            current_phase = stats.get('current_phase', 1)

                            # Check if we should advance to next phase
                            if current_phase < 3 and successful_checkpoints >= phase_advance_checkpoints[current_phase]:
                                next_phase = current_phase + 1
                                if personalization_engine.advance_rollout_phase(test_id, next_phase):
                                    logger.info(f"🚀 Test {test_id} phase advanced to {next_phase} at HORA {checkpoint_number}")
                                    successful_checkpoints = 0  # Reset counter

                    except Exception as e:
                        logger.warning(f"Error during phase advancement check: {e}")

                else:
                    # CAUTION status - reset successful checkpoint counter
                    successful_checkpoints = 0

                # Broadcast checkpoint event
                if self.alert_manager:
                    try:
                        event_data = {
                            'hora': checkpoint_number,
                            'healthy_metrics': healthy_count,
                            'decision': decision_status,
                            'metrics': decision.get('metrics', {}),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        self.alert_manager.send_alert(
                            level="INFO",
                            title=f"Phase 3 Checkpoint HORA {checkpoint_number}",
                            message=f"{healthy_count}/6 metrics GREEN - {decision_status}",
                            service="phase3_checkpoint",
                            metadata=event_data
                        )
                    except Exception as e:
                        logger.debug(f"Could not send checkpoint alert: {e}")

                # Advance checkpoint number (every 2 hours)
                checkpoint_number += 2
                if checkpoint_number > 72:
                    logger.info("✅ Phase 3 execution window completed (HORA 48-72)")
                    # Final decision
                    if healthy_count >= 5:
                        logger.info("🎉 Phase 3 DECISION: SUCCESS - All checkpoints healthy")
                    else:
                        logger.warning("⚠️  Phase 3 DECISION: CAUTION - Continue monitoring")
                    self.running = False  # End Phase 3 monitoring
                    break

                elapsed = time.time() - start_time
                time.sleep(max(0, checkpoint_interval - elapsed))

            except Exception as e:
                logger.error(f"Error in Phase 3 checkpoint loop: {e}", exc_info=True)
                time.sleep(checkpoint_interval)

        try:
            db.close()
        except:
            pass
        logger.info("Phase 3 checkpoint loop ended")

    def get_status(self) -> Dict[str, Any]:
        """Get daemon status"""
        status = {
            'running': self.running,
            'timestamp': datetime.utcnow().isoformat(),
            'threads': list(self.threads.keys()),
            'active_threads': [name for name, thread in self.threads.items() if thread.is_alive()],
        }

        if self.health_checker:
            try:
                health = self.health_checker.check_all()
                status['health'] = health.to_dict()
            except:
                pass

        if self.alert_manager:
            summary = self.alert_manager.get_alert_summary(hours=1)
            status['alerts'] = summary

        if self.error_tracker:
            summary = self.error_tracker.get_error_summary(hours=1)
            status['errors'] = summary

        return status


def setup_logging(log_level=logging.INFO):
    """Setup logging for daemon"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('monitoring_daemon.log'),
            logging.StreamHandler()
        ]
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FASE 14 Monitoring Daemon")
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--config', default=None, help='Path to config file')
    parser.add_argument('--status', action='store_true', help='Show daemon status and exit')

    args = parser.parse_args()

    setup_logging(getattr(logging, args.log_level))

    # Load config if provided
    config = {}
    if args.config:
        try:
            import yaml
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    # Create daemon
    daemon = MonitoringDaemon(config)

    if args.status:
        # Show status and exit
        status = daemon.get_status()
        import json
        print(json.dumps(status, indent=2))
    else:
        # Start daemon
        try:
            daemon.start()
        except KeyboardInterrupt:
            daemon.stop()
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            daemon.stop()
            sys.exit(1)
