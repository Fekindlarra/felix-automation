#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Checkpoint Monitoring System
Collects metrics every 2 hours during 24-hour execution window (13 checkpoints total)
HORA 48-72 = Oct 6-7, 2026
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MetricsCollectionError(Exception):
    """
    Raised when metrics cannot be collected from database.
    Indicates a data availability issue that should trigger rollback consideration.
    """
    pass


class CheckpointStatus(Enum):
    """Checkpoint evaluation status"""
    GREEN = "GREEN"        # 6/6 metrics passing
    YELLOW = "YELLOW"      # 5/6 metrics passing
    RED = "RED"           # <5/6 metrics passing
    CRITICAL = "CRITICAL"  # Rollback triggered


class CheckpointDecision(Enum):
    """Decision at each checkpoint"""
    CONTINUE = "CONTINUE"      # All metrics healthy, advance phase if eligible
    CAUTION = "CAUTION"        # Metrics marginal but acceptable, hold phase
    ROLLBACK = "ROLLBACK"      # Metrics degraded, immediate rollback


@dataclass
class MetricSnapshot:
    """Snapshot of a single metric at checkpoint time"""
    ml_accuracy: float          # 0.78-1.0 (target: ≥0.78)
    error_rate: float          # 0.0008-0.5 (target: <0.0008 = <0.08%)
    websocket_latency: float   # milliseconds (target: <95ms)
    predictions_hour: float    # per hour (target: ≥42)
    personalization_active: int # count (target: ≥140)
    active_tests: int          # count (target: ≥8)

    def health_score(self) -> int:
        """Calculate health score (0-6) based on thresholds"""
        checks = [
            self.ml_accuracy >= 0.78,
            self.error_rate < 0.0008,
            self.websocket_latency < 95,
            self.predictions_hour >= 42,
            self.personalization_active >= 140,
            self.active_tests >= 8
        ]
        return sum(checks)

    def status(self) -> CheckpointStatus:
        """Determine status based on health score"""
        score = self.health_score()
        if score == 6:
            return CheckpointStatus.GREEN
        elif score == 5:
            return CheckpointStatus.YELLOW
        else:
            return CheckpointStatus.RED

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class CircuitBreakerState:
    """Current state of circuit breakers"""
    database: str = "CLOSED"       # CLOSED/OPEN/HALF_OPEN
    websocket: str = "CLOSED"
    predictions: str = "CLOSED"
    any_open: bool = False


@dataclass
class Checkpoint:
    """Complete checkpoint record"""
    hora: int                       # 48-72 (2-hour increments)
    timestamp: str                  # ISO 8601
    metrics: MetricSnapshot
    circuit_breakers: CircuitBreakerState
    critical_alerts: List[str]      # List of critical alert IDs
    status: CheckpointStatus
    decision: CheckpointDecision
    reasoning: List[str]            # Why this decision was made


class Phase3CheckpointMonitor:
    """Monitor Phase 3 execution and collect checkpoint data"""

    def __init__(self, db_path: str = "fase15.db"):
        self.db_path = db_path
        self.db = None
        self.last_hora = 47
        self.checkpoints_collected: List[Checkpoint] = []

    def connect(self):
        """Connect to database"""
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        logger.info(f"✅ Connected to database: {self.db_path}")

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

    def is_phase3_active(self) -> bool:
        """Check if Phase 3 is currently active"""
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE'")
            result = cursor.fetchone()
            return result[0] == 'true' if result else False
        except Exception as e:
            logger.error(f"Error checking Phase 3 status: {e}")
            return False

    def collect_metrics(self) -> MetricSnapshot:
        """
        Collect current 6 metrics from database.
        Raises MetricsCollectionError if any metric cannot be collected.
        """
        try:
            cursor = self.db.cursor()

            # 1. ML Accuracy - from ab_test_ml_predictions
            cursor.execute("""
                SELECT AVG(ml_accuracy) as avg_accuracy
                FROM ab_test_ml_predictions
                WHERE created_at > datetime('now', '-2 hours')
                  AND ml_accuracy IS NOT NULL
            """)
            ml_row = cursor.fetchone()

            # Require valid data - no hardcoded fallback
            if not ml_row or ml_row['avg_accuracy'] is None:
                raise MetricsCollectionError(
                    "❌ ML Accuracy: No data collected in last 2 hours. "
                    "Either ab_test_ml_predictions table is empty or queries are not recording predictions."
                )
            ml_accuracy = float(ml_row['avg_accuracy'])

            # 2. Error Rate - from error_log (critical + major errors)
            cursor.execute("""
                SELECT COUNT(*) as error_count
                FROM error_log
                WHERE severity IN ('CRITICAL', 'MAJOR')
                  AND created_at > datetime('now', '-2 hours')
            """)
            error_row = cursor.fetchone()

            # Error count can be 0 (no errors) - that's healthy
            # But error_row should exist (count query always returns a row)
            if not error_row:
                raise MetricsCollectionError(
                    "❌ Error Rate: Query failed - error_log table may not exist"
                )
            error_count = error_row['error_count'] if error_row['error_count'] else 0
            # Convert count to rate: errors per 100,000 requests (assuming ~100k requests in 2h window)
            error_rate = (error_count / 100000.0)
            logger.info(f"ℹ️  Error Rate: {error_count} errors in last 2 hours = {error_rate:.4f}")

            # 3. WebSocket Latency - from metrics
            cursor.execute("""
                SELECT AVG(value) as avg_latency
                FROM metrics
                WHERE metric_name = 'websocket_latency'
                  AND created_at > datetime('now', '-2 hours')
            """)
            lat_row = cursor.fetchone()

            # Require valid latency data
            if not lat_row or lat_row['avg_latency'] is None:
                raise MetricsCollectionError(
                    "❌ WebSocket Latency: No data collected in last 2 hours. "
                    "Metrics table may not be recording WebSocket latencies."
                )
            websocket_latency = float(lat_row['avg_latency'])

            # 4. Predictions/Hour - from ab_test_ml_predictions
            cursor.execute("""
                SELECT COUNT(*) as prediction_count
                FROM ab_test_ml_predictions
                WHERE created_at > datetime('now', '-2 hours')
            """)
            pred_row = cursor.fetchone()

            if not pred_row:
                raise MetricsCollectionError(
                    "❌ Predictions/Hour: Query failed - ab_test_ml_predictions table may not exist"
                )

            # Extrapolate 2-hour window to per-hour rate
            prediction_count = pred_row['prediction_count'] if pred_row['prediction_count'] else 0
            predictions_hour = float(prediction_count * 30)  # 2h window × 30 = per-hour estimate

            if predictions_hour == 0:
                raise MetricsCollectionError(
                    "❌ Predictions/Hour: No predictions recorded in last 2 hours. "
                    "ML prediction service may not be running."
                )
            logger.info(f"ℹ️  Predictions/Hour: {prediction_count} in 2h window → {predictions_hour} per hour")

            # 5. Personalization Active - from personalization_variants
            cursor.execute("""
                SELECT COUNT(DISTINCT client_id) as active_personalization
                FROM personalization_variants
                WHERE applied_date > datetime('now', '-2 hours')
            """)
            pers_row = cursor.fetchone()

            if not pers_row:
                raise MetricsCollectionError(
                    "❌ Personalization Active: Query failed - personalization_variants table may not exist"
                )

            personalization_active = pers_row['active_personalization'] if pers_row['active_personalization'] else 0
            logger.info(f"ℹ️  Personalization Active: {personalization_active} clients personalized in last 2 hours")

            # 6. Active Tests - from ab_tests
            cursor.execute("""
                SELECT COUNT(*) as active_count
                FROM ab_tests
                WHERE status = 'ACTIVE'
                  AND created_at < datetime('now')
                  AND (end_date IS NULL OR end_date > datetime('now'))
            """)
            test_row = cursor.fetchone()

            if not test_row:
                raise MetricsCollectionError(
                    "❌ Active Tests: Query failed - ab_tests table may not exist"
                )

            active_tests = test_row['active_count'] if test_row['active_count'] else 0
            logger.info(f"ℹ️  Active Tests: {active_tests} currently running")

            metrics = MetricSnapshot(
                ml_accuracy=ml_accuracy,
                error_rate=error_rate,
                websocket_latency=websocket_latency,
                predictions_hour=predictions_hour,
                personalization_active=int(personalization_active),
                active_tests=int(active_tests)
            )

            logger.info(f"✅ All metrics collected successfully: {metrics}")
            return metrics

        except MetricsCollectionError as e:
            # Re-raise collection errors - these indicate real problems
            logger.error(str(e))
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            logger.error(f"❌ Unexpected error collecting metrics: {e}", exc_info=True)
            raise MetricsCollectionError(
                f"Unexpected error during metrics collection: {e}"
            )

    def check_circuit_breakers(self) -> CircuitBreakerState:
        """Check state of all circuit breakers"""
        try:
            cursor = self.db.cursor()

            # Query circuit_breaker_states table for current states
            cursor.execute("""
                SELECT name, state
                FROM circuit_breaker_states
                WHERE name IN ('database', 'websocket', 'predictions')
            """)

            states = {row['name']: row['state'] for row in cursor.fetchall()}

            cb_state = CircuitBreakerState(
                database=states.get('database', 'CLOSED'),
                websocket=states.get('websocket', 'CLOSED'),
                predictions=states.get('predictions', 'CLOSED')
            )

            cb_state.any_open = any(s == 'OPEN' for s in [cb_state.database, cb_state.websocket, cb_state.predictions])

            if cb_state.any_open:
                logger.warning(f"⚠️  Circuit breaker(s) OPEN: {cb_state}")
            else:
                logger.info(f"✅ All circuit breakers closed")

            return cb_state

        except Exception as e:
            logger.error(f"Error checking circuit breakers: {e}")
            return CircuitBreakerState()

    def check_critical_alerts(self) -> List[str]:
        """Check for any CRITICAL severity alerts in last 2 hours"""
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                SELECT DISTINCT alert_id, rule_name
                FROM alerts
                WHERE severity = 'CRITICAL'
                  AND triggered_at > datetime('now', '-2 hours')
                  AND status IN ('FIRING', 'ACKNOWLEDGED')
            """)

            alerts = [row['alert_id'] for row in cursor.fetchall()]

            if alerts:
                logger.warning(f"⚠️  {len(alerts)} CRITICAL alert(s) detected")

            return alerts

        except Exception as e:
            logger.error(f"Error checking critical alerts: {e}")
            return []

    def make_checkpoint_decision(self, checkpoint: Checkpoint) -> CheckpointDecision:
        """Decide whether to continue, caution, or rollback based on checkpoint"""
        reasoning = []

        # Evaluate metrics
        health_score = checkpoint.metrics.health_score()
        status = checkpoint.metrics.status()

        # Decision logic
        if checkpoint.circuit_breakers.any_open:
            reasoning.append("⚠️  Circuit breaker(s) open - graceful degradation active")

        if checkpoint.critical_alerts:
            reasoning.append(f"🚨 {len(checkpoint.critical_alerts)} CRITICAL alerts detected")
            return CheckpointDecision.ROLLBACK

        if health_score < 5:
            reasoning.append(f"❌ Health score {health_score}/6 below caution threshold")
            return CheckpointDecision.ROLLBACK

        if health_score == 5:
            reasoning.append(f"⚠️  Health score {health_score}/6 - marginal but acceptable")
            if checkpoint.circuit_breakers.any_open:
                reasoning.append("Circuit breaker open, holding phase advancement")
            return CheckpointDecision.CAUTION

        if health_score == 6:
            reasoning.append(f"✅ Health score {health_score}/6 - all metrics passing")
            if checkpoint.circuit_breakers.any_open:
                reasoning.append("Circuit breaker open, holding phase advancement despite green metrics")
                return CheckpointDecision.CAUTION
            return CheckpointDecision.CONTINUE

        return CheckpointDecision.CAUTION

    def save_checkpoint(self, checkpoint: Checkpoint):
        """Save checkpoint to database and JSON file"""
        try:
            cursor = self.db.cursor()

            # Insert into database
            cursor.execute("""
                INSERT INTO phase3_checkpoints (
                    hora, timestamp,
                    ml_accuracy, error_rate, websocket_latency,
                    predictions_hour, personalization_active, active_tests,
                    health_score, status, decision, reasoning
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                checkpoint.hora,
                checkpoint.timestamp,
                checkpoint.metrics.ml_accuracy,
                checkpoint.metrics.error_rate,
                checkpoint.metrics.websocket_latency,
                checkpoint.metrics.predictions_hour,
                checkpoint.metrics.personalization_active,
                checkpoint.metrics.active_tests,
                checkpoint.metrics.health_score(),
                checkpoint.status.value,
                checkpoint.decision.value,
                json.dumps(checkpoint.reasoning)
            ))

            self.db.commit()

            # Save JSON file
            output_dir = Path("logs/phase3")
            output_dir.mkdir(parents=True, exist_ok=True)

            checkpoint_file = output_dir / f"checkpoint_hora_{checkpoint.hora:02d}_{checkpoint.timestamp.split('T')[0]}.json"

            checkpoint_data = {
                "hora": checkpoint.hora,
                "timestamp": checkpoint.timestamp,
                "metrics": checkpoint.metrics.to_dict(),
                "circuit_breakers": {
                    "database": checkpoint.circuit_breakers.database,
                    "websocket": checkpoint.circuit_breakers.websocket,
                    "predictions": checkpoint.circuit_breakers.predictions,
                    "any_open": checkpoint.circuit_breakers.any_open
                },
                "critical_alerts": checkpoint.critical_alerts,
                "status": checkpoint.status.value,
                "decision": checkpoint.decision.value,
                "reasoning": checkpoint.reasoning
            }

            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            logger.info(f"✅ Checkpoint saved: {checkpoint_file}")
            self.checkpoints_collected.append(checkpoint)

        except Exception as e:
            logger.error(f"❌ Error saving checkpoint: {e}")

    def collect_checkpoint(self, hora: int) -> Optional[Checkpoint]:
        """
        Collect a single checkpoint at specified HORA.

        Returns:
            Checkpoint if successful
            None if metrics collection fails (indicating serious data issue)
        """
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"CHECKPOINT HORA {hora}")
            logger.info(f"{'='*70}")

            # Collect metrics - will raise MetricsCollectionError if data unavailable
            metrics = self.collect_metrics()

            # Check circuit breakers
            circuit_breakers = self.check_circuit_breakers()

            # Check critical alerts
            critical_alerts = self.check_critical_alerts()

            # Create checkpoint
            checkpoint = Checkpoint(
                hora=hora,
                timestamp=datetime.utcnow().isoformat() + "Z",
                metrics=metrics,
                circuit_breakers=circuit_breakers,
                critical_alerts=critical_alerts,
                status=metrics.status(),
                decision=CheckpointDecision.CONTINUE,  # Will be overridden below
                reasoning=[]
            )

            # Make decision
            checkpoint.decision = self.make_checkpoint_decision(checkpoint)

            # Log summary
            logger.info(f"Status: {checkpoint.status.value} ({checkpoint.metrics.health_score()}/6)")
            logger.info(f"Decision: {checkpoint.decision.value}")

            for reason in checkpoint.reasoning:
                logger.info(f"  {reason}")

            # Save checkpoint
            self.save_checkpoint(checkpoint)

            return checkpoint

        except MetricsCollectionError as e:
            logger.error(
                f"❌ Checkpoint HORA {hora} failed: Metrics not available. "
                f"This should trigger rollback consideration. Error: {e}"
            )
            # Signal that this checkpoint could not be collected
            # The calling code (rollback_manager) should handle this as a CRITICAL condition
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error collecting checkpoint HORA {hora}: {e}", exc_info=True)
            return None

    def generate_checkpoint_report(self) -> Dict:
        """Generate summary report of all checkpoints collected so far"""
        health_scores = [c.metrics.health_score() for c in self.checkpoints_collected]
        green_count = sum(1 for s in health_scores if s == 6)
        yellow_count = sum(1 for s in health_scores if s == 5)
        red_count = sum(1 for s in health_scores if s < 5)

        report = {
            "total_checkpoints": len(self.checkpoints_collected),
            "green_checkpoints": green_count,
            "yellow_checkpoints": yellow_count,
            "red_checkpoints": red_count,
            "average_health_score": sum(health_scores) / len(health_scores) if health_scores else 0,
            "checkpoints": [
                {
                    "hora": c.hora,
                    "health_score": c.metrics.health_score(),
                    "status": c.status.value,
                    "decision": c.decision.value
                }
                for c in self.checkpoints_collected
            ]
        }

        return report


def main():
    """Test checkpoint monitoring system"""
    import sys

    monitor = Phase3CheckpointMonitor()
    monitor.connect()

    # Check if Phase 3 is active
    if not monitor.is_phase3_active():
        logger.info("Phase 3 not active, exiting")
        monitor.close()
        return 1

    # Collect checkpoint for current HORA
    if len(sys.argv) > 1:
        try:
            hora = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid HORA: {sys.argv[1]}")
            monitor.close()
            return 1
    else:
        # Default to next checkpoint
        monitor.last_hora = 48
        hora = 48

    checkpoint = monitor.collect_checkpoint(hora)

    monitor.close()

    return 0 if checkpoint else 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    exit(main())
