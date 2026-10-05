#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads Auditor - Auditoría de Campañas en Google Ads
Métricas: Estructura, Keywords, Quality Score, Tracking
"""

import json
from typing import Dict, Optional
from datetime import datetime


class GoogleAdsAuditor:
    """Auditor especializado en Google Ads"""

    def __init__(self):
        self.platform = "google_ads"
        self.metrics = {
            "estructura": {"score": 0, "findings": []},
            "keywords": {"score": 0, "findings": []},
            "quality_score": {"score": 0, "findings": []},
            "tracking": {"score": 0, "findings": []}
        }

    def audit(self, campaign_data: Dict) -> Dict:
        """
        Realizar auditoría completa de Google Ads

        Esperado en campaign_data:
        {
            'account_id': str,
            'campaigns': List[Dict],
            'keywords': List[Dict],
            'tracking_template': str,
            'conversion_tracking': bool
        }
        """
        self.metrics = self._reset_metrics()

        # Auditar cada componente
        self._audit_estructura(campaign_data.get('campaigns', []))
        self._audit_keywords(campaign_data.get('keywords', []))
        self._audit_quality_score(campaign_data.get('campaigns', []))
        self._audit_tracking(campaign_data)

        # Calcular score general
        overall_score = self._calculate_overall_score()

        return {
            "platform": self.platform,
            "overall_score": overall_score,
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }

    def _audit_estructura(self, campaigns: list):
        """Auditar estructura de cuentas y campañas"""
        score = 100
        findings = []

        if not campaigns:
            score = 20
            findings.append({
                "severity": "critical",
                "issue": "Sin campañas activas",
                "recommendation": "Crear al menos 1 campaña de Search o Display"
            })
        else:
            # Verificar estructura jerárquica
            well_organized = 0
            for campaign in campaigns:
                if campaign.get('name') and campaign.get('budget'):
                    well_organized += 1

            score = int((well_organized / len(campaigns)) * 100)

            if score < 70:
                findings.append({
                    "severity": "medium",
                    "issue": "Estructura de campañas podría mejorar",
                    "recommendation": "Organizar por: Tipo de producto, Geografía, Presupuesto"
                })

            # Verificar presupuestos
            total_budget = sum(c.get('budget', 0) for c in campaigns)
            if total_budget == 0:
                findings.append({
                    "severity": "high",
                    "issue": "Presupuesto no asignado",
                    "recommendation": "Asignar presupuesto diario a campañas"
                })

        self.metrics["estructura"] = {"score": score, "findings": findings}

    def _audit_keywords(self, keywords: list):
        """Auditar keywords y tipos de concordancia"""
        score = 100
        findings = []

        if not keywords:
            score = 0
            findings.append({
                "severity": "critical",
                "issue": "No hay keywords configuradas",
                "recommendation": "Agregar keywords relevantes para Search"
            })
        else:
            # Verificar diversidad de tipos de concordancia
            match_types = {}
            for kw in keywords:
                match_type = kw.get('match_type', 'unknown')
                match_types[match_type] = match_types.get(match_type, 0) + 1

            # Verificar presencia de phrase y broad
            has_phrase = 'phrase' in match_types
            has_broad = 'broad' in match_types
            has_exact = 'exact' in match_types

            if not (has_exact and has_phrase):
                score = 60
                findings.append({
                    "severity": "high",
                    "issue": "Falta variedad en tipos de concordancia",
                    "recommendation": "Usar mix: Exact (control) + Phrase (cobertura) + Broad (alcance)"
                })

            # Verificar búsquedas de términos negativos
            negative_keywords = sum(1 for kw in keywords if kw.get('is_negative', False))
            if negative_keywords == 0:
                findings.append({
                    "severity": "medium",
                    "issue": "Sin keywords negativos configurados",
                    "recommendation": "Agregar negative keywords para evitar clics innecesarios"
                })
            else:
                score = min(score, 85)

        self.metrics["keywords"] = {"score": score, "findings": findings}

    def _audit_quality_score(self, campaigns: list):
        """Auditar Quality Score general"""
        score = 50
        findings = []

        if not campaigns:
            score = 0
            findings.append({
                "severity": "critical",
                "issue": "Sin campañas para evaluar Quality Score",
                "recommendation": "Crear y activar campañas"
            })
        else:
            # Simular QS promedio basado en estructura
            avg_qs = sum(c.get('avg_quality_score', 5) for c in campaigns) / len(campaigns)
            score = int(avg_qs * 10)

            if avg_qs < 5:
                findings.append({
                    "severity": "high",
                    "issue": f"Quality Score bajo: {avg_qs:.1f}/10",
                    "recommendation": "Mejorar CTR, relevancia de landing page, ad relevance"
                })
            elif avg_qs >= 8:
                findings.append({
                    "severity": "info",
                    "issue": f"Quality Score excelente: {avg_qs:.1f}/10",
                    "recommendation": "Mantener buenas prácticas, explorar pujas más bajas"
                })

        self.metrics["quality_score"] = {"score": score, "findings": findings}

    def _audit_tracking(self, campaign_data: Dict):
        """Auditar tracking de conversiones y etiquetado"""
        score = 100
        findings = []

        tracking_template = campaign_data.get('tracking_template', '')
        conversion_tracking = campaign_data.get('conversion_tracking', False)

        if not tracking_template:
            score = 30
            findings.append({
                "severity": "high",
                "issue": "Tracking template no configurado",
                "recommendation": "Agregar UTM parameters: utm_source, utm_medium, utm_campaign"
            })
        else:
            if not conversion_tracking:
                score = 60
                findings.append({
                    "severity": "high",
                    "issue": "Conversion tracking deshabilitado",
                    "recommendation": "Habilitar Google Ads Conversion Tracking"
                })
            else:
                score = 95
                findings.append({
                    "severity": "info",
                    "issue": "Tracking completo habilitado",
                    "recommendation": "Monitorear conversion rate > 2%"
                })

        self.metrics["tracking"] = {"score": score, "findings": findings}

    def _reset_metrics(self) -> Dict:
        """Reiniciar métricas"""
        return {
            "estructura": {"score": 0, "findings": []},
            "keywords": {"score": 0, "findings": []},
            "quality_score": {"score": 0, "findings": []},
            "tracking": {"score": 0, "findings": []}
        }

    def _calculate_overall_score(self) -> int:
        """Calcular score general ponderado"""
        weights = {
            "estructura": 0.25,
            "keywords": 0.25,
            "quality_score": 0.25,
            "tracking": 0.25
        }

        total = sum(
            self.metrics[metric]["score"] * weights[metric]
            for metric in weights.keys()
        )

        return int(total)


def create_sample_google_audit() -> Dict:
    """Crear auditoría de ejemplo para Google Ads"""
    sample_data = {
        "account_id": "123456789",
        "campaigns": [
            {
                "name": "Search_Ecommerce_Oct2026",
                "budget": 500,
                "avg_quality_score": 7.5
            }
        ],
        "keywords": [
            {"text": "auditoría web", "match_type": "exact", "is_negative": False},
            {"text": "auditoría digital", "match_type": "phrase", "is_negative": False},
            {"text": "gratis", "match_type": "broad", "is_negative": True},
        ],
        "tracking_template": "https://example.com?utm_source=google&utm_medium=cpc&utm_campaign={campaignid}",
        "conversion_tracking": True
    }

    auditor = GoogleAdsAuditor()
    return auditor.audit(sample_data)
