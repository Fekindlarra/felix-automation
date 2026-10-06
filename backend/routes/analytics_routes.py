#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytics Routes - PASO 1: Dashboard Integration
Endpoints para acceso a datos de FASE 10 (Predicciones, Anomalías, Recomendaciones)
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analytics.dashboard_integration import DashboardIntegration
from analytics.prediction_broadcaster import PredictionBroadcaster
from analytics.predictor import ConversionPredictor
from orchestrator import FelixAutomationOrchestrator

# Logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Global instances
_orchestrator: Optional[FelixAutomationOrchestrator] = None
_dashboard_integration: Optional[DashboardIntegration] = None
_predictor: Optional[ConversionPredictor] = None
_broadcaster: Optional[PredictionBroadcaster] = None


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


def get_predictor() -> ConversionPredictor:
    """Obtener instancia del predictor"""
    global _predictor
    if _predictor is None:
        orch = get_orchestrator()
        _predictor = ConversionPredictor(orch)
    return _predictor


def get_broadcaster(connection_manager=None) -> PredictionBroadcaster:
    """Obtener instancia del broadcaster"""
    global _broadcaster
    if _broadcaster is None:
        from backend.websocket_manager import get_connection_manager
        if connection_manager is None:
            connection_manager = get_connection_manager()
        orch = get_orchestrator()
        pred = get_predictor()
        _broadcaster = PredictionBroadcaster(connection_manager, orch, pred)
    return _broadcaster


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


# ============================================================================
# PREDICTION BROADCASTER ENDPOINTS (FASE 14)
# ============================================================================

@router.post("/predictions/broadcast-all")
async def broadcast_all_predictions(token: str) -> Dict[str, Any]:
    """
    Broadcast predictions to all clients via WebSocket

    Calcula predicciones para todos los clientes y las transmite en tiempo real
    al dashboard vía WebSocket para visualización inmediata.

    Retorna:
    - Número de predicciones broadcast
    - Estadísticas generales
    - Timestamp de ejecución
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)

        orch = get_orchestrator()
        broadcaster = get_broadcaster()
        predictor = get_predictor()

        clients = orch.get_all_clients()
        broadcast_count = 0

        logger.info(f"🚀 Broadcasting predictions for {len(clients)} clients...")

        for client in clients:
            try:
                # Get client data
                audits = orch.get_audits_by_client(client.id)
                audit_score = sum([a.score for a in audits]) / len(audits) if audits else 50

                client_data = {
                    'id': client.id,
                    'name': client.name,
                    'stage': client.stage,
                    'score': client.score,
                    'audit_score': audit_score,
                    'audit_count': len(audits)
                }

                # Calculate prediction
                prediction = predictor.predict_conversion(client.id, client_data)

                # Broadcast via WebSocket
                await broadcaster.broadcast_prediction(client.id, prediction)

                # Check and broadcast anomalies
                await broadcaster.check_and_broadcast_anomalies(
                    client.id, prediction, client
                )

                broadcast_count += 1

            except Exception as e:
                logger.warning(f"⚠️ Error broadcasting for client {client.id}: {e}")
                continue

        logger.info(f"✅ Broadcasted {broadcast_count} predictions")

        return {
            "status": "success",
            "message": f"Broadcast complete",
            "predictions_sent": broadcast_count,
            "total_clients": len(clients),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error broadcasting predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error broadcasting predictions: {str(e)}"
        )


@router.post("/predictions/broadcast/{client_id}")
async def broadcast_client_prediction(client_id: int, token: str) -> Dict[str, Any]:
    """
    Broadcast prediction for a specific client via WebSocket

    Calcula y transmite en tiempo real la predicción de un cliente específico.

    Retorna:
    - Predicción con probabilidad, confianza, factores
    - Anomalías detectadas (si las hay)
    - Recomendación de próximo paso
    """
    from backend.auth import verify_admin_token
    from datetime import datetime

    try:
        verify_admin_token(token)

        orch = get_orchestrator()
        broadcaster = get_broadcaster()
        predictor = get_predictor()

        # Get client
        client = orch.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client {client_id} not found"
            )

        # Get audits
        audits = orch.get_audits_by_client(client_id)
        audit_score = sum([a.score for a in audits]) / len(audits) if audits else 50

        client_data = {
            'id': client.id,
            'name': client.name,
            'stage': client.stage,
            'score': client.score,
            'audit_score': audit_score,
            'audit_count': len(audits)
        }

        # Calculate prediction
        prediction = predictor.predict_conversion(client_id, client_data)

        # Broadcast via WebSocket
        await broadcaster.broadcast_prediction(client_id, prediction)

        # Check and broadcast anomalies
        anomalies_detected = False
        if len(prediction.risk_factors) >= 3 or \
           (prediction.probability > 70 and prediction.confidence < 40) or \
           (prediction.probability < 30 and client.stage in ['propuesta', 'negociacion']):
            await broadcaster.check_and_broadcast_anomalies(
                client_id, prediction, client
            )
            anomalies_detected = True

        logger.info(f"📊 Broadcasted prediction for client {client_id}")

        return {
            "status": "success",
            "message": "Prediction broadcast successfully",
            "client_id": client_id,
            "client_name": client.name,
            "prediction": {
                "probability": prediction.probability,
                "confidence": prediction.confidence,
                "risk_factors": prediction.risk_factors,
                "positive_factors": prediction.positive_factors,
                "recommendation": prediction.recommendation,
                "predicted_timeline_days": prediction.predicted_timeline_days
            },
            "anomalies_detected": anomalies_detected,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error broadcasting prediction for client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error broadcasting prediction: {str(e)}"
        )


@router.get("/predictions/summary")
async def get_predictions_summary(token: str) -> Dict[str, Any]:
    """
    Get summary statistics of predictions across all clients

    Retorna estadísticas agregadas sobre todas las predicciones:
    - Probabilidad promedio
    - Confianza promedio
    - Distribución por rango
    - Distribución por etapa del pipeline
    """
    from backend.auth import verify_admin_token

    try:
        verify_admin_token(token)

        orch = get_orchestrator()
        predictor = get_predictor()

        clients = orch.get_all_clients()

        probabilities = []
        confidences = []
        by_stage = {'prospecto': [], 'propuesta': [], 'negociacion': [], 'cerrado': []}

        for client in clients:
            audits = orch.get_audits_by_client(client.id)
            audit_score = sum([a.score for a in audits]) / len(audits) if audits else 50

            client_data = {
                'id': client.id,
                'name': client.name,
                'stage': client.stage,
                'score': client.score,
                'audit_score': audit_score
            }

            pred = predictor.predict_conversion(client.id, client_data)
            probabilities.append(pred.probability)
            confidences.append(pred.confidence)

            if client.stage in by_stage:
                by_stage[client.stage].append(pred.probability)

        avg_prob = sum(probabilities) / len(probabilities) if probabilities else 0
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        return {
            "status": "success",
            "total_clients": len(clients),
            "average_probability": round(avg_prob, 2),
            "average_confidence": round(avg_conf, 2),
            "distribution": {
                "high_probability": sum(1 for p in probabilities if p >= 70),
                "medium_probability": sum(1 for p in probabilities if 30 <= p < 70),
                "low_probability": sum(1 for p in probabilities if p < 30)
            },
            "by_stage": {
                stage: round(sum(probs) / len(probs), 2) if probs else 0
                for stage, probs in by_stage.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error getting predictions summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting predictions summary: {str(e)}"
        )
