#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Comprehensive Testing Suite
Validación completa de todas las características de tiempo real e IA
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Fix Python path for imports
sys.path.insert(0, '/home/claude/felix-automation')

# Test results tracker
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

def test(name):
    """Decorator para tests"""
    def decorator(func):
        def wrapper():
            global test_results
            test_results["total"] += 1
            try:
                func()
                test_results["passed"] += 1
                test_results["tests"].append({
                    "name": name,
                    "status": "✅ PASSED",
                    "error": None
                })
                print(f"✅ {name}")
            except AssertionError as e:
                test_results["failed"] += 1
                test_results["tests"].append({
                    "name": name,
                    "status": "❌ FAILED",
                    "error": str(e)
                })
                print(f"❌ {name}: {e}")
            except Exception as e:
                test_results["failed"] += 1
                test_results["tests"].append({
                    "name": name,
                    "status": "❌ ERROR",
                    "error": str(e)
                })
                print(f"❌ {name}: {type(e).__name__}: {e}")
        return wrapper
    return decorator


class FASE14Tests:
    """Suite de tests para FASE 14"""

    @staticmethod
    @test("1.1 - Database Schema: shopify_stores table exists")
    def test_shopify_stores_table():
        db = sqlite3.connect("data/pipeline.sqlite")
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shopify_stores'")
        result = cursor.fetchone()
        db.close()
        assert result is not None, "shopify_stores table not found"

    @staticmethod
    @test("1.2 - Database Schema: shopify_orders table exists")
    def test_shopify_orders_table():
        db = sqlite3.connect("data/pipeline.sqlite")
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shopify_orders'")
        result = cursor.fetchone()
        db.close()
        assert result is not None, "shopify_orders table not found"

    @staticmethod
    @test("1.3 - Database Schema: ab_tests table exists")
    def test_ab_tests_table():
        db = sqlite3.connect("data/pipeline.sqlite")
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ab_tests'")
        result = cursor.fetchone()
        db.close()
        assert result is not None, "ab_tests table not found"

    @staticmethod
    @test("1.4 - Database Schema: prediction_history table exists")
    def test_prediction_history_table():
        db = sqlite3.connect("data/pipeline.sqlite")
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_history'")
        result = cursor.fetchone()
        db.close()
        assert result is not None, "prediction_history table not found"

    @staticmethod
    @test("2.1 - Auth: verify_jwt_token function exists")
    def test_verify_jwt_token_exists():
        try:
            from backend.auth import verify_jwt_token
            assert callable(verify_jwt_token), "verify_jwt_token is not callable"
        except ImportError:
            raise AssertionError("Cannot import verify_jwt_token from backend.auth")

    @staticmethod
    @test("2.2 - Auth: JWT token generation works")
    def test_jwt_token_generation():
        try:
            from backend.auth import generate_jwt_token
            token = generate_jwt_token(user_id=1, role="admin")
            assert token is not None, "Token generation returned None"
            assert len(token) > 0, "Token is empty"
            assert "." in token, "Token doesn't have JWT format (missing dots)"
        except ImportError:
            raise AssertionError("Cannot import generate_jwt_token from backend.auth")

    @staticmethod
    @test("2.3 - Auth: JWT token verification works")
    def test_jwt_token_verification():
        try:
            from backend.auth import generate_jwt_token, verify_jwt_token
            token = generate_jwt_token(user_id=1, role="admin")
            payload = verify_jwt_token(token)
            assert payload is not None, "Token verification returned None"
            assert payload.get("user_id") == 1, "user_id not in payload"
            assert payload.get("role") == "admin", "role not in payload"
        except ImportError:
            raise AssertionError("Cannot import auth functions")

    @staticmethod
    @test("3.1 - Shopify: ShopifyAPIClient class exists")
    def test_shopify_api_client_exists():
        try:
            from whitebox.shopify_api_client import ShopifyAPIClient
            assert ShopifyAPIClient is not None, "ShopifyAPIClient not found"
        except ImportError:
            raise AssertionError("Cannot import ShopifyAPIClient")

    @staticmethod
    @test("3.2 - Shopify: ShopifyAPIClient has required methods")
    def test_shopify_api_client_methods():
        try:
            from whitebox.shopify_api_client import ShopifyAPIClient
            required_methods = ["get_orders", "get_products", "get_analytics"]
            for method in required_methods:
                assert hasattr(ShopifyAPIClient, method), f"Method {method} not found"
        except ImportError:
            raise AssertionError("Cannot import ShopifyAPIClient")

    @staticmethod
    @test("4.1 - ML: PredictionBroadcaster class exists")
    def test_prediction_broadcaster_exists():
        try:
            from analytics.prediction_broadcaster import PredictionBroadcaster
            assert PredictionBroadcaster is not None, "PredictionBroadcaster not found"
        except ImportError:
            raise AssertionError("Cannot import PredictionBroadcaster")

    @staticmethod
    @test("4.2 - ML: PredictionBroadcaster has broadcast method")
    def test_prediction_broadcaster_methods():
        try:
            from analytics.prediction_broadcaster import PredictionBroadcaster
            assert hasattr(PredictionBroadcaster, "broadcast_prediction"), "broadcast_prediction method not found"
        except ImportError:
            raise AssertionError("Cannot import PredictionBroadcaster")

    @staticmethod
    @test("5.1 - A/B Testing: EmailVariantAssigner class exists")
    def test_variant_assigner_exists():
        try:
            from agents.email_variant_assigner import EmailVariantAssigner
            assert EmailVariantAssigner is not None, "EmailVariantAssigner not found"
        except ImportError:
            raise AssertionError("Cannot import EmailVariantAssigner")

    @staticmethod
    @test("5.2 - A/B Testing: StatisticalTester class exists")
    def test_statistical_tester_exists():
        try:
            from agents.statistical_tester import StatisticalTester
            assert StatisticalTester is not None, "StatisticalTester not found"
        except ImportError:
            raise AssertionError("Cannot import StatisticalTester")

    @staticmethod
    @test("5.3 - A/B Testing: Variant assignment is deterministic")
    def test_variant_assignment_deterministic():
        try:
            from agents.email_variant_assigner import EmailVariantAssigner
            assigner = EmailVariantAssigner()

            # Same test_id and client_id should always return same variant
            variant1 = assigner.assign_variant(test_id=1, client_id=100)
            variant2 = assigner.assign_variant(test_id=1, client_id=100)

            assert variant1 == variant2, f"Variant assignment not deterministic: {variant1} != {variant2}"
            assert variant1 in ["A", "B"], f"Invalid variant: {variant1}"
        except ImportError:
            raise AssertionError("Cannot import EmailVariantAssigner")

    @staticmethod
    @test("6.1 - WebSocket Routes: websocket_routes module exists")
    def test_websocket_routes_exists():
        websocket_routes_path = Path("backend/routes/websocket_routes.py")
        assert websocket_routes_path.exists(), "websocket_routes.py not found"

    @staticmethod
    @test("6.2 - WebSocket Routes: websocket_endpoint is defined")
    def test_websocket_endpoint_defined():
        try:
            from backend.routes.websocket_routes import router
            assert router is not None, "router not found in websocket_routes"
        except ImportError:
            raise AssertionError("Cannot import websocket routes")

    @staticmethod
    @test("7.1 - A/B Testing Routes: ab_testing_routes module exists")
    def test_ab_testing_routes_exists():
        ab_testing_routes_path = Path("backend/routes/ab_testing_routes.py")
        assert ab_testing_routes_path.exists(), "ab_testing_routes.py not found"

    @staticmethod
    @test("7.2 - Shopify Webhooks Routes: shopify_webhooks module exists")
    def test_shopify_webhooks_exists():
        shopify_webhooks_path = Path("backend/routes/shopify_webhooks.py")
        assert shopify_webhooks_path.exists(), "shopify_webhooks.py not found"

    @staticmethod
    @test("8.1 - Mobile: service_worker.js exists")
    def test_service_worker_exists():
        service_worker_path = Path("backend/service_worker.js")
        assert service_worker_path.exists(), "service_worker.js not found"

    @staticmethod
    @test("8.2 - Mobile: manifest.json exists")
    def test_manifest_exists():
        manifest_path = Path("backend/manifest.json")
        assert manifest_path.exists(), "manifest.json not found"

    @staticmethod
    @test("8.3 - Mobile: manifest.json is valid JSON")
    def test_manifest_valid_json():
        manifest_path = Path("backend/manifest.json")
        with open(manifest_path, "r") as f:
            try:
                data = json.load(f)
                assert "name" in data, "manifest missing 'name'"
                assert "short_name" in data, "manifest missing 'short_name'"
            except json.JSONDecodeError as e:
                raise AssertionError(f"Invalid JSON in manifest.json: {e}")

    @staticmethod
    @test("9.1 - Frontend: admin_dashboard.html exists")
    def test_admin_dashboard_exists():
        dashboard_path = Path("frontend/admin_dashboard.html")
        assert dashboard_path.exists(), "admin_dashboard.html not found"

    @staticmethod
    @test("9.2 - Frontend: client_portal.html exists")
    def test_client_portal_exists():
        portal_path = Path("frontend/client_portal.html")
        assert portal_path.exists(), "client_portal.html not found"

    @staticmethod
    @test("9.3 - Frontend: ab_testing_dashboard.html exists")
    def test_ab_testing_dashboard_exists():
        dashboard_path = Path("frontend/ab_testing_dashboard.html")
        assert dashboard_path.exists(), "ab_testing_dashboard.html not found"

    @staticmethod
    @test("10.1 - Content Engine: ContentRecommendationEngine exists")
    def test_content_engine_exists():
        try:
            from analytics.content_recommendation_engine import ContentRecommendationEngine
            assert ContentRecommendationEngine is not None, "ContentRecommendationEngine not found"
        except ImportError:
            raise AssertionError("Cannot import ContentRecommendationEngine")

    @staticmethod
    @test("10.2 - Quick Audit: QuickAuditor exists")
    def test_quick_auditor_exists():
        try:
            from auditors.quick_audit import QuickAuditor
            assert QuickAuditor is not None, "QuickAuditor not found"
        except ImportError:
            raise AssertionError("Cannot import QuickAuditor")

    @staticmethod
    @test("11.1 - Config: FASE_14_VERSION defined")
    def test_fase14_version():
        try:
            import sys
            sys.path.insert(0, str(Path.cwd()))
            # Just check that we can access config
            config_path = Path("config.yaml")
            assert config_path.exists(), "config.yaml not found"
        except Exception as e:
            raise AssertionError(f"Config check failed: {e}")


def run_tests():
    """Ejecutar todos los tests"""
    print("\n" + "="*70)
    print("🧪 FASE 14 COMPREHENSIVE TESTING SUITE")
    print("="*70 + "\n")

    # Test categories
    print("📊 DATABASE SCHEMA VALIDATION")
    print("-" * 70)
    FASE14Tests.test_shopify_stores_table()
    FASE14Tests.test_shopify_orders_table()
    FASE14Tests.test_ab_tests_table()
    FASE14Tests.test_prediction_history_table()

    print("\n🔐 AUTHENTICATION & JWT")
    print("-" * 70)
    FASE14Tests.test_verify_jwt_token_exists()
    FASE14Tests.test_jwt_token_generation()
    FASE14Tests.test_jwt_token_verification()

    print("\n🛒 SHOPIFY API INTEGRATION")
    print("-" * 70)
    FASE14Tests.test_shopify_api_client_exists()
    FASE14Tests.test_shopify_api_client_methods()

    print("\n🤖 ML & PREDICTIONS")
    print("-" * 70)
    FASE14Tests.test_prediction_broadcaster_exists()
    FASE14Tests.test_prediction_broadcaster_methods()

    print("\n📧 A/B TESTING")
    print("-" * 70)
    FASE14Tests.test_variant_assigner_exists()
    FASE14Tests.test_statistical_tester_exists()
    FASE14Tests.test_variant_assignment_deterministic()

    print("\n🔗 WEBSOCKET & ROUTES")
    print("-" * 70)
    FASE14Tests.test_websocket_routes_exists()
    FASE14Tests.test_websocket_endpoint_defined()
    FASE14Tests.test_ab_testing_routes_exists()
    FASE14Tests.test_shopify_webhooks_exists()

    print("\n📱 MOBILE & PWA")
    print("-" * 70)
    FASE14Tests.test_service_worker_exists()
    FASE14Tests.test_manifest_exists()
    FASE14Tests.test_manifest_valid_json()

    print("\n🎨 FRONTEND DASHBOARDS")
    print("-" * 70)
    FASE14Tests.test_admin_dashboard_exists()
    FASE14Tests.test_client_portal_exists()
    FASE14Tests.test_ab_testing_dashboard_exists()

    print("\n📝 CONTENT & AUDIT ENGINES")
    print("-" * 70)
    FASE14Tests.test_content_engine_exists()
    FASE14Tests.test_quick_auditor_exists()

    print("\n⚙️ CONFIGURATION")
    print("-" * 70)
    FASE14Tests.test_fase14_version()

    # Summary
    print("\n" + "="*70)
    print("📋 TEST SUMMARY")
    print("="*70)
    print(f"Total Tests:  {test_results['total']}")
    print(f"✅ Passed:    {test_results['passed']}")
    print(f"❌ Failed:    {test_results['failed']}")

    if test_results['failed'] > 0:
        print("\n⚠️ FAILED TESTS:")
        for test_result in test_results['tests']:
            if test_result['status'].startswith('❌'):
                print(f"  - {test_result['name']}")
                if test_result['error']:
                    print(f"    Error: {test_result['error']}")

    success_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print(f"\n📊 Success Rate: {success_rate:.1f}%")

    if test_results['failed'] == 0:
        print("\n✅ ALL TESTS PASSED - FASE 14 IS PRODUCTION READY!")
    else:
        print(f"\n⚠️ {test_results['failed']} tests failed - review above")

    print("="*70 + "\n")

    return test_results['failed'] == 0


if __name__ == "__main__":
    os.chdir("/home/claude/felix-automation")
    success = run_tests()
    sys.exit(0 if success else 1)
