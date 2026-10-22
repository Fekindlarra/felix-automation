#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes LLM Analyzer Service
Integración con API de Hermes (Nous Research) para análisis automático de auditorías
"""

import os
import json
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

HERMES_API_KEY = os.getenv("HERMES_API_KEY", "sk-nous-N7uxxgz5G75O3pz1a0Uioek4FQxms7fZ")
HERMES_API_URL = "https://api.nous.ai/v1/completions"  # Endpoint base
HERMES_MODEL = "nos-hermes-2-mixtral-8x7b-dpo"

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
Eres un experto en marketing digital y análisis de redes sociales.

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
    "resumen_ejecutivo": "Análisis ejecutivo de 2-3 líneas",
    "hallazgos_principales": ["Hallazgo 1", "Hallazgo 2", ...],
    "recomendaciones": ["Recomendación 1", "Recomendación 2", ...],
    "score_general": 75.5,
    "detalles_por_metrica": {{
        "engagement": {{"analisis": "...", "tendencia": "positiva/negativa"}},
        "alcance": {{"analisis": "...", "tendencia": "positiva/negativa"}},
        "crecimiento": {{"analisis": "...", "tendencia": "positiva/negativa"}}
    }},
    "proximos_pasos": ["Paso 1", "Paso 2", ...]
}}

Responde SOLO con el JSON válido, sin explicaciones adicionales.
"""
        return prompt

    @staticmethod
    def build_website_analysis_prompt(data: AuditoriaData) -> str:
        """Construye prompt para análisis de sitio web"""

        if not data.website_metrics:
            return "No hay datos de sitio web para analizar"

        metrics = data.website_metrics

        prompt = f"""
Eres un experto en auditoría técnica de sitios web y SEO.

DATOS DEL SITIO WEB PARA ANALIZAR:
{json.dumps(metrics, ensure_ascii=False, indent=2)}

TAREA:
1. Analiza el estado técnico del sitio web
2. Identifica PROBLEMAS CRÍTICOS (máximo 5)
3. Proporciona RECOMENDACIONES DE SEO (máximo 5)
4. Calcula un SCORE DE SALUD (0-100)
5. Estima IMPACTO POTENCIAL en tráfico

FORMATO DE RESPUESTA JSON:
{{
    "resumen_ejecutivo": "Análisis ejecutivo del sitio web",
    "hallazgos_principales": ["Problema 1", "Problema 2", ...],
    "recomendaciones": ["Recomendación 1", "Recomendación 2", ...],
    "score_general": 65.0,
    "detalles_por_metrica": {{
        "indexacion": {{"estado": "...", "accion": "..."}},
        "velocidad": {{"estado": "...", "accion": "..."}},
        "movil": {{"estado": "...", "accion": "..."}}
    }},
    "impacto_potencial": "Estimado aumento de 30-50% en tráfico orgánico"
}}

Responde SOLO con el JSON válido.
"""
        return prompt

# ═══════════════════════════════════════════════════════════════════════════
# CLIENTE DE HERMES
# ═══════════════════════════════════════════════════════════════════════════

class HermesClient:
    """Cliente para llamadas a API de Hermes"""

    def __init__(self, api_key: str = HERMES_API_KEY, api_url: str = HERMES_API_URL):
        self.api_key = api_key
        self.api_url = api_url
        self.model = HERMES_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)

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
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.95,
                "stop": ["\\n\\n", "Assistant:"]
            }

            response = await self.client.post(
                self.api_url,
                json=payload,
                headers=headers
            )

            if response.status_code != 200:
                raise Exception(f"Hermes API error: {response.status_code} - {response.text}")

            result = response.json()
            return result.get("choices", [{}])[0].get("text", "").strip()

        except httpx.RequestError as e:
            raise Exception(f"Hermes connection error: {str(e)}")
        except Exception as e:
            raise Exception(f"Hermes analysis error: {str(e)}")

    async def close(self):
        """Cierra la conexión del cliente"""
        await self.client.aclose()

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

        # Analizar website si hay datos
        if data.website_metrics:
            prompt = HermesPromptBuilder.build_website_analysis_prompt(data)
            try:
                response = await self.hermes.analyze(prompt)
                analyses["website"] = json.loads(response)
            except Exception as e:
                analyses["website"] = {"error": str(e)}

        # Construir respuesta estructurada
        return HermesAnalysis(
            auditoria_id=data.auditoria_id,
            cliente_id=data.cliente_id,
            timestamp=datetime.utcnow().isoformat(),
            resumen_ejecutivo=self._build_executive_summary(analyses),
            hallazgos_principales=self._extract_findings(analyses),
            recomendaciones=self._extract_recommendations(analyses),
            score_general=self._calculate_overall_score(analyses),
            detalles_por_metrica=self._extract_metric_details(analyses),
            proximos_pasos=self._extract_next_steps(analyses)
        )

    def _build_executive_summary(self, analyses: Dict) -> str:
        """Construye resumen ejecutivo a partir de análisis"""
        summaries = []

        if "instagram" in analyses and "resumen_ejecutivo" in analyses["instagram"]:
            summaries.append(f"Instagram: {analyses['instagram']['resumen_ejecutivo']}")

        if "website" in analyses and "resumen_ejecutivo" in analyses["website"]:
            summaries.append(f"Sitio web: {analyses['website']['resumen_ejecutivo']}")

        return " | ".join(summaries) if summaries else "Análisis completado sin detalles"

    def _extract_findings(self, analyses: Dict) -> List[str]:
        """Extrae hallazgos principales"""
        findings = []

        for key, analysis in analyses.items():
            if isinstance(analysis, dict) and "hallazgos_principales" in analysis:
                findings.extend(analysis["hallazgos_principales"])

        return findings[:5]  # Máximo 5 hallazgos

    def _extract_recommendations(self, analyses: Dict) -> List[str]:
        """Extrae recomendaciones"""
        recommendations = []

        for key, analysis in analyses.items():
            if isinstance(analysis, dict) and "recomendaciones" in analysis:
                recommendations.extend(analysis["recomendaciones"])

        return recommendations[:5]  # Máximo 5 recomendaciones

    def _calculate_overall_score(self, analyses: Dict) -> float:
        """Calcula score general promedio"""
        scores = []

        for key, analysis in analyses.items():
            if isinstance(analysis, dict) and "score_general" in analysis:
                scores.append(float(analysis["score_general"]))

        return sum(scores) / len(scores) if scores else 0.0

    def _extract_metric_details(self, analyses: Dict) -> Dict[str, Dict]:
        """Extrae detalles por métrica"""
        details = {}

        for key, analysis in analyses.items():
            if isinstance(analysis, dict) and "detalles_por_metrica" in analysis:
                details[key] = analysis["detalles_por_metrica"]

        return details

    def _extract_next_steps(self, analyses: Dict) -> List[str]:
        """Extrae próximos pasos"""
        steps = []

        for key, analysis in analyses.items():
            if isinstance(analysis, dict) and "proximos_pasos" in analysis:
                steps.extend(analysis["proximos_pasos"])

        return steps[:5]  # Máximo 5 pasos

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
