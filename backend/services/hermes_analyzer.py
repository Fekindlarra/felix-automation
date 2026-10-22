#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes LLM Analyzer Service
Integración con API de Hermes (Nous Research) para análisis automático de auditorías
"""

import os
import json
import asyncio
import ssl
import urllib.request
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

# Desactivar SSL verification para Windows
ssl._create_default_https_context = ssl._create_unverified_context

HERMES_API_KEY = os.getenv("HERMES_API_KEY", "")
HERMES_API_URL = "https://inference-api.nousresearch.com/v1/chat/completions"
HERMES_MODEL = "Hermes-4.3-36B"

# ═══════════════════════════════════════════════════════════════════════════
# MODELOS PYDANTIC
# ═══════════════════════════════════════════════════════════════════════════

class InstagramMetrics(BaseModel):
    """Datos de Instagram extraídos desde Make.com"""
    followers: int
    engagement_rate: float
    reach_daily: int
    impressions: int
    posts_created: int
    stories_views: int
    comments: int
    likes: int

class AuditoriaData(BaseModel):
    """Datos de auditoría a analizar"""
    cliente_id: str
    auditoria_id: str
    instagram: Optional[InstagramMetrics] = None
    website_metrics: Optional[Dict[str, Any]] = None
    otros_datos: Optional[Dict[str, Any]] = None

class HermesAnalysis(BaseModel):
    """Respuesta de análisis de Hermes"""
    auditoria_id: str
    cliente_id: str
    timestamp: str
    resumen_ejecutivo: str
    hallazgos_principales: List[str]
    recomendaciones: List[str]
    score_general: float
    detalles_por_metrica: Dict[str, Dict[str, Any]]
    proximos_pasos: List[str]

# ═══════════════════════════════════════════════════════════════════════════
# CONSTRUCTOR DE PROMPTS
# ═══════════════════════════════════════════════════════════════════════════

class HermesPromptBuilder:
    """Construye prompts estructurados para Hermes"""

    @staticmethod
    def build_instagram_analysis_prompt(data: AuditoriaData) -> str:
        """Construye prompt para análisis de Instagram"""

        if not data.instagram:
            return "No hay datos de Instagram para analizar"

        metrics = data.instagram

        prompt = f"""
Eres un experto en marketing digital y análisis de redes sociales con experiencia en estrategia Instagram.

DATOS DE INSTAGRAM PARA ANALIZAR:
- Seguidores: {metrics.followers:,}
- Tasa de engagement: {metrics.engagement_rate:.2f}%
- Alcance diario: {metrics.reach_daily:,}
- Impresiones: {metrics.impressions:,}
- Posts creados: {metrics.posts_created}
- Vistas de stories: {metrics.stories_views:,}
- Comentarios: {metrics.comments}
- Likes: {metrics.likes}

TAREA:
1. Analiza las métricas proporcionadas
2. Identifica HALLAZGOS PRINCIPALES (máximo 5)
3. Proporciona RECOMENDACIONES ESPECÍFICAS (máximo 5)
4. Calcula un SCORE GENERAL (0-100)
5. Sugiere PRÓXIMOS PASOS

FORMATO DE RESPUESTA JSON:
{{
    "resumen_ejecutivo": "Análisis ejecutivo de 2-3 líneas sobre el desempeño de Instagram",
    "hallazgos_principales": ["Hallazgo 1", "Hallazgo 2", "Hallazgo 3"],
    "recomendaciones": ["Recomendación 1", "Recomendación 2", "Recomendación 3"],
    "score_general": 75.5,
    "detalles_por_metrica": {{
        "engagement": {{"analisis": "El engagement es bajo", "tendencia": "negativa"}},
        "alcance": {{"analisis": "Alcance en descenso", "tendencia": "negativa"}},
        "crecimiento": {{"analisis": "Crecimiento lento", "tendencia": "negativa"}}
    }},
    "proximos_pasos": ["Paso 1", "Paso 2", "Paso 3"]
}}

Responde SOLO con el JSON válido, sin explicaciones adicionales.
"""
        return prompt

# ═══════════════════════════════════════════════════════════════════════════
# CLIENTE DE HERMES
# ═══════════════════════════════════════════════════════════════════════════

class HermesClient:
    """Cliente para llamadas a API de Hermes (Nous Research)"""

    def __init__(self, api_key: str = HERMES_API_KEY, api_url: str = HERMES_API_URL):
        self.api_key = api_key
        self.api_url = api_url
        self.model = HERMES_MODEL

    async def analyze(self, prompt: str, max_tokens: int = 1500) -> str:
        """
        Envía prompt a Hermes y obtiene respuesta

        Args:
            prompt: El prompt a enviar
            max_tokens: Máximo de tokens en respuesta

        Returns:
            Respuesta de Hermes (texto)
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }

            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode(),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())
                return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        except urllib.error.HTTPError as e:
            raise Exception(f"Hermes API error: {e.code} - {e.reason}")
        except Exception as e:
            raise Exception(f"Hermes error: {str(e)}")

    async def close(self):
        """Cierra la conexión del cliente"""
        pass

# ═══════════════════════════════════════════════════════════════════════════
# ANALIZADOR DE AUDITORÍAS
# ═══════════════════════════════════════════════════════════════════════════

class AuditoryAnalyzer:
    """Orquesta el análisis de auditorías usando Hermes"""

    def __init__(self):
        self.hermes = HermesClient()

    async def analyze_auditoria(self, data: AuditoriaData) -> HermesAnalysis:
        """
        Realiza análisis completo de una auditoría

        Args:
            data: Datos de auditoría a analizar

        Returns:
            Resultado de análisis estructurado
        """

        analyses = {}

        # Analizar Instagram si hay datos
        if data.instagram:
            prompt = HermesPromptBuilder.build_instagram_analysis_prompt(data)
            try:
                response = await self.hermes.analyze(prompt)
                analyses["instagram"] = json.loads(response)
            except Exception as e:
                analyses["instagram"] = {"error": str(e)}

        # Construir respuesta estructurada
        instagram_data = analyses.get("instagram", {})
        return HermesAnalysis(
            auditoria_id=data.auditoria_id,
            cliente_id=data.cliente_id,
            timestamp=datetime.utcnow().isoformat(),
            resumen_ejecutivo=instagram_data.get("resumen_ejecutivo", "Análisis completado"),
            hallazgos_principales=instagram_data.get("hallazgos_principales", []),
            recomendaciones=instagram_data.get("recomendaciones", []),
            score_general=float(instagram_data.get("score_general", 0)),
            detalles_por_metrica=instagram_data.get("detalles_por_metrica", {}),
            proximos_pasos=instagram_data.get("proximos_pasos", [])
        )

    async def close(self):
        """Cierra la conexión"""
        await self.hermes.close()

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE PRUEBA
# ═══════════════════════════════════════════════════════════════════════════

async def test_hermes():
    """Test rápido del servicio Hermes"""

    analyzer = AuditoryAnalyzer()

    # Datos de prueba
    test_data = AuditoriaData(
        cliente_id="test-123",
        auditoria_id="audit-456",
        instagram=InstagramMetrics(
            followers=1500,
            engagement_rate=3.2,
            reach_daily=450,
            impressions=2000,
            posts_created=12,
            stories_views=800,
            comments=45,
            likes=320
        )
    )

    try:
        print("🔄 Analizando con Hermes...")
        result = await analyzer.analyze_auditoria(test_data)
        print("\n✅ Análisis completado:")
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await analyzer.close()

if __name__ == "__main__":
    asyncio.run(test_hermes())
