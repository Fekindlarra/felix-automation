#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO Audit Routes - FASE 14: SEO Analysis Integration
Endpoints para auditoría SEO (Técnica, Contenido, Rendimiento, Seguridad)
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status, BackgroundTasks

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator, Audit
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from auditors.seo_auditor import SEOAuditor

# Logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/seo", tags=["seo"])

# Global instances
_orchestrator: Optional[FelixAutomationOrchestrator] = None
_auditor_agent: Optional[MultiPlatformAuditorAgent] = None
_seo_auditor: Optional[SEOAuditor] = None


def get_orchestrator() -> FelixAutomationOrchestrator:
    """Obtener instancia del orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = FelixAutomationOrchestrator()
        try:
            _orchestrator.connect_database()
        except Exception as e:
            logger.warning(f"⚠️ Base de datos no disponible: {e}")
    return _orchestrator


def get_auditor_agent() -> MultiPlatformAuditorAgent:
    """Obtener instancia del auditor agent"""
    global _auditor_agent
    if _auditor_agent is None:
        orch = get_orchestrator()
        _auditor_agent = MultiPlatformAuditorAgent(orch)
    return _auditor_agent


def get_seo_auditor() -> SEOAuditor:
    """Obtener instancia del SEO auditor"""
    global _seo_auditor
    if _seo_auditor is None:
        _seo_auditor = SEOAuditor()
    return _seo_auditor


# ============================================================================
# SEO AUDIT ENDPOINTS
# ============================================================================

@router.get("/audit/{client_id}")
async def get_latest_seo_audit(
    client_id: int,
    token: str
) -> Dict[str, Any]:
    """
    Obtener la auditoría SEO más reciente de un cliente

    Retorna:
    - overall_score (0-100)
    - metrics (técnica, contenido, rendimiento, seguridad)
    - keywords_detected
    - findings por categoría
    - timestamp de la auditoría
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        orch = get_orchestrator()

        # Buscar auditoría más reciente de SEO
        audits = orch.db.query(
            "SELECT * FROM audits WHERE client_id = ? AND platform = 'seo' ORDER BY created_at DESC LIMIT 1",
            (client_id,)
        )

        if not audits:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No SEO audit found for client {client_id}"
            )

        audit = audits[0]
        findings = orch.db.query(
            "SELECT * FROM audit_findings WHERE audit_id = ? ORDER BY severity DESC",
            (audit['id'],)
        )

        return {
            "status": "success",
            "client_id": client_id,
            "audit_id": audit['id'],
            "audit_type": audit['audit_type'],
            "platform": audit['platform'],
            "score": audit['score'],
            "findings_count": len(findings),
            "created_at": audit['created_at'],
            "findings": [dict(f) for f in findings]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo auditoría SEO para cliente {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener auditoría SEO: {str(e)}"
        )


@router.post("/audit/{client_id}")
async def run_seo_audit(
    client_id: int,
    token: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Ejecutar auditoría SEO para un cliente bajo demanda

    Parámetros:
    - client_id: ID del cliente
    - token: Token de autenticación

    Retorna:
    - audit_id: ID de la auditoría creada
    - status: running/completed
    - overall_score: Puntuación de SEO (0-100)
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        orch = get_orchestrator()

        # Verificar que el cliente existe
        client = orch.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente {client_id} no encontrado"
            )

        # Crear registro de auditoría
        audit_id = orch.create_audit(
            client_id=client_id,
            audit_type='seo',
            platform='seo'
        )

        # Ejecutar auditoría en background
        background_tasks.add_task(
            _run_audit_background,
            client_id=client_id,
            audit_id=audit_id,
            orchestrator=orch
        )

        return {
            "status": "success",
            "message": "SEO audit started",
            "audit_id": audit_id,
            "client_id": client_id,
            "audit_status": "running"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error iniciando auditoría SEO para cliente {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar auditoría SEO: {str(e)}"
        )


@router.get("/history/{client_id}")
async def get_seo_audit_history(
    client_id: int,
    token: str,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Obtener historial de auditorías SEO de un cliente

    Parámetros:
    - limit: Número de registros a retornar (max 50)
    - offset: Número de registros a saltar

    Retorna:
    - audits: Lista de auditorías SEO
    - total: Total de auditorías
    - limit/offset: Parámetros de paginación
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        orch = get_orchestrator()

        # Validar límite
        if limit > 50:
            limit = 50

        # Contar total
        total_result = orch.db.query(
            "SELECT COUNT(*) as total FROM audits WHERE client_id = ? AND platform = 'seo'",
            (client_id,)
        )
        total = total_result[0]['total'] if total_result else 0

        # Obtener auditorías
        audits = orch.db.query(
            """SELECT id, client_id, audit_type, platform, score, status, created_at
               FROM audits
               WHERE client_id = ? AND platform = 'seo'
               ORDER BY created_at DESC
               LIMIT ? OFFSET ?""",
            (client_id, limit, offset)
        )

        return {
            "status": "success",
            "client_id": client_id,
            "total": total,
            "limit": limit,
            "offset": offset,
            "audits": [dict(a) for a in audits]
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo historial SEO para cliente {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial: {str(e)}"
        )


@router.get("/report/{client_id}")
async def get_seo_detailed_report(
    client_id: int,
    token: str,
    audit_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Obtener reporte detallado de auditoría SEO

    Incluye:
    - Score en cada dimensión (Técnica, Contenido, Rendimiento, Seguridad)
    - Hallazgos detallados por severidad (crítico, advertencia, info)
    - Palabras clave detectadas
    - Recomendaciones de mejora
    - Timeline de progreso
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        orch = get_orchestrator()

        # Si no se especifica audit_id, usar la más reciente
        if audit_id is None:
            latest = orch.db.query(
                "SELECT id FROM audits WHERE client_id = ? AND platform = 'seo' ORDER BY created_at DESC LIMIT 1",
                (client_id,)
            )
            if not latest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No SEO audit found for client {client_id}"
                )
            audit_id = latest[0]['id']

        # Obtener auditoría
        audit_results = orch.db.query(
            "SELECT * FROM audits WHERE id = ? AND client_id = ?",
            (audit_id, client_id)
        )

        if not audit_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit {audit_id} not found"
            )

        audit = audit_results[0]

        # Obtener hallazgos
        findings = orch.db.query(
            "SELECT * FROM audit_findings WHERE audit_id = ? ORDER BY severity DESC, category",
            (audit_id,)
        )

        # Agrupar por severidad
        findings_by_severity = {
            'critical': [],
            'warning': [],
            'info': []
        }

        for f in findings:
            severity = f.get('severity', 'info').lower()
            if severity in findings_by_severity:
                findings_by_severity[severity].append(dict(f))

        # Obtener data completa de auditoría (JSON)
        audit_data = None
        if audit.get('findings_json'):
            try:
                audit_data = json.loads(audit['findings_json'])
            except:
                audit_data = {}

        return {
            "status": "success",
            "audit_id": audit_id,
            "client_id": client_id,
            "overall_score": audit['score'],
            "audit_date": audit['created_at'],
            "findings_by_severity": findings_by_severity,
            "findings_count": {
                "critical": len(findings_by_severity['critical']),
                "warning": len(findings_by_severity['warning']),
                "info": len(findings_by_severity['info']),
                "total": len(findings)
            },
            "audit_data": audit_data,
            "recommendations": _generate_seo_recommendations(audit['score'], findings_by_severity)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generando reporte SEO para cliente {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar reporte: {str(e)}"
        )


@router.get("/compare/{client_id}")
async def compare_seo_scores(
    client_id: int,
    token: str,
    days: int = 30
) -> Dict[str, Any]:
    """
    Comparar progreso de SEO score en el tiempo

    Parámetros:
    - days: Número de días a incluir en la comparación (default 30)

    Retorna:
    - scores: Lista de scores históricos
    - trend: Tendencia (improving/declining/stable)
    - improvement_percentage: Cambio porcentual en score
    - metrics_trend: Tendencia por métrica (técnica, contenido, rendimiento, seguridad)
    """
    from backend.auth import verify_admin_token
    from datetime import datetime, timedelta

    try:
        verify_admin_token(token)
        orch = get_orchestrator()

        # Calcular fecha límite
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Obtener auditorías en el período
        audits = orch.db.query(
            """SELECT id, score, created_at
               FROM audits
               WHERE client_id = ? AND platform = 'seo' AND created_at >= ?
               ORDER BY created_at ASC""",
            (client_id, cutoff_date)
        )

        if len(audits) < 2:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 2 audits to compare; found {len(audits)}",
                "audits_found": len(audits)
            }

        # Calcular tendencia
        first_score = float(audits[0]['score'])
        last_score = float(audits[-1]['score'])
        improvement = last_score - first_score
        improvement_pct = (improvement / first_score * 100) if first_score > 0 else 0

        # Determinar tendencia
        if improvement > 5:
            trend = "improving"
        elif improvement < -5:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "status": "success",
            "client_id": client_id,
            "days": days,
            "first_audit": {
                "date": audits[0]['created_at'],
                "score": first_score
            },
            "latest_audit": {
                "date": audits[-1]['created_at'],
                "score": last_score
            },
            "trend": trend,
            "improvement": improvement,
            "improvement_percentage": round(improvement_pct, 2),
            "total_audits": len(audits),
            "scores_over_time": [
                {
                    "date": a['created_at'],
                    "score": float(a['score'])
                } for a in audits
            ]
        }

    except Exception as e:
        logger.error(f"❌ Error comparando scores SEO para cliente {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al comparar scores: {str(e)}"
        )


@router.get("/dimensions/{client_id}")
async def get_seo_dimensions_breakdown(
    client_id: int,
    token: str,
    audit_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Obtener breakdown de SEO score por dimensión

    Dimensiones:
    - Técnica: Title, Meta, H1, Viewport, Charset, HTTPS, Robots
    - Contenido: Keywords, Headings, Content length, Images, Open Graph
    - Rendimiento: Page size, Load time, Core Web Vitals
    - Seguridad: HTTPS, Headers, Privacy policy, Cookies
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        orch = get_orchestrator()

        # Si no se especifica audit_id, usar la más reciente
        if audit_id is None:
            latest = orch.db.query(
                "SELECT id FROM audits WHERE client_id = ? AND platform = 'seo' ORDER BY created_at DESC LIMIT 1",
                (client_id,)
            )
            if not latest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No SEO audit found for client {client_id}"
                )
            audit_id = latest[0]['id']

        # Obtener auditoría completa con data JSON
        audit_results = orch.db.query(
            "SELECT score, findings_json FROM audits WHERE id = ? AND client_id = ?",
            (audit_id, client_id)
        )

        if not audit_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit {audit_id} not found"
            )

        audit = audit_results[0]
        audit_data = {}

        if audit.get('findings_json'):
            try:
                audit_data = json.loads(audit['findings_json'])
            except:
                pass

        # Extraer dimensiones del audit_data
        metrics = audit_data.get('metrics', {})

        return {
            "status": "success",
            "audit_id": audit_id,
            "client_id": client_id,
            "overall_score": audit['score'],
            "dimensions": {
                "tecnica": {
                    "score": metrics.get('tecnica', {}).get('score', 0),
                    "findings": len(metrics.get('tecnica', {}).get('findings', [])),
                    "weight": "25%"
                },
                "contenido": {
                    "score": metrics.get('contenido', {}).get('score', 0),
                    "findings": len(metrics.get('contenido', {}).get('findings', [])),
                    "weight": "30%"
                },
                "rendimiento": {
                    "score": metrics.get('rendimiento', {}).get('score', 0),
                    "findings": len(metrics.get('rendimiento', {}).get('findings', [])),
                    "weight": "25%"
                },
                "seguridad": {
                    "score": metrics.get('seguridad', {}).get('score', 0),
                    "findings": len(metrics.get('seguridad', {}).get('findings', [])),
                    "weight": "20%"
                }
            },
            "keywords_detected": audit_data.get('keywords_detected', [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo dimensiones SEO para cliente {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener dimensiones: {str(e)}"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _run_audit_background(
    client_id: int,
    audit_id: int,
    orchestrator: FelixAutomationOrchestrator
) -> None:
    """Ejecutar auditoría SEO en background"""
    try:
        logger.info(f"🔍 Iniciando auditoría SEO para cliente {client_id} (audit_id: {audit_id})")

        # Obtener agente
        agent = get_auditor_agent()

        # Ejecutar auditoría
        result = agent.audit_client(client_id, platforms=['seo'])

        if 'seo' in result:
            seo_result = result['seo']

            # Guardar score en BD
            orchestrator.update_audit_score(
                audit_id=audit_id,
                score=seo_result.get('overall_score', 0),
                findings=seo_result
            )

            logger.info(f"✅ Auditoría SEO completada para cliente {client_id}: score {seo_result.get('overall_score')}")
        else:
            logger.error(f"❌ No SEO result returned for client {client_id}")

    except Exception as e:
        logger.error(f"❌ Error en auditoría SEO background para cliente {client_id}: {e}")


def _generate_seo_recommendations(score: float, findings_by_severity: Dict[str, List]) -> List[str]:
    """Generar recomendaciones basadas en score y hallazgos"""
    recommendations = []

    # Recomendaciones por score general
    if score >= 90:
        recommendations.append("✅ Excelente score de SEO - Mantener las prácticas actuales")
    elif score >= 80:
        recommendations.append("📈 Buen score de SEO - Enfocarse en los hallazgos de advertencia")
    elif score >= 70:
        recommendations.append("⚠️ Score justo - Priorizar la resolución de problemas críticos")
    elif score >= 60:
        recommendations.append("🔴 Score bajo - Se recomienda auditoría técnica completa")
    else:
        recommendations.append("❌ Score muy bajo - Acción inmediata requerida")

    # Recomendaciones por hallazgos críticos
    if findings_by_severity['critical']:
        critical_count = len(findings_by_severity['critical'])
        recommendations.append(f"🚨 {critical_count} problema(s) crítico(s) requieren atención inmediata")

    # Recomendaciones por warnings
    if findings_by_severity['warning']:
        warning_count = len(findings_by_severity['warning'])
        recommendations.append(f"⚠️ {warning_count} advertencia(s) a considerar en próximas optimizaciones")

    return recommendations
