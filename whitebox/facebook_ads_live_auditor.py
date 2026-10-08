"""
Facebook Ads Live Auditor - FASE 13

Auditoría profunda de Facebook Ads con acceso via Graph API.
Analiza: campañas, audiencias, performance, presupuestos.
Score: 0-100 unificado
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FacebookAdsMetrics:
    """Métricas de rendimiento de Facebook Ads"""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    cpc: float = 0.0
    ctr: float = 0.0
    roas: float = 0.0
    conversion_rate: float = 0.0


class FacebookAdsLiveAuditor:
    """
    Auditor de Facebook Ads con API access

    Requiere:
    - access_token: FB user access token (con permisos ads_read)
    - ad_account_id: act_xxxxx (Account ID)
    - business_id: xxxxx (Business ID)
    """

    # Versión de Facebook Graph API
    API_VERSION = "v18.0"
    GRAPH_API_URL = f"https://graph.facebook.com/{API_VERSION}"

    # Breakdowns de rendimiento: quién vio y respondió a los anuncios
    DEMOGRAPHIC_BREAKDOWNS = ["age,gender", "region", "publisher_platform,platform_position"]
    DEMOGRAPHIC_FIELDS = "impressions,clicks,spend,ctr,cpc,actions"

    # Campos a extraer de campañas
    CAMPAIGN_FIELDS = [
        "id", "name", "status", "objective", "daily_budget",
        "lifetime_budget", "spend", "created_time", "updated_time",
        "insights{impressions,clicks,spend,actions,action_values,conversion_rate_ranking}"
    ]

    # Campos de ad sets
    ADSET_FIELDS = [
        "id", "name", "campaign_id", "status", "targeting",
        "bid_amount", "daily_budget", "lifetime_budget", "end_time",
        "insights{impressions,clicks,spend,conversions,conversion_rate}"
    ]

    # Campos de ads
    AD_FIELDS = [
        "id", "name", "adset_id", "status", "creative",
        "insights{impressions,clicks,spend,conversions,actions,cpc}"
    ]

    def __init__(self, orchestrator=None):
        """Inicializar auditor"""
        self.orchestrator = orchestrator
        self.access_token = None
        self.ad_account_id = None
        self.api_headers = {}

    def audit_client(self, client_id: int, fb_config: Dict) -> Dict:
        """
        Audita cuenta Facebook Ads del cliente

        Args:
            client_id: ID del cliente en BD
            fb_config: Dict con:
                - access_token: Token FB
                - ad_account_id: act_xxxxx
                - business_id: xxxxx (opcional)

        Returns:
            Dict con estructura de auditoria
        """
        try:
            logger.info(f"[FB_ADS] Iniciando auditoría para cliente {client_id}")

            # Validar credenciales
            if not self._validate_config(fb_config):
                return self._error_audit("Configuración Facebook inválida")

            # Configurar
            self.access_token = fb_config.get("access_token")
            self.ad_account_id = fb_config.get("ad_account_id")
            self.api_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            # Auditar componentes
            audit_result = {
                "platform": "facebook_ads_live",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "score": 0,
                "findings": {
                    "account": {},
                    "campaigns": {},
                    "adsets": {},
                    "audiences": {},
                    "budget_health": {},
                    "performance": {},
                    "recommendations": [],
                    "issues": []
                }
            }

            # Auditorías específicas
            self._audit_account(audit_result)
            self._audit_campaigns(audit_result)
            self._audit_adsets(audit_result)
            self._audit_audiences(audit_result)
            self._audit_budget_health(audit_result)
            self._audit_performance(audit_result)
            self._audit_demographics(audit_result)

            # Calcular score
            audit_result["score"] = self._calculate_score(audit_result)

            logger.info(f"[FB_ADS] Auditoría completada. Score: {audit_result['score']}/100")
            return audit_result

        except Exception as e:
            logger.error(f"[FB_ADS] Error auditando cliente {client_id}: {str(e)}")
            return self._error_audit(f"Error: {str(e)}")

    def _validate_config(self, fb_config: Dict) -> bool:
        """Validar configuración requerida"""
        required = ["access_token", "ad_account_id"]
        return all(key in fb_config for key in required)

    def _audit_account(self, audit_result: Dict) -> None:
        """Auditar información general de cuenta"""
        try:
            # GET /me/adaccounts
            url = f"{self.GRAPH_API_URL}/me/adaccounts"
            params = {
                "access_token": self.access_token,
                "fields": "id,name,status,currency,account_status,created_time"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json().get("data", [])
            if data:
                account = data[0]
                audit_result["findings"]["account"] = {
                    "id": account.get("id"),
                    "name": account.get("name"),
                    "status": account.get("status"),
                    "currency": account.get("currency"),
                    "account_status": account.get("account_status"),
                    "created_time": account.get("created_time")
                }
        except Exception as e:
            logger.warning(f"[FB_ADS] Error auditando account: {str(e)}")
            audit_result["findings"]["issues"].append(f"Account audit failed: {str(e)}")

    def _audit_campaigns(self, audit_result: Dict) -> None:
        """Auditar campañas"""
        try:
            # GET /adaccount/campaigns
            url = f"{self.GRAPH_API_URL}/{self.ad_account_id}/campaigns"
            params = {
                "access_token": self.access_token,
                "fields": ",".join(self.CAMPAIGN_FIELDS),
                "limit": 100,
                "date_preset": "last_30d"
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            campaigns = response.json().get("data", [])

            campaign_stats = {
                "total": len(campaigns),
                "active": 0,
                "paused": 0,
                "total_spend": 0.0,
                "campaigns": []
            }

            for campaign in campaigns:
                if campaign.get("status") == "ACTIVE":
                    campaign_stats["active"] += 1
                elif campaign.get("status") == "PAUSED":
                    campaign_stats["paused"] += 1

                spend = float(campaign.get("spend", 0))
                campaign_stats["total_spend"] += spend

                campaign_stats["campaigns"].append({
                    "id": campaign.get("id"),
                    "name": campaign.get("name"),
                    "status": campaign.get("status"),
                    "objective": campaign.get("objective"),
                    "spend": spend,
                    "daily_budget": float(campaign.get("daily_budget") or 0),
                    "lifetime_budget": float(campaign.get("lifetime_budget") or 0)
                })

            audit_result["findings"]["campaigns"] = campaign_stats

            # Detectar problemas
            if campaign_stats["active"] == 0:
                audit_result["findings"]["issues"].append("No active campaigns found")
            if campaign_stats["total"] > 50:
                audit_result["findings"]["recommendations"].append(
                    "Consider consolidating campaigns for better management"
                )

        except Exception as e:
            logger.warning(f"[FB_ADS] Error auditando campaigns: {str(e)}")
            audit_result["findings"]["issues"].append(f"Campaign audit failed: {str(e)}")

    def _audit_adsets(self, audit_result: Dict) -> None:
        """Auditar ad sets"""
        try:
            url = f"{self.GRAPH_API_URL}/{self.ad_account_id}/adsets"
            params = {
                "access_token": self.access_token,
                "fields": ",".join(self.ADSET_FIELDS),
                "limit": 100,
                "date_preset": "last_30d"
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            adsets = response.json().get("data", [])

            adset_stats = {
                "total": len(adsets),
                "active": sum(1 for a in adsets if a.get("status") == "ACTIVE"),
                "paused": sum(1 for a in adsets if a.get("status") == "PAUSED"),
                "total_spend": sum(float(a.get("spend", 0)) for a in adsets),
                "avg_cpc": self._calculate_avg_metric(adsets, "cpc")
            }

            # Intereses y segmentación que el cliente configuró (lo declarado, no lo inferido)
            interests: Dict[str, int] = {}
            genders_seen = set()
            geo_seen = set()
            for a in adsets:
                t = a.get("targeting") or {}
                for spec in t.get("flexible_spec", []) or []:
                    for interest in spec.get("interests", []) or []:
                        name = interest.get("name")
                        if name:
                            interests[name] = interests.get(name, 0) + 1
                for g in t.get("genders", []) or []:
                    genders_seen.add({1: "hombres", 2: "mujeres"}.get(g, str(g)))
                geo = t.get("geo_locations") or {}
                for c in geo.get("countries", []) or []:
                    geo_seen.add(c)
                for r in geo.get("regions", []) or []:
                    geo_seen.add(r.get("name", ""))
                for c in geo.get("cities", []) or []:
                    geo_seen.add(c.get("name", ""))
            adset_stats["configured_interests"] = sorted(
                interests.items(), key=lambda kv: kv[1], reverse=True
            )
            adset_stats["configured_genders"] = sorted(genders_seen)
            adset_stats["configured_geo"] = sorted(g for g in geo_seen if g)

            audit_result["findings"]["adsets"] = adset_stats

            if adset_stats["total"] == 0:
                audit_result["findings"]["issues"].append("No ad sets found")

        except Exception as e:
            logger.warning(f"[FB_ADS] Error auditando adsets: {str(e)}")
            audit_result["findings"]["issues"].append(f"Ad set audit failed: {str(e)}")

    def _audit_audiences(self, audit_result: Dict) -> None:
        """Auditar audiencias"""
        try:
            url = f"{self.GRAPH_API_URL}/{self.ad_account_id}/audiences"
            params = {
                "access_token": self.access_token,
                "fields": "id,name,audience_size,description,customer_list_status",
                "limit": 100
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            audiences = response.json().get("data", [])

            audience_stats = {
                "total": len(audiences),
                "saved_audiences": sum(1 for a in audiences if "SAVED" in a.get("description", "")),
                "total_size": sum(a.get("audience_size", 0) for a in audiences)
            }

            audit_result["findings"]["audiences"] = audience_stats

            if audience_stats["total"] == 0:
                audit_result["findings"]["recommendations"].append(
                    "Create custom audiences for better targeting"
                )

        except Exception as e:
            logger.warning(f"[FB_ADS] Error auditando audiences: {str(e)}")
            audit_result["findings"]["issues"].append(f"Audience audit failed: {str(e)}")

    def _audit_budget_health(self, audit_result: Dict) -> None:
        """Auditar salud del presupuesto"""
        try:
            campaigns = audit_result["findings"]["campaigns"].get("campaigns", [])

            budget_health = {
                "daily_budgets": len([c for c in campaigns if c.get("daily_budget", 0) > 0]),
                "lifetime_budgets": len([c for c in campaigns if c.get("lifetime_budget", 0) > 0]),
                "total_daily": sum(c.get("daily_budget", 0) for c in campaigns),
                "total_monthly_projection": sum(c.get("daily_budget", 0) * 30 for c in campaigns),
                "concerns": []
            }

            # Detectar campañas sin presupuesto
            no_budget = [c for c in campaigns if c.get("daily_budget", 0) == 0 and
                        c.get("lifetime_budget", 0) == 0]
            if no_budget:
                budget_health["concerns"].append(
                    f"{len(no_budget)} campaigns have no budget set"
                )

            audit_result["findings"]["budget_health"] = budget_health

        except Exception as e:
            logger.warning(f"[FB_ADS] Error auditando budget: {str(e)}")

    def _audit_performance(self, audit_result: Dict) -> None:
        """Auditar performance metrics"""
        try:
            url = f"{self.GRAPH_API_URL}/{self.ad_account_id}/insights"
            params = {
                "access_token": self.access_token,
                "fields": "impressions,clicks,spend,conversions,conversion_rate,cpc,ctr",
                "date_preset": "last_30d",
                "time_increment": 1
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json().get("data", [])
            if data:
                latest = data[-1]
                performance = {
                    "impressions": int(latest.get("impressions", 0)),
                    "clicks": int(latest.get("clicks", 0)),
                    "spend": float(latest.get("spend", 0)),
                    "conversions": int(latest.get("conversions", 0)),
                    "ctr": float(latest.get("ctr", 0)),
                    "cpc": float(latest.get("cpc", 0)),
                    "conversion_rate": float(latest.get("conversion_rate", 0))
                }
                audit_result["findings"]["performance"] = performance

        except Exception as e:
            logger.warning(f"[FB_ADS] Error auditando performance: {str(e)}")

    def _audit_demographics(self, audit_result: Dict) -> None:
        """Rendimiento por edad y género, región y ubicación de anuncio.

        Cada breakdown es una llamada separada. Si Meta rechaza uno, los demás siguen.
        """
        demographics: Dict[str, List[Dict]] = {}
        for breakdown in self.DEMOGRAPHIC_BREAKDOWNS:
            try:
                url = f"{self.GRAPH_API_URL}/{self.ad_account_id}/insights"
                params = {
                    "access_token": self.access_token,
                    "fields": self.DEMOGRAPHIC_FIELDS,
                    "breakdowns": breakdown,
                    "date_preset": "last_30d",
                    "limit": 500,
                }
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                demographics[breakdown] = response.json().get("data", [])
            except Exception as e:
                logger.warning(f"[FB_ADS] Breakdown {breakdown} falló: {str(e)}")
                audit_result["findings"]["issues"].append(f"Demographic breakdown {breakdown} failed: {str(e)}")
        audit_result["findings"]["demographics"] = demographics

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
        elif campaigns.get("active", 0) == 0:
            score -= 15

        # Evaluar ad sets
        adsets = findings.get("adsets", {})
        if adsets.get("total", 0) == 0:
            score -= 15
        elif adsets.get("active", 0) == 0:
            score -= 10

        # Evaluar audiencias
        audiences = findings.get("audiences", {})
        if audiences.get("total", 0) == 0:
            score -= 10

        # Evaluar performance
        perf = findings.get("performance", {})
        if perf.get("impressions", 0) == 0:
            score -= 5

        return max(score, 0)  # No menos de 0

    def _calculate_avg_metric(self, items: List[Dict], metric: str) -> float:
        """Calcular promedio de métrica en lista"""
        try:
            values = [float(item.get(metric, 0)) for item in items if metric in item]
            return sum(values) / len(values) if values else 0.0
        except:
            return 0.0

    def _error_audit(self, error_msg: str) -> Dict:
        """Retornar audit con error"""
        return {
            "platform": "facebook_ads_live",
            "timestamp": datetime.now().isoformat(),
            "score": 0,
            "error": error_msg,
            "findings": {"issues": [error_msg]}
        }
