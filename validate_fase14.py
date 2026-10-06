#!/usr/bin/env python3
"""
FASE 14 Implementation Validation Script
Comprehensive verification of all FASE 14 components
Run this to verify the implementation is complete and ready for testing
"""

import os
import sys
import json
import sqlite3
from pathlib import Path

class ValidationReport:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.root = Path(__file__).parent

    def check(self, name, condition, details=""):
        """Record a validation check result"""
        status = "✅" if condition else "❌"
        self.checks.append({
            'name': name,
            'passed': condition,
            'details': details
        })
        if condition:
            self.passed += 1
            print(f"{status} {name}")
        else:
            self.failed += 1
            print(f"{status} {name}")
            if details:
                print(f"   └─ {details}")

    def warn(self, message):
        """Record a warning"""
        self.warnings += 1
        print(f"⚠️  {message}")

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*70)
        print("FASE 14 VALIDATION SUMMARY")
        print("="*70)
        print(f"✅ Passed:  {self.passed}")
        print(f"❌ Failed:  {self.failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        print("="*70)

        if self.failed == 0:
            print("\n🎉 ALL CHECKS PASSED - FASE 14 IMPLEMENTATION COMPLETE")
            print("Ready for PASO 15-16 Testing & Deployment")
            return 0
        else:
            print(f"\n⚠️  {self.failed} checks failed - review needed")
            return 1

    def run_all_checks(self):
        """Run all validation checks"""
        print("\n" + "="*70)
        print("FASE 14 IMPLEMENTATION VALIDATION")
        print("="*70 + "\n")

        self.check_file_structure()
        self.check_python_syntax()
        self.check_database_schema()
        self.check_api_endpoints()
        self.check_configuration()
        self.check_dependencies()

        return self.print_summary()

    def check_file_structure(self):
        """Verify all required files exist"""
        print("📁 Checking File Structure...")

        # Core new files
        new_files = {
            'backend/service_worker.js': 'Service Worker (PWA offline)',
            'backend/manifest.json': 'PWA Manifest',
            'frontend/mobile_optimization.js': 'Mobile Optimization Module',
            'frontend/ab_testing_dashboard.html': 'A/B Testing Dashboard',
            'agents/email_variant_assigner.py': 'Email Variant Assigner',
            'agents/statistical_tester.py': 'Statistical Tester',
            'analytics/prediction_broadcaster.py': 'Prediction Broadcaster',
            'whitebox/shopify_api_client.py': 'Shopify API Client',
            'backend/routes/shopify_webhooks.py': 'Shopify Webhooks',
            'backend/routes/ab_testing_routes.py': 'A/B Testing Routes',
            'MOBILE_OPTIMIZATION_GUIDE.md': 'Mobile Optimization Guide',
        }

        for file_path, description in new_files.items():
            full_path = self.root / file_path
            exists = full_path.exists()
            self.check(
                f"New file: {file_path}",
                exists,
                f"{description}" if exists else f"Missing: {full_path}"
            )

        # Modified files
        modified_files = [
            'backend/auth.py',
            'backend/events.py',
            'backend/websocket_manager.py',
            'init_database.py',
        ]

        for file_path in modified_files:
            full_path = self.root / file_path
            exists = full_path.exists()
            self.check(f"Modified: {file_path}", exists)

    def check_python_syntax(self):
        """Verify Python files compile correctly"""
        print("\n🐍 Checking Python Syntax...")

        import py_compile
        python_files = [
            'agents/email_variant_assigner.py',
            'agents/statistical_tester.py',
            'analytics/prediction_broadcaster.py',
            'whitebox/shopify_api_client.py',
            'backend/routes/shopify_webhooks.py',
            'backend/routes/ab_testing_routes.py',
        ]

        for py_file in python_files:
            full_path = self.root / py_file
            try:
                py_compile.compile(str(full_path), doraise=True)
                self.check(f"Syntax: {py_file}", True)
            except py_compile.PyCompileError as e:
                self.check(f"Syntax: {py_file}", False, str(e))

    def check_database_schema(self):
        """Verify database schema extensions"""
        print("\n🗄️  Checking Database Schema...")

        db_path = self.root / 'data' / 'pipeline.sqlite'
        if not db_path.exists():
            db_path = self.root / 'felix_automation.db'

        if not db_path.exists():
            self.check("Database file exists", False, f"No database found at {db_path}")
            return

        self.check("Database file exists", True)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check for new tables
            new_tables = [
                'shopify_stores',
                'shopify_orders',
                'shopify_webhooks',
                'prediction_history',
                'ab_tests',
                'ab_test_results',
                'anomalies'
            ]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cursor.fetchall()}

            for table in new_tables:
                self.check(
                    f"Database table: {table}",
                    table in existing_tables,
                    f"Table not found in database" if table not in existing_tables else ""
                )

            conn.close()

        except Exception as e:
            self.check("Database schema verification", False, str(e))

    def check_api_endpoints(self):
        """Verify API routes are registered"""
        print("\n🔌 Checking API Endpoints...")

        routes_to_check = [
            ('backend/routes/shopify_webhooks.py', [
                'POST /webhooks/shopify/orders',
                'Webhook signature validation'
            ]),
            ('backend/routes/ab_testing_routes.py', [
                'POST /api/tests',
                'GET /api/tests',
                'GET /api/tests/{id}/results'
            ]),
        ]

        for route_file, expected_patterns in routes_to_check:
            full_path = self.root / route_file
            try:
                with open(full_path) as f:
                    content = f.read()
                    for pattern in expected_patterns:
                        has_pattern = pattern.lower() in content.lower()
                        self.check(
                            f"API Route in {route_file}: {pattern}",
                            has_pattern
                        )
            except Exception as e:
                self.check(f"Read {route_file}", False, str(e))

    def check_configuration(self):
        """Verify configuration files"""
        print("\n⚙️  Checking Configuration...")

        config_file = self.root / 'config.yaml'
        if config_file.exists():
            try:
                import yaml
                with open(config_file) as f:
                    config = yaml.safe_load(f)

                # Check for FASE 14 config sections
                self.check(
                    "config.yaml has shopify section",
                    'shopify' in config
                )
                self.check(
                    "config.yaml has ab_testing section",
                    'ab_testing' in config
                )
                self.check(
                    "config.yaml has websocket section",
                    'websocket' in config
                )
            except ImportError:
                self.warn("PyYAML not installed - skipping YAML validation")
            except Exception as e:
                self.check("Parse config.yaml", False, str(e))
        else:
            self.warn("config.yaml not found - using defaults")

        env_file = self.root / '.env'
        self.check(".env file exists", env_file.exists())

    def check_dependencies(self):
        """Verify required dependencies"""
        print("\n📦 Checking Dependencies...")

        requirements_file = self.root / 'requirements.txt'
        required_packages = [
            'flask',
            'requests',
            'pyjwt',
            'scipy',
            'cryptography',
        ]

        if requirements_file.exists():
            try:
                with open(requirements_file) as f:
                    content = f.read().lower()
                    for package in required_packages:
                        has_package = package in content
                        self.check(
                            f"Dependency: {package}",
                            has_package,
                            f"Not found in requirements.txt" if not has_package else ""
                        )
            except Exception as e:
                self.check("Read requirements.txt", False, str(e))
        else:
            self.warn("requirements.txt not found")


def main():
    """Run validation"""
    validator = ValidationReport()
    exit_code = validator.run_all_checks()

    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    if exit_code == 0:
        print("1. Review MOBILE_OPTIMIZATION_GUIDE.md for integration steps")
        print("2. Review PASO_15_16_TESTING_PLAN.md for testing procedures")
        print("3. Deploy to staging: bash deploy_staging.sh")
        print("4. Run unit tests: pytest tests/")
        print("5. Run load tests: python3 load_testing.py")
        print("6. Deploy to production when ready")
    else:
        print("Please fix the issues identified above before proceeding.")

    print("="*70 + "\n")
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
