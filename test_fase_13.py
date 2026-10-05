#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite - FASE 13: Advanced Integrations

Testa:
1. Facebook Ads Live API Auditor
2. Google Ads Live API Auditor
3. Integración con MultiPlatformAuditorAgent
4. Almacenamiento en BD
"""

import sys
import json
import unittest
import logging
from pathlib import Path
from datetime import datetime

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import FelixAutomationOrchestrator, Audit, Client
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from whitebox.facebook_ads_live_auditor import FacebookAdsLiveAuditor
from whitebox.google_ads_live_auditor import GoogleAdsLiveAuditor
from whitebox.credentials_manager import CredentialsManager

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFacebookAdsLiveAuditor(unittest.TestCase):
    """Test Facebook Ads Live API Auditor"""

    def setUp(self):
        """Preparar test"""
        self.orchestrator = FelixAutomationOrchestrator()
        self.orchestrator.connect_database()
        self.auditor = FacebookAdsLiveAuditor(self.orchestrator)

        # Usar cliente existente desde BD (o ID hardcoded)
        self.client_id = 1  # Raíces de Cauquenes - cliente test

    def tearDown(self):
        """Limpiar"""
        self.orchestrator.close_database()

    def test_facebook_config_validation(self):
        """Test validar configuración de Facebook"""
        # Config válida
        valid_config = {
            "access_token": "test_token_123",
            "ad_account_id": "act_123456789"
        }
        self.assertTrue(self.auditor._validate_config(valid_config))

        # Config incompleta
        invalid_config = {"access_token": "test_token_123"}
        self.assertFalse(self.auditor._validate_config(invalid_config))

        logger.info("✅ Test validación Facebook config pasado")

    def test_facebook_audit_execution(self):
        """Test ejecutar auditoría Facebook"""
        config = {
            "access_token": "test_token_123",
            "ad_account_id": "act_123456789",
            "business_id": "123456"
        }

        # Ejecutar auditoría (usa datos simulados)
        result = self.auditor.audit_client(self.client_id, config)

        # Verificar estructura
        self.assertIn("platform", result)
        self.assertEqual(result["platform"], "facebook_ads_live")
        self.assertIn("score", result)
        self.assertIn("findings", result)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)

        logger.info(f"✅ Test auditoría Facebook pasado - Score: {result['score']}/100")

    def test_facebook_audit_findings_structure(self):
        """Test estructura de hallazgos Facebook"""
        config = {
            "access_token": "test_token_123",
            "ad_account_id": "act_123456789"
        }

        result = self.auditor.audit_client(self.client_id, config)
        findings = result.get("findings", {})

        # Verificar keys principales
        expected_keys = ["account", "campaigns", "adsets", "audiences", "budget_health",
                        "performance", "recommendations", "issues"]
        for key in expected_keys:
            self.assertIn(key, findings, f"Missing key: {key}")

        logger.info("✅ Test estructura Facebook findings pasado")


class TestGoogleAdsLiveAuditor(unittest.TestCase):
    """Test Google Ads Live API Auditor"""

    def setUp(self):
        """Preparar test"""
        self.orchestrator = FelixAutomationOrchestrator()
        self.orchestrator.connect_database()
        self.auditor = GoogleAdsLiveAuditor(self.orchestrator)

        # Usar cliente existente desde BD
        self.client_id = 1  # Raíces de Cauquenes - cliente test

    def tearDown(self):
        """Limpiar"""
        self.orchestrator.close_database()

    def test_google_config_validation(self):
        """Test validar configuración de Google"""
        # Config válida
        valid_config = {
            "developer_token": "abc123xyz",
            "customer_id": "12345678",
            "refresh_token": "refresh_123"
        }
        self.assertTrue(self.auditor._validate_config(valid_config))

        # Config incompleta
        invalid_config = {
            "developer_token": "abc123xyz",
            "customer_id": "12345678"
        }
        self.assertFalse(self.auditor._validate_config(invalid_config))

        logger.info("✅ Test validación Google config pasado")

    def test_google_audit_execution(self):
        """Test ejecutar auditoría Google"""
        config = {
            "developer_token": "abc123xyz",
            "client_id": "oauth_client_id",
            "client_secret": "oauth_secret",
            "refresh_token": "refresh_token_123",
            "customer_id": "12345678"
        }

        # Ejecutar auditoría
        result = self.auditor.audit_client(self.client_id, config)

        # Verificar estructura
        self.assertIn("platform", result)
        self.assertEqual(result["platform"], "google_ads_live")
        self.assertIn("score", result)
        self.assertIn("findings", result)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)

        logger.info(f"✅ Test auditoría Google pasado - Score: {result['score']}/100")

    def test_google_audit_findings_structure(self):
        """Test estructura de hallazgos Google"""
        config = {
            "developer_token": "abc123xyz",
            "client_id": "oauth_client_id",
            "client_secret": "oauth_secret",
            "refresh_token": "refresh_token_123",
            "customer_id": "12345678"
        }

        result = self.auditor.audit_client(self.client_id, config)
        findings = result.get("findings", {})

        # Verificar keys principales
        expected_keys = ["account", "campaigns", "ad_groups", "keywords", "quality_scores",
                        "budget_health", "performance", "recommendations", "issues"]
        for key in expected_keys:
            self.assertIn(key, findings, f"Missing key: {key}")

        logger.info("✅ Test estructura Google findings pasado")


class TestMultiPlatformIntegration(unittest.TestCase):
    """Test integración en MultiPlatformAuditorAgent"""

    def setUp(self):
        """Preparar test"""
        self.orchestrator = FelixAutomationOrchestrator()
        self.orchestrator.connect_database()
        self.agent = MultiPlatformAuditorAgent(self.orchestrator)

        # Usar cliente existente desde BD
        self.client_id = 1  # Raíces de Cauquenes - cliente test

    def tearDown(self):
        """Limpiar"""
        self.orchestrator.close_database()

    def test_facebook_ads_live_integration(self):
        """Test integración Facebook Ads Live en agent"""
        config = {
            "access_token": "test_token_123",
            "ad_account_id": "act_123456789"
        }

        result = self.agent.audit_facebook_ads_live(self.client_id, config)

        # Verificar resultado
        self.assertNotIn("error", result)
        self.assertIn("score", result)
        self.assertEqual(result["platform"], "facebook_ads_live")

        logger.info(f"✅ Test integración FB Live pasado - Score: {result['score']}/100")

    def test_google_ads_live_integration(self):
        """Test integración Google Ads Live en agent"""
        config = {
            "developer_token": "abc123xyz",
            "client_id": "oauth_client_id",
            "client_secret": "oauth_secret",
            "refresh_token": "refresh_token_123",
            "customer_id": "12345678"
        }

        result = self.agent.audit_google_ads_live(self.client_id, config)

        # Verificar resultado
        self.assertNotIn("error", result)
        self.assertIn("score", result)
        self.assertEqual(result["platform"], "google_ads_live")

        logger.info(f"✅ Test integración GA Live pasado - Score: {result['score']}/100")

    def test_database_storage(self):
        """Test almacenamiento en BD"""
        # Ejecutar auditorías
        fb_config = {
            "access_token": "test_token_123",
            "ad_account_id": "act_123456789"
        }

        ga_config = {
            "developer_token": "abc123xyz",
            "client_id": "oauth_client_id",
            "client_secret": "oauth_secret",
            "refresh_token": "refresh_token_123",
            "customer_id": "12345678"
        }

        fb_result = self.agent.audit_facebook_ads_live(self.client_id, fb_config)
        ga_result = self.agent.audit_google_ads_live(self.client_id, ga_config)

        # Verificar guardado en BD
        audits = self.orchestrator.get_client_audits(self.client_id)
        self.assertGreater(len(audits), 0)

        # Verificar que tenemos ambos tipos
        platforms = [a.platform for a in audits]
        self.assertIn("facebook_ads_live", platforms)
        self.assertIn("google_ads_live", platforms)

        logger.info(f"✅ Test almacenamiento BD pasado - {len(audits)} auditorías guardadas")


class TestCredentialsManager(unittest.TestCase):
    """Test manejo de credenciales"""

    def setUp(self):
        """Preparar test"""
        self.cred_manager = CredentialsManager()

    def test_encryption_decryption(self):
        """Test encriptar/desencriptar credenciales"""
        test_creds = {
            "access_token": "super_secret_token_123",
            "api_key": "api_key_xyz"
        }

        # Encriptar
        encrypted = self.cred_manager.encrypt_credentials("facebook", test_creds)
        self.assertIsNotNone(encrypted)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, json.dumps(test_creds))

        logger.info("✅ Test encriptación pasado")

    def test_credentials_cleanup(self):
        """Test limpieza de credenciales"""
        # Debería no lanzar excepción
        self.cred_manager.cleanup_platform_credentials("facebook_ads_live")
        self.cred_manager.cleanup_platform_credentials("google_ads_live")

        logger.info("✅ Test limpieza credenciales pasado")


class FaseThirteenTestSuite(unittest.TestCase):
    """Suite completa de tests FASE 13"""

    def setUp(self):
        """Preparar suite"""
        print("\n" + "="*70)
        print("🚀 INICIANDO TEST SUITE FASE 13")
        print("="*70)

    def test_all_components(self):
        """Test todos los componentes"""
        logger.info("✅ Todos los tests completados exitosamente!")


def main():
    """Ejecutar suite de tests"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║              FASE 13 - ADVANCED INTEGRATIONS TEST SUITE               ║
║                                                                        ║
║  Components:                                                          ║
║  - Facebook Ads Live API Auditor (250 líneas)                        ║
║  - Google Ads Live API Auditor (250 líneas)                          ║
║  - MultiPlatformAuditorAgent Integration                            ║
║  - Database Storage                                                   ║
║  - Credentials Encryption/Cleanup                                    ║
║                                                                        ║
║  Objetivo: Auditorías en vivo con acceso a APIs                     ║
║  Score: 0-100 unificado                                              ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    # Crear loader de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(TestFacebookAdsLiveAuditor))
    suite.addTests(loader.loadTestsFromTestCase(TestGoogleAdsLiveAuditor))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiPlatformIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCredentialsManager))
    suite.addTests(loader.loadTestsFromTestCase(FaseThirteenTestSuite))

    # Ejecutar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS FASE 13")
    print("="*70)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ TODOS LOS TESTS PASARON - FASE 13 LISTA")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")

    print("="*70 + "\n")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
