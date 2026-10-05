#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST SCRIPT - FASE 9: White-Box Audit Integration
Verifica: Credentials Manager, Shopify/Jumpseller/Code Auditors, Integration
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from whitebox.credentials_manager import CredentialsManager
from whitebox.shopify_auditor import ShopifyAuditor
from whitebox.jumpseller_auditor import JumpsellerAuditor
from whitebox.code_auditor import CodeAuditor

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FaseNineTestSuite:
    """Suite de pruebas para FASE 9"""

    def __init__(self):
        self.orchestrator = FelixAutomationOrchestrator()
        self.orchestrator.connect_database()
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        logger.info("✅ Test Suite FASE 9 inicializado")

    # ========================================================================
    # TEST 1: Credentials Manager
    # ========================================================================

    def test_credentials_manager(self):
        """Verifica encriptación/desencriptación de credenciales"""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: CREDENTIALS MANAGER")
        logger.info("="*70)

        try:
            creds_manager = CredentialsManager(ttl_seconds=3600)

            # Test 1a: Encriptación Shopify
            logger.info("  [1a] Encriptando credenciales Shopify...")
            shopify_creds = {
                "store_url": "test-store.myshopify.com",
                "access_token": "shpat_test1234567890abcdef",
                "api_version": "2024-01"
            }
            encrypted = creds_manager.encrypt_credentials("shopify", shopify_creds)
            logger.info(f"    ✅ Encriptadas exitosamente (longitud: {len(encrypted)})")

            # Test 1b: Desencriptación
            logger.info("  [1b] Desencriptando credenciales...")
            decrypted = creds_manager.decrypt_credentials("shopify")
            assert decrypted == shopify_creds, "Mismatch en desencriptación"
            logger.info("    ✅ Desencriptadas correctamente")

            # Test 1c: Encriptación Jumpseller
            logger.info("  [1c] Encriptando credenciales Jumpseller...")
            jumpseller_creds = {
                "api_key": "test_api_key_1234567890",
                "api_url": "https://api.jumpseller.com",
                "store_id": "12345"
            }
            encrypted = creds_manager.encrypt_credentials("jumpseller", jumpseller_creds)
            logger.info(f"    ✅ Encriptadas exitosamente (longitud: {len(encrypted)})")

            # Test 1d: Encriptación Code/SSH
            logger.info("  [1d] Encriptando credenciales Code/SSH...")
            code_creds = {
                "ssh_host": "example.com",
                "ssh_user": "deploy",
                "ssh_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n...",
                "ssh_port": 22
            }
            encrypted = creds_manager.encrypt_credentials("code", code_creds)
            logger.info(f"    ✅ Encriptadas exitosamente (longitud: {len(encrypted)})")

            # Test 1e: Cleanup
            logger.info("  [1e] Limpiando credenciales...")
            creds_manager.cleanup_platform_credentials("shopify")
            creds_manager.cleanup_platform_credentials("jumpseller")
            creds_manager.cleanup_platform_credentials("code")
            logger.info("    ✅ Credenciales limpiadas")

            self.test_results["tests"]["credentials_manager"] = {
                "status": "PASSED",
                "tests": 5,
                "passed": 5,
                "details": "Encriptación, desencriptación y cleanup funcionando"
            }
            logger.info("✅ TEST 1 PASSED: Credentials Manager")

        except Exception as e:
            logger.error(f"❌ TEST 1 FAILED: {str(e)}")
            self.test_results["tests"]["credentials_manager"] = {
                "status": "FAILED",
                "error": str(e)
            }

    # ========================================================================
    # TEST 2: Shopify Auditor
    # ========================================================================

    def test_shopify_auditor(self):
        """Verifica auditoría Shopify (demo mode)"""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: SHOPIFY AUDITOR")
        logger.info("="*70)

        try:
            auditor = ShopifyAuditor(self.orchestrator)

            # Test con datos demo
            logger.info("  [2a] Audiendo cliente de prueba (cliente_id=1)...")
            demo_creds = {
                "store_url": "raices.myshopify.com",
                "access_token": "shpat_demo123",
                "api_version": "2024-01"
            }

            result = auditor.audit_client(1, demo_creds)

            # Validar resultado
            assert "platform" in result, "Missing 'platform' in result"
            assert result["platform"] == "shopify", "Platform should be 'shopify'"
            assert "score" in result, "Missing 'score' in result"
            assert "findings" in result, "Missing 'findings' in result"

            logger.info(f"    ✅ Auditoría completada - Score: {result.get('score', 0)}/100")
            logger.info(f"    ✅ Findings: {list(result.get('findings', {}).keys())}")

            self.test_results["tests"]["shopify_auditor"] = {
                "status": "PASSED",
                "score": result.get("score", 0),
                "details": f"Auditoría completada con {len(result.get('findings', {}))} categorías"
            }
            logger.info("✅ TEST 2 PASSED: Shopify Auditor")

        except Exception as e:
            logger.error(f"❌ TEST 2 FAILED: {str(e)}")
            self.test_results["tests"]["shopify_auditor"] = {
                "status": "FAILED",
                "error": str(e)
            }

    # ========================================================================
    # TEST 3: Jumpseller Auditor
    # ========================================================================

    def test_jumpseller_auditor(self):
        """Verifica auditoría Jumpseller (demo mode)"""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: JUMPSELLER AUDITOR")
        logger.info("="*70)

        try:
            auditor = JumpsellerAuditor(self.orchestrator)

            # Test con datos demo
            logger.info("  [3a] Auditando cliente de prueba (cliente_id=1)...")
            demo_creds = {
                "api_key": "demo_key_123",
                "api_url": "https://api.jumpseller.com",
                "store_id": "99999"
            }

            result = auditor.audit_client(1, demo_creds)

            # Validar resultado
            assert "platform" in result, "Missing 'platform' in result"
            assert result["platform"] == "jumpseller", "Platform should be 'jumpseller'"
            assert "score" in result, "Missing 'score' in result"
            assert "findings" in result, "Missing 'findings' in result"

            logger.info(f"    ✅ Auditoría completada - Score: {result.get('score', 0)}/100")
            logger.info(f"    ✅ Findings: {list(result.get('findings', {}).keys())}")

            self.test_results["tests"]["jumpseller_auditor"] = {
                "status": "PASSED",
                "score": result.get("score", 0),
                "details": f"Auditoría completada con {len(result.get('findings', {}))} categorías"
            }
            logger.info("✅ TEST 3 PASSED: Jumpseller Auditor")

        except Exception as e:
            logger.error(f"❌ TEST 3 FAILED: {str(e)}")
            self.test_results["tests"]["jumpseller_auditor"] = {
                "status": "FAILED",
                "error": str(e)
            }

    # ========================================================================
    # TEST 4: Code Auditor
    # ========================================================================

    def test_code_auditor(self):
        """Verifica auditoría de código (demo mode)"""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: CODE AUDITOR")
        logger.info("="*70)

        try:
            auditor = CodeAuditor(self.orchestrator)

            # Test con datos demo
            logger.info("  [4a] Auditando código de cliente (cliente_id=1)...")
            demo_creds = {
                "repo_url": "https://github.com/example/repo",
                "ssh_host": "example.com",
                "ssh_user": "deploy",
                "ssh_port": 22,
                "ssh_key": "demo_key"
            }

            result = auditor.audit_client(1, demo_creds)

            # Validar resultado
            assert "platform" in result, "Missing 'platform' in result"
            assert result["platform"] == "code", "Platform should be 'code'"
            assert "score" in result, "Missing 'score' in result"
            assert "findings" in result, "Missing 'findings' in result"

            logger.info(f"    ✅ Auditoría completada - Score: {result.get('score', 0)}/100")
            logger.info(f"    ✅ Findings: {list(result.get('findings', {}).keys())}")

            self.test_results["tests"]["code_auditor"] = {
                "status": "PASSED",
                "score": result.get("score", 0),
                "details": f"Auditoría completada con {len(result.get('findings', {}))} categorías"
            }
            logger.info("✅ TEST 4 PASSED: Code Auditor")

        except Exception as e:
            logger.error(f"❌ TEST 4 FAILED: {str(e)}")
            self.test_results["tests"]["code_auditor"] = {
                "status": "FAILED",
                "error": str(e)
            }

    # ========================================================================
    # TEST 5: Multi-Platform Auditor Integration
    # ========================================================================

    def test_multiplatform_agent(self):
        """Verifica integración de auditor multi-plataforma"""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: MULTI-PLATFORM AUDITOR AGENT")
        logger.info("="*70)

        try:
            agent = MultiPlatformAuditorAgent(self.orchestrator)

            # Test 5a: Black-box audit
            logger.info("  [5a] Ejecutando auditoría BLACK-BOX (cliente_id=1)...")
            results = agent.audit_client(1, platforms=['web', 'facebook_ads', 'google_ads'])

            assert len(results) > 0, "No results from black-box audit"
            logger.info(f"    ✅ BLACK-BOX completada - Plataformas: {list(results.keys())}")

            for platform, data in results.items():
                if 'overall_score' in data:
                    logger.info(f"       - {platform}: {data['overall_score']}/100")

            # Test 5b: White-box audit (Shopify)
            logger.info("  [5b] Ejecutando auditoría WHITE-BOX (Shopify)...")
            whitebox_result = agent.audit_client_whitebox(
                client_id=1,
                platform="shopify",
                credentials={
                    "store_url": "raices.myshopify.com",
                    "access_token": "shpat_test123"
                }
            )

            assert "platform" in whitebox_result, "Missing platform in whitebox result"
            logger.info(f"    ✅ WHITE-BOX (Shopify) completada - Score: {whitebox_result.get('score', 0)}/100")

            # Test 5c: White-box audit (Jumpseller)
            logger.info("  [5c] Ejecutando auditoría WHITE-BOX (Jumpseller)...")
            whitebox_result = agent.audit_client_whitebox(
                client_id=1,
                platform="jumpseller",
                credentials={
                    "api_key": "test_key",
                    "api_url": "https://api.jumpseller.com",
                    "store_id": "12345"
                }
            )

            assert "platform" in whitebox_result, "Missing platform in whitebox result"
            logger.info(f"    ✅ WHITE-BOX (Jumpseller) completada - Score: {whitebox_result.get('score', 0)}/100")

            self.test_results["tests"]["multiplatform_agent"] = {
                "status": "PASSED",
                "black_box_platforms": list(results.keys()),
                "white_box_tested": ["shopify", "jumpseller"],
                "details": "Agente funcionando con auditorías black-box y white-box"
            }
            logger.info("✅ TEST 5 PASSED: Multi-Platform Auditor Agent")

        except Exception as e:
            logger.error(f"❌ TEST 5 FAILED: {str(e)}")
            self.test_results["tests"]["multiplatform_agent"] = {
                "status": "FAILED",
                "error": str(e)
            }

    # ========================================================================
    # TEST 6: Database Integration
    # ========================================================================

    def test_database_integration(self):
        """Verifica que auditorías se guardan correctamente en BD"""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: DATABASE INTEGRATION")
        logger.info("="*70)

        try:
            # Contar auditorías antes
            audits_before = len(self.orchestrator.get_audits_by_client(1))
            logger.info(f"  [6a] Auditorías en BD (cliente_id=1): {audits_before}")

            # Crear auditoría de prueba
            from orchestrator import Audit
            audit = Audit(
                client_id=1,
                audit_type="whitebox",
                platform="test",
                status="completed"
            )
            audit_id = self.orchestrator.create_audit(audit)
            logger.info(f"    ✅ Auditoría creada (id={audit_id})")

            # Actualizar score
            self.orchestrator.update_audit_score(
                audit_id,
                score=85,
                details={"test": "data"}
            )
            logger.info(f"    ✅ Score actualizado: 85/100")

            # Contar auditorías después
            audits_after = len(self.orchestrator.get_audits_by_client(1))
            logger.info(f"  [6b] Auditorías en BD (cliente_id=1): {audits_after}")

            assert audits_after > audits_before, "Auditoría no se guardó en BD"
            logger.info(f"    ✅ Auditoría guardada correctamente (total: {audits_after})")

            self.test_results["tests"]["database_integration"] = {
                "status": "PASSED",
                "audits_before": audits_before,
                "audits_after": audits_after,
                "details": f"Auditorías guardadas correctamente en BD"
            }
            logger.info("✅ TEST 6 PASSED: Database Integration")

        except Exception as e:
            logger.error(f"❌ TEST 6 FAILED: {str(e)}")
            self.test_results["tests"]["database_integration"] = {
                "status": "FAILED",
                "error": str(e)
            }

    # ========================================================================
    # Run All Tests
    # ========================================================================

    def run_all_tests(self):
        """Ejecuta todos los tests"""
        logger.info("\n")
        logger.info("╔════════════════════════════════════════════════════════════════╗")
        logger.info("║         FASE 9: WHITE-BOX AUDIT INTEGRATION - TEST SUITE      ║")
        logger.info("╚════════════════════════════════════════════════════════════════╝")

        self.test_credentials_manager()
        self.test_shopify_auditor()
        self.test_jumpseller_auditor()
        self.test_code_auditor()
        self.test_multiplatform_agent()
        self.test_database_integration()

        # Resumen
        self._print_summary()

        # Cerrar BD
        self.orchestrator.close_database()

    def _print_summary(self):
        """Imprime resumen de tests"""
        logger.info("\n" + "="*70)
        logger.info("RESUMEN DE TESTS - FASE 9")
        logger.info("="*70)

        total_tests = len(self.test_results["tests"])
        passed_tests = sum(1 for t in self.test_results["tests"].values() if t.get("status") == "PASSED")
        failed_tests = total_tests - passed_tests

        logger.info(f"\n📊 RESULTADOS:")
        logger.info(f"   ✅ Passed: {passed_tests}/{total_tests}")
        logger.info(f"   ❌ Failed: {failed_tests}/{total_tests}")

        logger.info(f"\n📋 DETALLE POR TEST:")
        for test_name, result in self.test_results["tests"].items():
            status = "✅ PASSED" if result.get("status") == "PASSED" else "❌ FAILED"
            logger.info(f"   {status}: {test_name}")
            if result.get("details"):
                logger.info(f"      {result['details']}")

        if failed_tests == 0:
            logger.info("\n🎉 ¡TODOS LOS TESTS PASARON! FASE 9 LISTA PARA PRODUCCIÓN")
        else:
            logger.info(f"\n⚠️  {failed_tests} TEST(S) FALLARON - REVISAR LOGS ARRIBA")

        # Guardar resultados
        with open("/tmp/fase_9_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        logger.info(f"\n💾 Resultados guardados: /tmp/fase_9_test_results.json")

        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
        }


def main():
    """Ejecuta suite de tests FASE 9"""
    suite = FaseNineTestSuite()
    suite.run_all_tests()


if __name__ == "__main__":
    main()
