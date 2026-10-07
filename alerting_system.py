#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Alertas Multi-Canal
Notificaciones a Email, Slack, y Sistema Local
Escalation automático basado en severidad
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from enum import Enum

class AlertSeverity(Enum):
    INFO = "INFO"
    CAUTION = "CAUTION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AlertChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    LOCAL_LOG = "local_log"
    ALL = "all"

class AlertingSystem:
    def __init__(self):
        self.alerts_dir = Path("logs/alerts")
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        self.alert_history = []

    def create_alert(self, title: str, message: str, severity: AlertSeverity,
                    metric: str = None, current_value: float = None,
                    threshold: float = None, channels: AlertChannel = AlertChannel.ALL):
        """Crear alerta con contexto completo"""

        alert = {
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'message': message,
            'severity': severity.value,
            'metric': metric,
            'current_value': current_value,
            'threshold': threshold,
            'channels': [channels.value] if channels != AlertChannel.ALL else [c.value for c in AlertChannel if c != AlertChannel.ALL]
        }

        self.alert_history.append(alert)

        # Route to channels
        if AlertChannel.EMAIL.value in alert['channels']:
            self._send_email_alert(alert)
        if AlertChannel.SLACK.value in alert['channels']:
            self._send_slack_alert(alert)
        if AlertChannel.LOCAL_LOG.value in alert['channels'] or channels == AlertChannel.ALL:
            self._log_local_alert(alert)

        return alert

    def _send_email_alert(self, alert):
        """Enviar alerta por email (configuración placeholder)"""
        print(f"""
📧 EMAIL ALERT:
   To: felipe@enbuenamesa.com
   Subject: [{alert['severity']}] {alert['title']}

   {alert['message']}

   Metric: {alert['metric']} | Current: {alert['current_value']} | Threshold: {alert['threshold']}
        """)

    def _send_slack_alert(self, alert):
        """Enviar alerta a Slack (webhook placeholder)"""
        severity_emoji = {
            'INFO': '💡',
            'CAUTION': '🟡',
            'WARNING': '🟠',
            'CRITICAL': '🔴'
        }

        print(f"""
💬 SLACK ALERT:
   Channel: #fase-15-alerts
   {severity_emoji.get(alert['severity'], '❓')} {alert['title']}

   {alert['message']}

   Metric: {alert['metric']} | Current: {alert['current_value']} | Threshold: {alert['threshold']}
        """)

    def _log_local_alert(self, alert):
        """Guardar alerta localmente"""
        filename = self.alerts_dir / f"alert_{alert['severity'].lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(alert, f, indent=2)

    def check_and_alert_metrics(self, metrics: dict):
        """Evaluar métricas y generar alertas automáticas"""
        alerts_generated = []

        # WebSocket Latency
        ws_latency = metrics.get('websocket_latency_ms', 0)
        if ws_latency > 80:
            severity = AlertSeverity.WARNING if ws_latency > 100 else AlertSeverity.CAUTION
            alert = self.create_alert(
                title="WebSocket Latency Alert",
                message=f"WebSocket latency has increased to {ws_latency}ms",
                severity=severity,
                metric="WebSocket Latency",
                current_value=ws_latency,
                threshold=100
            )
            alerts_generated.append(alert)

        # Error Rate
        error_rate = metrics.get('error_rate_percent', 0)
        if error_rate > 0.08:
            severity = AlertSeverity.WARNING if error_rate > 0.1 else AlertSeverity.CAUTION
            alert = self.create_alert(
                title="Error Rate Alert",
                message=f"Error rate has increased to {error_rate}%",
                severity=severity,
                metric="Error Rate",
                current_value=error_rate,
                threshold=0.1
            )
            alerts_generated.append(alert)

        # ML Accuracy Drop
        ml_accuracy = metrics.get('ml_accuracy_percent', 0)
        if ml_accuracy < 75:
            alert = self.create_alert(
                title="ML Accuracy Below Threshold",
                message=f"ML accuracy has dropped to {ml_accuracy}%",
                severity=AlertSeverity.CRITICAL,
                metric="ML Accuracy",
                current_value=ml_accuracy,
                threshold=75
            )
            alerts_generated.append(alert)

        # Positive Performance
        predictions = metrics.get('predictions_per_hour', 0)
        if predictions > 36:
            alert = self.create_alert(
                title="Excellent Prediction Rate",
                message=f"Predictions per hour: {predictions} (exceeds projection)",
                severity=AlertSeverity.INFO,
                metric="Predictions Per Hour",
                current_value=predictions,
                threshold=36
            )
            alerts_generated.append(alert)

        return alerts_generated

    def generate_alert_summary(self):
        """Generar resumen de alertas"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_alerts': len(self.alert_history),
            'by_severity': {
                'INFO': len([a for a in self.alert_history if a['severity'] == 'INFO']),
                'CAUTION': len([a for a in self.alert_history if a['severity'] == 'CAUTION']),
                'WARNING': len([a for a in self.alert_history if a['severity'] == 'WARNING']),
                'CRITICAL': len([a for a in self.alert_history if a['severity'] == 'CRITICAL'])
            },
            'latest_alerts': self.alert_history[-5:] if self.alert_history else []
        }
        return summary

def main():
    """Demostración del sistema de alertas"""
    system = AlertingSystem()

    print("="*80)
    print("🚨 ALERTING SYSTEM - DEMO")
    print("="*80)

    # Simular métricas
    metrics = {
        'websocket_latency_ms': 45,
        'error_rate_percent': 0.02,
        'ml_accuracy_percent': 81.2,
        'predictions_per_hour': 40
    }

    print("\n📊 Evaluando métricas...")
    alerts = system.check_and_alert_metrics(metrics)
    print(f"\n✅ {len(alerts)} alertas generadas")

    # Resumen
    summary = system.generate_alert_summary()
    print("\n📈 Resumen de Alertas:")
    print(f"   Total: {summary['total_alerts']}")
    print(f"   INFO: {summary['by_severity']['INFO']}")
    print(f"   CAUTION: {summary['by_severity']['CAUTION']}")
    print(f"   WARNING: {summary['by_severity']['WARNING']}")
    print(f"   CRITICAL: {summary['by_severity']['CRITICAL']}")

if __name__ == "__main__":
    main()
