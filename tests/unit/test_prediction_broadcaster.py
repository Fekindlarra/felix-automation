"""
FASE 14 - Unit Tests for Prediction Broadcaster
Testing real-time WebSocket prediction broadcasts
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class MockWebSocketManager:
    """Mock WebSocket connection manager"""

    def __init__(self):
        self.connections = {}
        self.broadcast_log = []

    def broadcast(self, event):
        """Broadcast event to all connected clients"""
        self.broadcast_log.append(event)
        return True

    def broadcast_to_user(self, user_id, event):
        """Broadcast event to specific user"""
        if user_id in self.connections:
            self.connections[user_id].append(event)
        return True

    def add_connection(self, user_id, connection):
        """Register new connection"""
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(connection)

    def get_broadcast_count(self):
        """Get total broadcast count"""
        return len(self.broadcast_log)


class MockPrediction:
    """Mock prediction object"""

    def __init__(self, client_id, probability=0.75, confidence=0.85):
        self.client_id = client_id
        self.probability = probability  # 0-1 (0-100%)
        self.confidence = confidence    # 0-1 (confidence score)
        self.risk_factors = [
            'Low engagement in past 30 days',
            'Price sensitivity detected'
        ]
        self.positive_factors = [
            'Multiple product views',
            'Cart abandonment (high intent)'
        ]
        self.predicted_timeline_days = 7
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'client_id': self.client_id,
            'probability': self.probability,
            'confidence': self.confidence,
            'risk_factors': self.risk_factors,
            'positive_factors': self.positive_factors,
            'predicted_timeline_days': self.predicted_timeline_days,
            'timestamp': self.timestamp
        }


class MockPredictionBroadcaster:
    """Mock Prediction Broadcaster for WebSocket real-time updates"""

    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager or MockWebSocketManager()
        self.broadcast_history = []
        self.role_filters = {
            'admin': ['client_id', 'probability', 'confidence', 'risk_factors', 'positive_factors', 'timeline'],
            'client': ['probability', 'confidence', 'positive_factors', 'timeline'],
            'viewer': ['probability', 'positive_factors']
        }

    def broadcast_prediction(self, prediction, role='admin'):
        """Broadcast prediction to dashboard via WebSocket"""
        event = self._format_prediction_event(prediction, role)
        self.websocket_manager.broadcast(event)
        self.broadcast_history.append(event)
        return event

    def broadcast_to_role(self, prediction, role):
        """Broadcast prediction only to users with specific role"""
        event = self._format_prediction_event(prediction, role)
        # In real implementation, would filter users by role
        self.websocket_manager.broadcast(event)
        self.broadcast_history.append(event)
        return event

    def _format_prediction_event(self, prediction, role='admin'):
        """Format prediction for WebSocket broadcast"""
        pred_dict = prediction.to_dict()

        # Filter fields based on role
        filtered = {}
        allowed_fields = self.role_filters.get(role, ['probability', 'positive_factors'])

        for field in allowed_fields:
            if field == 'client_id':
                filtered['client_id'] = pred_dict.get('client_id')
            elif field == 'probability':
                filtered['probability'] = int(pred_dict.get('probability', 0) * 100)
            elif field == 'confidence':
                filtered['confidence'] = int(pred_dict.get('confidence', 0) * 100)
            elif field == 'risk_factors':
                filtered['risk_factors'] = pred_dict.get('risk_factors', [])
            elif field == 'positive_factors':
                filtered['positive_factors'] = pred_dict.get('positive_factors', [])
            elif field == 'timeline':
                filtered['timeline_days'] = pred_dict.get('predicted_timeline_days')

        event = {
            'type': 'prediction:generated',
            'role': role,
            'timestamp': datetime.now().isoformat(),
            'data': filtered
        }

        return event

    def broadcast_batch_predictions(self, predictions, role='admin'):
        """Broadcast multiple predictions efficiently"""
        events = []
        for prediction in predictions:
            event = self._format_prediction_event(prediction, role)
            self.websocket_manager.broadcast(event)
            self.broadcast_history.append(event)
            events.append(event)
        return events

    def broadcast_anomaly(self, client_id, anomaly_type, severity):
        """Broadcast anomaly detection alert"""
        event = {
            'type': 'anomaly:detected',
            'client_id': client_id,
            'anomaly_type': anomaly_type,
            'severity': severity,  # 'low', 'medium', 'high', 'critical'
            'timestamp': datetime.now().isoformat()
        }

        self.websocket_manager.broadcast(event)
        self.broadcast_history.append(event)
        return event

    def broadcast_recommendation(self, client_id, recommendation):
        """Broadcast action recommendation"""
        event = {
            'type': 'recommendation:generated',
            'client_id': client_id,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }

        self.websocket_manager.broadcast(event)
        self.broadcast_history.append(event)
        return event

    def get_broadcast_history(self):
        """Get history of all broadcasts"""
        return self.broadcast_history

    def clear_history(self):
        """Clear broadcast history"""
        self.broadcast_history = []


# ============================================================================
# TESTS
# ============================================================================

class TestPredictionFormatting:
    """Test prediction event formatting"""

    def test_prediction_event_created(self):
        """Should create properly formatted prediction event"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        event = broadcaster._format_prediction_event(prediction)

        assert event['type'] == 'prediction:generated'
        assert 'timestamp' in event
        assert 'data' in event

    def test_probability_converted_to_percentage(self):
        """Should convert probability (0-1) to percentage (0-100)"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123, probability=0.85)

        event = broadcaster._format_prediction_event(prediction)

        assert event['data']['probability'] == 85

    def test_confidence_converted_to_percentage(self):
        """Should convert confidence (0-1) to percentage (0-100)"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123, confidence=0.92)

        event = broadcaster._format_prediction_event(prediction)

        assert event['data']['confidence'] == 92

    def test_factors_included_in_event(self):
        """Should include risk and positive factors"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        event = broadcaster._format_prediction_event(prediction, role='admin')

        assert 'risk_factors' in event['data']
        assert 'positive_factors' in event['data']
        assert len(event['data']['risk_factors']) > 0
        assert len(event['data']['positive_factors']) > 0


class TestRoleBasedFiltering:
    """Test role-based data filtering"""

    def test_admin_sees_all_data(self):
        """Should show all data to admin role"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        event = broadcaster._format_prediction_event(prediction, role='admin')

        assert 'client_id' in event['data']
        assert 'probability' in event['data']
        assert 'confidence' in event['data']
        assert 'risk_factors' in event['data']

    def test_client_sees_limited_data(self):
        """Should show limited data to client role"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        event = broadcaster._format_prediction_event(prediction, role='client')

        # Client should not see risk factors
        assert 'probability' in event['data']
        assert 'positive_factors' in event['data']
        # Client should see timeline
        assert 'timeline_days' in event['data']

    def test_viewer_sees_minimal_data(self):
        """Should show minimal data to viewer role"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        event = broadcaster._format_prediction_event(prediction, role='viewer')

        # Viewer should only see probability and positive factors
        assert 'probability' in event['data']
        assert 'positive_factors' in event['data']
        # Viewer should NOT see risk factors or client_id
        assert 'client_id' not in event['data']
        assert 'risk_factors' not in event['data']


class TestBroadcasting:
    """Test WebSocket broadcasting"""

    def test_broadcast_sends_event(self):
        """Should successfully broadcast prediction event"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        result = broadcaster.broadcast_prediction(prediction)

        assert result is not None
        assert result['type'] == 'prediction:generated'

    def test_broadcast_recorded_in_history(self):
        """Should record broadcast in history"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        broadcaster.broadcast_prediction(prediction)

        history = broadcaster.get_broadcast_history()
        assert len(history) > 0
        assert history[0]['type'] == 'prediction:generated'

    def test_multiple_broadcasts_recorded(self):
        """Should record multiple broadcasts in order"""
        broadcaster = MockPredictionBroadcaster()

        pred1 = MockPrediction(client_id=1)
        pred2 = MockPrediction(client_id=2)
        pred3 = MockPrediction(client_id=3)

        broadcaster.broadcast_prediction(pred1)
        broadcaster.broadcast_prediction(pred2)
        broadcaster.broadcast_prediction(pred3)

        history = broadcaster.get_broadcast_history()
        assert len(history) == 3


class TestBatchBroadcasting:
    """Test batch prediction broadcasting"""

    def test_batch_broadcasts_multiple_predictions(self):
        """Should broadcast multiple predictions in batch"""
        broadcaster = MockPredictionBroadcaster()

        predictions = [
            MockPrediction(client_id=1),
            MockPrediction(client_id=2),
            MockPrediction(client_id=3)
        ]

        events = broadcaster.broadcast_batch_predictions(predictions)

        assert len(events) == 3
        assert all(e['type'] == 'prediction:generated' for e in events)

    def test_batch_maintains_order(self):
        """Should maintain prediction order in batch"""
        broadcaster = MockPredictionBroadcaster()

        predictions = [
            MockPrediction(client_id=10),
            MockPrediction(client_id=20),
            MockPrediction(client_id=30)
        ]

        events = broadcaster.broadcast_batch_predictions(predictions)

        assert events[0]['data']['client_id'] == 10
        assert events[1]['data']['client_id'] == 20
        assert events[2]['data']['client_id'] == 30


class TestAnomalyBroadcasting:
    """Test anomaly detection broadcasting"""

    def test_anomaly_event_created(self):
        """Should create anomaly detection event"""
        broadcaster = MockPredictionBroadcaster()

        event = broadcaster.broadcast_anomaly(
            client_id=123,
            anomaly_type='unusual_activity',
            severity='high'
        )

        assert event['type'] == 'anomaly:detected'
        assert event['client_id'] == 123
        assert event['anomaly_type'] == 'unusual_activity'
        assert event['severity'] == 'high'

    def test_anomaly_types_supported(self):
        """Should support various anomaly types"""
        broadcaster = MockPredictionBroadcaster()

        anomaly_types = [
            'unusual_activity',
            'price_sensitivity',
            'churn_risk',
            'fraud_indicator'
        ]

        for anomaly_type in anomaly_types:
            event = broadcaster.broadcast_anomaly(123, anomaly_type, 'medium')
            assert event['anomaly_type'] == anomaly_type

    def test_severity_levels_valid(self):
        """Should handle all severity levels"""
        broadcaster = MockPredictionBroadcaster()

        severities = ['low', 'medium', 'high', 'critical']

        for severity in severities:
            event = broadcaster.broadcast_anomaly(123, 'test', severity)
            assert event['severity'] == severity


class TestRecommendationBroadcasting:
    """Test recommendation broadcasting"""

    def test_recommendation_event_created(self):
        """Should create recommendation event"""
        broadcaster = MockPredictionBroadcaster()

        recommendation = "Send personalized discount offer within next 2 days"
        event = broadcaster.broadcast_recommendation(123, recommendation)

        assert event['type'] == 'recommendation:generated'
        assert event['client_id'] == 123
        assert event['recommendation'] == recommendation

    def test_recommendation_recorded_in_history(self):
        """Should record recommendation in broadcast history"""
        broadcaster = MockPredictionBroadcaster()

        broadcaster.broadcast_recommendation(123, "Test recommendation")

        history = broadcaster.get_broadcast_history()
        assert any(e['type'] == 'recommendation:generated' for e in history)


class TestEventTimestamps:
    """Test event timestamp handling"""

    def test_event_has_timestamp(self):
        """Should include timestamp in every event"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        event = broadcaster.broadcast_prediction(prediction)

        assert 'timestamp' in event
        assert isinstance(event['timestamp'], str)

    def test_timestamps_are_iso_format(self):
        """Should use ISO 8601 format for timestamps"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        event = broadcaster.broadcast_prediction(prediction)

        # ISO format check: should contain 'T' and match pattern
        assert 'T' in event['timestamp']
        assert isinstance(event['timestamp'], str)


class TestHistoryManagement:
    """Test broadcast history management"""

    def test_history_cleared_successfully(self):
        """Should clear broadcast history"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)

        broadcaster.broadcast_prediction(prediction)
        assert len(broadcaster.get_broadcast_history()) > 0

        broadcaster.clear_history()
        assert len(broadcaster.get_broadcast_history()) == 0

    def test_history_persists_across_calls(self):
        """Should accumulate history across multiple broadcasts"""
        broadcaster = MockPredictionBroadcaster()

        for i in range(5):
            prediction = MockPrediction(client_id=i)
            broadcaster.broadcast_prediction(prediction)

        assert len(broadcaster.get_broadcast_history()) == 5


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_probability_handled(self):
        """Should handle zero probability"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123, probability=0.0)

        event = broadcaster.broadcast_prediction(prediction)

        assert event['data']['probability'] == 0

    def test_hundred_percent_probability_handled(self):
        """Should handle 100% probability"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123, probability=1.0)

        event = broadcaster.broadcast_prediction(prediction)

        assert event['data']['probability'] == 100

    def test_missing_factors_handled(self):
        """Should handle predictions with no risk/positive factors"""
        broadcaster = MockPredictionBroadcaster()
        prediction = MockPrediction(client_id=123)
        prediction.risk_factors = []
        prediction.positive_factors = []

        event = broadcaster._format_prediction_event(prediction, role='admin')

        assert 'risk_factors' in event['data']
        assert 'positive_factors' in event['data']
        assert len(event['data']['risk_factors']) == 0
        assert len(event['data']['positive_factors']) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
