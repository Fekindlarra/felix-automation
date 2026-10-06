"""
FASE 14 PASO 2: Lead Capture → Prediction → Real-Time WebSocket Broadcast
Integración de captura de leads con predicciones ML en tiempo real
"""

import logging
from typing import Optional
from datetime import datetime
import asyncio

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr

from backend.websocket_manager import get_connection_manager, get_event_broadcaster
from analytics.predictor import ConversionPredictor
from analytics.prediction_broadcaster import PredictionBroadcaster
from analytics.anomaly_detector import AnomalyDetector
from analytics.recommender import RecommendationEngine

logger = logging.getLogger(__name__)

# Global instances
_predictor: Optional[ConversionPredictor] = None
_broadcaster: Optional[PredictionBroadcaster] = None
_anomaly_detector: Optional[AnomalyDetector] = None
_recommender: Optional[RecommendationEngine] = None


def initialize_prediction_system(orchestrator=None):
    """Initialize prediction system with orchestrator"""
    global _predictor, _broadcaster, _anomaly_detector, _recommender

    try:
        _predictor = ConversionPredictor()
        _broadcaster = PredictionBroadcaster(get_connection_manager(), orchestrator, _predictor)
        _anomaly_detector = AnomalyDetector()
        _recommender = RecommendationEngine()

        logger.info("✅ Prediction system initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing prediction system: {e}")
        return False


async def process_lead_prediction(lead_data: dict, client_id: Optional[int] = None) -> dict:
    """
    Process lead and generate real-time ML prediction

    Args:
        lead_data: Dict with lead information
        client_id: Optional client ID for existing customer

    Returns:
        Dict with prediction results
    """
    if not _predictor or not _broadcaster:
        logger.warning("⚠️ Prediction system not initialized")
        return {"success": False, "error": "Prediction system not ready"}

    try:
        # Extract lead info
        company = lead_data.get('company', 'Unknown')
        audit_type = lead_data.get('audit_type', 'complete')
        email = lead_data.get('email', 'unknown@example.com')

        # Create client dict for prediction
        client = {
            'id': client_id or 0,
            'name': lead_data.get('name', 'Unknown'),
            'email': email,
            'company': company,
            'industry': lead_data.get('industry', 'Unknown'),
            'stage': 'prospecto',  # New leads are prospects
            'audit_type': audit_type,
            'message': lead_data.get('message', ''),
            'phone': lead_data.get('phone', ''),
            'created_at': datetime.utcnow().isoformat()
        }

        # Generate prediction
        logger.info(f"🎯 Generating prediction for lead: {company}")
        prediction = _predictor.predict(client)

        if not prediction:
            logger.warning(f"⚠️ No prediction generated for {company}")
            return {"success": False, "error": "Could not generate prediction"}

        # Check for anomalies
        anomalies_detected = await _broadcaster.check_and_broadcast_anomalies(
            client_id=client.get('id', 0),
            prediction=prediction,
            client=client
        )

        # Get recommendations
        recommendations = _recommender.get_recommendations(
            conversion_probability=prediction.probability,
            stage='prospecto',
            audit_type=audit_type
        )

        # Prepare broadcast data
        prediction_data = {
            'client_id': client.get('id', 0),
            'client_name': client['name'],
            'company': company,
            'email': email,
            'audit_type': audit_type,
            'probability': prediction.probability,
            'confidence': prediction.confidence,
            'risk_factors': prediction.risk_factors,
            'positive_factors': prediction.positive_factors,
            'recommendation': recommendations.get('next_action', 'Contacto inmediato'),
            'predicted_timeline_days': recommendations.get('predicted_days_to_close', 14)
        }

        # Broadcast prediction to WebSocket
        await _broadcaster.broadcast_prediction(client.get('id', 0), prediction)

        logger.info(
            f"✅ Prediction broadcast: "
            f"{company} → {prediction.probability:.0f}% probability, "
            f"{prediction.confidence:.0f}% confidence"
        )

        return {
            'success': True,
            'prediction': prediction_data,
            'message': f'Lead capturado y analizado: {prediction.probability:.0f}% de probabilidad de conversión'
        }

    except Exception as e:
        logger.error(f"❌ Error processing lead prediction: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def broadcast_lead_event(lead_data: dict):
    """
    Broadcast lead capture event to all connected clients
    Used to notify dashboard of new lead
    """
    if not _broadcaster:
        return

    try:
        manager = get_connection_manager()

        # Create notification event
        notification = {
            'event_type': 'lead:captured',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'company': lead_data.get('company'),
                'email': lead_data.get('email'),
                'phone': lead_data.get('phone'),
                'audit_type': lead_data.get('audit_type'),
                'message': lead_data.get('message', '')
            }
        }

        # Broadcast to all admins
        await manager.broadcast_to_admin(notification)

        logger.info(f"📢 Lead event broadcast: {lead_data.get('company')}")

    except Exception as e:
        logger.error(f"Error broadcasting lead event: {e}")


def get_prediction_system() -> tuple:
    """Get prediction system instances"""
    return _predictor, _broadcaster, _anomaly_detector, _recommender


# Model for prediction response
class PredictionResponse(BaseModel):
    """Response for prediction endpoint"""
    success: bool
    probability: float
    confidence: float
    risk_factors: list
    positive_factors: list
    recommendation: str
    predicted_timeline_days: int
    message: str
