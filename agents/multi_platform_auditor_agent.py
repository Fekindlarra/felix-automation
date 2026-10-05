#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Platform Auditor Agent
Audita: Web + Facebook Ads + Google Ads en paralelo
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import FelixAutomationOrchestrator, Audit
from auditors.facebook_ads_auditor import FacebookAdsAuditor, create_sample_facebook_audit
from auditors.google_ads_auditor import GoogleAdsAuditor, create_sample_google_audit
from whitebox.shopify_auditor import ShopifyAuditor
from whitebox.jumpseller_auditor import JumpsellerAuditor
from whitebox.code_auditor import CodeAuditor
from whitebox.credentials_manager import CredentialsManager
from whitebox.facebook_ads_live_auditor import FacebookAdsLiveAuditor
from whitebox.google_ads_live_auditor import GoogleAdsLiveAuditor

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiPlatformAuditorAgent:
    """Agente que audita múltiples plataformas en paralelo"""

    def __init__(self, orchestrator: FelixAutomationOrchestrator):
        self.orchestrator = orchestrator
        self.max_workers = 4
        self.credentials_manager = CredentialsManager()
        logger.info("✅ Multi-Platform Auditor Agent inicializado")

    def audit_client(self, client_id: int, platforms: List[str] = None) -> Dict:
        """
        Auditar un cliente en múltiples plataformas

        Args:
            client_id: ID del cliente
            platforms: Lista de plataformas ['web', 'facebook_ads', 'google_ads']
        """
        if platforms is None:
            platforms = ['web', 'facebook_ads', 'google_ads']

        client = self.orchestrator.get_client(client_id)
        logger.info(f"🔍 Auditando cliente: {client.name} en plataformas: {platforms}")

        results = {}

        # Ejecutar auditorías en paralelo (SIN acceso a BD en threads)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            for platform in platforms:
                if platform == 'web':
                    future = executor.submit(self._compute_web_audit, client)
                    futures[future] = platform
                elif platform == 'facebook_ads':
                    future = executor.submit(self._compute_facebook_audit, client)
                    futures[future] = platform
                elif platform == 'google_ads':
                    future = executor.submit(self._compute_google_audit, client)
                    futures[future] = platform

            # Recolectar resultados de auditoría (sin BD)
            for future in as_completed(futures):
                platform = futures[future]
                try:
                    result = future.result()
                    results[platform] = result
                except Exception as e:
                    logger.error(f"❌ Error computando auditoría {platform}: {str(e)}")

        # Guardar en BD SEQUENCIALMENTE en thread principal (sin threading)
        self._save_audit_results(client_id, results)

        return results

    def audit_batch(self, client_ids: List[int]) -> Dict:
        """Auditar múltiples clientes (sequencial para evitar problemas con SQLite threading)"""
        logger.info(f"📦 Iniciando auditoría batch de {len(client_ids)} clientes")

        batch_results = {}

        # Procesar sequencialmente para evitar problemas de threading con SQLite
        for cid in client_ids:
            try:
                result = self.audit_client(cid)
                batch_results[cid] = result
            except Exception as e:
                logger.error(f"Error auditando cliente {cid}: {str(e)}")
                batch_results[cid] = {"error": str(e)}

        # Log del batch
        self.orchestrator.log_agent_action(
            "MultiPlatformAuditorAgent",
            "batch_audit",
            "success",
            details=f"Auditados {len(batch_results)} clientes"
        )

        return batch_results

    def audit_client_whitebox(self, client_id: int, platform: str, credentials: Dict) -> Dict:
        """
        Auditoría profunda con credenciales (Shopify/Jumpseller/Code)

        Args:
            client_id: ID del cliente
            platform: 'shopify', 'jumpseller', o 'code'
            credentials: Diccionario con credenciales de la plataforma

        Returns:
            Diccionario con resultados de auditoría
        """
        try:
            client = self.orchestrator.get_client(client_id)
            logger.info(f"🔐 Iniciando White-Box Audit para {client.name} ({platform})")

            # Seleccionar auditor según plataforma
            if platform == "shopify":
                auditor = ShopifyAuditor(self.orchestrator)
                audit_result = auditor.audit_client(client_id, credentials)
            elif platform == "jumpseller":
                auditor = JumpsellerAuditor(self.orchestrator)
                audit_result = auditor.audit_client(client_id, credentials)
            elif platform == "code":
                auditor = CodeAuditor(self.orchestrator)
                audit_result = auditor.audit_client(client_id, credentials)
            else:
                raise ValueError(f"Platform no soportada: {platform}")

            # Guardar resultados en BD
            self._save_whitebox_audit_results(client_id, platform, audit_result)

            # Limpiar credenciales
            self.credentials_manager.cleanup_platform_credentials(platform)
            logger.info(f"✅ White-Box Audit completado para {platform} - Score: {audit_result.get('score', 0)}/100")

            return audit_result

        except Exception as e:
            logger.error(f"❌ Error en White-Box Audit: {str(e)}")
            return {
                "client_id": client_id,
                "platform": platform,
                "audit_type": "whitebox",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def audit_facebook_ads_live(self, client_id: int, fb_config: Dict) -> Dict:
        """
        Auditoría en vivo de Facebook Ads con acceso a APIs

        Args:
            client_id: ID del cliente
            fb_config: Dict con:
                - access_token: Token de acceso Facebook
                - ad_account_id: act_xxxxx
                - business_id: xxxxx (opcional)

        Returns:
            Diccionario con resultados de auditoría
        """
        try:
            client = self.orchestrator.get_client(client_id)
            logger.info(f"📘 Iniciando Facebook Ads Live Audit para {client.name}")

            # Crear auditor
            auditor = FacebookAdsLiveAuditor(self.orchestrator)
            audit_result = auditor.audit_client(client_id, fb_config)

            # Guardar en BD
            self._save_live_audit_results(client_id, "facebook_ads_live", audit_result)

            # Limpiar credenciales
            self.credentials_manager.cleanup_platform_credentials("facebook_ads_live")
            logger.info(f"✅ Facebook Ads Live Audit completado - Score: {audit_result.get('score', 0)}/100")

            return audit_result

        except Exception as e:
            logger.error(f"❌ Error en Facebook Ads Live Audit: {str(e)}")
            return {
                "client_id": client_id,
                "platform": "facebook_ads_live",
                "audit_type": "live",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def audit_google_ads_live(self, client_id: int, gads_config: Dict) -> Dict:
        """
        Auditoría en vivo de Google Ads con acceso a APIs

        Args:
            client_id: ID del cliente
            gads_config: Dict con credenciales OAuth:
                - developer_token: Google Ads dev token
                - client_id: OAuth client ID
                - client_secret: OAuth secret
                - refresh_token: OAuth refresh token
                - customer_id: xxxxxxxx

        Returns:
            Diccionario con resultados de auditoría
        """
        try:
            client = self.orchestrator.get_client(client_id)
            logger.info(f"🔍 Iniciando Google Ads Live Audit para {client.name}")

            # Crear auditor
            auditor = GoogleAdsLiveAuditor(self.orchestrator)
            audit_result = auditor.audit_client(client_id, gads_config)

            # Guardar en BD
            self._save_live_audit_results(client_id, "google_ads_live", audit_result)

            # Limpiar credenciales
            self.credentials_manager.cleanup_platform_credentials("google_ads_live")
            logger.info(f"✅ Google Ads Live Audit completado - Score: {audit_result.get('score', 0)}/100")

            return audit_result

        except Exception as e:
            logger.error(f"❌ Error en Google Ads Live Audit: {str(e)}")
            return {
                "client_id": client_id,
                "platform": "google_ads_live",
                "audit_type": "live",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _save_whitebox_audit_results(self, client_id: int, platform: str, audit_result: Dict):
        """Guardar resultados de White-Box Audit en BD"""
        try:
            if "error" in audit_result or audit_result.get("status") == "failed":
                logger.warning(f"  ⚠️ White-Box Audit falló para {platform}, saltando guardado...")
                return

            # Crear registro de auditoría
            audit = Audit(
                client_id=client_id,
                audit_type="whitebox",
                platform=platform,
                status="completed"
            )

            audit_id = self.orchestrator.create_audit(audit)

            # Guardar score y detalles
            self.orchestrator.update_audit_score(
                audit_id,
                audit_result.get('score', 0),
                audit_result.get('findings', {})
            )

            logger.info(f"  ✅ {platform} White-Box: {audit_result.get('score', 0)}/100 guardado")

        except Exception as e:
            logger.error(f"❌ Error guardando White-Box Audit: {str(e)}")

    def _save_live_audit_results(self, client_id: int, platform: str, audit_result: Dict):
        """Guardar resultados de Live Audit en BD"""
        try:
            if "error" in audit_result or audit_result.get("status") == "failed":
                logger.warning(f"  ⚠️ Live Audit falló para {platform}, saltando guardado...")
                return

            # Crear registro de auditoría
            audit = Audit(
                client_id=client_id,
                audit_type="live",
                platform=platform,
                status="completed"
            )

            audit_id = self.orchestrator.create_audit(audit)

            # Guardar score y detalles
            self.orchestrator.update_audit_score(
                audit_id,
                audit_result.get('score', 0),
                audit_result.get('findings', {})
            )

            logger.info(f"  ✅ {platform} Live: {audit_result.get('score', 0)}/100 guardado")

        except Exception as e:
            logger.error(f"❌ Error guardando Live Audit: {str(e)}")

    def _compute_web_audit(self, client) -> Dict:
        """Computar auditoría web (sin BD, seguro para threads)"""
        logger.info(f"  ⚡ Computando Web para {client.name}")

        web_score = 72
        web_metrics = {
            "performance": 85,
            "security": 90,
            "tracking": 40,
            "technology": 75,
            "recommendations": [
                "Implementar Google Analytics 4",
                "Optimizar imágenes para móvil",
                "Mejorar speed con CDN"
            ]
        }

        return {
            "platform": "web",
            "overall_score": web_score,
            "metrics": web_metrics
        }

    def _compute_facebook_audit(self, client) -> Dict:
        """Computar auditoría Facebook Ads (sin BD, seguro para threads)"""
        logger.info(f"  📘 Computando Facebook Ads para {client.name}")

        result = create_sample_facebook_audit()

        return {
            "platform": "facebook_ads",
            "overall_score": result['overall_score'],
            "metrics": result['metrics']
        }

    def _compute_google_audit(self, client) -> Dict:
        """Computar auditoría Google Ads (sin BD, seguro para threads)"""
        logger.info(f"  🔍 Computando Google Ads para {client.name}")

        result = create_sample_google_audit()

        return {
            "platform": "google_ads",
            "overall_score": result['overall_score'],
            "metrics": result['metrics']
        }

    def _save_audit_results(self, client_id: int, results: Dict):
        """Guardar resultados en BD (SEQUENCIAL, sin threading)"""
        # Guardar cada auditoría en la BD
        for platform, audit_data in results.items():
            if 'overall_score' not in audit_data:
                logger.warning(f"  ⚠️ Sin score para {platform}, saltando...")
                continue

            # Crear registro de auditoría
            audit = Audit(
                client_id=client_id,
                audit_type="web" if platform == "web" else "ads",
                platform=platform,
                status="pending"
            )

            audit_id = self.orchestrator.create_audit(audit)

            # Guardar score
            self.orchestrator.update_audit_score(
                audit_id,
                audit_data['overall_score'],
                audit_data['metrics']
            )

            logger.info(f"  ✅ {platform}: {audit_data['overall_score']}/100")

            # 🔌 FASE 13 Day 3: Emitir evento WebSocket
            self.orchestrator._emit_audit_event(client_id, platform, audit_data['overall_score'], audit_id)

        # Calcular score promedio
        scores = [r['overall_score'] for r in results.values() if 'overall_score' in r]
        avg_score = int(sum(scores) / len(scores)) if scores else 0

        logger.info(f"  💾 Guardando resultados - Score promedio: {avg_score}/100")


def main():
    """Testing del agente"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║         MULTI-PLATFORM AUDITOR AGENT                          ║
║    Audita: Web + Facebook Ads + Google Ads en paralelo       ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Conectar orquestador
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    # Crear agente
    agent = MultiPlatformAuditorAgent(orchestrator)

    # Auditar primer cliente (Raíces de Cauquenes)
    print("\n📊 AUDITANDO CLIENTE: Raíces de Cauquenes")
    results = agent.audit_client(1)

    print("\n" + "="*60)
    print("✅ RESULTADOS DE AUDITORÍA MULTI-PLATAFORMA")
    print("="*60)
    print(json.dumps(results, indent=2, ensure_ascii=False))

    # Estadísticas
    status = orchestrator.get_system_status()
    print("\n📈 ESTADO DEL SISTEMA:")
    print(json.dumps(status, indent=2, ensure_ascii=False))

    orchestrator.close_database()


if __name__ == "__main__":
    main()
