#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 14: Prediction Broadcaster
Real-time broadcast of ML predictions via WebSocket to dashboards
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PredictionBroadcaster:
    """Broadcast predictions to WebSocket clients in real-time"""

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)

    async def broadcast_prediction(self, client_id: int, prediction):
        """
        Broadcast prediction to dashboard via WebSocket
        Sends to admin dashboard for monitoring
        """
        message = {
            "event_type": "prediction:generated",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": prediction.client_id,
                "client_name": prediction.client_name,
                "probability": prediction.probability,
                "confidence": prediction.confidence,
                "risk_factors": prediction.risk_factors,
                "positive_factors": prediction.positive_factors,
                "recommendation": prediction.recommendation,
                "predicted_timeline_days": prediction.predicted_timeline_days
            }
        }

        # Broadcast to admin connections only
        await self.connection_manager.broadcast_to_admin(message)

        self.logger.info(
            f"📊 Prediction: Client {client_id} "
            f"prob={prediction.probability}% conf={prediction.confidence}%"
        )

    async def broadcast_anomaly_detection(self, client_id: int,
                                         anomaly_type: str,
                                         severity: str,
                                         description: str):
        """Broadcast anomaly detection alert"""
        message = {
            "event_type": "anomaly:detected",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "anomaly_type": anomaly_type,
                "severity": severity,
                "description": description
            }
        }
        await self.connection_manager.broadcast_to_admin(message)
        self.logger.warning(
            f"⚠️ Anomaly: {anomaly_type} ({severity}) - {description}"
        )

    async def broadcast_recommendation(self, client_id: int,
                                      recommendation: str,
                                      action_type: str,
                                      urgency: str = "normal"):
        """Broadcast recommendation for next action"""
        message = {
            "event_type": "recommendation:generated",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "recommendation": recommendation,
                "action_type": action_type,
                "urgency": urgency
            }
        }
        await self.connection_manager.broadcast_to_admin(message)
        self.logger.info(
            f"💡 Recommendation: {recommendation} "
            f"(type={action_type}, urgency={urgency})"
        )
