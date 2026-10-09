#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Auditor (White-Box)
Requiere token de Meta (Page/usuario de sistema) y el ID de la cuenta de Instagram Business.
Audita: audiencia (edad, género, ciudad, país), alcance y visitas, crecimiento,
contenido por publicación (tipo, alcance, guardados, compartidos, interacciones).

Solo lectura. Sin credenciales devuelve estado WAITING_FOR_CREDENTIALS, sin datos inventados.
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v18.0"

# Demografía de seguidores: un breakdown por llamada.
FOLLOWER_BREAKDOWNS = ["age", "gender", "city", "country"]

# Métricas diarias de cuenta (28 días).
ACCOUNT_DAILY_METRICS = ["reach", "profile_views", "website_clicks"]

# Métricas por publicación (IMAGE / CAROUSEL / VIDEO / REEL comparten estas).
MEDIA_FIELDS = "id,caption,media_type,timestamp,permalink,like_count,comments_count"
MEDIA_INSIGHT_METRICS = "reach,saved,shares,total_interactions"


class InstagramAuditor:
    """Auditor de cuenta Instagram Business (solo lectura)."""

    def __init__(self, credentials: Optional[Dict] = None, session=None):
        """
        Args:
            credentials: {
                'access_token': str,                    # token de Meta con insights de Instagram
                'instagram_business_account_id': str,   # ID de la cuenta Instagram Business
                'page_id': str                          # (opcional) página de Facebook vinculada
            }
            session: objeto con get(); por defecto requests (permite pruebas sin red).
        """
        self.platform = "instagram"
        self.credentials = credentials or {}
        self.is_connected = credentials is not None and all(
            k in credentials for k in ["access_token", "instagram_business_account_id"]
        )
        self.session = session or requests
        self.audit_date = date.today().isoformat()
        self.findings: List[Dict] = []
        self.score = 0
        self.audience_data: Dict = {}
        self.account_data: Dict = {}
        self.content_data: Dict = {}

    # ------------------------------------------------------------------ API
    def _get(self, path: str, params: Dict) -> Dict:
        params = {**params, "access_token": self.credentials["access_token"]}
        response = self.session.get(f"{GRAPH_URL}/{path}", params=params, timeout=20)
        response.raise_for_status()
        return response.json()

    def _ig_id(self) -> str:
        return self.credentials["instagram_business_account_id"]

    @staticmethod
    def _window(days: int = 28):
        end = date.today() - timedelta(days=1)  # el día actual aún no tiene datos completos
        start = end - timedelta(days=days - 1)
        return int(_ts(start)), int(_ts(end + timedelta(days=1)))

    # ---------------------------------------------------------------- audit
    def audit(self, site_data: Optional[Dict] = None) -> Dict:
        if not self.is_connected:
            return self._generate_no_credentials_report()

        for step in (
            self._get_audience_demographics,
            self._get_account_metrics,
            self._get_content_performance,
        ):
            try:
                step()
            except Exception as e:  # una sección que falla no tumba el resto
                logger.warning(f"Instagram: {step.__name__} falló: {e}")
                self.findings.append({
                    "severity": "ERROR",
                    "title": f"No se pudo leer: {step.__name__.strip('_').replace('_', ' ')}",
                    "description": str(e),
                    "category": "connection",
                })

        self.score = self._calculate_score()
        return self._generate_report()

    def _get_audience_demographics(self) -> None:
        """Seguidores por edad, género, ciudad y país (follower_demographics)."""
        result: Dict[str, Dict] = {}
        for breakdown in FOLLOWER_BREAKDOWNS:
            data = self._get(f"{self._ig_id()}/insights", {
                "metric": "follower_demographics",
                "period": "lifetime",
                "metric_type": "total_value",
                "breakdown": breakdown,
            })
            items = data.get("data", [])
            if not items:
                continue
            breakdowns = (items[0].get("total_value") or {}).get("breakdowns", [])
            values = {}
            for block in breakdowns:
                for r in block.get("results", []):
                    key = ",".join(r.get("dimension_values", []))
                    values[key] = r.get("value", 0)
            result[breakdown] = values
        self.audience_data = result
        if not result:
            self.findings.append({
                "severity": "INFO",
                "title": "Audiencia no disponible",
                "description": "Meta no devolvió demografía de seguidores. Suele requerir al menos 100 seguidores y permiso de insights.",
                "category": "audience",
            })

    def _get_account_metrics(self) -> None:
        """Alcance, visitas al perfil, clics al sitio y seguidores en 28 días."""
        since, until = self._window(28)
        data = self._get(f"{self._ig_id()}/insights", {
            "metric": ",".join(ACCOUNT_DAILY_METRICS + ["follower_count"]),
            "period": "day",
            "since": since,
            "until": until,
        })
        totals: Dict[str, int] = {}
        for item in data.get("data", []):
            values = item.get("values", [])
            totals[item.get("name")] = sum(int(v.get("value", 0)) for v in values)
        self.account_data = totals

    def _get_content_performance(self) -> None:
        """Publicaciones de la cuenta con métricas por post."""
        media = self._get(f"{self._ig_id()}/media", {"fields": MEDIA_FIELDS, "limit": 50})
        posts = []
        for m in media.get("data", []):
            row = {
                "id": m.get("id"),
                "media_type": m.get("media_type"),
                "timestamp": m.get("timestamp"),
                "permalink": m.get("permalink"),
                "caption": (m.get("caption") or "")[:300],
                "likes": int(m.get("like_count", 0)),
                "comments": int(m.get("comments_count", 0)),
            }
            try:
                ins = self._get(f"{m.get('id')}/insights", {"metric": MEDIA_INSIGHT_METRICS})
                for metric in ins.get("data", []):
                    vals = metric.get("values", [{}])
                    row[metric.get("name")] = int((vals[0] or {}).get("value", 0))
            except requests.RequestException as e:  # tipos de media pueden no tener todas las métricas
                logger.info(f"Instagram: sin insights para {m.get('id')}: {e}")
            posts.append(row)

        by_type: Dict[str, Dict] = {}
        for p in posts:
            t = p.get("media_type") or "OTHER"
            agg = by_type.setdefault(t, {"posts": 0, "reach": 0, "saved": 0})
            agg["posts"] += 1
            agg["reach"] += p.get("reach", 0)
            agg["saved"] += p.get("saved", 0)
        self.content_data = {"posts": posts, "by_media_type": by_type}

    def _calculate_score(self) -> Optional[int]:
        """Sin regla de puntaje medida todavía: None (no 0 fijo)."""
        return None

    # --------------------------------------------------------------- reports
    def _generate_no_credentials_report(self) -> Dict:
        return {
            "platform": self.platform,
            "score": 0,
            "audit_date": self.audit_date,
            "status": "WAITING_FOR_CREDENTIALS",
            "findings": [
                {
                    "severity": "INFO",
                    "title": "Instagram Business no conectado",
                    "description": "Para auditar Instagram se requiere un token de Meta y el ID de la cuenta Instagram Business.",
                    "required_fields": {
                        "access_token": "Token de Meta con permisos de insights de Instagram",
                        "instagram_business_account_id": "ID de la cuenta Instagram Business",
                        "page_id": "ID de la página de Facebook vinculada (opcional)",
                    },
                    "category": "setup",
                }
            ],
            "summary": {
                "status": "AWAITING_CREDENTIALS",
                "can_audit": False,
                "recommendation": "Conecta Instagram para medir audiencia, alcance y contenido por publicación",
            },
        }

    def _generate_report(self) -> Dict:
        return {
            "platform": self.platform,
            "score": self.score,
            "audit_date": self.audit_date,
            "findings": self.findings,
            "audience_data": self.audience_data,
            "account_data": self.account_data,
            "content_data": self.content_data,
            "summary": {
                "total_findings": len(self.findings),
                "status": "CREDENTIALS_PROVIDED" if self.is_connected else "NO_CREDENTIALS",
                "can_audit": self.is_connected,
            },
        }


def _ts(d: date) -> float:
    from datetime import datetime, time
    return datetime.combine(d, time.min).timestamp()


def audit_instagram(credentials: Optional[Dict] = None, site_data: Optional[Dict] = None) -> Dict:
    """Función helper para auditar Instagram."""
    return InstagramAuditor(credentials).audit(site_data)
