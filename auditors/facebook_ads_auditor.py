#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facebook Ads Auditor - Auditoría de Campañas en Facebook
Métricas: Estructura, Contenido, Targeting, Tracking
"""

import json
from typing import Dict, Optional
from datetime import datetime


class FacebookAdsAuditor:
    """Auditor especializado en Facebook Ads"""

    def __init__(self):
        self.platform = "facebook_ads"
        self.metrics = {
            "estructura": {"score": 0, "findings": []},
            "contenido": {"score": 0, "findings": []},
            "targeting": {"score": 0, "findings": []},
            "tracking": {"score": 0, "findings": []}
        }

    def audit(self, campaign_data: Dict) -> Dict:
        """
        Realizar auditoría completa de Facebook Ads

        Esperado en campaign_data:
        {
            'account_id': str,
            'campaigns': List[Dict],
            'pixel_id': str,
            'tracking_enabled': bool
        }
        """
        self.metrics = self._reset_metrics()

        # Auditar cada componente
        self._audit_estructura(campaign_data.get('campaigns', []))
        self._audit_contenido(campaign_data.get('campaigns', []))
        self._audit_targeting(campaign_data.get('campaigns', []))
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
        """Auditar estructura y organización de campañas"""
        score = 100
        findings = []

        if not campaigns:
            score = 20
            findings.append({
                "severity": "critical",
                "issue": "Sin campañas encontradas",
                "recommendation": "Crear al menos 1 campaña activa"
            })
        else:
            # Verificar estructura
            well_organized = sum(1 for c in campaigns if self._is_well_named(c.get('name', ''))) / len(campaigns)
            score = int(well_organized * 100)

            if well_organized < 0.8:
                findings.append({
                    "severity": "medium",
                    "issue": "Campañas con nombres poco descriptivos",
                    "recommendation": "Usar naming: [Objetivo]_[Audiencia]_[Fecha]"
                })

            # Verificar duplicados
            unique_campaigns = len(set(c.get('name') for c in campaigns))
            if unique_campaigns < len(campaigns):
                findings.append({
                    "severity": "low",
                    "issue": f"Encontradas {len(campaigns) - unique_campaigns} campañas duplicadas",
                    "recommendation": "Consolidar campañas duplicadas"
                })

        self.metrics["estructura"] = {"score": score, "findings": findings}

    def _audit_contenido(self, campaigns: list):
        """Auditar contenido de anuncios"""
        score = 100
        findings = []

        if not campaigns:
            score = 0
            findings.append({
                "severity": "critical",
                "issue": "Sin contenido de anuncios",
                "recommendation": "Crear anuncios en las campañas"
            })
        else:
            total_ads = sum(len(c.get('ads', [])) for c in campaigns)
            if total_ads == 0:
                score = 10
                findings.append({
                    "severity": "critical",
                    "issue": "No hay anuncios activos",
                    "recommendation": "Crear y activar anuncios en campañas"
                })
            else:
                # Verificar calidad de copywriting
                good_quality = sum(
                    1 for c in campaigns
                    for ad in c.get('ads', [])
                    if self._has_good_copy(ad.get('headline', ''), ad.get('body', ''))
                ) / max(total_ads, 1)

                score = int(good_quality * 100)

                if good_quality < 0.7:
                    findings.append({
                        "severity": "medium",
                        "issue": "Copy de anuncios podría mejorar",
                        "recommendation": "A/B testing: headlines más atractivos, CTAs claros"
                    })

        self.metrics["contenido"] = {"score": score, "findings": findings}

    def _audit_targeting(self, campaigns: list):
        """Auditar segmentación y targeting"""
        score = 100
        findings = []

        if not campaigns:
            score = 0
        else:
            # Verificar si hay targeting definido
            campaigns_with_targeting = sum(
                1 for c in campaigns
                if c.get('targeting', {}).get('audience_size', 0) > 0
            ) / len(campaigns)

            score = int(campaigns_with_targeting * 100)

            if campaigns_with_targeting < 0.5:
                findings.append({
                    "severity": "high",
                    "issue": "Targeting no está optimizado",
                    "recommendation": "Definir audiencias específicas por campaña"
                })

            # Verificar si hay overlapping
            audiences = [c.get('targeting', {}).get('audience_id') for c in campaigns]
            if len(audiences) != len(set(audiences)):
                findings.append({
                    "severity": "medium",
                    "issue": "Posible overlapping entre audiencias",
                    "recommendation": "Revisar exclusiones y audiencias excluidas"
                })

        self.metrics["targeting"] = {"score": score, "findings": findings}

    def _audit_tracking(self, campaign_data: Dict):
        """Auditar tracking y píxel de Facebook"""
        score = 100
        findings = []

        pixel_id = campaign_data.get('pixel_id')
        tracking_enabled = campaign_data.get('tracking_enabled', False)

        if not pixel_id:
            score = 10
            findings.append({
                "severity": "critical",
                "issue": "Píxel de Facebook no instalado",
                "recommendation": "Instalar píxel FB en sitio web"
            })
        else:
            if not tracking_enabled:
                score = 40
                findings.append({
                    "severity": "high",
                    "issue": "Tracking de eventos no configurado",
                    "recommendation": "Habilitar tracking: ViewContent, AddToCart, Purchase"
                })
            else:
                score = 90
                findings.append({
                    "severity": "info",
                    "issue": "Tracking activo",
                    "recommendation": "Monitorear CalidadDelConversión > 50%"
                })

        self.metrics["tracking"] = {"score": score, "findings": findings}

    def _reset_metrics(self) -> Dict:
        """Reiniciar métricas"""
        return {
            "estructura": {"score": 0, "findings": []},
            "contenido": {"score": 0, "findings": []},
            "targeting": {"score": 0, "findings": []},
            "tracking": {"score": 0, "findings": []}
        }

    def _calculate_overall_score(self) -> int:
        """Calcular score general ponderado"""
        weights = {
            "estructura": 0.25,
            "contenido": 0.25,
            "targeting": 0.25,
            "tracking": 0.25
        }

        total = sum(
            self.metrics[metric]["score"] * weights[metric]
            for metric in weights.keys()
        )

        return int(total)

    def _is_well_named(self, name: str) -> bool:
        """Verificar si el nombre de campaña es descriptivo"""
        return len(name) > 10 and any(
            keyword in name.lower()
            for keyword in ['objetivo', 'audiencia', 'test', 'v1', 'v2']
        )

    def _has_good_copy(self, headline: str, body: str) -> bool:
        """Verificar calidad básica de copy"""
        return len(headline) > 20 and len(body) > 30 and '?' in headline or '!' in headline


def create_sample_facebook_audit() -> Dict:
    """Crear auditoría de ejemplo para Facebook Ads"""
    sample_data = {
        "account_id": "123456789",
        "campaigns": [
            {
                "name": "Objetivo_Ventas_Oct2026",
                "ads": [
                    {
                        "headline": "¿Quieres mejorar tus ventas? ¡Descubre nuestras soluciones!",
                        "body": "Auditoría digital gratuita para optimizar tu negocio online"
                    }
                ],
                "targeting": {
                    "audience_id": "aud_001",
                    "audience_size": 50000
                }
            }
        ],
        "pixel_id": "123456789",
        "tracking_enabled": True
    }

    auditor = FacebookAdsAuditor()
    return auditor.audit(sample_data)
