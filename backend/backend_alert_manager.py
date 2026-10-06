"""
Alert Management System - FASE 14 Production Monitoring
Manages alert rules, evaluates conditions, and dispatches notifications
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertConditionType(Enum):
    """Types of alert conditions"""
    THRESHOLD = "threshold"  # Value exceeds threshold
    THRESHOLD_BELOW = "threshold_below"  # Value falls below threshold
    ERROR_RATE = "error_rate"  # Error rate exceeds threshold
    ANOMALY = "anomaly"  # Anomaly detected
    PATTERN = "pattern"  # Pattern matching (e.g., N errors in M time)
    CUSTOM = "custom"  # Custom evaluation function


class AlertChannelType(Enum):
    """Notification channels"""
    LOG = "log"
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    DATABASE = "database"


@dataclass
class AlertRule:
    """Alert rule definition"""
    rule_id: str
    name: str
    description: str
    condition_type: AlertConditionType
    component: str
    metric_or_error_type: str  # Metric name or error type to monitor
    threshold_value: float = 0
    window_seconds: int = 60  # Time window for evaluation
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    channels: List[AlertChannelType] = field(default_factory=lambda: [AlertChannelType.LOG])
    cooldown_seconds: int = 300  # Prevent alert spam
    custom_evaluator: Optional[Callable] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'condition_type': self.condition_type.value,
            'component': self.component,
            'metric_or_error_type': self.metric_or_error_type,
            'threshold_value': self.threshold_value,
            'window_seconds': self.window_seconds,
            'severity': self.severity.value,
            'enabled': self.enabled,
            'channels': [c.value for c in self.channels],
            'cooldown_seconds': self.cooldown_seconds
        }


@dataclass
class Alert:
    """Alert instance"""
    alert_id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    component: str
    context: Dict[str, Any]
    timestamp: str
    fired_count: int = 1  # How many times this alert has fired in cooldown period
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    acknowledged_by: str = ""
    resolved: bool = False
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'severity': self.severity.value,
            'message': self.message,
            'component': self.component,
            'context': self.context,
            'timestamp': self.timestamp,
            'fired_count': self.fired_count,
            'acknowledged': self.acknowledged,
            'resolved': self.resolved
        }


class AlertManager:
    """Alert management and rule evaluation system"""

    def __init__(self, config: Dict = None):
        """
        Initialize alert manager

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_alert_time: Dict[str, float] = defaultdict(float)  # For cooldown
        self.notification_handlers: Dict[AlertChannelType, Callable] = {}

        # Register default notification handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default notification handlers"""
        self.notification_handlers[AlertChannelType.LOG] = self._handle_log_notification
        self.notification_handlers[AlertChannelType.EMAIL] = self._handle_email_notification
        self.notification_handlers[AlertChannelType.SLACK] = self._handle_slack_notification
        self.notification_handlers[AlertChannelType.DATABASE] = self._handle_database_notification

    def register_rule(self, rule: AlertRule) -> bool:
        """Register an alert rule"""
        if rule.rule_id in self.rules:
            logger.warning(f"Rule {rule.rule_id} already exists, overwriting")

        self.rules[rule.rule_id] = rule
        logger.info(f"Registered alert rule: {rule.name}")
        return True

    def register_notification_handler(self, channel: AlertChannelType, handler: Callable):
        """Register a custom notification handler"""
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for {channel.value}")

    def evaluate_rule(self, rule: AlertRule, current_value: float) -> Optional[Alert]:
        """Evaluate a single rule and return alert if triggered"""
        if not rule.enabled:
            return None

        # Check cooldown
        if self._is_in_cooldown(rule.rule_id):
            return None

        should_alert = False
        message = ""

        if rule.condition_type == AlertConditionType.THRESHOLD:
            if current_value > rule.threshold_value:
                should_alert = True
                message = f"{rule.metric_or_error_type} = {current_value} exceeds threshold {rule.threshold_value}"

        elif rule.condition_type == AlertConditionType.THRESHOLD_BELOW:
            if current_value < rule.threshold_value:
                should_alert = True
                message = f"{rule.metric_or_error_type} = {current_value} below threshold {rule.threshold_value}"

        elif rule.condition_type == AlertConditionType.CUSTOM:
            if rule.custom_evaluator:
                try:
                    should_alert = rule.custom_evaluator(current_value, rule)
                    message = f"Custom condition triggered for {rule.metric_or_error_type}"
                except Exception as e:
                    logger.error(f"Error in custom evaluator: {e}")

        if should_alert:
            return self._create_and_dispatch_alert(rule, message, {'current_value': current_value})

        return None

    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if rule is in cooldown period"""
        last_time = self.last_alert_time.get(rule_id, 0)
        rule = self.rules.get(rule_id)
        if not rule:
            return False

        cooldown = rule.cooldown_seconds
        return (time.time() - last_time) < cooldown

    def _create_and_dispatch_alert(self, rule: AlertRule, message: str, context: Dict) -> Alert:
        """Create alert and dispatch to channels"""
        alert_id = f"{rule.rule_id}_{int(time.time() * 1000)}"
        timestamp = datetime.utcnow().isoformat()

        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            rule_name=rule.name,
            severity=rule.severity,
            message=message,
            component=rule.component,
            context=context,
            timestamp=timestamp
        )

        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Keep history limited
        if len(self.alert_history) > 10000:
            self.alert_history = self.alert_history[-10000:]

        # Update cooldown
        self.last_alert_time[rule.rule_id] = time.time()

        # Dispatch to channels
        for channel in rule.channels:
            try:
                handler = self.notification_handlers.get(channel)
                if handler:
                    handler(alert, rule)
            except Exception as e:
                logger.error(f"Error dispatching to {channel.value}: {e}")

        logger.warning(f"Alert fired: {rule.name} - {message}")
        return alert

    # Notification Handlers
    def _handle_log_notification(self, alert: Alert, rule: AlertRule):
        """Log notification handler"""
        level = getattr(logging, alert.severity.value.upper(), logging.WARNING)
        logger.log(level, f"[ALERT] {alert.rule_name}: {alert.message}")

    def _handle_email_notification(self, alert: Alert, rule: AlertRule):
        """Email notification handler (stub)"""
        # In production, this would integrate with SendGrid
        logger.info(f"[EMAIL] Would send email for alert: {alert.rule_name}")

    def _handle_slack_notification(self, alert: Alert, rule: AlertRule):
        """Slack notification handler (stub)"""
        # In production, this would integrate with Slack API
        logger.info(f"[SLACK] Would send Slack message for alert: {alert.rule_name}")

    def _handle_database_notification(self, alert: Alert, rule: AlertRule):
        """Database notification handler"""
        # In production, this would store in alerts table
        logger.info(f"[DATABASE] Would store alert in database: {alert.rule_name}")

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Mark alert as acknowledged"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow().isoformat()
            alert.acknowledged_by = acknowledged_by
            logger.info(f"Alert acknowledged: {alert.rule_name} by {acknowledged_by}")
            return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark alert as resolved"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow().isoformat()
            logger.info(f"Alert resolved: {alert.rule_name}")
            return True
        return False

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get all active alerts"""
        alerts = [a for a in self.active_alerts.values() if not a.resolved]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts

    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of alerts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent = [
            a for a in self.alert_history
            if datetime.fromisoformat(a.timestamp) > cutoff_time
        ]

        if not recent:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'active_count': 0,
                'critical_count': 0
            }

        by_severity = defaultdict(int)
        for alert in recent:
            by_severity[alert.severity.value] += 1

        active = [a for a in recent if not a.resolved]
        critical = [a for a in recent if a.severity == AlertSeverity.CRITICAL]

        return {
            'total_alerts': len(recent),
            'by_severity': dict(by_severity),
            'active_count': len(active),
            'critical_count': len(critical),
            'unacknowledged_count': len([a for a in active if not a.acknowledged]),
            'hours_covered': hours
        }

    def get_rule_status(self) -> Dict[str, Any]:
        """Get status of all rules"""
        return {
            'total_rules': len(self.rules),
            'enabled_rules': len([r for r in self.rules.values() if r.enabled]),
            'disabled_rules': len([r for r in self.rules.values() if not r.enabled]),
            'by_component': defaultdict(list)(
                {r.component: [rule.name for rule in self.rules.values() if rule.component == r.component]
                 for r in self.rules.values()}
            )
        }


# Predefined Alert Rules
class AlertRuleLibrary:
    """Library of common alert rules"""

    @staticmethod
    def create_latency_spike_rule() -> AlertRule:
        """Alert for API latency spike"""
        return AlertRule(
            rule_id="latency_spike",
            name="API Latency Spike",
            description="Alert when API latency exceeds 500ms",
            condition_type=AlertConditionType.THRESHOLD,
            component="api_server",
            metric_or_error_type="latency_ms",
            threshold_value=500,
            window_seconds=60,
            severity=AlertSeverity.WARNING,
            channels=[AlertChannelType.LOG, AlertChannelType.SLACK],
            cooldown_seconds=300
        )

    @staticmethod
    def create_error_rate_rule() -> AlertRule:
        """Alert for high error rate"""
        return AlertRule(
            rule_id="high_error_rate",
            name="High Error Rate",
            description="Alert when error rate exceeds 1%",
            condition_type=AlertConditionType.THRESHOLD,
            component="api_server",
            metric_or_error_type="error_rate",
            threshold_value=1.0,
            window_seconds=300,
            severity=AlertSeverity.CRITICAL,
            channels=[AlertChannelType.LOG, AlertChannelType.SLACK, AlertChannelType.EMAIL],
            cooldown_seconds=600
        )

    @staticmethod
    def create_database_latency_rule() -> AlertRule:
        """Alert for database latency"""
        return AlertRule(
            rule_id="database_latency",
            name="Database Latency High",
            description="Alert when database latency exceeds 100ms",
            condition_type=AlertConditionType.THRESHOLD,
            component="database",
            metric_or_error_type="latency_ms",
            threshold_value=100,
            window_seconds=60,
            severity=AlertSeverity.WARNING,
            channels=[AlertChannelType.LOG],
            cooldown_seconds=300
        )

    @staticmethod
    def create_memory_usage_rule() -> AlertRule:
        """Alert for high memory usage"""
        return AlertRule(
            rule_id="high_memory",
            name="High Memory Usage",
            description="Alert when memory usage exceeds 85%",
            condition_type=AlertConditionType.THRESHOLD,
            component="system",
            metric_or_error_type="memory_percent",
            threshold_value=85,
            window_seconds=120,
            severity=AlertSeverity.CRITICAL,
            channels=[AlertChannelType.LOG, AlertChannelType.SLACK],
            cooldown_seconds=300
        )

    @staticmethod
    def create_shopify_sync_rule() -> AlertRule:
        """Alert for Shopify sync failure"""
        return AlertRule(
            rule_id="shopify_sync_fail",
            name="Shopify Sync Failed",
            description="Alert when Shopify sync hasn't completed in 6+ hours",
            condition_type=AlertConditionType.THRESHOLD,
            component="shopify",
            metric_or_error_type="last_sync_hours_ago",
            threshold_value=6,
            window_seconds=300,
            severity=AlertSeverity.CRITICAL,
            channels=[AlertChannelType.LOG, AlertChannelType.SLACK, AlertChannelType.EMAIL],
            cooldown_seconds=3600
        )


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager(config: Dict = None) -> AlertManager:
    """Get or create global alert manager"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(config)
    return _alert_manager


def setup_default_alerts(manager: Optional[AlertManager] = None) -> AlertManager:
    """Setup default alert rules"""
    if manager is None:
        manager = get_alert_manager()

    manager.register_rule(AlertRuleLibrary.create_latency_spike_rule())
    manager.register_rule(AlertRuleLibrary.create_error_rate_rule())
    manager.register_rule(AlertRuleLibrary.create_database_latency_rule())
    manager.register_rule(AlertRuleLibrary.create_memory_usage_rule())
    manager.register_rule(AlertRuleLibrary.create_shopify_sync_rule())

    logger.info("Default alert rules registered")
    return manager


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    manager = setup_default_alerts()

    # Evaluate rules
    print("\n" + "="*60)
    print("ALERT MANAGER DEMO")
    print("="*60)

    # Simulate latency spike
    alert = manager.evaluate_rule(
        manager.rules['latency_spike'],
        current_value=550
    )
    if alert:
        print(f"\nAlert fired: {alert.rule_name}")
        print(f"Message: {alert.message}")

    # Get active alerts
    active = manager.get_active_alerts()
    print(f"\nActive alerts: {len(active)}")

    # Get summary
    summary = manager.get_alert_summary(hours=24)
    print("\nAlert Summary:")
    print(json.dumps(summary, indent=2))
