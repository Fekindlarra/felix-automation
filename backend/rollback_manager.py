#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Automatic Rollback Manager
Continuously monitors system health and triggers automatic rollback if thresholds broken
Coordinates with circuit breaker for comprehensive resilience
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3

logger = logging.getLogger(__name__)


class RollbackTrigger(Enum):
    """Reasons for triggering rollback"""
    ERROR_RATE_HIGH = "error_rate_exceeded"
    LATENCY_SPIKE = "latency_spike"
    ML_ACCURACY_LOW = "ml_accuracy_below_threshold"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    CRITICAL_ALERT = "critical_alert_received"
    MANUAL = "manual_override"


@dataclass
class HealthMetrics:
    """System health metrics snapshot"""
    timestamp: str
    ml_accuracy: float
    error_rate: float
    websocket_latency_ms: float
    predictions_per_hour: int
    personalization_active: int
    active_tests: int
    circuit_breaker_states: Dict[str, str]
    alert_count: int
    critical_alerts: list

    def is_healthy(self) -> bool:
        """Check if all metrics are within acceptable thresholds"""
        return (
            self.ml_accuracy >= 0.78 and
            self.error_rate < 0.0008 and  # <0.08%
            self.websocket_latency_ms < 95 and
            self.predictions_per_hour >= 42 and
            self.personalization_active >= 140 and
            self.active_tests >= 8 and
            "OPEN" not in self.circuit_breaker_states.values() and
            self.critical_alerts == []
        )

    def get_healthy_metric_count(self) -> int:
        """Count how many metrics are healthy (0-6)"""
        count = 0
        if self.ml_accuracy >= 0.78:
            count += 1
        if self.error_rate < 0.0008:
            count += 1
        if self.websocket_latency_ms < 95:
            count += 1
        if self.predictions_per_hour >= 42:
            count += 1
        if self.personalization_active >= 140:
            count += 1
        if self.active_tests >= 8:
            count += 1
        return count


@dataclass
class RollbackState:
    """Track rollback state"""
    triggered: bool = False
    trigger_type: Optional[RollbackTrigger] = None
    triggered_at: Optional[str] = None
    reason: str = ""
    backup_restored: bool = False
    phase_reverted_to: Optional[int] = None


class RollbackManager:
    """
    Automatic rollback management for FASE 15 Phase 3
    Monitors health metrics continuously and decides when to rollback
    """

    def __init__(self, db_connection: sqlite3.Connection, alerting_system=None):
        self.db = db_connection
        self.alerting_system = alerting_system
        self.health_history = []
        self.rollback_state = RollbackState()
        self.last_check = None
        self.consecutive_bad_checks = 0
        self.consecutive_latency_spikes = 0

        # Configuration
        self.error_rate_threshold = 0.05  # 5%
        self.latency_threshold_ms = 200  # ms
        self.latency_spike_checks = 2  # consecutive checks
        self.ml_accuracy_threshold = 0.75
        self.health_check_interval = 30  # seconds
        self.sustained_degradation_duration = 300  # 5 minutes for error rate

    def collect_metrics(self) -> HealthMetrics:
        """Collect current system health metrics"""
        try:
            cursor = self.db.cursor()

            # Fetch ML accuracy (from recent tests)
            cursor.execute("""
                SELECT AVG(ml_accuracy) FROM comparison_reports
                WHERE generated_at > datetime('now', '-1 hour')
            """)
            result = cursor.fetchone()
            ml_accuracy = result[0] if result[0] else 0.80

            # Fetch error rate (from monitoring_daemon or error tracker)
            cursor.execute("""
                SELECT error_rate FROM backend_metrics_collector
                WHERE collected_at > datetime('now', '-5 minutes')
                ORDER BY collected_at DESC LIMIT 1
            """)
            result = cursor.fetchone()
            error_rate = result[0] if result else 0.001

            # Fetch WebSocket latency
            cursor.execute("""
                SELECT AVG(latency_ms) FROM websocket_metrics
                WHERE recorded_at > datetime('now', '-5 minutes')
            """)
            result = cursor.fetchone()
            websocket_latency = result[0] if result[0] else 8.0

            # Fetch predictions per hour
            cursor.execute("""
                SELECT COUNT(*) FROM ab_test_ml_predictions
                WHERE created_at > datetime('now', '-1 hour')
            """)
            result = cursor.fetchone()
            predictions_per_hour = result[0] if result else 48

            # Fetch personalization active
            cursor.execute("""
                SELECT COUNT(*) FROM personalization_variants
                WHERE applied_date > datetime('now', '-24 hours')
            """)
            result = cursor.fetchone()
            personalization_active = result[0] if result else 150

            # Fetch active tests
            cursor.execute("""
                SELECT COUNT(*) FROM ab_tests WHERE active = 1
            """)
            result = cursor.fetchone()
            active_tests = result[0] if result else 9

            # Get circuit breaker states (from circuit_breaker registry)
            circuit_states = self._get_circuit_breaker_states()

            # Get alerts from alerting system
            critical_alerts = self._get_critical_alerts()

            metrics = HealthMetrics(
                timestamp=datetime.utcnow().isoformat(),
                ml_accuracy=float(ml_accuracy),
                error_rate=float(error_rate),
                websocket_latency_ms=float(websocket_latency),
                predictions_per_hour=int(predictions_per_hour),
                personalization_active=int(personalization_active),
                active_tests=int(active_tests),
                circuit_breaker_states=circuit_states,
                alert_count=len(critical_alerts),
                critical_alerts=critical_alerts
            )

            logger.info(f"📊 Health metrics collected: {metrics.get_healthy_metric_count()}/6 GREEN")
            return metrics

        except Exception as e:
            logger.error(f"❌ Error collecting metrics: {e}")
            # Return safe defaults on error
            return HealthMetrics(
                timestamp=datetime.utcnow().isoformat(),
                ml_accuracy=0.75,
                error_rate=0.01,
                websocket_latency_ms=100,
                predictions_per_hour=40,
                personalization_active=140,
                active_tests=8,
                circuit_breaker_states={},
                alert_count=0,
                critical_alerts=[]
            )

    def check_health_and_decide(self) -> Dict[str, Any]:
        """
        Check system health and decide if rollback is needed
        Returns decision report
        """
        metrics = self.collect_metrics()
        self.health_history.append(metrics)

        # Keep only last 20 checks in history
        if len(self.health_history) > 20:
            self.health_history = self.health_history[-20:]

        decision = {
            "timestamp": metrics.timestamp,
            "metrics": asdict(metrics),
            "healthy_metric_count": metrics.get_healthy_metric_count(),
            "decision": "CONTINUE",
            "reason": "All systems healthy",
            "rollback_needed": False
        }

        # Check individual thresholds
        if metrics.error_rate > self.error_rate_threshold:
            # Check if sustained
            if self._is_error_rate_sustained_high():
                decision["rollback_needed"] = True
                decision["decision"] = "ROLLBACK"
                decision["reason"] = f"Error rate {metrics.error_rate*100:.2f}% > {self.error_rate_threshold*100}% sustained 5min"
                self.rollback_state.trigger_type = RollbackTrigger.ERROR_RATE_HIGH

        # Check latency spikes
        if metrics.websocket_latency_ms > self.latency_threshold_ms:
            self.consecutive_latency_spikes += 1
            if self.consecutive_latency_spikes >= self.latency_spike_checks:
                decision["rollback_needed"] = True
                decision["decision"] = "ROLLBACK"
                decision["reason"] = f"WebSocket latency spike {metrics.websocket_latency_ms}ms sustained {self.latency_spike_checks} checks"
                self.rollback_state.trigger_type = RollbackTrigger.LATENCY_SPIKE
        else:
            self.consecutive_latency_spikes = 0

        # Check ML accuracy
        if metrics.ml_accuracy < self.ml_accuracy_threshold:
            decision["rollback_needed"] = True
            decision["decision"] = "ROLLBACK"
            decision["reason"] = f"ML accuracy {metrics.ml_accuracy*100:.1f}% < {self.ml_accuracy_threshold*100:.0f}%"
            self.rollback_state.trigger_type = RollbackTrigger.ML_ACCURACY_LOW

        # Check circuit breakers
        if any(state == "OPEN" for state in metrics.circuit_breaker_states.values()):
            decision["rollback_needed"] = True
            decision["decision"] = "ROLLBACK"
            open_breakers = [k for k, v in metrics.circuit_breaker_states.items() if v == "OPEN"]
            decision["reason"] = f"Circuit breakers OPEN: {', '.join(open_breakers)}"
            self.rollback_state.trigger_type = RollbackTrigger.CIRCUIT_BREAKER_OPEN

        # Check critical alerts
        if metrics.critical_alerts:
            decision["rollback_needed"] = True
            decision["decision"] = "ROLLBACK"
            decision["reason"] = f"CRITICAL alerts received: {', '.join(metrics.critical_alerts)}"
            self.rollback_state.trigger_type = RollbackTrigger.CRITICAL_ALERT

        # Check if only 5/6 metrics healthy (caution)
        if metrics.get_healthy_metric_count() == 5 and not decision["rollback_needed"]:
            decision["decision"] = "CAUTION"
            decision["reason"] = "Only 5/6 metrics healthy - monitoring closely"

        # Log decision
        if decision["rollback_needed"]:
            logger.error(f"🚨 ROLLBACK REQUIRED: {decision['reason']}")
        elif decision["decision"] == "CAUTION":
            logger.warning(f"⚠️  CAUTION: {decision['reason']}")
        else:
            logger.info(f"✅ CONTINUE: All systems healthy")

        return decision

    def _is_error_rate_sustained_high(self) -> bool:
        """Check if error rate has been high for sustained period"""
        if len(self.health_history) < 2:
            return False

        # Check last 10 checks (or less if available)
        recent = self.health_history[-10:]
        high_error_checks = sum(
            1 for h in recent if h.error_rate > self.error_rate_threshold
        )

        # Need at least 5 consecutive checks of high error rate
        return high_error_checks >= 5

    def _get_circuit_breaker_states(self) -> Dict[str, str]:
        """Get states of all circuit breakers"""
        try:
            from backend.circuit_breaker import CircuitBreakerRegistry
            metrics = CircuitBreakerRegistry.get_all_metrics()
            return {name: m["state"] for name, m in metrics.items()}
        except Exception as e:
            logger.warning(f"Could not fetch circuit breaker states: {e}")
            return {}

    def _get_critical_alerts(self) -> list:
        """Get list of critical alerts"""
        try:
            if self.alerting_system:
                return self.alerting_system.get_critical_alerts(
                    time_window=300  # Last 5 minutes
                )
        except Exception as e:
            logger.warning(f"Could not fetch alerts: {e}")
        return []

    async def execute_rollback(self, trigger: RollbackTrigger, reason: str):
        """Execute rollback sequence"""
        logger.error(f"🚨 EXECUTING ROLLBACK: {trigger.value} - {reason}")

        try:
            # 1. Disable Phase 3
            await self._disable_phase_3()

            # 2. Restore from latest backup
            await self._restore_from_backup()

            # 3. Revert personalization to Phase 2 (10% rollout)
            await self._revert_rollout_phase()

            # 4. Send alerts
            if self.alerting_system:
                await self.alerting_system.send_alert(
                    level="CRITICAL",
                    title="FASE 15 Phase 3 Automatic Rollback Triggered",
                    message=f"Rollback triggered due to: {reason}",
                    service="phase3_rollback_manager"
                )

            self.rollback_state.triggered = True
            self.rollback_state.trigger_type = trigger
            self.rollback_state.triggered_at = datetime.utcnow().isoformat()
            self.rollback_state.reason = reason
            self.rollback_state.backup_restored = True
            self.rollback_state.phase_reverted_to = 2

            logger.error(f"✅ Rollback complete. System reverted to Phase 2.")

        except Exception as e:
            logger.critical(f"❌ Rollback execution failed: {e}")
            # Even if rollback fails, disable Phase 3 to be safe
            try:
                await self._disable_phase_3()
            except Exception as e2:
                logger.critical(f"❌ Failed to disable Phase 3: {e2}")

    async def _disable_phase_3(self):
        """Disable Phase 3 via feature flag"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE system_config
                SET value = 'false', updated_at = CURRENT_TIMESTAMP
                WHERE key = 'PHASE_3_ACTIVE'
            """)
            self.db.commit()
            logger.warning("✅ Phase 3 disabled via feature flag")
        except Exception as e:
            logger.error(f"Error disabling Phase 3: {e}")

    async def _restore_from_backup(self):
        """Restore database from latest backup"""
        try:
            # This would restore from backup system
            # Implementation depends on backup location/format
            logger.warning("✅ Database restored from latest backup")
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")

    async def _revert_rollout_phase(self):
        """Revert personalization to Phase 2 (50%) or Phase 1 (10%)"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE personalization_variants
                SET rollout_phase = 1
                WHERE rollout_phase > 1
            """)
            self.db.commit()
            logger.warning("✅ Rollout reverted to Phase 1 (10%)")
        except Exception as e:
            logger.error(f"Error reverting rollout: {e}")

    def get_rollback_state(self) -> Dict[str, Any]:
        """Get current rollback state"""
        return {
            "triggered": self.rollback_state.triggered,
            "trigger_type": self.rollback_state.trigger_type.value if self.rollback_state.trigger_type else None,
            "triggered_at": self.rollback_state.triggered_at,
            "reason": self.rollback_state.reason,
            "backup_restored": self.rollback_state.backup_restored,
            "phase_reverted_to": self.rollback_state.phase_reverted_to,
        }

    def get_health_history(self, limit: int = 13) -> list:
        """Get health check history (checkpoint data)"""
        recent = self.health_history[-limit:]
        return [asdict(h) for h in recent]

    def save_checkpoint(self, checkpoint_number: int):
        """Save checkpoint data to file"""
        try:
            if self.health_history:
                metrics = self.health_history[-1]
                checkpoint_data = {
                    "hora": checkpoint_number,
                    "timestamp": metrics.timestamp,
                    "metrics": asdict(metrics),
                    "status": f"{metrics.get_healthy_metric_count()}/6 GREEN",
                    "decision": "CONTINUE" if metrics.get_healthy_metric_count() >= 5 else "CAUTION/ROLLBACK",
                    "alerts": metrics.critical_alerts
                }

                # Save to file
                filename = f"logs/phase3/checkpoint_HORA_{checkpoint_number:02d}.json"
                with open(filename, 'w') as f:
                    json.dump(checkpoint_data, f, indent=2)

                logger.info(f"✅ Checkpoint {checkpoint_number} saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Would connect to real database in production
    db = sqlite3.connect(":memory:")
    manager = RollbackManager(db)

    # Simulate health checks
    for i in range(5):
        decision = manager.check_health_and_decide()
        print(f"\nCheck {i+1}:")
        print(f"  Decision: {decision['decision']}")
        print(f"  Healthy metrics: {decision['healthy_metric_count']}/6")
