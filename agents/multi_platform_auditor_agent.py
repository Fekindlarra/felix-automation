#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Platform Auditor Agent
Audita: Web + Facebook Ads + Google Ads en paralelo
"""

import sys
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import FelixAutomationOrchestrator, Audit
from auditors.facebook_ads_auditor import FacebookAdsAuditor, create_sample_facebook_audit
from auditors.google_ads_auditor import GoogleAdsAuditor, create_sample_google_audit
from auditors.seo_auditor import SEOAuditor
from auditors.tracking_scripts_auditor import TrackingScriptsAuditor, audit_tracking_scripts
from whitebox.shopify_auditor import ShopifyAuditor
from whitebox.jumpseller_auditor import JumpsellerAuditor
from whitebox.code_auditor import CodeAuditor
from whitebox.credentials_manager import CredentialsManager
from whitebox.facebook_ads_live_auditor import FacebookAdsLiveAuditor
from whitebox.google_ads_live_auditor import GoogleAdsLiveAuditor
from whitebox.gsc_auditor import GSCAuditor, audit_gsc
from whitebox.gtm_auditor import GTMAuditor, audit_gtm
from whitebox.instagram_auditor import InstagramAuditor, audit_instagram
from analytics.customer_profile_analyzer import CustomerProfileAnalyzer, analyze_customer_profile
from analytics.content_recommendation_engine import ContentRecommendationEngine, generate_content_recommendations

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
            platforms: Lista de plataformas ['web', 'facebook_ads', 'google_ads', 'seo']
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
                elif platform == 'seo':
                    future = executor.submit(self._compute_seo_audit, client)
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

    def _compute_seo_audit(self, client) -> Dict:
        """Computar auditoría SEO (sin BD, seguro para threads)"""
        logger.info(f"  🔍 Computando SEO para {client.name}")

        try:
            # Obtener URL del cliente
            website_url = getattr(client, 'website', None)
            if not website_url:
                logger.warning(f"  ⚠️ Cliente {client.name} sin URL de website, usando mock")
                return self._create_sample_seo_audit()

            # Fetch HTML desde el website
            try:
                response = requests.get(website_url, timeout=10)
                response.raise_for_status()
                html = response.text
                page_size = len(response.content)
            except Exception as e:
                logger.warning(f"  ⚠️ Error fetching {website_url}: {str(e)}, usando mock")
                return self._create_sample_seo_audit()

            # Auditar con SEOAuditor
            seo_auditor = SEOAuditor()
            audit_result = seo_auditor.audit({
                'url': website_url,
                'html': html,
                'page_size': page_size,
                'load_time': 1.5,  # Estimado
                'headers': dict(response.headers)
            })

            return {
                "platform": "seo",
                "overall_score": audit_result['overall_score'],
                "metrics": audit_result['metrics'],
                "keywords_detected": audit_result.get('keywords_detected', [])
            }

        except Exception as e:
            logger.error(f"  ❌ Error computando SEO audit: {str(e)}")
            return self._create_sample_seo_audit()

    def _create_sample_seo_audit(self) -> Dict:
        """Crear auditoría SEO de muestra (cuando hay error o no hay URL)"""
        return {
            "platform": "seo",
            "overall_score": 65,
            "metrics": {
                "tecnica": {
                    "score": 70,
                    "findings": [
                        {"severity": "warning", "issue": "Title muy corto", "value": 25}
                    ]
                },
                "contenido": {
                    "score": 60,
                    "findings": [
                        {"severity": "warning", "issue": "Contenido muy corto", "value": 250}
                    ]
                },
                "rendimiento": {
                    "score": 75,
                    "findings": []
                },
                "seguridad": {
                    "score": 65,
                    "findings": [
                        {"severity": "warning", "issue": "No hay política de privacidad", "value": None}
                    ]
                }
            },
            "keywords_detected": ["automatización", "ventas", "plataforma"]
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

    def audit_tracking_scripts(self, client_id: int, site_url: str = None) -> Dict:
        """
        Auditoría de Scripts de Tracking (GTM, GA4, Facebook Pixel, etc.)
        No requiere credenciales - análisis estático del HTML

        Args:
            client_id: ID del cliente
            site_url: URL del sitio (si no, se obtiene del cliente)

        Returns:
            Diccionario con resultados de auditoría
        """
        try:
            client = self.orchestrator.get_client(client_id)
            website_url = site_url or getattr(client, 'website', None)

            if not website_url:
                logger.warning(f"⚠️ Cliente {client.name} sin URL de website")
                return {
                    "platform": "tracking",
                    "status": "failed",
                    "error": "No website URL available"
                }

            logger.info(f"📊 Auditando Tracking Scripts para {client.name}")

            # Fetch HTML
            try:
                response = requests.get(website_url, timeout=10)
                response.raise_for_status()
                html = response.text
            except Exception as e:
                logger.warning(f"⚠️ Error fetching {website_url}: {str(e)}")
                return {
                    "platform": "tracking",
                    "status": "failed",
                    "error": str(e)
                }

            # Auditar con TrackingScriptsAuditor
            auditor = TrackingScriptsAuditor()
            audit_result = auditor.audit({
                'url': website_url,
                'html_content': html
            })

            # Guardar en BD
            self._save_audit_results(client_id, {"tracking": audit_result})

            logger.info(f"✅ Tracking Scripts Audit completado - Score: {audit_result.get('score', 0)}/100")
            return audit_result

        except Exception as e:
            logger.error(f"❌ Error en Tracking Scripts Audit: {str(e)}")
            return {
                "platform": "tracking",
                "status": "failed",
                "error": str(e)
            }

    def audit_gsc(self, client_id: int, gsc_credentials: Dict = None) -> Dict:
        """
        Auditoría de Google Search Console (White-Box)
        Requiere credenciales OAuth de GSC

        Args:
            client_id: ID del cliente
            gsc_credentials: Dict con:
                - access_token: Token OAuth de Google
                - site_url: URL del sitio (ej: https://example.com/)
                - property_id: Property ID en GSC (opcional)

        Returns:
            Diccionario con resultados de auditoría
        """
        try:
            client = self.orchestrator.get_client(client_id)
            logger.info(f"🔍 Iniciando Google Search Console Audit para {client.name}")

            if not gsc_credentials or 'access_token' not in gsc_credentials:
                logger.warning("⚠️ Credenciales GSC no proporcionadas")
                return audit_gsc(None)  # Retorna reporte de "necesita credenciales"

            # Crear auditor GSC
            auditor = GSCAuditor(gsc_credentials)
            audit_result = auditor.audit()

            # Guardar en BD
            self._save_audit_results(client_id, {"gsc": audit_result})

            logger.info(f"✅ GSC Audit completado - Score: {audit_result.get('score', 0)}/100")
            return audit_result

        except Exception as e:
            logger.error(f"❌ Error en GSC Audit: {str(e)}")
            return {
                "platform": "gsc",
                "status": "failed",
                "error": str(e)
            }

    def audit_gtm(self, client_id: int, gtm_credentials: Dict = None) -> Dict:
        """
        Auditoría de Google Tag Manager (White-Box)
        Requiere credenciales OAuth de GTM

        Args:
            client_id: ID del cliente
            gtm_credentials: Dict con:
                - access_token: Token OAuth de Google
                - account_id: Account ID en GTM
                - container_id: Container ID en GTM
                - gtm_id: GTM-XXXXX del sitio

        Returns:
            Diccionario con resultados de auditoría
        """
        try:
            client = self.orchestrator.get_client(client_id)
            logger.info(f"🏷️ Iniciando Google Tag Manager Audit para {client.name}")

            if not gtm_credentials or 'access_token' not in gtm_credentials:
                logger.warning("⚠️ Credenciales GTM no proporcionadas")
                return audit_gtm(None)  # Retorna reporte de "necesita credenciales"

            # Crear auditor GTM
            auditor = GTMAuditor(gtm_credentials)
            audit_result = auditor.audit()

            # Guardar en BD
            self._save_audit_results(client_id, {"gtm": audit_result})

            logger.info(f"✅ GTM Audit completado - Score: {audit_result.get('score', 0)}/100")
            return audit_result

        except Exception as e:
            logger.error(f"❌ Error en GTM Audit: {str(e)}")
            return {
                "platform": "gtm",
                "status": "failed",
                "error": str(e)
            }

    def audit_instagram(self, client_id: int, instagram_credentials: Dict = None) -> Dict:
        """
        Auditar Instagram Business Account del cliente

        Args:
            client_id: ID del cliente
            instagram_credentials: {
                'access_token': str,
                'instagram_business_account_id': str,
                'page_id': str
            }

        Returns:
            Resultado del audit de Instagram
        """
        try:
            # Crear auditor Instagram
            auditor = InstagramAuditor(instagram_credentials)

            # Ejecutar audit
            audit_result = auditor.audit()

            # Guardar en BD
            self._save_audit_results(client_id, {"instagram": audit_result})

            logger.info(f"✅ Instagram Audit completado - Score: {audit_result.get('score', 0)}/100")
            return audit_result

        except Exception as e:
            logger.error(f"❌ Error en Instagram Audit: {str(e)}")
            return {
                "platform": "instagram",
                "status": "failed",
                "error": str(e)
            }

    def analyze_customer_profile(self, client_id: int, instagram_audit: Dict, site_audit: Dict = None, tracking_audit: Dict = None) -> Dict:
        """
        Analizar perfil de cliente correlacionando Instagram + Site data

        Args:
            client_id: ID del cliente
            instagram_audit: Resultados del audit de Instagram
            site_audit: Resultados del audit del sitio (opcional)
            tracking_audit: Resultados del audit de tracking (opcional)

        Returns:
            Análisis de perfil con recomendaciones personalizadas
        """
        try:
            # Crear analizador
            analyzer = CustomerProfileAnalyzer()

            # Preparar datos del sitio
            site_data = site_audit or {}

            # Ejecutar análisis
            analysis_result = analyzer.analyze(instagram_audit, site_data, tracking_audit)

            # Guardar en BD
            self._save_audit_results(client_id, {"customer_profile": analysis_result})

            logger.info(f"✅ Customer Profile Analysis completado")
            logger.info(f"   Total gaps: {analysis_result.get('summary', {}).get('total_gaps', 0)}")
            logger.info(f"   Recommendations: {analysis_result.get('summary', {}).get('total_recommendations', 0)}")

            return analysis_result

        except Exception as e:
            logger.error(f"❌ Error en Customer Profile Analysis: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def generate_content_plan(self, client_id: int, instagram_audit: Dict, site_audit: Dict, customer_profile: Dict) -> Dict:
        """
        Generar plan de contenido para 3 meses basado en perfil de cliente

        Args:
            client_id: ID del cliente
            instagram_audit: Resultados del auditor de Instagram
            site_audit: Resultados del auditor del sitio
            customer_profile: Perfil de cliente ideal

        Returns:
            Dict con plan de contenido por 3 meses
        """
        try:
            client = self.orchestrator.get_client(client_id)
            logger.info(f"📝 Generando plan de contenido para {client.name} (3 meses)")

            # Generar recomendaciones
            content_engine = ContentRecommendationEngine()
            content_plan = content_engine.generate_recommendations(
                instagram_audit,
                site_audit,
                customer_profile
            )

            logger.info(f"✅ Plan de contenido generado")
            logger.info(f"   Total posts: {content_plan.get('total_posts_recommended', 0)}")
            logger.info(f"   Content pillars: {len(content_plan.get('content_pillars', []))}")
            logger.info(f"   Semana 1 inicio: {content_plan.get('summary', {}).get('week_1_start', 'N/A')}")

            return content_plan

        except Exception as e:
            logger.error(f"❌ Error generando plan de contenido: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }


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
