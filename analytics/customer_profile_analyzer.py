#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Customer Profile Analyzer
Correlaciona datos de Instagram con datos del site para recomendaciones personalizadas
Crea perfiles de cliente ideal basado en audiencia real en Instagram
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CustomerProfileAnalyzer:
    """Analizador de perfiles de clientes basado en Instagram + Site data"""

    def __init__(self):
        self.audit_date = datetime.now().isoformat()
        self.recommendations = []
        self.insights = []
        self.profile_gaps = []

    def analyze(self, instagram_data: Dict, site_data: Dict, tracking_data: Dict = None) -> Dict:
        """
        Analizar perfil de cliente cruzando Instagram + Site data

        Args:
            instagram_data: Resultados del Instagram auditor
            site_data: Datos del sitio (SEO audit, tracking, conversiones)
            tracking_data: Datos de tracking (opcional)

        Returns:
            Dict con análisis de perfil de cliente
        """

        self.recommendations = []
        self.insights = []
        self.profile_gaps = []

        # 1. Extraer datos de Instagram
        ig_audience = self._extract_instagram_audience(instagram_data)

        # 2. Extraer datos del site
        site_metrics = self._extract_site_metrics(site_data)

        # 3. Analizar gaps
        self._analyze_audience_site_gap(ig_audience, site_metrics)

        # 4. Generar recomendaciones
        self._generate_recommendations(ig_audience, site_metrics, tracking_data)

        # 5. Crear perfil de cliente ideal
        ideal_profile = self._create_ideal_customer_profile(ig_audience, site_metrics)

        return self._generate_report(ig_audience, site_metrics, ideal_profile)

    def _extract_instagram_audience(self, instagram_data: Dict) -> Dict:
        """Extrae datos de audiencia de Instagram"""

        if instagram_data.get("status") == "WAITING_FOR_CREDENTIALS":
            return {
                "connected": False,
                "message": "Instagram no conectado - proporciona credenciales OAuth"
            }

        audience = {
            "connected": instagram_data.get("summary", {}).get("can_audit", False),
            "platform_score": instagram_data.get("score", 0),
            "findings_count": instagram_data.get("summary", {}).get("total_findings", 0),
            "audience_data": instagram_data.get("audience_data", {})
        }

        return audience

    def _extract_site_metrics(self, site_data: Dict) -> Dict:
        """Extrae métricas del sitio"""

        metrics = {
            "seo_score": 0,
            "tracking_score": 0,
            "conversion_potential": "unknown",
            "primary_keywords": [],
            "tracking_platforms": []
        }

        # Extraer de auditoría de tracking
        if isinstance(site_data, dict) and "tracking" in site_data:
            tracking_audit = site_data["tracking"]
            metrics["tracking_score"] = tracking_audit.get("score", 0)

            # Identificar plataformas de tracking
            for finding in tracking_audit.get("findings", []):
                if "GTM" in finding.get("title", ""):
                    metrics["tracking_platforms"].append("GTM")
                if "GA4" in finding.get("title", ""):
                    metrics["tracking_platforms"].append("GA4")
                if "Facebook" in finding.get("title", ""):
                    metrics["tracking_platforms"].append("Facebook Pixel")

        return metrics

    def _analyze_audience_site_gap(self, ig_audience: Dict, site_metrics: Dict):
        """Analiza gaps entre audiencia de Instagram y el sitio"""

        if not ig_audience.get("connected"):
            self.insights.append({
                "type": "missing_data",
                "title": "Instagram no conectado",
                "description": "No se puede analizar la audiencia sin credenciales de Instagram",
                "priority": "HIGH"
            })
            return

        # Gaps comunes
        if site_metrics.get("tracking_score", 0) < 50:
            self.profile_gaps.append({
                "gap": "Tracking insuficiente",
                "description": "No puedes trackear correctamente a los clientes de Instagram al sitio",
                "impact": "No sabes si tus followers en Instagram se convierten en el sitio",
                "priority": "HIGH"
            })

        if "GA4" not in site_metrics.get("tracking_platforms", []):
            self.profile_gaps.append({
                "gap": "Google Analytics 4 faltante",
                "description": "Sin GA4 no puedes medir comportamiento de visitantes",
                "impact": "Desconoces qué hacen tus followers cuando llegan al sitio",
                "priority": "MEDIUM"
            })

        if "Facebook Pixel" not in site_metrics.get("tracking_platforms", []):
            self.profile_gaps.append({
                "gap": "Facebook Pixel faltante",
                "description": "Sin Pixel no puedes retargetear a visitors en Instagram",
                "impact": "Pierdes oportunidad de reconectar con visitors interesados",
                "priority": "MEDIUM"
            })

    def _generate_recommendations(self, ig_audience: Dict, site_metrics: Dict, tracking_data: Dict = None):
        """Genera recomendaciones basadas en el análisis"""

        priority_level = "HIGH" if not ig_audience.get("connected") else "MEDIUM"

        # Recomendación 1: Conectar Instagram
        if not ig_audience.get("connected"):
            self.recommendations.append({
                "priority": "CRITICAL",
                "category": "setup",
                "recommendation": "Conectar Instagram Business Account",
                "description": "Proporciona credenciales OAuth de Meta para analizar tu audiencia",
                "expected_impact": "Conocerás exactamente quién es tu audiencia en Instagram",
                "timeline": "Inmediato (15 min)"
            })

        # Recomendación 2: Mejorar tracking
        if site_metrics.get("tracking_score", 0) < 70:
            self.recommendations.append({
                "priority": "HIGH",
                "category": "tracking",
                "recommendation": "Mejorar tracking del sitio",
                "description": "Instala/mejora GTM, GA4 y Facebook Pixel para medir conversiones",
                "expected_impact": "Sabrás qué followers se convierten y dónde",
                "timeline": "1-2 días"
            })

        # Recomendación 3: Crear perfil de cliente ideal
        self.recommendations.append({
            "priority": "HIGH",
            "category": "strategy",
            "recommendation": "Crear buyer persona basado en Instagram",
            "description": "Usa datos de audiencia para crear mensajes personalizados",
            "expected_impact": "Mensajes más relevantes = mejor engagement y conversiones",
            "timeline": "3-5 días"
        })

        # Recomendación 4: Crear conversión funnel
        self.recommendations.append({
            "priority": "MEDIUM",
            "category": "conversion",
            "recommendation": "Crear conversión funnel Instagram → Sitio",
            "description": "Diseña landing page específica para followers de Instagram",
            "expected_impact": "Followers de Instagram tendrán experiencia optimizada",
            "timeline": "1 semana"
        })

    def _create_ideal_customer_profile(self, ig_audience: Dict, site_metrics: Dict) -> Dict:
        """Crea perfil de cliente ideal basado en audiencia real"""

        if not ig_audience.get("connected"):
            return {
                "status": "awaiting_data",
                "message": "Conecta Instagram para generar perfil automático"
            }

        # Placeholder: cuando se conecte Instagram, esto vendrá de la API
        ideal_profile = {
            "data_source": "Instagram + Site Analytics",
            "generated_at": self.audit_date,
            "demographics": {
                "age_range": "Pendiente datos de Instagram",
                "location": "Pendiente datos de Instagram",
                "interests": "Pendiente datos de Instagram",
                "language": "Pendiente datos de Instagram"
            },
            "behavior": {
                "engagement_pattern": "Pendiente datos de Instagram",
                "content_preferences": "Pendiente datos de Instagram",
                "purchase_intent": "Pendiente datos de Instagram"
            },
            "conversion_potential": "high" if site_metrics.get("tracking_score", 0) > 60 else "unknown"
        }

        return ideal_profile

    def _generate_report(self, ig_audience: Dict, site_metrics: Dict, ideal_profile: Dict) -> Dict:
        """Genera el reporte de análisis"""

        return {
            "analysis_date": self.audit_date,
            "status": "partial" if not ig_audience.get("connected") else "complete",
            "instagram_connected": ig_audience.get("connected", False),
            "instagram_score": ig_audience.get("platform_score", 0),
            "site_tracking_score": site_metrics.get("tracking_score", 0),
            "audience_data": ig_audience.get("audience_data", {}),
            "profile_gaps": self.profile_gaps,
            "recommendations": self.recommendations,
            "ideal_customer_profile": ideal_profile,
            "summary": {
                "total_gaps": len(self.profile_gaps),
                "total_recommendations": len(self.recommendations),
                "critical_recommendations": len([r for r in self.recommendations if r.get("priority") == "CRITICAL"]),
                "next_action": self.recommendations[0] if self.recommendations else None
            }
        }


def analyze_customer_profile(instagram_data: Dict, site_data: Dict, tracking_data: Dict = None) -> Dict:
    """Función helper para analizar perfil de cliente"""
    analyzer = CustomerProfileAnalyzer()
    return analyzer.analyze(instagram_data, site_data, tracking_data)
