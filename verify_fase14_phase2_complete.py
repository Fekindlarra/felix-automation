#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Phase 2 - Verification Script
Verifies all A/B Testing Framework components are operational
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

class Phase2Verifier:
    """Comprehensive Phase 2 verification"""

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
        """Verify database has A/B testing tables"""
        try:
            import sqlite3
            db_path = Path(__file__).parent / "database.sqlite"

            if not db_path.exists():
                self.log_result("Database exists", False, "database.sqlite not found")
                return False

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check for A/B testing tables
            required_tables = [
                'ab_tests',
                'ab_test_results',
                'ab_test_assignments'
            ]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing = set(required_tables) - existing_tables

            conn.close()

            if missing:
                self.log_result(
                    "A/B Testing tables",
                    False,
                    f"Missing tables: {', '.join(missing)}"
                )
                return False

            self.log_result(
                "A/B Testing tables",
                True,
                f"All {len(required_tables)} tables present"
            )
            return True

        except Exception as e:
            self.log_result("Database schema", False, str(e))
            return False

    def verify_variant_assigner(self) -> bool:
        """Verify EmailVariantAssigner component"""
        try:
            from agents.email_variant_assigner import EmailVariantAssigner

            # Test basic functionality
            assigner = EmailVariantAssigner(db_connection=None)

            # Test deterministic assignment
            variant1 = assigner.assign_variant(test_id=1, client_id=100)
            variant2 = assigner.assign_variant(test_id=1, client_id=100)

            if variant1 != variant2:
                self.log_result(
                    "EmailVariantAssigner",
                    False,
                    "Assignment not deterministic"
                )
                return False

            if variant1 not in ['A', 'B']:
                self.log_result(
                    "EmailVariantAssigner",
                    False,
                    f"Invalid variant: {variant1}"
                )
                return False

            self.log_result(
                "EmailVariantAssigner",
                True,
                f"Deterministic assignment working (client 100 → {variant1})"
            )
            return True

        except Exception as e:
            self.log_result("EmailVariantAssigner", False, str(e))
            return False

    def verify_statistical_tester(self) -> bool:
        """Verify StatisticalTester component"""
        try:
            import sqlite3
            from agents.statistical_tester import StatisticalTester

            db_path = Path(__file__).parent / "database.sqlite"
            conn = sqlite3.connect(str(db_path))

            tester = StatisticalTester(db_connection=conn)

            # Test chi-square calculation
            variant_a = {'sent': 1000, 'conversions': 100}
            variant_b = {'sent': 1000, 'conversions': 110}

            result = tester.chi_square_test(variant_a, variant_b)

            if 'chi_square' not in result or 'p_value' not in result:
                self.log_result(
                    "StatisticalTester",
                    False,
                    "Missing chi_square or p_value"
                )
                return False

            # Test confidence interval
            ci = tester.calculate_confidence_interval(100, 1000)
            if not isinstance(ci, tuple) or len(ci) != 2:
                self.log_result(
                    "StatisticalTester",
                    False,
                    "Invalid confidence interval"
                )
                return False

            conn.close()

            self.log_result(
                "StatisticalTester",
                True,
                f"Chi-square: {result['chi_square']:.4f}, p-value: {result['p_value']}"
            )
            return True

        except Exception as e:
            self.log_result("StatisticalTester", False, str(e))
            return False

    def verify_ab_testing_routes(self) -> bool:
        """Verify A/B testing API endpoints"""
        try:
            from backend.routes.ab_testing_routes import router, init_ab_testing
            import sqlite3

            db_path = Path(__file__).parent / "database.sqlite"
            conn = sqlite3.connect(str(db_path))

            # Initialize routes
            init_ab_testing(conn)

            # Check if router is properly configured
            if not hasattr(router, 'routes'):
                self.log_result(
                    "A/B Testing Routes",
                    False,
                    "Router not properly configured"
                )
                return False

            self.log_result(
                "A/B Testing Routes",
                True,
                f"Router configured with {len(router.routes)} routes"
            )
            return True

        except Exception as e:
            self.log_result("A/B Testing Routes", False, str(e))
            return False

    def verify_email_sender_integration(self) -> bool:
        """Verify email sender has A/B test integration"""
        try:
            email_sender_path = Path(__file__).parent / "agents" / "email_sender_agent.py"

            if not email_sender_path.exists():
                self.log_result(
                    "Email Sender Integration",
                    False,
                    "email_sender_agent.py not found"
                )
                return False

            # Check for A/B test imports and integration
            with open(email_sender_path, 'r') as f:
                content = f.read()

            if 'EmailVariantAssigner' not in content:
                self.log_result(
                    "Email Sender Integration",
                    False,
                    "EmailVariantAssigner not imported"
                )
                return False

            if '_check_and_apply_ab_test' not in content:
                self.log_result(
                    "Email Sender Integration",
                    False,
                    "A/B test method not implemented"
                )
                return False

            self.log_result(
                "Email Sender Integration",
                True,
                "A/B testing integrated in email sender"
            )
            return True

        except Exception as e:
            self.log_result("Email Sender Integration", False, str(e))
            return False

    def verify_ab_testing_dashboard(self) -> bool:
        """Verify dashboard files exist"""
        try:
            dashboard_path = Path(__file__).parent / "frontend" / "ab_testing_dashboard.html"

            if not dashboard_path.exists():
                self.log_result(
                    "A/B Testing Dashboard",
                    False,
                    "ab_testing_dashboard.html not found"
                )
                return False

            # Check for key components
            with open(dashboard_path, 'r') as f:
                content = f.read()

            required_elements = [
                'variant', 'conversion', 'test'  # Core A/B testing elements
            ]

            # Additional elements that may be in different forms (estadística, significancia, etc.)
            statistical_indicators = ['significance', 'estadístic', 'chi', 'conversión']

            missing = [elem for elem in required_elements if elem.lower() not in content.lower()]

            # Check for statistical indicators
            has_stats = any(stat.lower() in content.lower() for stat in statistical_indicators)

            if missing or not has_stats:
                self.log_result(
                    "A/B Testing Dashboard",
                    False,
                    f"Missing elements: {', '.join(missing)}"
                )
                return False

            self.log_result(
                "A/B Testing Dashboard",
                True,
                f"Dashboard file present ({len(content)} bytes)"
            )
            return True

        except Exception as e:
            self.log_result("A/B Testing Dashboard", False, str(e))
            return False

    def verify_dependencies(self) -> bool:
        """Verify required dependencies are installed"""
        try:
            import scipy
            import numpy

            scipy_version = scipy.__version__
            numpy_version = numpy.__version__

            self.log_result(
                "Dependencies",
                True,
                f"scipy {scipy_version}, numpy {numpy_version}"
            )
            return True

        except ImportError as e:
            self.log_result("Dependencies", False, f"Missing: {str(e)}")
            return False

    def run_all_verifications(self) -> bool:
        """Run complete verification suite"""
        logger.info("\n" + "="*70)
        logger.info("🚀 FASE 14 PHASE 2 - VERIFICATION SUITE")
        logger.info("="*70 + "\n")

        logger.info("📋 Running verification checks...\n")

        # Run all checks
        self.verify_database_schema()
        self.verify_dependencies()
        self.verify_variant_assigner()
        self.verify_statistical_tester()
        self.verify_ab_testing_routes()
        self.verify_email_sender_integration()
        self.verify_ab_testing_dashboard()

        # Summary
        logger.info("\n" + "="*70)
        logger.info("📊 VERIFICATION SUMMARY")
        logger.info("="*70)
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        logger.info(f"📈 Total: {self.passed + self.failed}")

        total = self.passed + self.failed
        if total > 0:
            success_rate = (self.passed / total) * 100
            logger.info(f"📊 Success Rate: {success_rate:.1f}%")

        if self.failed == 0:
            logger.info("\n🎉 PHASE 2 READY FOR PRODUCTION!")
            logger.info("="*70 + "\n")
            return True
        else:
            logger.warning(f"\n⚠️  {self.failed} verification(s) failed")
            logger.warning("="*70 + "\n")
            return False

    def export_results(self, filepath: str = None):
        """Export verification results to JSON"""
        if filepath is None:
            filepath = Path(__file__).parent / "fase14_phase2_verification.json"

        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'phase': 'FASE 14 - Phase 2',
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
    verifier = Phase2Verifier()
    success = verifier.run_all_verifications()
    verifier.export_results()

    sys.exit(0 if success else 1)
