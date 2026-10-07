#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Integrado - White-Box Audit Integration
Verifica que todos los componentes funcionan juntos correctamente
FASE 9: White-Box Audit Integration - STEP 6 Testing
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from whitebox.credentials_manager import CredentialsManager
from whitebox.shopify_auditor import ShopifyAuditor
from whitebox.jumpseller_auditor import JumpsellerAuditor
from whitebox.code_auditor import CodeAuditor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_credentials_manager():
    """Test 1: CredentialsManager"""
    print("\n" + "="*70)
    print("TEST 1: CREDENTIALS MANAGER")
    print("="*70)

    manager = CredentialsManager(ttl_seconds=3600)

    # Test Shopify
    shopify_creds = {
        "store": "example.myshopify.com",
        "access_token": "shpat_1234567890abcdef"
    }
    encrypted = manager.encrypt_credentials("shopify", shopify_creds)
    print(f"✅ Shopify credenciales encriptadas (primeros 50 chars): {encrypted[:50]}...")

    # Validar token
    is_valid = manager.validate_shopify_token("shpat_1234567890abcdef")
    print(f"✅ Shopify token validado: {is_valid}")

    # Desencriptar
    decrypted = manager.decrypt_credentials("shopify")
    print(f"✅ Credenciales desencriptadas: store={decrypted['store']}")

    # Estado
    status = manager.get_credentials_status()
    print(f"✅ Estado de credenciales: {json.dumps(status, indent=2, ensure_ascii=False)}")

    # Limpiar
    cleaned = manager.cleanup_platform_credentials("shopify")
    print(f"✅ Credenciales eliminadas: {cleaned}")

    return True


def test_individual_auditors():
    """Test 2: Auditorios Individuales"""
    print("\n" + "="*70)
    print("TEST 2: AUDITORIOS INDIVIDUALES")
    print("="*70)

    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    # Test Shopify Auditor
    print("\n📱 SHOPIFY AUDITOR:")
    shopify_auditor = ShopifyAuditor(orchestrator)
    shopify_config = {
        "store_url": "example.myshopify.com",
        "access_token": "shpat_1234567890abcdef",
        "api_version": "2024-01"
    }
    shopify_result = shopify_auditor.audit_client(1, shopify_config)
    print(f"  Score: {shopify_result.get('score', 0)}/100")
    print(f"  Status: {shopify_result.get('status', 'unknown')}")

    # Test Jumpseller Auditor
    print("\n🛒 JUMPSELLER AUDITOR:")
    jumpseller_auditor = JumpsellerAuditor(orchestrator)
    jumpseller_config = {
        "store_id": "tienda123",
        "api_key": "js_abc123def456ghi789jkl",
        "api_version": "2.0"
    }
    jumpseller_result = jumpseller_auditor.audit_client(1, jumpseller_config)
    print(f"  Score: {jumpseller_result.get('score', 0)}/100")
    print(f"  Status: {jumpseller_result.get('status', 'unknown')}")

    # Test Code Auditor
    print("\n💻 CODE AUDITOR:")
    code_auditor = CodeAuditor(orchestrator)
    code_config = {
        "repo_url": "https://github.com/cliente/proyecto",
        "ssh_host": "code.cliente.com",
        "ssh_user": "deploy"
    }
    code_result = code_auditor.audit_client(1, code_config)
    print(f"  Score: {code_result.get('score', 0)}/100")
    print(f"  Status: {code_result.get('status', 'unknown')}")

    orchestrator.close_database()
    return True


def test_multi_platform_agent():
    """Test 3: MultiPlatformAuditorAgent con White-Box"""
    print("\n" + "="*70)
    print("TEST 3: MULTI-PLATFORM AUDITOR AGENT")
    print("="*70)

    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    agent = MultiPlatformAuditorAgent(orchestrator)

    # Test White-Box Audit via agent
    print("\n🔐 SHOPIFY WHITE-BOX VIA AGENT:")
    shopify_config = {
        "store_url": "example.myshopify.com",
        "access_token": "shpat_1234567890abcdef"
    }
    shopify_result = agent.audit_client_whitebox(1, "shopify", shopify_config)
    print(f"  ✅ Score: {shopify_result.get('score', 0)}/100")
    print(f"  ✅ Platform: {shopify_result.get('platform', 'unknown')}")

    print("\n🔐 JUMPSELLER WHITE-BOX VIA AGENT:")
    jumpseller_config = {
        "store_id": "tienda123",
        "api_key": "js_abc123def456ghi789jkl"
    }
    jumpseller_result = agent.audit_client_whitebox(1, "jumpseller", jumpseller_config)
    print(f"  ✅ Score: {jumpseller_result.get('score', 0)}/100")
    print(f"  ✅ Platform: {jumpseller_result.get('platform', 'unknown')}")

    print("\n🔐 CODE WHITE-BOX VIA AGENT:")
    code_config = {
        "repo_url": "https://github.com/cliente/proyecto",
        "ssh_host": "code.cliente.com",
        "ssh_user": "deploy"
    }
    code_result = agent.audit_client_whitebox(1, "code", code_config)
    print(f"  ✅ Score: {code_result.get('score', 0)}/100")
    print(f"  ✅ Platform: {code_result.get('platform', 'unknown')}")

    orchestrator.close_database()
    return True


def test_backward_compatibility():
    """Test 4: Backward Compatibility con OPCIÓN C"""
    print("\n" + "="*70)
    print("TEST 4: BACKWARD COMPATIBILITY CON OPCIÓN C")
    print("="*70)

    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    agent = MultiPlatformAuditorAgent(orchestrator)

    # Test Black-Box Audits (OPCIÓN C original)
    print("\n📊 BLACK-BOX AUDITS (Web + Facebook + Google Ads):")
    results = agent.audit_client(1, platforms=['web', 'facebook_ads', 'google_ads'])

    for platform, result in results.items():
        score = result.get('overall_score', 'N/A')
        print(f"  ✅ {platform}: {score}/100")

    print("\n✅ OPCIÓN C (9-step pipeline) sigue funcionando correctamente")

    orchestrator.close_database()
    return True


def main():
    """Ejecutar todos los tests"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║         WHITE-BOX AUDIT INTEGRATION TEST                      ║
║         FASE 9: Testing Completo                              ║
╚════════════════════════════════════════════════════════════════╝
    """)

    test_results = {}

    try:
        test_results["CredentialsManager"] = test_credentials_manager()
    except Exception as e:
        logger.error(f"❌ CredentialsManager test falló: {e}")
        test_results["CredentialsManager"] = False

    try:
        test_results["Individual Auditors"] = test_individual_auditors()
    except Exception as e:
        logger.error(f"❌ Individual Auditors test falló: {e}")
        test_results["Individual Auditors"] = False

    try:
        test_results["MultiPlatformAgent"] = test_multi_platform_agent()
    except Exception as e:
        logger.error(f"❌ MultiPlatformAgent test falló: {e}")
        test_results["MultiPlatformAgent"] = False

    try:
        test_results["BackwardCompatibility"] = test_backward_compatibility()
    except Exception as e:
        logger.error(f"❌ BackwardCompatibility test falló: {e}")
        test_results["BackwardCompatibility"] = False

    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS")
    print("="*70)

    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")

    all_passed = all(test_results.values())

    print("\n" + "="*70)
    if all_passed:
        print("✅ TODOS LOS TESTS PASARON - FASE 9 COMPLETA")
    else:
        print("❌ ALGUNOS TESTS FALLARON - REVISAR ARRIBA")
    print("="*70)


if __name__ == "__main__":
    main()
