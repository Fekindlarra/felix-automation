#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14: Prediction Broadcaster
Real-time ML prediction broadcasting via WebSocket to dashboard

Integrates conversion predictor with WebSocket event system for live dashboard updates
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class PredictionBroadcaster:
    """Broadcast ML predictions to WebSocket clients in real-time"""

    def __init__(self, connection_manager, orchestrator=None, predictor=None):
        """
        Initialize broadcaster

        Args:
            connection_manager: WebSocketConnectionManager instance
            orchestrator: FelixAutomationOrchestrator instance (optional)
            predictor: ConversionPredictor instance (optional)
        """
        self.connection_manager = connection_manager
        self.orchestrator = orchestrator
        self.predictor = predictor
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ Prediction Broadcaster initialized")

    async def broadcast_prediction(self, client_id: int, prediction):
        """
        Broadcast prediction to dashboard via WebSocket
        Sends to admin and client connections
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

        # Broadcast to admin and relevant client connections
        await self.connection_manager.broadcast_to_admin(message)
        await self.connection_manager.broadcast_to_client(client_id, message)

        self.logger.info(
            f"📊 Prediction: Client {client_id} "
            f"prob={prediction.probability:.1f}% conf={prediction.confidence:.1f}%"
        )

    async def broadcast_anomaly_detection(self, client_id: int,
                                         anomaly_type: str,
                                         severity: str,
                                         description: str,
                                         affected_metric: str = ""):
        """Broadcast anomaly detection alert"""
        message = {
            "event_type": "anomaly:detected",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "anomaly_type": anomaly_type,
                "severity": severity,
                "description": description,
                "affected_metric": affected_metric
            }
        }
        await self.connection_manager.broadcast_to_admin(message)
        self.logger.warning(
            f"⚠️ Anomaly ({severity}): {anomaly_type} - {description}"
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

    async def broadcast_predictions_batch(self, predictions: list):
        """Broadcast multiple predictions at once"""
        for prediction in predictions:
            await self.broadcast_prediction(prediction.client_id, prediction)

    async def check_and_broadcast_anomalies(self, client_id: int,
                                           prediction, client=None):
        """
        Check for anomalies in prediction and broadcast alerts if found

        Args:
            client_id: Client ID
            prediction: ConversionPrediction object
            client: Client object for stage info
        """
        try:
            anomalies = []

            # Anomaly 1: High probability but low confidence
            if prediction.probability > 70 and prediction.confidence < 40:
                anomalies.append({
                    'type': 'prediction_uncertainty',
                    'severity': 'medium',
                    'description': f'High probability ({prediction.probability:.0f}%) but low confidence ({prediction.confidence:.0f}%)',
                    'metric': 'confidence_score'
                })

            # Anomaly 2: Many risk factors
            if len(prediction.risk_factors) >= 4:
                anomalies.append({
                    'type': 'high_risk_profile',
                    'severity': 'high',
                    'description': f'{len(prediction.risk_factors)} risk factors identified',
                    'metric': 'risk_factor_count'
                })

            # Anomaly 3: Low probability but advanced stage
            if client and prediction.probability < 30 and client.stage in ['propuesta', 'negociacion']:
                anomalies.append({
                    'type': 'stage_probability_mismatch',
                    'severity': 'high',
                    'description': f'Low probability ({prediction.probability:.0f}%) but client in {client.stage} stage',
                    'metric': 'stage_progression'
                })

            # Broadcast anomalies
            for anomaly in anomalies:
                await self.broadcast_anomaly_detection(
                    client_id=client_id,
                    anomaly_type=anomaly['type'],
                    severity=anomaly['severity'],
                    description=anomaly['description'],
                    affected_metric=anomaly['metric']
                )

            if anomalies:
                self.logger.warning(f"⚠️ {len(anomalies)} anomaly(ies) detected for client {client_id}")

        except Exception as e:
            self.logger.error(f"Error checking anomalies: {e}")
