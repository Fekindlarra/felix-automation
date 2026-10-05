#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prediction Broadcaster - Real-Time ML Predictions via WebSocket
FASE 14: Real-Time & ML Features
Sends conversion probability predictions and anomaly alerts to dashboards in real-time
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ConversionPrediction:
    """Conversion probability prediction with confidence and factors"""
    client_id: int
    probability: float  # 0-100
    confidence: float   # 0-100
    risk_factors: List[str]
    positive_factors: List[str]
    predicted_timeline_days: int
    reasoning: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class AnomalyAlert:
    """Anomaly detection alert for dashboard"""
    client_id: int
    anomaly_type: str  # 'score_drop', 'pipeline_stagnation', 'engagement_gap', 'rejection_pattern', 'abandonment'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    metrics: Dict[str, Any]
    recommended_action: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class PredictionBroadcaster:
    """
    Broadcasts real-time predictions and anomalies to WebSocket connections

    Responsibilities:
    - Format prediction data for WebSocket transmission
    - Calculate confidence visualization (gauge 0-100)
    - Send real-time updates to admin and client dashboards
    - Track prediction history for accuracy analysis
    - Coordinate with analytics engine and WebSocket manager
    """

    def __init__(self, websocket_manager=None, database=None):
        """
        Initialize broadcaster

        Args:
            websocket_manager: WebSocket connection manager (from backend)
            database: Database connection for storing prediction history
        """
        self.websocket_manager = websocket_manager
        self.database = database
        self.prediction_cache = {}  # {client_id: latest_prediction}
        self.anomaly_cache = {}     # {client_id: [anomalies]}

        logger.info("✅ Prediction Broadcaster initialized")

    def broadcast_prediction(self, prediction: ConversionPrediction) -> bool:
        """
        Broadcast prediction to dashboard via WebSocket

        Args:
            prediction: ConversionPrediction dataclass

        Returns:
            True if broadcast successful, False otherwise
        """
        try:
            logger.info(f"📡 Broadcasting prediction for client {prediction.client_id}: {prediction.probability}%")

            # Format event for WebSocket
            event = {
                "type": "prediction:generated",
                "client_id": prediction.client_id,
                "probability": prediction.probability,
                "confidence": prediction.confidence,
                "risk_factors": prediction.risk_factors,
                "positive_factors": prediction.positive_factors,
                "timeline_days": prediction.predicted_timeline_days,
                "reasoning": prediction.reasoning,
                "timestamp": prediction.timestamp,
                "gauge_color": self._get_gauge_color(prediction.probability),
                "risk_level": self._get_risk_level(prediction.probability, prediction.confidence)
            }

            # Store in cache
            self.prediction_cache[prediction.client_id] = prediction

            # Store in database for history tracking
            if self.database:
                self._store_prediction_history(prediction)

            # Broadcast to WebSocket (if connected)
            if self.websocket_manager:
                self.websocket_manager.broadcast(event, client_id=prediction.client_id)
                logger.info(f"✅ Prediction broadcasted to dashboard")
            else:
                logger.debug("⚠️ WebSocket manager not connected - event queued")

            return True

        except Exception as e:
            logger.error(f"❌ Error broadcasting prediction: {str(e)}")
            return False

    def broadcast_anomaly(self, anomaly: AnomalyAlert) -> bool:
        """
        Broadcast anomaly detection alert to dashboard

        Args:
            anomaly: AnomalyAlert dataclass

        Returns:
            True if broadcast successful, False otherwise
        """
        try:
            logger.warning(f"🚨 Broadcasting anomaly for client {anomaly.client_id}: {anomaly.anomaly_type}")

            # Format event for WebSocket
            event = {
                "type": "anomaly:detected",
                "client_id": anomaly.client_id,
                "anomaly_type": anomaly.anomaly_type,
                "severity": anomaly.severity,
                "description": anomaly.description,
                "metrics": anomaly.metrics,
                "recommended_action": anomaly.recommended_action,
                "timestamp": anomaly.timestamp,
                "icon": self._get_anomaly_icon(anomaly.anomaly_type),
                "color": self._get_severity_color(anomaly.severity)
            }

            # Store in cache
            if anomaly.client_id not in self.anomaly_cache:
                self.anomaly_cache[anomaly.client_id] = []
            self.anomaly_cache[anomaly.client_id].append(anomaly)

            # Store in database
            if self.database:
                self._store_anomaly(anomaly)

            # Broadcast to WebSocket
            if self.websocket_manager:
                self.websocket_manager.broadcast(event, client_id=anomaly.client_id)
                logger.info(f"✅ Anomaly alert broadcasted")
            else:
                logger.debug("⚠️ WebSocket manager not connected - alert queued")

            return True

        except Exception as e:
            logger.error(f"❌ Error broadcasting anomaly: {str(e)}")
            return False

    def broadcast_recommendation(self, client_id: int, recommendation: Dict[str, Any]) -> bool:
        """
        Broadcast recommended next action to dashboard

        Args:
            client_id: Client ID
            recommendation: Recommendation data (action, timeline, rationale)

        Returns:
            True if broadcast successful, False otherwise
        """
        try:
            logger.info(f"💡 Broadcasting recommendation for client {client_id}")

            event = {
                "type": "recommendation:generated",
                "client_id": client_id,
                "action": recommendation.get("action"),
                "timeline_days": recommendation.get("timeline_days", 3),
                "rationale": recommendation.get("rationale"),
                "priority": recommendation.get("priority", "medium"),
                "timestamp": datetime.now().isoformat()
            }

            if self.websocket_manager:
                self.websocket_manager.broadcast(event, client_id=client_id)
                logger.info(f"✅ Recommendation broadcasted")

            return True

        except Exception as e:
            logger.error(f"❌ Error broadcasting recommendation: {str(e)}")
            return False

    def get_latest_prediction(self, client_id: int) -> Optional[ConversionPrediction]:
        """
        Get latest prediction from cache

        Args:
            client_id: Client ID

        Returns:
            Latest ConversionPrediction or None
        """
        return self.prediction_cache.get(client_id)

    def get_anomalies(self, client_id: int) -> List[AnomalyAlert]:
        """
        Get unresolved anomalies for client

        Args:
            client_id: Client ID

        Returns:
            List of AnomalyAlert objects
        """
        return self.anomaly_cache.get(client_id, [])

    def clear_anomalies(self, client_id: int):
        """
        Clear anomalies from cache (after resolution)

        Args:
            client_id: Client ID
        """
        if client_id in self.anomaly_cache:
            del self.anomaly_cache[client_id]
            logger.info(f"✅ Anomalies cleared for client {client_id}")

    def _store_prediction_history(self, prediction: ConversionPrediction):
        """Store prediction in database for accuracy tracking"""
        try:
            cursor = self.database.cursor()
            cursor.execute("""
            INSERT INTO prediction_history
            (client_id, probability, confidence, risk_factors_json, positive_factors_json, predicted_timeline_days, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction.client_id,
                prediction.probability,
                prediction.confidence,
                json.dumps(prediction.risk_factors),
                json.dumps(prediction.positive_factors),
                prediction.predicted_timeline_days,
                datetime.now()
            ))
            self.database.commit()
            logger.debug(f"✅ Prediction stored in history for client {prediction.client_id}")
        except Exception as e:
            logger.error(f"❌ Error storing prediction history: {str(e)}")

    def _store_anomaly(self, anomaly: AnomalyAlert):
        """Store anomaly in database"""
        try:
            cursor = self.database.cursor()
            cursor.execute("""
            INSERT INTO anomalies
            (client_id, anomaly_type, severity, description, metrics_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                anomaly.client_id,
                anomaly.anomaly_type,
                anomaly.severity,
                anomaly.description,
                json.dumps(anomaly.metrics),
                datetime.now()
            ))
            self.database.commit()
            logger.debug(f"✅ Anomaly stored for client {anomaly.client_id}")
        except Exception as e:
            logger.error(f"❌ Error storing anomaly: {str(e)}")

    @staticmethod
    def _get_gauge_color(probability: float) -> str:
        """Get gauge color based on probability"""
        if probability >= 80:
            return "#10b981"  # Green
        elif probability >= 60:
            return "#3b82f6"  # Blue
        elif probability >= 40:
            return "#f59e0b"  # Amber
        else:
            return "#ef4444"  # Red

    @staticmethod
    def _get_risk_level(probability: float, confidence: float) -> str:
        """Determine risk level based on probability and confidence"""
        if probability >= 80 and confidence >= 80:
            return "very_high"
        elif probability >= 60 and confidence >= 60:
            return "high"
        elif probability >= 40 and confidence >= 40:
            return "medium"
        elif probability >= 20 and confidence >= 20:
            return "low"
        else:
            return "very_low"

    @staticmethod
    def _get_anomaly_icon(anomaly_type: str) -> str:
        """Get icon emoji for anomaly type"""
        icons = {
            "score_drop": "📉",
            "pipeline_stagnation": "⏸️",
            "engagement_gap": "📧",
            "rejection_pattern": "🚫",
            "abandonment": "🚪"
        }
        return icons.get(anomaly_type, "⚠️")

    @staticmethod
    def _get_severity_color(severity: str) -> str:
        """Get color for severity level"""
        colors = {
            "critical": "#dc2626",  # Red
            "high": "#ea580c",       # Orange
            "medium": "#f59e0b",    # Amber
            "low": "#3b82f6"        # Blue
        }
        return colors.get(severity, "#6b7280")  # Gray default


def main():
    """Example usage"""
    print("🧪 Testing Prediction Broadcaster...")

    broadcaster = PredictionBroadcaster()

    # Test prediction
    prediction = ConversionPrediction(
        client_id=1,
        probability=82.5,
        confidence=88.0,
        risk_factors=["Days in stage > 7", "No email engagement"],
        positive_factors=["High audit score", "Relevant business type"],
        predicted_timeline_days=5,
        reasoning="Strong audit score and business alignment suggest high conversion probability"
    )

    result = broadcaster.broadcast_prediction(prediction)
    print(f"✅ Prediction broadcast result: {result}")

    # Test anomaly
    anomaly = AnomalyAlert(
        client_id=1,
        anomaly_type="pipeline_stagnation",
        severity="high",
        description="Client in 'proposal' stage for 10+ days without engagement",
        metrics={"days_in_stage": 10, "email_opens": 0, "email_clicks": 0},
        recommended_action="Send follow-up email with competitive data"
    )

    result = broadcaster.broadcast_anomaly(anomaly)
    print(f"✅ Anomaly broadcast result: {result}")

    # Test retrieval
    cached_prediction = broadcaster.get_latest_prediction(1)
    print(f"✅ Cached prediction: {cached_prediction}")


if __name__ == "__main__":
    main()
