#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook para recibir datos de Make.com, analizarlos con Hermes y generar PDFs
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import logging
from datetime import datetime

from backend.services.hermes_analyzer import (
    AuditoryAnalyzer,
    AuditoriaData,
    InstagramMetrics,
    HermesAnalysis
)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/auditorias", tags=["auditorias"])
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# MODELOS
# ═══════════════════════════════════════════════════════════════════════════

class WebhookPayload(BaseModel):
    """Payload recibido desde Make.com"""
    cliente_id: str
    auditoria_id: str
    instagram: Optional[Dict[str, Any]] = None
    website_metrics: Optional[Dict[str, Any]] = None
    otros_datos: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    """Respuesta del análisis"""
    status: str
    auditoria_id: str
    cliente_id: str
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON DEL ANALIZADOR
# ═══════════════════════════════════════════════════════════════════════════

_analyzer = None

async def get_analyzer() -> AuditoryAnalyzer:
    """Obtiene o crea el analizador (singleton)"""
    global _analyzer
    if _analyzer is None:
        _analyzer = AuditoryAnalyzer()
    return _analyzer

# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/webhook", response_model=AnalysisResponse)
async def audit_webhook(payload: WebhookPayload):
    """
    Webhook para recibir datos de auditoría desde Make.com

    Flujo:
    1. Recibe datos de Instagram (u otros orígenes) de Make.com
    2. Procesa con Hermes LLM
    3. Genera análisis automático
    4. Retorna datos para PDF
    5. (Próximo) Envía PDF por email con Brevo
    """

    try:
        logger.info(f"📥 Webhook recibido para auditoría {payload.auditoria_id}")

        # Convertir payload a objeto AuditoriaData
        instagram_data = None
        if payload.instagram:
            instagram_data = InstagramMetrics(**payload.instagram)

        auditoria_data = AuditoriaData(
            cliente_id=payload.cliente_id,
            auditoria_id=payload.auditoria_id,
            instagram=instagram_data,
            website_metrics=payload.website_metrics,
            otros_datos=payload.otros_datos
        )

        # Obtener analizador
        analyzer = await get_analyzer()

        # Analizar con Hermes
        logger.info(f"🧠 Analizando con Hermes...")
        analysis = await analyzer.analyze_auditoria(auditoria_data)

        logger.info(f"✅ Análisis completado: {analysis.auditoria_id}")

        return AnalysisResponse(
            status="success",
            auditoria_id=analysis.auditoria_id,
            cliente_id=analysis.cliente_id,
            analysis=analysis.model_dump(),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"❌ Error en webhook: {str(e)}")
        return AnalysisResponse(
            status="error",
            auditoria_id=payload.auditoria_id,
            cliente_id=payload.cliente_id,
            error=str(e),
            timestamp=datetime.utcnow().isoformat()
        )

@router.get("/health", tags=["health"])
async def health_check():
    """Health check del servicio de auditorías"""
    return {
        "status": "healthy",
        "service": "audit-analyzer",
        "hermes": "connected",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/test", response_model=AnalysisResponse)
async def test_analysis():
    """
    Endpoint de prueba para validar el flujo completo
    (Sin parámetros, usa datos de ejemplo)
    """

    try:
        # Datos de prueba
        test_payload = WebhookPayload(
            cliente_id="test-client-001",
            auditoria_id="test-audit-001",
            instagram={
                "followers": 2500,
                "engagement_rate": 4.5,
                "reach_daily": 650,
                "impressions": 3200,
                "posts_created": 15,
                "stories_views": 1200,
                "comments": 65,
                "likes": 450
            }
        )

        logger.info("🧪 Iniciando prueba de análisis...")

        # Convertir a AuditoriaData
        instagram_data = InstagramMetrics(**test_payload.instagram)
        auditoria_data = AuditoriaData(
            cliente_id=test_payload.cliente_id,
            auditoria_id=test_payload.auditoria_id,
            instagram=instagram_data
        )

        # Analizar
        analyzer = await get_analyzer()
        analysis = await analyzer.analyze_auditoria(auditoria_data)

        logger.info("✅ Prueba completada exitosamente")

        return AnalysisResponse(
            status="success",
            auditoria_id=analysis.auditoria_id,
            cliente_id=analysis.cliente_id,
            analysis=analysis.model_dump(),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"❌ Error en prueba: {str(e)}")
        return AnalysisResponse(
            status="error",
            auditoria_id="test-audit-001",
            cliente_id="test-client-001",
            error=str(e),
            timestamp=datetime.utcnow().isoformat()
        )

# ═══════════════════════════════════════════════════════════════════════════
# STARTUP/SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════

async def startup_hermes():
    """Inicializa el analizador al startup de la app"""
    global _analyzer
    _analyzer = AuditoryAnalyzer()
    logger.info("✅ Servicio Hermes inicializado")

async def shutdown_hermes():
    """Cierra el analizador al shutdown de la app"""
    global _analyzer
    if _analyzer:
        await _analyzer.close()
        _analyzer = None
        logger.info("✅ Servicio Hermes cerrado")
