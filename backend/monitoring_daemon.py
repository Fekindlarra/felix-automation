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
        self.memory_monitoring_interval = self.config.get('memory_monitoring_interval', 60)  # Sprint 4
        self.memory_alert_threshold = self.config.get('memory_alert_threshold', 80)  # Alert at 80% usage

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
        self._start_thread('memory_monitoring', self._memory_monitoring_loop)  # Sprint 4 optimization

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

    def _memory_monitoring_loop(self):
        """Continuous memory monitoring loop (Sprint 4 optimization)"""
        logger.info("💾 Memory monitoring loop started")

        try:
            import psutil
        except ImportError:
            logger.warning("psutil not available, skipping memory monitoring")
            return

        while self.running:
            try:
                start_time = time.time()

                # Get memory stats
                mem = psutil.virtual_memory()
                mem_percent = mem.percent
                mem_mb = mem.used / 1024 / 1024

                # Record metric
                if self.metrics_collector:
                    self.metrics_collector.record_metric(
                        metric_name="memory_usage_percent",
                        value=mem_percent,
                        metric_type="resource_usage",
                        unit="%",
                        component="system"
                    )

                # Alert if memory usage exceeds threshold
                if mem_percent > self.memory_alert_threshold:
                    alert_msg = f"💾 Memory usage CRITICAL: {mem_percent:.1f}% ({mem_mb:.0f}MB)"
                    logger.warning(alert_msg)

                    if self.alert_manager:
                        try:
                            self.alert_manager.send_alert(
                                level="CRITICAL",
                                title="Memory Usage High",
                                message=f"Memory at {mem_percent:.1f}% (threshold: {self.memory_alert_threshold}%)",
                                service="monitoring_daemon"
                            )
                        except:
                            pass

                    if self.error_tracker:
                        self.error_tracker.record_error(
                            category="system",
                            severity="critical",
                            message=alert_msg,
                            error_type="MemoryUsageHigh",
                            component="system",
                            context={'memory_percent': mem_percent, 'memory_mb': mem_mb}
                        )
                elif mem_percent > (self.memory_alert_threshold - 20):
                    # Warning level
                    logger.warning(f"⚠️  Memory usage elevated: {mem_percent:.1f}% ({mem_mb:.0f}MB)")

                elapsed = time.time() - start_time
                time.sleep(max(0, self.memory_monitoring_interval - elapsed))

            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}", exc_info=True)
                time.sleep(self.memory_monitoring_interval)

    def _phase3_checkpoint_loop(self):
        """Phase 3 checkpoint monitoring loop - runs every 2 hours during 24h execution window"""
        try:
            from backend.phase3_checkpoint_monitor import Phase3CheckpointMonitor, CheckpointDecision, HealthStatus
            from backend.phase3_rollout_engine import Phase3RolloutEngine
            from backend.rollback_manager import RollbackManager, RollbackTrigger
        except ImportError as e:
            logger.warning(f"Required modules not available for Phase 3 monitoring: {e}")
            return

        logger.info("🚀 Phase 3 checkpoint loop started")

        # Initialize monitoring system
        monitor = Phase3CheckpointMonitor()
        monitor.connect()

        rollout_engine = Phase3RolloutEngine()
        rollout_engine.connect()
        rollout_engine.load_current_phase()

        try:
            from backend.rollback_manager import RollbackManager
            import sqlite3
            from backend.config import DATABASE_PATH
            db = sqlite3.connect(DATABASE_PATH)
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            rollback_mgr = RollbackManager(db)
        except Exception as e:
            logger.warning(f"Rollback manager not available: {e}")
            rollback_mgr = None

        # Checkpoint schedule: HORA 48-72 (13 checkpoints total)
        checkpoints = [48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72]
        checkpoint_interval = 7200  # 2 hours in seconds
        checkpoint_stats = {
            'total': len(checkpoints),
            'completed': 0,
            'green': 0,
            'yellow': 0,
            'red': 0,
            'continue': 0,
            'caution': 0,
            'rollback': 0
        }

        for hora in checkpoints:
            if not self.running:
                break

            try:
                start_time = time.time()

                # Check if Phase 3 is still active
                if not monitor.is_phase3_active():
                    logger.info("Phase 3 no longer active, stopping checkpoint loop")
                    break

                logger.info(f"\n{'='*80}")
                logger.info(f"CHECKPOINT {checkpoint_stats['completed'] + 1}/{len(checkpoints)} - HORA {hora}")
                logger.info(f"{'='*80}")

                # Collect checkpoint
                checkpoint = monitor.collect_checkpoint(hora)

                if checkpoint:
                    checkpoint_stats['completed'] += 1

                    # Count by status
                    if checkpoint.status == HealthStatus.GREEN:
                        checkpoint_stats['green'] += 1
                    elif checkpoint.status == HealthStatus.YELLOW:
                        checkpoint_stats['yellow'] += 1
                    else:
                        checkpoint_stats['red'] += 1

                    # Count by decision
                    if checkpoint.decision == CheckpointDecision.CONTINUE:
                        checkpoint_stats['continue'] += 1
                    elif checkpoint.decision == CheckpointDecision.CAUTION:
                        checkpoint_stats['caution'] += 1
                    else:
                        checkpoint_stats['rollback'] += 1

                    # Log checkpoint result
                    logger.info(f"✅ HORA {hora}: {checkpoint.status.value} - Decision: {checkpoint.decision.value}")
                    logger.info(f"   ML Accuracy: {checkpoint.metrics.ml_accuracy:.1%}")
                    logger.info(f"   Error Rate: {checkpoint.metrics.error_rate:.4%}")
                    logger.info(f"   WebSocket Latency: {checkpoint.metrics.websocket_latency:.1f}ms")

                    # Evaluate phase advancement
                    try:
                        new_phase = rollout_engine.evaluate_phase_advancement(hora)
                        if new_phase:
                            logger.info(f"🚀 PHASE ADVANCEMENT: Moving to PHASE {new_phase.value} ({rollout_engine.get_rollout_percentage()}%)")
                    except Exception as e:
                        logger.debug(f"Phase advancement evaluation failed: {e}")

                    # Handle rollback if needed
                    if checkpoint.decision == CheckpointDecision.ROLLBACK:
                        logger.error(f"🚨 ROLLBACK TRIGGERED AT HORA {hora}")

                        if rollback_mgr:
                            try:
                                reason = f"Checkpoint decision: {checkpoint.decision.value}"
                                if checkpoint.reasoning:
                                    reason += f" - {checkpoint.reasoning[0]}" if checkpoint.reasoning else ""

                                import asyncio
                                asyncio.run(rollback_mgr.execute_rollback(
                                    RollbackTrigger.CRITICAL_ALERT,
                                    reason
                                ))
                                logger.error("✅ Rollback completed successfully")
                            except Exception as e:
                                logger.error(f"Error executing rollback: {e}")

                        # Stop checkpoint loop on rollback
                        break

                    # Broadcast checkpoint event
                    if self.alert_manager:
                        try:
                            event_data = {
                                'hora': hora,
                                'status': checkpoint.status.value,
                                'decision': checkpoint.decision.value,
                                'health_score': checkpoint.health_score,
                                'metrics': {
                                    'ml_accuracy': checkpoint.metrics.ml_accuracy,
                                    'error_rate': checkpoint.metrics.error_rate,
                                    'websocket_latency': checkpoint.metrics.websocket_latency,
                                    'predictions_hour': checkpoint.metrics.predictions_hour,
                                    'personalization_active': checkpoint.metrics.personalization_active,
                                    'active_tests': checkpoint.metrics.active_tests
                                },
                                'timestamp': datetime.utcnow().isoformat()
                            }
                            self.alert_manager.send_alert(
                                level="INFO",
                                title=f"Phase 3 Checkpoint HORA {hora}",
                                message=f"{checkpoint.status.value} - {checkpoint.decision.value}",
                                service="phase3_checkpoint",
                                metadata=event_data
                            )
                        except Exception as e:
                            logger.debug(f"Could not send checkpoint alert: {e}")

                else:
                    logger.error(f"❌ Failed to collect checkpoint for HORA {hora}")

                # Wait before next checkpoint
                if hora < checkpoints[-1]:
                    elapsed = time.time() - start_time
                    wait_time = max(0, checkpoint_interval - elapsed)
                    logger.info(f"⏰ Waiting {wait_time/3600:.1f}h until next checkpoint...")
                    time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Error in Phase 3 checkpoint loop at HORA {hora}: {e}", exc_info=True)
                time.sleep(checkpoint_interval)

        # Print final summary
        logger.info("\n" + "█"*80)
        logger.info("█  PHASE 3 CHECKPOINT MONITORING SUMMARY")
        logger.info("█"*80)
        logger.info(f"\nTotal Checkpoints: {checkpoint_stats['total']}")
        logger.info(f"Completed: {checkpoint_stats['completed']}/{checkpoint_stats['total']}")
        logger.info(f"\nHealth Status:")
        logger.info(f"  🟢 GREEN (6/6):  {checkpoint_stats['green']}")
        logger.info(f"  🟡 YELLOW (5/6): {checkpoint_stats['yellow']}")
        logger.info(f"  🔴 RED (<5/6):   {checkpoint_stats['red']}")
        logger.info(f"\nDecisions:")
        logger.info(f"  ✅ CONTINUE:    {checkpoint_stats['continue']}")
        logger.info(f"  ⚠️  CAUTION:     {checkpoint_stats['caution']}")
        logger.info(f"  🚨 ROLLBACK:    {checkpoint_stats['rollback']}")

        # Final status
        if checkpoint_stats['rollback'] > 0:
            logger.error(f"\n❌ PHASE 3 EXECUTION FAILED - ROLLBACK TRIGGERED")
            final_status = "NO-GO"
        elif checkpoint_stats['red'] > 0:
            logger.warning(f"\n⚠️  PHASE 3 EXECUTION COMPLETED - CAUTION STATUS")
            final_status = "CAUTION"
        elif checkpoint_stats['green'] >= 10:
            logger.info(f"\n✅ PHASE 3 EXECUTION SUCCESSFUL - GO STATUS")
            final_status = "GO"
        else:
            logger.warning(f"\n⚠️  PHASE 3 EXECUTION COMPLETED - MARGINAL STATUS")
            final_status = "CAUTION"

        logger.info(f"Final Status: {final_status}")
        logger.info("█"*80 + "\n")

        # Cleanup
        try:
            monitor.close()
            rollout_engine.close()
            if rollback_mgr and hasattr(rollback_mgr, 'db'):
                rollback_mgr.db.close()
        except:
            pass

        logger.info("✅ Phase 3 checkpoint loop ended")

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
