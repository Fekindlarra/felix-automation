#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Phase 1 - Verification Script
Verifies all Phase 1 monitoring infrastructure is operational
"""

import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# VERIFICATION SUITE
# ============================================================================

class Phase1Verifier:
    """Comprehensive Phase 1 verification"""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def log_result(self, test_name: str, status: bool, details: str = ""):
        """Log verification result"""
        symbol = "✅" if status else "❌"
        msg = f"{symbol} {test_name}"
        if details:
            msg += f": {details}"
        logger.info(msg)
        self.results.append({
            'test': test_name,
            'passed': status,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
        if status:
            self.passed += 1
        else:
            self.failed += 1

    def verify_database_schema(self) -> bool:
        """Verify database has all Phase 1 tables"""
        try:
            import sqlite3
            db_path = Path(__file__).parent / "database.sqlite"

            if not db_path.exists():
                self.log_result("Database schema", False, "database.sqlite not found")
                return False

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check for Phase 1 tables
            required_tables = [
                'shopify_stores',
                'shopify_orders',
                'shopify_webhooks',
                'prediction_history',
                'ab_tests',
                'ab_test_results',
                'ab_test_assignments',
                'anomalies'
            ]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing = set(required_tables) - existing_tables

            conn.close()

            if missing:
                self.log_result(
                    "Database schema",
                    False,
                    f"Missing tables: {', '.join(missing)}"
                )
                return False

            self.log_result(
                "Database schema",
                True,
                f"All {len(required_tables)} Phase 1 tables present"
            )
            return True

        except Exception as e:
            self.log_result("Database schema", False, str(e))
            return False

    def verify_monitoring_components(self) -> bool:
        """Verify all monitoring components initialize correctly"""
        try:
            from backend.monitoring_startup import (
                get_metrics_collector,
                get_error_tracker,
                get_alert_manager,
                get_prediction_broadcaster,
                get_monitoring_daemon
            )

            results = []

            # MetricsCollector
            metrics = get_metrics_collector()
            if metrics and hasattr(metrics, 'record_metric'):
                self.log_result("MetricsCollector", True, "Initialized and ready")
                results.append(True)
            else:
                self.log_result("MetricsCollector", False, "Failed to initialize")
                results.append(False)

            # ErrorTracker
            errors = get_error_tracker()
            if errors and hasattr(errors, 'record_error'):
                self.log_result("ErrorTracker", True, "Initialized and ready")
                results.append(True)
            else:
                self.log_result("ErrorTracker", False, "Failed to initialize")
                results.append(False)

            # AlertManager
            alerts = get_alert_manager()
            if alerts and hasattr(alerts, 'evaluate_rule'):
                self.log_result("AlertManager", True, "Initialized and ready")
                results.append(True)
            else:
                self.log_result("AlertManager", False, "Failed to initialize")
                results.append(False)

            # PredictionBroadcaster
            broadcaster = get_prediction_broadcaster()
            if broadcaster and hasattr(broadcaster, 'broadcast_prediction'):
                self.log_result("PredictionBroadcaster", True, "Initialized and ready")
                results.append(True)
            else:
                self.log_result("PredictionBroadcaster", False, "Failed to initialize")
                results.append(False)

            # MonitoringDaemon
            daemon = get_monitoring_daemon()
            if daemon:
                self.log_result("MonitoringDaemon", True, "Initialized and ready")
                results.append(True)
            else:
                self.log_result("MonitoringDaemon", False, "Failed to initialize")
                results.append(False)

            return all(results)

        except Exception as e:
            self.log_result("Monitoring components", False, str(e))
            return False

    def verify_api_endpoints(self) -> bool:
        """Verify monitoring API endpoints respond correctly"""
        try:
            from fastapi.testclient import TestClient
            from backend.app import app

            client = TestClient(app)

            endpoints = [
                ("/api/monitoring/health", "Health status"),
                ("/api/monitoring/status", "Overall status"),
                ("/api/monitoring/metrics", "Metrics summary"),
                ("/api/monitoring/errors", "Errors summary"),
                ("/api/monitoring/alerts", "Active alerts"),
                ("/api/monitoring/anomalies", "Anomalies"),
                ("/api/monitoring/predictions", "Predictions stats"),
            ]

            all_ok = True

            for endpoint, description in endpoints:
                try:
                    response = client.get(endpoint)
                    if response.status_code == 200:
                        self.log_result(
                            f"Endpoint {endpoint}",
                            True,
                            f"{description} - {response.status_code}"
                        )
                    else:
                        self.log_result(
                            f"Endpoint {endpoint}",
                            False,
                            f"Unexpected status {response.status_code}"
                        )
                        all_ok = False
                except Exception as e:
                    self.log_result(
                        f"Endpoint {endpoint}",
                        False,
                        f"Error: {str(e)[:50]}"
                    )
                    all_ok = False

            return all_ok

        except Exception as e:
            self.log_result("API endpoints", False, str(e))
            return False

    def verify_metrics_collection(self) -> bool:
        """Verify metrics are being collected"""
        try:
            from backend.monitoring_startup import get_metrics_collector

            metrics = get_metrics_collector()

            if not metrics:
                self.log_result("Metrics collection", False, "Collector not available")
                return False

            # Record test metric
            metrics.record_metric(
                metric_name="phase1_verification",
                value=42.5,
                metric_type="LATENCY_MS",
                unit="ms",
                component="verification"
            )

            # Get summary
            summary = metrics.get_metric_summary()

            if summary and summary.get('total_metrics_recorded', 0) >= 1:
                self.log_result(
                    "Metrics collection",
                    True,
                    f"{summary.get('total_metrics_recorded')} metrics recorded"
                )
                return True
            else:
                self.log_result("Metrics collection", False, "No metrics collected")
                return False

        except Exception as e:
            self.log_result("Metrics collection", False, str(e))
            return False

    def verify_error_tracking(self) -> bool:
        """Verify errors are being tracked"""
        try:
            from backend.monitoring_startup import get_error_tracker
            from backend.backend_error_tracker import ErrorCategory, ErrorSeverity

            errors = get_error_tracker()

            if not errors:
                self.log_result("Error tracking", False, "Tracker not available")
                return False

            # Record test error
            errors.record_error(
                category=ErrorCategory.API,
                severity=ErrorSeverity.WARNING,
                message="Phase 1 verification error",
                error_type="VerificationError",
                component="verification"
            )

            # Get summary
            summary = errors.get_error_summary()

            if summary and summary.get('total_errors', 0) >= 1:
                self.log_result(
                    "Error tracking",
                    True,
                    f"{summary.get('total_errors')} errors tracked"
                )
                return True
            else:
                self.log_result("Error tracking", False, "No errors tracked")
                return False

        except Exception as e:
            self.log_result("Error tracking", False, str(e))
            return False

    def verify_alert_rules(self) -> bool:
        """Verify alert rules are configured"""
        try:
            from backend.monitoring_startup import get_alert_manager

            alerts = get_alert_manager()

            if not alerts:
                self.log_result("Alert rules", False, "Manager not available")
                return False

            if not hasattr(alerts, 'rules'):
                self.log_result("Alert rules", False, "No rules attribute")
                return False

            rules_count = len(alerts.rules)

            if rules_count > 0:
                self.log_result(
                    "Alert rules",
                    True,
                    f"{rules_count} default rules configured"
                )
                return True
            else:
                self.log_result("Alert rules", False, "No rules configured")
                return False

        except Exception as e:
            self.log_result("Alert rules", False, str(e))
            return False

    def verify_prediction_capability(self) -> bool:
        """Verify prediction broadcasting capability"""
        try:
            from backend.monitoring_startup import get_prediction_broadcaster
            from backend.prediction_broadcaster import ConversionPrediction

            broadcaster = get_prediction_broadcaster()

            if not broadcaster:
                self.log_result("Prediction broadcasting", False, "Broadcaster not available")
                return False

            # Create test prediction
            prediction = ConversionPrediction(
                client_id=999,
                probability=75.5,
                confidence=88.2,
                positive_factors=['Phase 1 verified'],
                risk_factors=[],
                predicted_timeline_days=7,
                anomalies_detected=[],
                recommendation='Continue to Phase 2'
            )

            # Broadcast (won't actually send to WebSocket without manager)
            result = broadcaster.broadcast_prediction(prediction)

            # Get statistics
            stats = broadcaster.get_statistics()

            if stats and isinstance(stats, dict):
                self.log_result(
                    "Prediction broadcasting",
                    True,
                    f"{stats.get('total_predictions')} predictions in memory"
                )
                return True
            else:
                self.log_result("Prediction broadcasting", False, "Invalid statistics")
                return False

        except Exception as e:
            self.log_result("Prediction broadcasting", False, str(e))
            return False

    def run_all_verifications(self) -> bool:
        """Run complete verification suite"""
        logger.info("\n" + "="*70)
        logger.info("🚀 FASE 14 PHASE 1 - VERIFICATION SUITE")
        logger.info("="*70 + "\n")

        logger.info("📋 Running verification checks...\n")

        # Run all checks
        self.verify_database_schema()
        self.verify_monitoring_components()
        self.verify_api_endpoints()
        self.verify_metrics_collection()
        self.verify_error_tracking()
        self.verify_alert_rules()
        self.verify_prediction_capability()

        # Summary
        logger.info("\n" + "="*70)
        logger.info("📊 VERIFICATION SUMMARY")
        logger.info("="*70)
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        logger.info(f"📈 Total: {self.passed + self.failed}")
        logger.info(f"📊 Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")

        if self.failed == 0:
            logger.info("\n🎉 PHASE 1 COMPLETE - ALL SYSTEMS OPERATIONAL!")
            logger.info("="*70 + "\n")
            return True
        else:
            logger.warning(f"\n⚠️  {self.failed} verification(s) failed")
            logger.warning("="*70 + "\n")
            return False

    def export_results(self, filepath: str = None):
        """Export verification results to JSON"""
        if filepath is None:
            filepath = Path(__file__).parent / "fase14_phase1_verification.json"

        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'phase': 'FASE 14 - Phase 1',
            'passed': self.passed,
            'failed': self.failed,
            'total': self.passed + self.failed,
            'success_rate': (self.passed/(self.passed+self.failed)*100) if (self.passed+self.failed) > 0 else 0,
            'status': 'COMPLETE' if self.failed == 0 else 'INCOMPLETE',
            'results': self.results
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n📄 Report saved to: {filepath}")
        return filepath


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    verifier = Phase1Verifier()
    success = verifier.run_all_verifications()
    verifier.export_results()

    sys.exit(0 if success else 1)
