#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard de Auditorías - Visualizar resultados y histórico
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

router = APIRouter(prefix="/api/dashboard/audits", tags=["audit-dashboard"])
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# MODELOS
# ═══════════════════════════════════════════════════════════════════════════

class AuditSummary(BaseModel):
    """Resumen de una auditoría"""
    auditoria_id: str
    cliente_id: str
    cliente_nombre: str
    timestamp: str
    score_general: float
    status: str
    hallazgos_count: int
    recomendaciones_count: int

class AuditDetail(BaseModel):
    """Detalles completos de una auditoría"""
    auditoria_id: str
    cliente_id: str
    cliente_nombre: str
    timestamp: str
    score_general: float
    resumen_ejecutivo: str
    hallazgos_principales: List[str]
    recomendaciones: List[str]
    proximos_pasos: List[str]
    detalles_por_metrica: Dict[str, Any]

class DashboardStats(BaseModel):
    """Estadísticas del dashboard"""
    total_auditorias: int
    promedio_score: float
    auditorias_excelentes: int  # >= 75
    auditorias_buenas: int       # >= 50
    auditorias_mejorar: int      # < 50
    ultima_auditoria: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════
# DATOS DE EJEMPLO (En producción, esto vendría de la BD)
# ═══════════════════════════════════════════════════════════════════════════

AUDITS_DB = {
    "audit-luz-20261021": {
        "auditoria_id": "audit-luz-20261021",
        "cliente_id": "luz-agencia-001",
        "cliente_nombre": "Luz Agencia",
        "timestamp": datetime.now().isoformat(),
        "score_general": 72.5,
        "status": "completada",
        "resumen_ejecutivo": "Instagram de Luz Agencia muestra engagement competitivo con crecimiento estable.",
        "hallazgos_principales": [
            "Engagement rate del 3.2% es competitivo para el sector",
            "Alcance diario de 450 es bajo considerando 1500 seguidores",
            "Stories tienen 77% más engagement que feed posts",
            "Comentarios son bajos: ratio de 1 comentario por 7 likes"
        ],
        "recomendaciones": [
            "Aumentar frecuencia de stories a 3-5 por día",
            "Implementar calls-to-action en captions para más comentarios",
            "Crear polls y quizzes en stories para engagement interactivo",
            "Colaborar con influencers locales de Santiago"
        ],
        "proximos_pasos": [
            "Implementar plan de contenido de 2 semanas",
            "Aumentar presupuesto de ads a $200/semana",
            "Hacer seguimiento semanal de métricas"
        ],
        "detalles_por_metrica": {
            "instagram": {
                "followers": 1500,
                "engagement_rate": 3.2,
                "reach_daily": 450,
                "impressions": 2000,
                "posts_created": 12,
                "stories_views": 800,
                "comments": 45,
                "likes": 320
            }
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Obtener estadísticas generales del dashboard"""
    try:
        audits = list(AUDITS_DB.values())
        
        if not audits:
            return DashboardStats(
                total_auditorias=0,
                promedio_score=0,
                auditorias_excelentes=0,
                auditorias_buenas=0,
                auditorias_mejorar=0
            )
        
        scores = [a["score_general"] for a in audits]
        excelentes = len([s for s in scores if s >= 75])
        buenas = len([s for s in scores if 50 <= s < 75])
        mejorar = len([s for s in scores if s < 50])
        
        return DashboardStats(
            total_auditorias=len(audits),
            promedio_score=sum(scores) / len(scores),
            auditorias_excelentes=excelentes,
            auditorias_buenas=buenas,
            auditorias_mejorar=mejorar,
            ultima_auditoria=audits[-1]["timestamp"]
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estadísticas"
        )

@router.get("/list", response_model=List[AuditSummary])
async def list_audits(skip: int = 0, limit: int = 10):
    """Listar auditorías (últimas primero)"""
    try:
        audits = sorted(
            AUDITS_DB.values(),
            key=lambda x: x["timestamp"],
            reverse=True
        )
        
        paginated = audits[skip:skip + limit]
        
        return [
            AuditSummary(
                auditoria_id=a["auditoria_id"],
                cliente_id=a["cliente_id"],
                cliente_nombre=a["cliente_nombre"],
                timestamp=a["timestamp"],
                score_general=a["score_general"],
                status=a["status"],
                hallazgos_count=len(a["hallazgos_principales"]),
                recomendaciones_count=len(a["recomendaciones"])
            )
            for a in paginated
        ]
    except Exception as e:
        logger.error(f"Error listing audits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar auditorías"
        )

@router.get("/{auditoria_id}", response_model=AuditDetail)
async def get_audit_detail(auditoria_id: str):
    """Obtener detalles completos de una auditoría"""
    try:
        audit = AUDITS_DB.get(auditoria_id)
        
        if not audit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Auditoría no encontrada"
            )
        
        return AuditDetail(
            auditoria_id=audit["auditoria_id"],
            cliente_id=audit["cliente_id"],
            cliente_nombre=audit["cliente_nombre"],
            timestamp=audit["timestamp"],
            score_general=audit["score_general"],
            resumen_ejecutivo=audit["resumen_ejecutivo"],
            hallazgos_principales=audit["hallazgos_principales"],
            recomendaciones=audit["recomendaciones"],
            proximos_pasos=audit["proximos_pasos"],
            detalles_por_metrica=audit["detalles_por_metrica"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener detalles de auditoría"
        )

@router.get("/client/{cliente_id}", response_model=List[AuditSummary])
async def get_client_audits(cliente_id: str):
    """Obtener todas las auditorías de un cliente"""
    try:
        audits = [
            a for a in AUDITS_DB.values()
            if a["cliente_id"] == cliente_id
        ]
        
        if not audits:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron auditorías para este cliente"
            )
        
        return [
            AuditSummary(
                auditoria_id=a["auditoria_id"],
                cliente_id=a["cliente_id"],
                cliente_nombre=a["cliente_nombre"],
                timestamp=a["timestamp"],
                score_general=a["score_general"],
                status=a["status"],
                hallazgos_count=len(a["hallazgos_principales"]),
                recomendaciones_count=len(a["recomendaciones"])
            )
            for a in sorted(audits, key=lambda x: x["timestamp"], reverse=True)
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client audits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener auditorías del cliente"
        )

