#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Phase 3: Prediction Broadcaster
Real-time ML prediction broadcasting via WebSocket to dashboard

Integrates conversion predictor with WebSocket event system for live dashboard updates.
Features:
- Real-time probability gauge updates (0-100%)
- Confidence score visualization
- Risk factor and positive factor highlighting
- Anomaly detection and alerting
- Recommendation generation
- Event logging and history tracking
- Statistics and reporting
"""

import sys
import logging
import json
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class GaugeUpdate:
    """Conversion probability gauge update data"""
    client_id: int
    probability_percentage: int  # 0-100
    confidence_percentage: int   # 0-100
    gauge_color: str            # Hex color based on probability
    risk_factors: List[str]
    positive_factors: List[str]
    timeline_days: int

    def get_color(self) -> str:
        """Get gauge color based on probability"""
        pct = self.probability_percentage
        if pct >= 80:
            return '#22c55e'  # Green
        elif pct >= 60:
            return '#eab308'  # Amber
        elif pct >= 40:
            return '#f97316'  # Orange
        elif pct >= 20:
            return '#ef4444'  # Red
        else:
            return '#6b7280'  # Gray


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

        # Event tracking and statistics
        self.event_log: List[Dict[str, Any]] = []
        self.max_log_size = 1000
        self.statistics = {
            'total_broadcasts': 0,
            'total_anomalies': 0,
            'total_recommendations': 0,
            'by_type': {}
        }

        self.logger.info("✅ Prediction Broadcaster initialized (FASE 14 Phase 3)")

    def _get_gauge_color(self, probability: float) -> str:
        """
        Get gauge color based on conversion probability

        Args:
            probability: Probability value (0.0-1.0 or 0-100)

        Returns:
            Hex color string
        """
        # Normalize to 0-100 if 0-1
        pct = probability if probability > 1 else probability * 100

        if pct >= 80:
            return '#22c55e'  # Green - high probability
        elif pct >= 60:
            return '#eab308'  # Amber - medium-high
        elif pct >= 40:
            return '#f97316'  # Orange - medium
        elif pct >= 20:
            return '#ef4444'  # Red - low
        else:
            return '#6b7280'  # Gray - very low

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log event for tracking"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }

        self.event_log.append(event)

        # Trim log if too large
        if len(self.event_log) > self.max_log_size:
            self.event_log = self.event_log[-self.max_log_size:]

        # Update statistics
        self.statistics['by_type'][event_type] = self.statistics['by_type'].get(event_type, 0) + 1

    async def broadcast_prediction(self, client_id: int, prediction):
        """
        Broadcast prediction to dashboard via WebSocket
        Sends to admin and client connections with gauge formatting

        Args:
            client_id: Client ID
            prediction: ConversionPrediction object with probability, confidence, risk_factors, etc.
        """
        # Normalize probability to 0-100 range
        prob_pct = prediction.probability if prediction.probability > 1 else prediction.probability * 100
        conf_pct = prediction.confidence if prediction.confidence > 1 else prediction.confidence * 100

        message = {
            "event_type": "prediction:generated",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "client_name": getattr(prediction, 'client_name', f'Client {client_id}'),
                "probability": prob_pct,
                "probability_normalized": prediction.probability if prediction.probability <= 1 else prediction.probability / 100,
                "confidence": conf_pct,
                "confidence_normalized": prediction.confidence if prediction.confidence <= 1 else prediction.confidence / 100,
                "risk_factors": getattr(prediction, 'risk_factors', []),
                "positive_factors": getattr(prediction, 'positive_factors', []),
                "recommendation": getattr(prediction, 'recommendation', ''),
                "predicted_timeline_days": getattr(prediction, 'predicted_timeline_days', 7),
                # Gauge widget data
                "gauge_value": int(prob_pct),
                "gauge_color": self._get_gauge_color(prob_pct),
                "gauge_label": f"{int(prob_pct)}% Conversion Probability"
            }
        }

        # Log event
        self._log_event("prediction:generated", message['data'])
        self.statistics['total_broadcasts'] += 1

        try:
            # Broadcast to admin and relevant client connections
            if self.connection_manager:
                await self.connection_manager.broadcast_to_admin(message)
                await self.connection_manager.broadcast_to_client(client_id, message)

            self.logger.info(
                f"📊 Prediction: Client {client_id} "
                f"prob={prob_pct:.1f}% conf={conf_pct:.1f}% | "
                f"Risk: {len(getattr(prediction, 'risk_factors', []))} | "
                f"Positive: {len(getattr(prediction, 'positive_factors', []))}"
            )
        except Exception as e:
            self.logger.error(f"Failed to broadcast prediction: {e}")

    async def broadcast_anomaly_detection(self, client_id: int,
                                         anomaly_type: str,
                                         severity: str,
                                         description: str,
                                         affected_metric: str = ""):
        """
        Broadcast anomaly detection alert

        Args:
            client_id: Client ID
            anomaly_type: Type of anomaly (e.g., 'churn_risk', 'engagement_drop')
            severity: Severity level ('low', 'medium', 'high', 'critical')
            description: Detailed description of anomaly
            affected_metric: Metric that triggered the anomaly
        """
        # Severity to number mapping for sorting
        severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        severity_num = severity_map.get(severity, 0)

        message = {
            "event_type": "anomaly:detected",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "anomaly_type": anomaly_type,
                "severity": severity,
                "severity_number": severity_num,
                "description": description,
                "affected_metric": affected_metric,
                "alert_icon": "⚠️",
                "badge_color": {
                    'low': '#3b82f6',
                    'medium': '#f97316',
                    'high': '#ef4444',
                    'critical': '#7c2d12'
                }.get(severity, '#6b7280')
            }
        }

        # Log event
        self._log_event("anomaly:detected", message['data'])
        self.statistics['total_anomalies'] += 1

        try:
            if self.connection_manager:
                await self.connection_manager.broadcast_to_admin(message)

            self.logger.warning(
                f"⚠️ Anomaly ({severity}): {anomaly_type} for client {client_id} - {description}"
            )
        except Exception as e:
            self.logger.error(f"Failed to broadcast anomaly: {e}")

    async def broadcast_recommendation(self, client_id: int,
                                      recommendation: str,
                                      action_type: str,
                                      urgency: str = "normal"):
        """
        Broadcast recommendation for next action

        Args:
            client_id: Client ID
            recommendation: Recommendation text
            action_type: Type of action (e.g., 'email', 'call', 'follow-up')
            urgency: Urgency level ('low', 'normal', 'high', 'urgent')
        """
        urgency_map = {'low': 1, 'normal': 2, 'high': 3, 'urgent': 4}
        urgency_num = urgency_map.get(urgency, 2)

        message = {
            "event_type": "recommendation:generated",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "recommendation": recommendation,
                "action_type": action_type,
                "urgency": urgency,
                "urgency_number": urgency_num,
                "action_icon": {
                    'email': '📧',
                    'call': '📞',
                    'follow-up': '📋',
                    'meeting': '📅',
                    'proposal': '📄'
                }.get(action_type, '💡'),
                "badge_color": {
                    'low': '#3b82f6',
                    'normal': '#10b981',
                    'high': '#f97316',
                    'urgent': '#ef4444'
                }.get(urgency, '#6b7280')
            }
        }

        # Log event
        self._log_event("recommendation:generated", message['data'])
        self.statistics['total_recommendations'] += 1

        try:
            if self.connection_manager:
                await self.connection_manager.broadcast_to_admin(message)

            self.logger.info(
                f"💡 Recommendation (urgency={urgency}): {recommendation} "
                f"(type={action_type}) for client {client_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to broadcast recommendation: {e}")

    async def broadcast_predictions_batch(self, predictions: list):
        """
        Broadcast multiple predictions at once

        Args:
            predictions: List of ConversionPrediction objects
        """
        for prediction in predictions:
            await self.broadcast_prediction(prediction.client_id, prediction)

        self.logger.info(f"📊 Broadcasted batch of {len(predictions)} predictions")

    def get_event_history(self, client_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """
        Get event history

        Args:
            client_id: Filter by client ID (optional)
            limit: Maximum events to return

        Returns:
            List of event dictionaries
        """
        events = self.event_log[-limit:]

        if client_id:
            events = [e for e in events if e['data'].get('client_id') == client_id]

        return events

    def get_latest_prediction(self, client_id: int) -> Optional[Dict]:
        """
        Get latest prediction for a client

        Args:
            client_id: Client ID

        Returns:
            Latest prediction event or None
        """
        for event in reversed(self.event_log):
            if (event['type'] == 'prediction:generated' and
                event['data'].get('client_id') == client_id):
                return event
        return None

    def get_active_anomalies(self, client_id: Optional[int] = None, hours: int = 1) -> List[Dict]:
        """
        Get active anomalies from last N hours

        Args:
            client_id: Filter by client ID (optional)
            hours: Time window in hours

        Returns:
            List of active anomaly events
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        anomalies = []

        for event in reversed(self.event_log):
            if event['type'] == 'anomaly:detected':
                if client_id and event['data'].get('client_id') != client_id:
                    continue

                try:
                    event_time = datetime.fromisoformat(event['timestamp'])
                    if event_time > cutoff:
                        anomalies.append(event)
                except (ValueError, KeyError):
                    pass

        return anomalies

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get broadcaster statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'total_events': len(self.event_log),
            'total_broadcasts': self.statistics['total_broadcasts'],
            'total_anomalies': self.statistics['total_anomalies'],
            'total_recommendations': self.statistics['total_recommendations'],
            'events_by_type': self.statistics['by_type']
        }

    def clear_history(self):
        """Clear event history"""
        self.event_log.clear()
        self.logger.info("Event history cleared")

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
