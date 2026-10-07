#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - System Validation Test
Comprehensive validation of all Phase 3 components before production activation
"""

import logging
import sqlite3
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


class Phase3SystemValidator:
    """Validate Phase 3 system readiness"""

    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.db = None

    def run_all_validations(self):
        """Run all validation tests"""
        print("\n" + "=" * 80)
        print("🔍 FASE 15 Phase 3 - System Validation")
        print("=" * 80 + "\n")

        # Database connectivity
        self._test_database_connectivity()

        # Admin routes
        self._test_admin_routes_exist()

        # Phase 3 preflights
        self._test_preflights_module()

        # Feature flags
        self._test_feature_flags()

        # Monitoring daemon
        self._test_monitoring_daemon()

        # Circuit breaker
        self._test_circuit_breaker()

        # Rollback manager
        self._test_rollback_manager()

        # Personalization engine
        self._test_personalization_engine()

        # WebSocket manager
        self._test_websocket_manager()

        # Dashboard exists
        self._test_dashboard_files()

        # Activation script
        self._test_activation_script()

        # Report generator
        self._test_report_generator()

        # Print results
        self._print_results()

        return self.failed == 0

    def _test_database_connectivity(self):
        """Test database can be connected"""
        test_name = "Database Connectivity"
        try:
            db_path = "fase15.db"
            if not os.path.exists(db_path):
                self._record_test(test_name, False, f"Database not found at {db_path}")
                return

            db = sqlite3.connect(db_path, check_same_thread=False)
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            db.close()
            self._record_test(test_name, True, "Database accessible and responding")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_admin_routes_exist(self):
        """Test admin routes module exists"""
        test_name = "Admin Routes Module"
        try:
            from backend.routes.phase3_admin_routes import router, init_phase3_admin_routes
            from backend.phase3_preflights import Phase3Preflights

            # Check routes are registered
            routes = [r.path for r in router.routes]
            required_routes = [
                "/api/admin/phase3/activate",
                "/api/admin/phase3/deactivate",
                "/api/admin/phase3/status"
            ]

            missing = [r for r in required_routes if not any(r in route for route in routes)]
            if missing:
                self._record_test(test_name, False, f"Missing routes: {missing}")
            else:
                self._record_test(test_name, True, f"All 3 admin routes registered")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_preflights_module(self):
        """Test preflights module"""
        test_name = "Pre-Flight Checks Module"
        try:
            from backend.phase3_preflights import Phase3Preflights

            if not hasattr(Phase3Preflights, 'run_all_checks'):
                self._record_test(test_name, False, "run_all_checks method missing")
                return

            # Verify all 5 check methods exist
            required_checks = [
                'check_phase2_metrics',
                'check_backup_age',
                'check_database_integrity',
                'check_all_components',
                'check_circuit_breakers'
            ]

            missing = [c for c in required_checks if not hasattr(Phase3Preflights, c)]
            if missing:
                self._record_test(test_name, False, f"Missing checks: {missing}")
            else:
                self._record_test(test_name, True, "All 5 pre-flight checks implemented")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_feature_flags(self):
        """Test feature flag guards"""
        test_name = "Feature Flag Guards"
        try:
            from backend.routes.ab_testing_routes import is_phase3_active, require_phase3_active

            # Test flag functions exist and are callable
            if not callable(is_phase3_active):
                self._record_test(test_name, False, "is_phase3_active not callable")
                return

            if not callable(require_phase3_active):
                self._record_test(test_name, False, "require_phase3_active not callable")
                return

            self._record_test(test_name, True, "Feature flag guards implemented")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_monitoring_daemon(self):
        """Test monitoring daemon"""
        test_name = "Monitoring Daemon"
        try:
            from backend.monitoring_daemon import MonitoringDaemon

            # Check Phase 3 checkpoint loop exists
            if not hasattr(MonitoringDaemon, '_phase3_checkpoint_loop'):
                self._record_test(test_name, False, "_phase3_checkpoint_loop method missing")
                return

            daemon = MonitoringDaemon()
            if not hasattr(daemon, 'running'):
                self._record_test(test_name, False, "MonitoringDaemon doesn't have running attribute")
                return

            self._record_test(test_name, True, "Monitoring daemon with checkpoint loop ready")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_circuit_breaker(self):
        """Test circuit breaker pattern"""
        test_name = "Circuit Breaker Pattern"
        try:
            from backend.circuit_breaker import CircuitBreakerRegistry, CircuitBreaker

            registry = CircuitBreakerRegistry()
            if not hasattr(registry, 'breakers'):
                self._record_test(test_name, False, "CircuitBreakerRegistry missing breakers")
                return

            if not hasattr(registry, 'get_all_metrics'):
                self._record_test(test_name, False, "CircuitBreakerRegistry missing get_all_metrics")
                return

            self._record_test(test_name, True, "Circuit breaker pattern implemented")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_rollback_manager(self):
        """Test rollback manager"""
        test_name = "Rollback Manager"
        try:
            from backend.rollback_manager import RollbackManager, RollbackTrigger

            # Verify RollbackTrigger enum has required values
            required_triggers = [
                'ERROR_RATE_HIGH',
                'LATENCY_SPIKE',
                'ML_ACCURACY_LOW',
                'CIRCUIT_BREAKER_OPEN',
                'MANUAL',
                'CRITICAL_ALERT'
            ]

            missing = [t for t in required_triggers if not hasattr(RollbackTrigger, t)]
            if missing:
                self._record_test(test_name, False, f"Missing triggers: {missing}")
                return

            # Verify key methods
            if not hasattr(RollbackManager, 'check_health_and_decide'):
                self._record_test(test_name, False, "check_health_and_decide method missing")
                return

            self._record_test(test_name, True, "Rollback manager with 6 trigger types ready")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_personalization_engine(self):
        """Test personalization engine"""
        test_name = "Personalization Engine"
        try:
            from agents.personalization_engine import PersonalizationEngine

            required_methods = [
                'apply_test_winner',
                'advance_rollout_phase',
                'should_use_variant'
            ]

            missing = [m for m in required_methods if not hasattr(PersonalizationEngine, m)]
            if missing:
                self._record_test(test_name, False, f"Missing methods: {missing}")
            else:
                self._record_test(test_name, True, "Personalization engine with rollout phases ready")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_websocket_manager(self):
        """Test WebSocket manager"""
        test_name = "WebSocket Manager"
        try:
            from backend.websocket_manager import WebSocketConnectionManager

            if not hasattr(WebSocketConnectionManager, 'broadcast'):
                self._record_test(test_name, False, "broadcast method missing")
                return

            self._record_test(test_name, True, "WebSocket manager with broadcasting ready")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_dashboard_files(self):
        """Test dashboard files exist"""
        test_name = "Dashboard Files"
        try:
            required_files = [
                'frontend/phase3_realtime_dashboard.html',
                'frontend/phase3_analysis_dashboard.html'
            ]

            missing = [f for f in required_files if not os.path.exists(f)]
            if missing:
                self._record_test(test_name, False, f"Missing files: {missing}")
            else:
                self._record_test(test_name, True, "Both dashboards present and ready")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_activation_script(self):
        """Test activation script exists and is executable"""
        test_name = "Activation Script"
        try:
            script_path = "phase3_activate.py"
            if not os.path.exists(script_path):
                self._record_test(test_name, False, f"Script not found at {script_path}")
                return

            if not os.access(script_path, os.X_OK):
                logger.warning(f"Script at {script_path} is not executable, attempting chmod...")
                os.chmod(script_path, 0o755)

            self._record_test(test_name, True, "Activation script present and executable")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _test_report_generator(self):
        """Test report generator module"""
        test_name = "Report Generator"
        try:
            from phase3_generate_report import Phase3ReportGenerator

            required_methods = [
                'load_checkpoints',
                'calculate_metrics_summary',
                'generate_report'
            ]

            missing = [m for m in required_methods if not hasattr(Phase3ReportGenerator, m)]
            if missing:
                self._record_test(test_name, False, f"Missing methods: {missing}")
            else:
                self._record_test(test_name, True, "Report generator ready for post-execution analysis")
        except Exception as e:
            self._record_test(test_name, False, str(e))

    def _record_test(self, name: str, passed: bool, message: str):
        """Record test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.tests.append({
            'name': name,
            'passed': passed,
            'message': message
        })

        if passed:
            self.passed += 1
        else:
            self.failed += 1

        print(f"{status}: {name}")
        print(f"      {message}\n")

    def _print_results(self):
        """Print validation results"""
        total = self.passed + self.failed

        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        print(f"\n  ✅ Passed: {self.passed}/{total}")
        print(f"  ❌ Failed: {self.failed}/{total}")

        if self.failed == 0:
            print("\n🎉 ALL VALIDATIONS PASSED - SYSTEM READY FOR PRODUCTION")
            print("\n✅ Next Step: Run 'python3 phase3_activate.py' to begin Phase 3")
        else:
            print("\n⚠️  SOME VALIDATIONS FAILED - PLEASE FIX BEFORE ACTIVATION")
            print("\nFailed Tests:")
            for test in self.tests:
                if not test['passed']:
                    print(f"  • {test['name']}: {test['message']}")

        print("\n" + "=" * 80 + "\n")


def main():
    """Main entry point"""
    validator = Phase3SystemValidator()
    success = validator.run_all_validations()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
