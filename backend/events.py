#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 13 Day 3: Event Model Definitions
WebSocket Real-Time Updates + Dashboards

Define event types and data structures for real-time communication
"""

from enum import Enum
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from datetime import datetime
import json


class EventType(Enum):
    """Event types emitted by system"""

    # Pipeline Events
    PIPELINE_STAGE_CHANGED = "pipeline:stage_changed"
    PIPELINE_CLIENT_ADDED = "pipeline:client_added"
    PIPELINE_CLIENT_REMOVED = "pipeline:client_removed"
    PIPELINE_STATUS_UPDATED = "pipeline:status_updated"

    # Audit Events
    AUDIT_STARTED = "audit:started"
    AUDIT_COMPLETED = "audit:completed"
    AUDIT_FAILED = "audit:failed"
    AUDIT_SCORE_UPDATED = "audit:score_updated"

    # Proposal Events
    PROPOSAL_GENERATED = "proposal:generated"
    PROPOSAL_SENT = "proposal:sent"
    PROPOSAL_VIEWED = "proposal:viewed"

    # Email Events
    EMAIL_SENT = "email:sent"
    EMAIL_OPENED = "email:opened"
    EMAIL_CLICKED = "email:clicked"
    EMAIL_BOUNCED = "email:bounced"

    # KPI Events
    KPI_UPDATED = "kpi:updated"
    METRIC_SNAPSHOT = "metric:snapshot"

    # Prediction Events (FASE 14)
    PREDICTION_GENERATED = "prediction:generated"
    ANOMALY_DETECTED = "anomaly:detected"

    # A/B Testing Events (FASE 15 Phase 3)
    TEST_CREATED = "test:created"
    TEST_STARTED = "test:started"
    TEST_COMPLETED = "test:completed"
    TEST_PAUSED = "test:paused"
    TEST_WINNER_ANNOUNCED = "test:winner_announced"

    # Comparison Events (FASE 15 Phase 3)
    COMPARISON_STARTED = "comparison:started"
    COMPARISON_COMPLETED = "comparison:completed"

    # Notification Events
    NOTIFICATION_CREATED = "notification:created"
    NOTIFICATION_DISMISSED = "notification:dismissed"

    # System Events
    CONNECTION_ESTABLISHED = "system:connection_established"
    CONNECTION_CLOSED = "system:connection_closed"
    SYNC_REQUEST = "system:sync_request"


@dataclass
class EventPayload:
    """Base event payload structure"""
    event_type: EventType
    timestamp: datetime
    client_id: int
    user_id: Optional[int] = None
    data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "client_id": self.client_id,
            "user_id": self.user_id,
            "data": self.data or {}
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


@dataclass
class PipelineEvent(EventPayload):
    """Pipeline stage change event"""
    old_stage: Optional[str] = None
    new_stage: Optional[str] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "old_stage": self.old_stage,
                "new_stage": self.new_stage
            }


@dataclass
class AuditEvent(EventPayload):
    """Audit completion event"""
    platform: Optional[str] = None
    score: Optional[float] = None
    audit_id: Optional[int] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "platform": self.platform,
                "score": self.score,
                "audit_id": self.audit_id
            }


@dataclass
class ProposalEvent(EventPayload):
    """Proposal event"""
    proposal_id: Optional[int] = None
    proposal_amount: Optional[float] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "proposal_id": self.proposal_id,
                "proposal_amount": self.proposal_amount
            }


@dataclass
class EmailEvent(EventPayload):
    """Email tracking event"""
    email_id: Optional[int] = None
    email_type: Optional[str] = None
    recipient: Optional[str] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "email_id": self.email_id,
                "email_type": self.email_type,
                "recipient": self.recipient
            }


@dataclass
class KPIEvent(EventPayload):
    """KPI update event"""
    metric_name: str = None
    metric_value: float = None
    metric_unit: str = None

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "metric_name": self.metric_name,
                "metric_value": self.metric_value,
                "metric_unit": self.metric_unit
            }


@dataclass
class PredictionEvent(EventPayload):
    """ML Prediction event (FASE 14)"""
    probability: Optional[float] = None
    confidence: Optional[float] = None
    risk_factors: Optional[list] = None
    positive_factors: Optional[list] = None
    recommendation: Optional[str] = None
    predicted_timeline_days: Optional[int] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "probability": self.probability,
                "confidence": self.confidence,
                "risk_factors": self.risk_factors or [],
                "positive_factors": self.positive_factors or [],
                "recommendation": self.recommendation,
                "predicted_timeline_days": self.predicted_timeline_days
            }


@dataclass
class AnomalyEvent(EventPayload):
    """Anomaly detection event (FASE 14)"""
    anomaly_type: Optional[str] = None
    severity: Optional[str] = None  # "low", "medium", "high"
    description: Optional[str] = None
    affected_metric: Optional[str] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "anomaly_type": self.anomaly_type,
                "severity": self.severity,
                "description": self.description,
                "affected_metric": self.affected_metric
            }


@dataclass
class ABTestEvent(EventPayload):
    """A/B Test lifecycle event (FASE 15 Phase 3)"""
    test_id: Optional[int] = None
    test_name: Optional[str] = None
    active: Optional[bool] = None
    variant_winner: Optional[str] = None  # "A" or "B"
    email_type: Optional[str] = None
    duration_days: Optional[int] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "test_id": self.test_id,
                "test_name": self.test_name,
                "active": self.active,
                "variant_winner": self.variant_winner,
                "email_type": self.email_type,
                "duration_days": self.duration_days
            }


@dataclass
class ComparisonEvent(EventPayload):
    """ML vs Rules comparison event (FASE 15 Phase 3)"""
    test_id: Optional[int] = None
    ml_accuracy: Optional[float] = None
    rules_accuracy: Optional[float] = None
    sample_size: Optional[int] = None
    winner: Optional[str] = None  # "ML" or "RULES"
    confidence_interval: Optional[Dict] = None  # {"lower": x, "upper": y}

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "test_id": self.test_id,
                "ml_accuracy": self.ml_accuracy,
                "rules_accuracy": self.rules_accuracy,
                "sample_size": self.sample_size,
                "winner": self.winner,
                "confidence_interval": self.confidence_interval or {}
            }


@dataclass
class NotificationEvent(EventPayload):
    """Notification event"""
    notification_id: Optional[int] = None
    title: Optional[str] = None
    message: Optional[str] = None
    notification_type: Optional[str] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {
                "notification_id": self.notification_id,
                "title": self.title,
                "message": self.message,
                "notification_type": self.notification_type
            }


@dataclass
class MetricSnapshot:
    """Real-time KPI snapshot"""
    timestamp: datetime
    metrics: Dict[str, float]  # metric_name -> value
    pipeline_stats: Dict[str, int]  # stage -> count
    daily_revenue: float
    monthly_revenue: float
    conversion_rate: float
    average_deal_size: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "pipeline_stats": self.pipeline_stats,
            "daily_revenue": self.daily_revenue,
            "monthly_revenue": self.monthly_revenue,
            "conversion_rate": self.conversion_rate,
            "average_deal_size": self.average_deal_size
        }


class EventFactory:
    """Factory for creating events"""

    @staticmethod
    def pipeline_stage_changed(client_id: int, old_stage: str, new_stage: str,
                               user_id: Optional[int] = None) -> PipelineEvent:
        """Create pipeline stage changed event"""
        return PipelineEvent(
            event_type=EventType.PIPELINE_STAGE_CHANGED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            old_stage=old_stage,
            new_stage=new_stage
        )

    @staticmethod
    def audit_completed(client_id: int, platform: str, score: float,
                       audit_id: int, user_id: Optional[int] = None) -> AuditEvent:
        """Create audit completed event"""
        return AuditEvent(
            event_type=EventType.AUDIT_COMPLETED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            platform=platform,
            score=score,
            audit_id=audit_id
        )

    @staticmethod
    def proposal_sent(client_id: int, proposal_id: int, proposal_amount: float,
                     user_id: Optional[int] = None) -> ProposalEvent:
        """Create proposal sent event"""
        return ProposalEvent(
            event_type=EventType.PROPOSAL_SENT,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            proposal_id=proposal_id,
            proposal_amount=proposal_amount
        )

    @staticmethod
    def email_opened(client_id: int, email_id: int, email_type: str,
                    recipient: str, user_id: Optional[int] = None) -> EmailEvent:
        """Create email opened event"""
        return EmailEvent(
            event_type=EventType.EMAIL_OPENED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            email_id=email_id,
            email_type=email_type,
            recipient=recipient
        )

    @staticmethod
    def kpi_updated(client_id: int, metric_name: str, metric_value: float,
                   metric_unit: str = "", user_id: Optional[int] = None) -> KPIEvent:
        """Create KPI updated event"""
        return KPIEvent(
            event_type=EventType.KPI_UPDATED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit
        )

    @staticmethod
    def prediction_generated(client_id: int, probability: float, confidence: float,
                            risk_factors: list, positive_factors: list,
                            recommendation: str, predicted_timeline_days: int,
                            user_id: Optional[int] = None) -> PredictionEvent:
        """Create prediction generated event (FASE 14)"""
        return PredictionEvent(
            event_type=EventType.PREDICTION_GENERATED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            probability=probability,
            confidence=confidence,
            risk_factors=risk_factors,
            positive_factors=positive_factors,
            recommendation=recommendation,
            predicted_timeline_days=predicted_timeline_days
        )

    @staticmethod
    def anomaly_detected(client_id: int, anomaly_type: str, severity: str,
                        description: str, affected_metric: str,
                        user_id: Optional[int] = None) -> AnomalyEvent:
        """Create anomaly detected event (FASE 14)"""
        return AnomalyEvent(
            event_type=EventType.ANOMALY_DETECTED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            affected_metric=affected_metric
        )

    @staticmethod
    def test_created(client_id: int, test_id: int, test_name: str,
                    email_type: str, duration_days: int,
                    user_id: Optional[int] = None) -> ABTestEvent:
        """Create A/B test created event (FASE 15 Phase 3)"""
        return ABTestEvent(
            event_type=EventType.TEST_CREATED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            test_id=test_id,
            test_name=test_name,
            email_type=email_type,
            duration_days=duration_days,
            active=True
        )

    @staticmethod
    def test_started(client_id: int, test_id: int, test_name: str,
                    user_id: Optional[int] = None) -> ABTestEvent:
        """Create A/B test started event (FASE 15 Phase 3)"""
        return ABTestEvent(
            event_type=EventType.TEST_STARTED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            test_id=test_id,
            test_name=test_name,
            active=True
        )

    @staticmethod
    def test_completed(client_id: int, test_id: int, test_name: str,
                      variant_winner: str, user_id: Optional[int] = None) -> ABTestEvent:
        """Create A/B test completed event (FASE 15 Phase 3)"""
        return ABTestEvent(
            event_type=EventType.TEST_COMPLETED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            test_id=test_id,
            test_name=test_name,
            variant_winner=variant_winner,
            active=False
        )

    @staticmethod
    def test_paused(client_id: int, test_id: int, test_name: str,
                   user_id: Optional[int] = None) -> ABTestEvent:
        """Create A/B test paused event (FASE 15 Phase 3)"""
        return ABTestEvent(
            event_type=EventType.TEST_PAUSED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            test_id=test_id,
            test_name=test_name,
            active=False
        )

    @staticmethod
    def test_winner_announced(client_id: int, test_id: int, test_name: str,
                             variant_winner: str, user_id: Optional[int] = None) -> ABTestEvent:
        """Create A/B test winner announced event (FASE 15 Phase 3)"""
        return ABTestEvent(
            event_type=EventType.TEST_WINNER_ANNOUNCED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            test_id=test_id,
            test_name=test_name,
            variant_winner=variant_winner,
            active=False
        )

    @staticmethod
    def comparison_started(client_id: int, test_id: int, user_id: Optional[int] = None) -> ComparisonEvent:
        """Create comparison started event (FASE 15 Phase 3)"""
        return ComparisonEvent(
            event_type=EventType.COMPARISON_STARTED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            test_id=test_id
        )

    @staticmethod
    def comparison_completed(client_id: int, test_id: int, ml_accuracy: float,
                            rules_accuracy: float, sample_size: int,
                            winner: str, confidence_interval: Dict,
                            user_id: Optional[int] = None) -> ComparisonEvent:
        """Create comparison completed event (FASE 15 Phase 3)"""
        return ComparisonEvent(
            event_type=EventType.COMPARISON_COMPLETED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            test_id=test_id,
            ml_accuracy=ml_accuracy,
            rules_accuracy=rules_accuracy,
            sample_size=sample_size,
            winner=winner,
            confidence_interval=confidence_interval
        )

    @staticmethod
    def notification_created(client_id: int, title: str, message: str,
                            notification_type: str = "info",
                            user_id: Optional[int] = None) -> NotificationEvent:
        """Create notification event"""
        return NotificationEvent(
            event_type=EventType.NOTIFICATION_CREATED,
            timestamp=datetime.utcnow(),
            client_id=client_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type
        )


class ConnectionState(Enum):
    """WebSocket connection states"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """WebSocket connection information"""
    connection_id: str
    user_id: int
    client_id: Optional[int]
    state: ConnectionState
    connected_at: datetime
    last_heartbeat: datetime
    role: str  # "admin", "client"
    is_mobile: bool = False  # Mobile device detection
    user_agent: Optional[str] = None  # Client user agent for detection

    def is_active(self) -> bool:
        """Check if connection is active"""
        return self.state == ConnectionState.CONNECTED

    def get_heartbeat_interval(self) -> int:
        """Get heartbeat interval in seconds (60s mobile, 30s desktop)"""
        return 60 if self.is_mobile else 30


# Event routing configuration
EVENT_ROUTING = {
    EventType.PIPELINE_STAGE_CHANGED: ["admin", "client"],
    EventType.PIPELINE_CLIENT_ADDED: ["admin"],
    EventType.AUDIT_COMPLETED: ["admin", "client"],
    EventType.PROPOSAL_SENT: ["admin", "client"],
    EventType.EMAIL_OPENED: ["admin"],
    EventType.EMAIL_CLICKED: ["admin"],
    EventType.KPI_UPDATED: ["admin"],
    EventType.METRIC_SNAPSHOT: ["admin"],
    EventType.PREDICTION_GENERATED: ["admin", "client"],  # FASE 14
    EventType.ANOMALY_DETECTED: ["admin"],  # FASE 14
    EventType.TEST_CREATED: ["admin"],  # FASE 15 Phase 3
    EventType.TEST_STARTED: ["admin"],  # FASE 15 Phase 3
    EventType.TEST_COMPLETED: ["admin"],  # FASE 15 Phase 3
    EventType.TEST_PAUSED: ["admin"],  # FASE 15 Phase 3
    EventType.TEST_WINNER_ANNOUNCED: ["admin"],  # FASE 15 Phase 3
    EventType.COMPARISON_STARTED: ["admin"],  # FASE 15 Phase 3
    EventType.COMPARISON_COMPLETED: ["admin"],  # FASE 15 Phase 3
    EventType.NOTIFICATION_CREATED: ["admin", "client"],
}


def get_target_roles(event_type: EventType) -> list:
    """Get roles that should receive this event"""
    return EVENT_ROUTING.get(event_type, ["admin"])
