#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Week 2: Prometheus Metrics Exporter
Exports monitoring system metrics in Prometheus format
"""

import logging
from typing import Dict, List
from datetime import datetime, timezone
from dataclasses import dataclass

from backend.monitoring import (
    get_metrics_collector,
    get_health_checker,
    get_performance_profiler,
    get_monitoring_dashboard
)

logger = logging.getLogger(__name__)


@dataclass
class PrometheusMetric:
    """Represents a single Prometheus metric"""
    name: str
    type: str  # gauge, counter, histogram, summary
    help_text: str
    samples: List[tuple]  # List of (labels_dict, value) tuples

    def to_prometheus_format(self) -> str:
        """Convert to Prometheus text format"""
        lines = []

        # Add TYPE and HELP comments
        lines.append(f"# HELP {self.name} {self.help_text}")
        lines.append(f"# TYPE {self.name} {self.type}")

        # Add metric samples
        for labels_dict, value in self.samples:
            if labels_dict:
                labels_str = ",".join(f'{k}="{v}"' for k, v in labels_dict.items())
                lines.append(f'{self.name}{{{labels_str}}} {value}')
            else:
                lines.append(f'{self.name} {value}')

        return "\n".join(lines)


class PrometheusExporter:
    """Exports monitoring metrics in Prometheus format"""

    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self.health_checker = get_health_checker()
        self.performance_profiler = get_performance_profiler()
        self.dashboard = get_monitoring_dashboard()
        self.start_time = datetime.now(timezone.utc)

    def export_metrics(self) -> str:
        """Export all metrics in Prometheus text format"""
        all_lines = []

        # Add timestamp
        all_lines.append(f"# Generated at {datetime.now(timezone.utc).isoformat()}")
        all_lines.append("")

        # Export each metric group
        all_lines.extend(self._export_health_metrics())
        all_lines.extend(self._export_system_metrics())
        all_lines.extend(self._export_performance_metrics())
        all_lines.extend(self._export_websocket_metrics())
        all_lines.extend(self._export_uptime_metric())

        return "\n".join(all_lines)

    def _export_health_metrics(self) -> List[str]:
        """Export health check metrics"""
        lines = []
        health_status = self.health_checker.evaluate_health()

        # Overall health status
        lines.append("# HELP felix_health_status Overall system health (1=healthy, 0=degraded, -1=unhealthy)")
        lines.append("# TYPE felix_health_status gauge")

        status_value = 1 if health_status["overall_status"] == "healthy" else (
            0 if health_status["overall_status"] == "degraded" else -1
        )
        lines.append(f"felix_health_status {status_value}")
        lines.append("")

        # Individual health checks
        lines.append("# HELP felix_health_check Individual health check status (1=healthy, 0=warning, -1=critical)")
        lines.append("# TYPE felix_health_check gauge")

        for metric_name, metric_data in health_status.get("metrics", {}).items():
            status = metric_data.get("status", "unknown")
            status_value = 1 if status == "healthy" else (0 if status == "warning" else -1)
            lines.append(f'felix_health_check{{check="{metric_name}"}} {status_value}')

        lines.append("")
        return lines

    def _export_system_metrics(self) -> List[str]:
        """Export system-level metrics"""
        lines = []

        # Get latest metrics from collector
        lines.append("# HELP felix_websocket_latency WebSocket event latency in milliseconds")
        lines.append("# TYPE felix_websocket_latency gauge")

        ws_latency = self.metrics_collector.get_latest("websocket_latency")
        if ws_latency:
            lines.append(f"felix_websocket_latency {ws_latency.value}")
        lines.append("")

        lines.append("# HELP felix_api_response_time API response time in milliseconds")
        lines.append("# TYPE felix_api_response_time gauge")

        api_time = self.metrics_collector.get_latest("api_response_time")
        if api_time:
            lines.append(f"felix_api_response_time {api_time.value}")
        lines.append("")

        lines.append("# HELP felix_cache_hit_rate Cache hit rate percentage (0-100)")
        lines.append("# TYPE felix_cache_hit_rate gauge")

        cache_rate = self.metrics_collector.get_latest("cache_hit_rate")
        if cache_rate:
            lines.append(f"felix_cache_hit_rate {cache_rate.value}")
        lines.append("")

        lines.append("# HELP felix_error_rate Error rate percentage (0-100)")
        lines.append("# TYPE felix_error_rate gauge")

        error_rate = self.metrics_collector.get_latest("error_rate")
        if error_rate:
            lines.append(f"felix_error_rate {error_rate.value}")
        lines.append("")

        return lines

    def _export_performance_metrics(self) -> List[str]:
        """Export performance profiling metrics"""
        lines = []

        lines.append("# HELP felix_operation_duration_seconds Operation execution time in seconds")
        lines.append("# TYPE felix_operation_duration_seconds summary")

        # Get some common operations
        operations = [
            "database.get_client",
            "prediction.generate",
            "email.send",
            "audit.run"
        ]

        for op_name in operations:
            stats = self.performance_profiler.get_operation_stats(op_name)
            if stats and stats.get("count", 0) > 0:
                # Convert ms to seconds for Prometheus
                avg_seconds = stats.get("avg", 0) / 1000.0
                count = stats.get("count", 0)

                lines.append(f'felix_operation_duration_seconds_sum{{operation="{op_name}"}} {avg_seconds * count}')
                lines.append(f'felix_operation_duration_seconds_count{{operation="{op_name}"}} {count}')

        lines.append("")
        return lines

    def _export_websocket_metrics(self) -> List[str]:
        """Export WebSocket-specific metrics"""
        lines = []

        lines.append("# HELP felix_websocket_connections Active WebSocket connections")
        lines.append("# TYPE felix_websocket_connections gauge")

        ws_conn = self.metrics_collector.get_latest("websocket_connections")
        if ws_conn:
            lines.append(f"felix_websocket_connections {ws_conn.value}")
        lines.append("")

        lines.append("# HELP felix_websocket_events_emitted Total WebSocket events emitted")
        lines.append("# TYPE felix_websocket_events_emitted counter")

        ws_events = self.metrics_collector.get_latest("websocket_events_emitted")
        if ws_events:
            lines.append(f"felix_websocket_events_emitted {ws_events.value}")
        lines.append("")

        lines.append("# HELP felix_websocket_errors WebSocket transmission errors")
        lines.append("# TYPE felix_websocket_errors counter")

        ws_errors = self.metrics_collector.get_latest("websocket_event_errors")
        if ws_errors:
            lines.append(f"felix_websocket_errors {ws_errors.value}")
        lines.append("")

        return lines

    def _export_uptime_metric(self) -> List[str]:
        """Export system uptime"""
        lines = []

        lines.append("# HELP felix_uptime_seconds System uptime in seconds")
        lines.append("# TYPE felix_uptime_seconds gauge")

        uptime_seconds = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        lines.append(f"felix_uptime_seconds {uptime_seconds}")
        lines.append("")

        return lines

    def export_alert_metrics(self) -> str:
        """Export active alerts as metrics"""
        lines = []

        health_status = self.health_checker.evaluate_health()
        alerts = health_status.get("alerts", [])

        lines.append("# HELP felix_alerts_active Number of active alerts by severity")
        lines.append("# TYPE felix_alerts_active gauge")

        # Count by severity
        severity_counts = {"info": 0, "warning": 0, "critical": 0}

        for alert in alerts:
            severity = alert.get("severity", "info").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        for severity, count in severity_counts.items():
            lines.append(f'felix_alerts_active{{severity="{severity}"}} {count}')

        lines.append("")
        return "\n".join(lines)

    def get_scrape_config(self) -> Dict:
        """Get Prometheus scrape configuration"""
        return {
            "scrape_interval": "15s",
            "evaluation_interval": "15s",
            "scrape_configs": [
                {
                    "job_name": "felix-monitoring",
                    "static_configs": [
                        {
                            "targets": ["localhost:8000"],
                            "labels": {
                                "service": "felix-automation",
                                "environment": "production"
                            }
                        }
                    ],
                    "metrics_path": "/metrics",
                    "scrape_interval": "15s",
                }
            ]
        }


def get_prometheus_exporter() -> PrometheusExporter:
    """Singleton getter for PrometheusExporter"""
    if not hasattr(get_prometheus_exporter, '_instance'):
        get_prometheus_exporter._instance = PrometheusExporter()
    return get_prometheus_exporter._instance
