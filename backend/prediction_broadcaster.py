"""
Prediction Broadcaster - FASE 14 Real-Time ML Integration
Sends real-time sales probability predictions to WebSocket dashboard
"""

import logging
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions"""
    CONVERSION_PROBABILITY = "conversion_probability"
    CHURN_RISK = "churn_risk"
    REVENUE_FORECAST = "revenue_forecast"
    ENGAGEMENT_SCORE = "engagement_score"


@dataclass
class ConversionPrediction:
    """Conversion probability prediction"""
    client_id: int
    probability: float  # 0-100
    confidence: float  # 0-100
    positive_factors: List[str]
    risk_factors: List[str]
    predicted_timeline_days: int
    anomalies_detected: List[Dict]
    recommendation: str
    prediction_id: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'client_id': self.client_id,
            'probability': round(self.probability, 2),
            'confidence': round(self.confidence, 2),
            'positive_factors': self.positive_factors,
            'risk_factors': self.risk_factors,
            'predicted_timeline_days': self.predicted_timeline_days,
            'anomalies_detected': self.anomalies_detected,
            'recommendation': self.recommendation,
            'prediction_id': self.prediction_id,
            'timestamp': self.timestamp
        }


class WebSocketEventBuilder:
    """Builds WebSocket events for dashboard updates"""

    @staticmethod
    def build_prediction_event(prediction: ConversionPrediction) -> Dict[str, Any]:
        """Build WebSocket event for prediction update"""
        return {
            'type': 'prediction:generated',
            'timestamp': datetime.utcnow().isoformat(),
            'data': prediction.to_dict(),
            'severity': PredictionBroadcaster._get_severity(prediction.probability),
            'action_required': prediction.probability < 30 or prediction.probability > 80
        }

    @staticmethod
    def build_anomaly_event(anomaly_data: Dict) -> Dict[str, Any]:
        """Build WebSocket event for anomaly detection"""
        return {
            'type': 'anomaly:detected',
            'timestamp': datetime.utcnow().isoformat(),
            'data': anomaly_data,
            'severity': anomaly_data.get('severity', 'medium'),
            'client_id': anomaly_data.get('client_id')
        }

    @staticmethod
    def build_test_started_event(test_id: int, test_name: str) -> Dict[str, Any]:
        """Build WebSocket event for A/B test start"""
        return {
            'type': 'test:started',
            'timestamp': datetime.utcnow().isoformat(),
            'test_id': test_id,
            'test_name': test_name
        }

    @staticmethod
    def build_test_completed_event(test_id: int, winner: str, p_value: float) -> Dict[str, Any]:
        """Build WebSocket event for A/B test completion"""
        return {
            'type': 'test:completed',
            'timestamp': datetime.utcnow().isoformat(),
            'test_id': test_id,
            'winner': winner,
            'p_value': round(p_value, 4),
            'confidence': round((1 - p_value) * 100, 2)
        }

    @staticmethod
    def build_recommendation_event(
        client_id: int,
        recommendation_type: str,
        recommendation_text: str,
        confidence: float
    ) -> Dict[str, Any]:
        """Build WebSocket event for recommendation"""
        return {
            'type': 'recommendation:generated',
            'timestamp': datetime.utcnow().isoformat(),
            'client_id': client_id,
            'recommendation_type': recommendation_type,
            'text': recommendation_text,
            'confidence': round(confidence, 2),
            'priority': 'high' if confidence > 80 else 'medium' if confidence > 60 else 'low'
        }


class PredictionBroadcaster:
    """Manages real-time prediction broadcasting to WebSocket clients"""

    def __init__(self, websocket_manager=None, metrics_collector=None, db_connection=None):
        """
        Initialize broadcaster

        Args:
            websocket_manager: WebSocket manager instance for broadcasting
            metrics_collector: MetricsCollector for anomaly detection
            db_connection: Database connection for storing predictions
        """
        self.websocket_manager = websocket_manager
        self.metrics_collector = metrics_collector
        self.db = db_connection
        self.active_predictions: Dict[int, ConversionPrediction] = {}
        self.broadcast_history: List[Dict] = []
        self.event_handlers: Dict[str, List[Callable]] = {}

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register handler for specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type}")

    def _call_event_handlers(self, event_type: str, event_data: Dict):
        """Call all registered handlers for event type"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(event_data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

    def broadcast_prediction(self, prediction: ConversionPrediction) -> bool:
        """
        Broadcast prediction to dashboard via WebSocket

        Args:
            prediction: ConversionPrediction instance

        Returns:
            True if broadcast succeeded
        """
        try:
            # Set prediction metadata
            if not prediction.prediction_id:
                prediction.prediction_id = f"pred_{prediction.client_id}_{int(datetime.utcnow().timestamp() * 1000)}"
            if not prediction.timestamp:
                prediction.timestamp = datetime.utcnow().isoformat()

            # Store prediction in cache
            self.active_predictions[prediction.client_id] = prediction

            # Build event
            event = WebSocketEventBuilder.build_prediction_event(prediction)

            # Store in history
            self.broadcast_history.append(event)
            if len(self.broadcast_history) > 1000:
                self.broadcast_history = self.broadcast_history[-1000:]

            # Broadcast to WebSocket
            if self.websocket_manager:
                try:
                    self.websocket_manager.broadcast_to_admin(event)
                    self.websocket_manager.broadcast_to_client(prediction.client_id, event)
                except Exception as e:
                    logger.error(f"WebSocket broadcast error: {e}")

            # Store in database
            if self.db:
                self._store_prediction(prediction)

            # Call event handlers
            self._call_event_handlers('prediction:generated', event)

            logger.info(f"Prediction broadcast: client {prediction.client_id}, probability {prediction.probability}%")
            return True

        except Exception as e:
            logger.error(f"Error broadcasting prediction: {e}")
            return False

    def _store_prediction(self, prediction: ConversionPrediction):
        """Store prediction in database"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO prediction_history (
                    client_id, probability, confidence,
                    risk_factors, positive_factors, predicted_timeline_days,
                    recommendation, predicted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction.client_id,
                prediction.probability,
                prediction.confidence,
                json.dumps(prediction.risk_factors),
                json.dumps(prediction.positive_factors),
                prediction.predicted_timeline_days,
                prediction.recommendation,
                prediction.timestamp
            ))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")

    def broadcast_anomaly(self, anomaly_data: Dict) -> bool:
        """Broadcast detected anomaly"""
        try:
            event = WebSocketEventBuilder.build_anomaly_event(anomaly_data)

            if self.websocket_manager:
                self.websocket_manager.broadcast_to_admin(event)

            self._call_event_handlers('anomaly:detected', event)

            logger.warning(f"Anomaly broadcast: {anomaly_data.get('anomaly_type')}")
            return True

        except Exception as e:
            logger.error(f"Error broadcasting anomaly: {e}")
            return False

    def broadcast_test_event(self, event_type: str, test_data: Dict) -> bool:
        """Broadcast A/B test event"""
        try:
            if event_type == 'started':
                event = WebSocketEventBuilder.build_test_started_event(
                    test_data.get('test_id'),
                    test_data.get('test_name')
                )
            elif event_type == 'completed':
                event = WebSocketEventBuilder.build_test_completed_event(
                    test_data.get('test_id'),
                    test_data.get('winner'),
                    test_data.get('p_value')
                )
            else:
                return False

            if self.websocket_manager:
                self.websocket_manager.broadcast_to_admin(event)

            self._call_event_handlers(f'test:{event_type}', event)

            logger.info(f"Test event broadcast: {event_type}")
            return True

        except Exception as e:
            logger.error(f"Error broadcasting test event: {e}")
            return False

    def broadcast_recommendation(
        self,
        client_id: int,
        recommendation_type: str,
        recommendation_text: str,
        confidence: float
    ) -> bool:
        """Broadcast recommendation to dashboard"""
        try:
            event = WebSocketEventBuilder.build_recommendation_event(
                client_id,
                recommendation_type,
                recommendation_text,
                confidence
            )

            if self.websocket_manager:
                self.websocket_manager.broadcast_to_admin(event)
                self.websocket_manager.broadcast_to_client(client_id, event)

            self._call_event_handlers('recommendation:generated', event)

            logger.info(f"Recommendation broadcast: {recommendation_type} for client {client_id}")
            return True

        except Exception as e:
            logger.error(f"Error broadcasting recommendation: {e}")
            return False

    def get_active_prediction(self, client_id: int) -> Optional[ConversionPrediction]:
        """Get most recent prediction for client"""
        return self.active_predictions.get(client_id)

    def get_predictions_by_probability_range(
        self,
        min_prob: float = 0,
        max_prob: float = 100
    ) -> List[ConversionPrediction]:
        """Get predictions within probability range"""
        return [
            p for p in self.active_predictions.values()
            if min_prob <= p.probability <= max_prob
        ]

    def get_high_risk_clients(self, threshold: float = 30) -> List[int]:
        """Get clients with churn risk above threshold"""
        return [
            client_id for client_id, pred in self.active_predictions.items()
            if pred.probability < threshold
        ]

    def get_high_opportunity_clients(self, threshold: float = 80) -> List[int]:
        """Get clients with high conversion probability"""
        return [
            client_id for client_id, pred in self.active_predictions.items()
            if pred.probability > threshold
        ]

    def get_broadcast_history(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """Get broadcast history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent = [
            e for e in self.broadcast_history
            if datetime.fromisoformat(e['timestamp']) > cutoff_time
        ]
        return recent[-limit:] if limit else recent

    def get_statistics(self) -> Dict[str, Any]:
        """Get broadcaster statistics"""
        if not self.active_predictions:
            return {
                'total_predictions': 0,
                'avg_probability': 0,
                'high_risk_count': 0,
                'high_opportunity_count': 0,
                'broadcast_count': len(self.broadcast_history)
            }

        predictions = list(self.active_predictions.values())
        probabilities = [p.probability for p in predictions]

        return {
            'total_predictions': len(predictions),
            'avg_probability': round(sum(probabilities) / len(probabilities), 2),
            'min_probability': round(min(probabilities), 2),
            'max_probability': round(max(probabilities), 2),
            'high_risk_count': len(self.get_high_risk_clients()),
            'high_opportunity_count': len(self.get_high_opportunity_clients()),
            'broadcast_count': len(self.broadcast_history),
            'avg_confidence': round(
                sum(p.confidence for p in predictions) / len(predictions),
                2
            )
        }

    @staticmethod
    def _get_severity(probability: float) -> str:
        """Determine severity from probability"""
        if probability < 20:
            return "critical"  # High churn risk
        elif probability < 50:
            return "warning"  # Below average conversion
        elif probability > 80:
            return "info"  # High opportunity
        else:
            return "normal"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    broadcaster = PredictionBroadcaster()

    # Create sample prediction
    prediction = ConversionPrediction(
        client_id=123,
        probability=75.5,
        confidence=88.2,
        positive_factors=['Recent engagement', 'High email open rate', 'Multiple page visits'],
        risk_factors=['Long time since last contact', 'Budget concerns mentioned'],
        predicted_timeline_days=7,
        anomalies_detected=[],
        recommendation='Follow up with case study on ROI'
    )

    # Broadcast prediction
    if broadcaster.broadcast_prediction(prediction):
        print("✓ Prediction broadcast sent")
    else:
        print("✗ Broadcast failed")

    # Get statistics
    stats = broadcaster.get_statistics()
    print(f"\nBroadcaster Stats:")
    print(f"  Total Predictions: {stats['total_predictions']}")
    print(f"  Avg Probability: {stats['avg_probability']}%")
    print(f"  Avg Confidence: {stats['avg_confidence']}%")
