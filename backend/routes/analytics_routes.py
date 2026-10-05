#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytics Routes - PASO 1: Dashboard Integration
Endpoints para acceso a datos de FASE 10 (Predicciones, Anomalías, Recomendaciones)
"""

import sys
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analytics.dashboard_integration import DashboardIntegration
from orchestrator import FelixAutomationOrchestrator

# Logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Global instances
_orchestrator: Optional[FelixAutomationOrchestrator] = None
_dashboard_integration: Optional[DashboardIntegration] = None


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


def get_dashboard_integration() -> DashboardIntegration:
    """Obtener instancia del dashboard integration"""
    global _dashboard_integration
    if _dashboard_integration is None:
        orch = get_orchestrator()
        _dashboard_integration = DashboardIntegration(orch)
    return _dashboard_integration


# ============================================================================
# DASHBOARD ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/dashboard")
async def get_analytics_dashboard(token: str) -> Dict[str, Any]:
    """
    Obtener todos los datos de analytics para dashboard interno

    Retorna:
    - Predicciones de conversión (top 10)
    - Anomalías detectadas
    - Recomendaciones por prioridad
    - Forecast de revenue
    - Timestamp de última actualización
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        dashboard = get_dashboard_integration()
        data = dashboard.generate_dashboard_data()
        return data

    except Exception as e:
        logger.error(f"❌ Error generando analytics dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar dashboard: {str(e)}"
        )


@router.get("/client/{client_id}")
async def get_client_analytics(client_id: int, token: str) -> Dict[str, Any]:
    """
    Obtener analytics detallados para un cliente específico

    Retorna:
    - Predicción de conversión
    - Anomalías detectadas
    - Recomendaciones personalizadas
    - Factores positivos y de riesgo
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        dashboard = get_dashboard_integration()
        data = dashboard.get_client_dashboard_data(client_id)

        if data.get('status') == 'error':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=data.get('message', 'Cliente no encontrado')
            )

        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generando analytics para cliente {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar analytics: {str(e)}"
        )


@router.get("/predictions")
async def get_predictions(
    token: str,
    min_probability: float = 0,
    max_probability: float = 100,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Obtener predicciones filtradas por probabilidad

    Parámetros:
    - min_probability: Probabilidad mínima (0-100)
    - max_probability: Probabilidad máxima (0-100)
    - limit: Número máximo de resultados
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        dashboard = get_dashboard_integration()
        data = dashboard.generate_dashboard_data()

        predictions = data.get('predictions', {}).get('top_10', [])

        # Filtrar por rango de probabilidad
        filtered = [
            p for p in predictions
            if min_probability <= float(p['probability']) <= max_probability
        ]

        return {
            "total": len(filtered),
            "limit": limit,
            "predictions": filtered[:limit],
            "summary": data.get('predictions', {}).get('summary', {})
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo predicciones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener predicciones"
        )


@router.get("/anomalies")
async def get_anomalies(
    token: str,
    severity: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Obtener anomalías detectadas, opcionalmente filtradas por severidad

    Parámetros:
    - severity: CRITICAL, HIGH, MEDIUM, LOW (opcional)
    - limit: Número máximo de resultados
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        dashboard = get_dashboard_integration()
        data = dashboard.generate_dashboard_data()

        anomalies = data.get('anomalies', {}).get('active', [])

        # Filtrar por severidad si se especifica
        if severity:
            filtered_anomalies = []
            for client_anomalies in anomalies:
                filtered_client_anomalies = {
                    'client_id': client_anomalies['client_id'],
                    'anomalies': [
                        a for a in client_anomalies['anomalies']
                        if a['severity'] == severity
                    ]
                }
                if filtered_client_anomalies['anomalies']:
                    filtered_anomalies.append(filtered_client_anomalies)
            anomalies = filtered_anomalies

        return {
            "total": len(anomalies),
            "limit": limit,
            "anomalies": anomalies[:limit],
            "summary": data.get('anomalies', {}).get('summary', {})
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo anomalías: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener anomalías"
        )


@router.get("/recommendations")
async def get_recommendations(
    token: str,
    priority: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Obtener recomendaciones, opcionalmente filtradas por prioridad

    Parámetros:
    - priority: URGENT, HIGH, MEDIUM, LOW (opcional)
    - limit: Número máximo de resultados
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        dashboard = get_dashboard_integration()
        data = dashboard.generate_dashboard_data()

        urgent_recs = data.get('recommendations', {}).get('urgent', [])
        high_recs = data.get('recommendations', {}).get('high', [])

        all_recs = urgent_recs + high_recs

        # Filtrar por prioridad si se especifica
        if priority == 'URGENT':
            all_recs = urgent_recs
        elif priority == 'HIGH':
            all_recs = high_recs

        return {
            "total": len(all_recs),
            "limit": limit,
            "recommendations": all_recs[:limit],
            "summary": data.get('recommendations', {}).get('summary', {})
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener recomendaciones"
        )


@router.get("/forecast")
async def get_revenue_forecast(token: str) -> Dict[str, Any]:
    """
    Obtener forecast de revenue para 30, 60 y 90 días
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        dashboard = get_dashboard_integration()
        data = dashboard.generate_dashboard_data()

        forecast = data.get('revenue_forecast', {})
        timestamp = data.get('timestamp', '')

        return {
            "forecast": forecast,
            "timestamp": timestamp
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo forecast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener forecast"
        )


@router.get("/summary")
async def get_analytics_summary(token: str) -> Dict[str, Any]:
    """
    Obtener resumen ejecutivo de analytics
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        dashboard = get_dashboard_integration()
        data = dashboard.generate_dashboard_data()

        return {
            "predictions": data.get('predictions', {}).get('summary', {}),
            "anomalies": data.get('anomalies', {}).get('summary', {}),
            "recommendations": data.get('recommendations', {}).get('summary', {}),
            "forecast": data.get('revenue_forecast', {}),
            "timestamp": data.get('timestamp', '')
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener resumen"
        )


@router.post("/refresh")
async def refresh_analytics(token: str) -> Dict[str, Any]:
    """
    Forzar actualización manual de todos los analytics
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)
        dashboard = get_dashboard_integration()

        # Generar datos actualizados
        data = dashboard.generate_dashboard_data()

        return {
            "status": "success",
            "message": "Analytics actualizados correctamente",
            "timestamp": data.get('timestamp', '')
        }

    except Exception as e:
        logger.error(f"❌ Error refrescando analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al refrescar analytics"
        )
