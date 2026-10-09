"""
Google Ads Live Auditor - FASE 13

Auditoría profunda de Google Ads con acceso via Google Ads API.
Analiza: campañas, keywords, quality scores, performance, presupuestos.
Score: 0-100 unificado
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GoogleAdsMetrics:
    """Métricas de rendimiento de Google Ads"""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    cpc: float = 0.0
    ctr: float = 0.0
    roas: float = 0.0
    conversion_rate: float = 0.0
    quality_score: int = 0


class GoogleAdsLiveAuditor:
    """
    Auditor de Google Ads con API access

    Requiere (OAuth 2.0 flow):
    - developer_token: Google Ads developer token
    - client_id: OAuth client ID from GCP
    - client_secret: OAuth client secret
    - refresh_token: OAuth refresh token
    - customer_id: xxxxxxxx (sin dashes)
    """

    def __init__(self, orchestrator=None):
        """Inicializar auditor"""
        self.orchestrator = orchestrator
        self.client = None
        self.customer_id = None
        self.client_initialized_with_real_api = False

    def audit_client(self, client_id: int, gads_config: Dict) -> Dict:
        """
        Audita cuenta Google Ads del cliente

        Args:
            client_id: ID del cliente en BD
            gads_config: Dict con credenciales OAuth
                - developer_token: Google Ads dev token
                - client_id: OAuth client ID
                - client_secret: OAuth secret
                - refresh_token: OAuth refresh token
                - customer_id: xxxxxxxx

        Returns:
            Dict con estructura de auditoria
        """
        try:
            logger.info(f"[GOOGLE_ADS] Iniciando auditoría para cliente {client_id}")

            # Validar configuración
            if not self._validate_config(gads_config):
                return self._error_audit("Configuración Google Ads inválida")

            # Configurar credenciales
            self.customer_id = gads_config.get("customer_id")

            # Sin conexión real a la API de Google Ads, no se devuelven datos inventados
            # (bloqueante 3.4.3). Las secciones _audit_* son esqueleto con valores fijos.
            return self._error_audit(
                "Auditoría Google Ads en vivo no conectada a la API: sin datos medidos"
            )

            # Inicializar cliente (cuando exista la conexión real)
            self._init_client(gads_config)

            # Estructura de auditoria
            audit_result = {
                "platform": "google_ads_live",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "score": 0,
                "findings": {
                    "account": {},
                    "campaigns": {},
                    "ad_groups": {},
                    "keywords": {},
                    "quality_scores": {},
                    "budget_health": {},
                    "performance": {},
                    "recommendations": [],
                    "issues": []
                }
            }

            # Auditorías específicas
            self._audit_account(audit_result)
            self._audit_campaigns(audit_result)
            self._audit_ad_groups(audit_result)
            self._audit_keywords(audit_result)
            self._audit_quality_scores(audit_result)
            self._audit_budget_health(audit_result)
            self._audit_performance(audit_result)

            # Calcular score
            audit_result["score"] = self._calculate_score(audit_result)

            logger.info(f"[GOOGLE_ADS] Auditoría completada. Score: {audit_result['score']}/100")
            return audit_result

        except Exception as e:
            logger.error(f"[GOOGLE_ADS] Error auditando cliente {client_id}: {str(e)}")
            return self._error_audit(f"Error: {str(e)}")

    def _validate_config(self, gads_config: Dict) -> bool:
        """Validar configuración requerida"""
        required = ["developer_token", "customer_id", "refresh_token"]
        # Check that all required keys exist AND have non-None, non-empty values
        for key in required:
            if key not in gads_config or not gads_config[key]:
                return False

        # Validate customer_id format (should be numeric, not "invalid")
        customer_id = gads_config.get("customer_id", "")
        if not isinstance(customer_id, str) or not customer_id.replace("-", "").isdigit():
            return False

        return True

    def _init_client(self, gads_config: Dict) -> None:
        """Inicializar cliente de Google Ads"""
        try:
            # Try to use the real Google Ads client
            try:
                from google.ads.googleads.client import GoogleAdsClient
                self.client = GoogleAdsClient.load_from_storage(version='v17')
                self.client_initialized_with_real_api = True
            except ImportError:
                # google-ads library not available
                logger.warning("[GOOGLE_ADS] google-ads library not available, cannot authenticate")
                self.client = None
                self.client_initialized_with_real_api = False
                raise Exception("Google Ads API client library not available. Cannot authenticate credentials.")
        except Exception as e:
            logger.error(f"[GOOGLE_ADS] Error inicializando cliente: {str(e)}")
            raise

    def _audit_account(self, audit_result: Dict) -> None:
        """Auditar información general de cuenta"""
        try:
            # En producción, hacer query: SELECT customer.id, customer.descriptive_name FROM customer
            account_info = {
                "customer_id": self.customer_id,
                "status": "ENABLED",
                "currency": "USD",
                "time_zone": "America/Los_Angeles",
                "audit_timestamp": datetime.now().isoformat()
            }

            audit_result["findings"]["account"] = account_info
            logger.info(f"[GOOGLE_ADS] Account info retrieved: {self.customer_id}")

        except Exception as e:
            logger.warning(f"[GOOGLE_ADS] Error auditando account: {str(e)}")
            audit_result["findings"]["issues"].append(f"Account audit failed: {str(e)}")

    def _audit_campaigns(self, audit_result: Dict) -> None:
        """Auditar campañas"""
        try:
            # Only return data if we successfully authenticated with real API
            if not self.client_initialized_with_real_api:
                audit_result["findings"]["campaigns"] = {}
                return

            # En producción, query: SELECT campaign.id, campaign.name, campaign.status,
            # campaign.advertising_channel_type, metrics.impressions, metrics.clicks,
            # metrics.cost_micros FROM campaign WHERE campaign.status != REMOVED

            # Query real data from API
            # ... API call code here ...
            campaigns = []  # Would be populated from API

            campaign_stats = {
                "total": len(campaigns),
                "enabled": sum(1 for c in campaigns if c.get("status") == "ENABLED"),
                "paused": sum(1 for c in campaigns if c.get("status") == "PAUSED"),
                "total_budget": sum(c.get("budget", 0) for c in campaigns),
                "total_spend": sum(c.get("spend", 0) for c in campaigns),
                "total_impressions": sum(c.get("impressions", 0) for c in campaigns),
                "total_clicks": sum(c.get("clicks", 0) for c in campaigns),
                "campaigns": campaigns
            }

            audit_result["findings"]["campaigns"] = campaign_stats

            # Detectar problemas
            if campaign_stats["enabled"] == 0:
                audit_result["findings"]["issues"].append("No enabled campaigns found")
            if campaign_stats["total"] > 100:
                audit_result["findings"]["recommendations"].append(
                    "Consider consolidating campaigns for better management"
                )

        except Exception as e:
            logger.warning(f"[GOOGLE_ADS] Error auditando campaigns: {str(e)}")
            audit_result["findings"]["issues"].append(f"Campaign audit failed: {str(e)}")

    def _audit_ad_groups(self, audit_result: Dict) -> None:
        """Auditar ad groups"""
        try:
            # Only return data if we successfully authenticated with real API
            if not self.client_initialized_with_real_api:
                audit_result["findings"]["ad_groups"] = {}
                return

            # En producción, query para obtener ad groups desde Google Ads API
            adgroup_stats = {
                "total": 0,
                "enabled": 0,
                "paused": 0,
                "total_keywords": 0,
                "avg_quality_score": 0,
                "critical_quality": 0
            }

            audit_result["findings"]["ad_groups"] = adgroup_stats

            if adgroup_stats["critical_quality"] > 0:
                audit_result["findings"]["issues"].append(
                    f"{adgroup_stats['critical_quality']} ad groups with low quality scores"
                )

        except Exception as e:
            logger.warning(f"[GOOGLE_ADS] Error auditando ad groups: {str(e)}")
            audit_result["findings"]["issues"].append(f"Ad group audit failed: {str(e)}")

    def _audit_keywords(self, audit_result: Dict) -> None:
        """Auditar keywords"""
        try:
            # Only return data if we successfully authenticated with real API
            if not self.client_initialized_with_real_api:
                audit_result["findings"]["keywords"] = {}
                return

            # En producción, query para obtener keywords y performance
            keyword_stats = {
                "total": 0,
                "active": 0,
                "paused": 0,
                "match_types": {
                    "broad": 0,
                    "phrase": 0,
                    "exact": 0
                },
                "negative_keywords": 0,
                "high_volume_keywords": 0,
                "low_volume_keywords": 0,
                "search_volume_coverage": 0
            }

            audit_result["findings"]["keywords"] = keyword_stats

            if keyword_stats["low_volume_keywords"] > 50:
                audit_result["findings"]["recommendations"].append(
                    f"Review {keyword_stats['low_volume_keywords']} low-volume keywords"
                )

        except Exception as e:
            logger.warning(f"[GOOGLE_ADS] Error auditando keywords: {str(e)}")
            audit_result["findings"]["issues"].append(f"Keyword audit failed: {str(e)}")

    def _audit_quality_scores(self, audit_result: Dict) -> None:
        """Auditar quality scores"""
        try:
            # Only return data if we successfully authenticated with real API
            if not self.client_initialized_with_real_api:
                audit_result["findings"]["quality_scores"] = {}
                return

            # En producción, obtener del API
            qs_distribution = {
                "qs_10": 0,
                "qs_9": 0,
                "qs_8": 0,
                "qs_7": 0,
                "qs_6_below": 0,
                "avg_quality_score": 0,
                "expected_ctr": 0,
                "expected_cpc": 0,
                "ad_relevance": "Unknown",
                "landing_page_exp": "Unknown"
            }

            audit_result["findings"]["quality_scores"] = qs_distribution

            if qs_distribution["qs_6_below"] > 10:
                audit_result["findings"]["issues"].append(
                    f"{qs_distribution['qs_6_below']} keywords below QS 6"
                )

            if qs_distribution["landing_page_exp"] != "Good":
                audit_result["findings"]["recommendations"].append(
                    "Improve landing page experience for better quality scores"
                )

        except Exception as e:
            logger.warning(f"[GOOGLE_ADS] Error auditando quality scores: {str(e)}")
            audit_result["findings"]["issues"].append(f"Quality score audit failed: {str(e)}")

    def _audit_budget_health(self, audit_result: Dict) -> None:
        """Auditar salud del presupuesto"""
        try:
            campaigns = audit_result["findings"]["campaigns"].get("campaigns", [])

            total_budget = sum(c.get("budget", 0) for c in campaigns)
            total_spend = sum(c.get("spend", 0) for c in campaigns)

            budget_health = {
                "total_daily_budget": total_budget,
                "total_monthly_projection": total_budget * 30,
                "last_30_days_spend": total_spend,
                "utilization": (total_spend / total_budget * 100) if total_budget > 0 else 0,
                "remaining_budget": total_budget - (total_spend / 30),  # Approximate
                "concerns": []
            }

            # Detectar problemas de presupuesto
            if budget_health["utilization"] > 95:
                budget_health["concerns"].append("Budget utilization very high (>95%)")
            if budget_health["utilization"] < 20:
                budget_health["concerns"].append("Low budget utilization (<20%)")

            audit_result["findings"]["budget_health"] = budget_health

        except Exception as e:
            logger.warning(f"[GOOGLE_ADS] Error auditando budget: {str(e)}")

    def _audit_performance(self, audit_result: Dict) -> None:
        """Auditar performance metrics"""
        try:
            # Only return data if we successfully authenticated with real API
            if not self.client_initialized_with_real_api:
                audit_result["findings"]["performance"] = {}
                return

            # Agregar metrics de campaña
            campaigns = audit_result["findings"]["campaigns"].get("campaigns", [])

            total_impressions = sum(c.get("impressions", 0) for c in campaigns)
            total_clicks = sum(c.get("clicks", 0) for c in campaigns)
            total_spend = sum(c.get("spend", 0) for c in campaigns)

            ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

            performance = {
                "impressions": total_impressions,
                "clicks": total_clicks,
                "spend": total_spend,
                "conversions": 0,
                "ctr": round(ctr, 2),
                "cpc": round(cpc, 2),
                "conversion_rate": 0,
                "roas": 0
            }

            audit_result["findings"]["performance"] = performance

        except Exception as e:
            logger.warning(f"[GOOGLE_ADS] Error auditando performance: {str(e)}")

    def _calculate_score(self, audit_result: Dict) -> int:
        """Calcular score 0-100 basado en hallazgos"""
        score = 100
        findings = audit_result["findings"]

        # Penalidades por problemas
        issues_count = len(findings.get("issues", []))
        score -= min(issues_count * 5, 30)  # Max -30

        # Evaluar campañas
        campaigns = findings.get("campaigns", {})
        if campaigns.get("total", 0) == 0:
            score -= 20
        elif campaigns.get("enabled", 0) == 0:
            score -= 15

        # Evaluar keywords
        keywords = findings.get("keywords", {})
        if keywords.get("total", 0) == 0:
            score -= 15
        elif keywords.get("low_volume_keywords", 0) > 100:
            score -= 5

        # Evaluar quality scores
        qs = findings.get("quality_scores", {})
        if qs.get("qs_6_below", 0) > 20:
            score -= 10
        elif qs.get("avg_quality_score", 0) < 6:
            score -= 15

        # Evaluar performance
        perf = findings.get("performance", {})
        if perf.get("impressions", 0) == 0:
            score -= 5
        if perf.get("ctr", 0) < 0.5:
            score -= 5

        return max(score, 0)  # No menos de 0

    def _error_audit(self, error_msg: str) -> Dict:
        """Retornar audit con error"""
        return {
            "platform": "google_ads_live",
            "timestamp": datetime.now().isoformat(),
            "score": 0,
            "error": error_msg,
            "findings": {"issues": [error_msg]}
        }
