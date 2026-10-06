"""
Production Monitoring & Health Checks - FASE 14
Real-time metrics collection, alerting, and health dashboard
"""

import time
import threading
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
from collections import deque
import statistics


class MetricType(Enum):
    """Metric types for monitoring"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """Single health metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: str
    unit: str = ""
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


@dataclass
class Alert:
    """Alert/notification structure"""
    id: str
    severity: AlertSeverity
    title: str
    description: str
    metric_name: str
    threshold: float
    current_value: float
    timestamp: str
    resolved: bool = False
    resolution_timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "current_value": self.current_value,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "resolution_timestamp": self.resolution_timestamp
        }


class MetricsCollector:
    """Real-time metrics collection and aggregation"""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector
        
        Args:
            max_history: Maximum number of data points to keep per metric
        """
        self.max_history = max_history
        self.metrics: Dict[str, deque] = {}
        self.lock = threading.Lock()
    
    def record(self, metric: HealthMetric):
        """Record a metric data point"""
        with self.lock:
            if metric.name not in self.metrics:
                self.metrics[metric.name] = deque(maxlen=self.max_history)
            self.metrics[metric.name].append(metric)
    
    def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[HealthMetric]:
        """
        Get metric history for last N minutes

        Args:
            metric_name: Name of the metric
            minutes: How many minutes back to retrieve

        Returns:
            List of metric data points
        """
        with self.lock:
            if metric_name not in self.metrics:
                return []

            # Use timezone-aware datetime for comparison
            from datetime import timezone
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            history = []

            for metric in self.metrics[metric_name]:
                metric_time = datetime.fromisoformat(metric.timestamp.replace("Z", "+00:00"))
                if metric_time >= cutoff_time:
                    history.append(metric)

            return history
    
    def get_latest(self, metric_name: str) -> Optional[HealthMetric]:
        """Get latest value for a metric"""
        with self.lock:
            if metric_name in self.metrics and len(self.metrics[metric_name]) > 0:
                return self.metrics[metric_name][-1]
            return None
    
    def get_stats(self, metric_name: str, minutes: int = 60) -> Dict[str, float]:
        """
        Get statistics for a metric over time period
        
        Args:
            metric_name: Name of the metric
            minutes: Time window in minutes
            
        Returns:
            Dictionary with min, max, avg, p95, p99
        """
        history = self.get_metric_history(metric_name, minutes)
        
        if not history:
            return {
                "min": 0,
                "max": 0,
                "avg": 0,
                "p95": 0,
                "p99": 0,
                "count": 0
            }
        
        values = [m.value for m in history]
        values_sorted = sorted(values)
        
        return {
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "p95": values_sorted[int(len(values_sorted) * 0.95)] if len(values_sorted) > 1 else values[0],
            "p99": values_sorted[int(len(values_sorted) * 0.99)] if len(values_sorted) > 1 else values[0],
            "count": len(values)
        }


class HealthChecker:
    """System health checking and monitoring"""
    
    def __init__(self, metrics: MetricsCollector):
        """Initialize health checker"""
        self.metrics = metrics
        self.checks: Dict[str, Dict[str, Any]] = {
            "websocket_latency": {
                "threshold": 100,  # ms
                "unit": "ms",
                "critical": 200,
                "description": "WebSocket event latency"
            },
            "api_response_time": {
                "threshold": 500,  # ms
                "unit": "ms",
                "critical": 1000,
                "description": "API response time"
            },
            "cache_hit_rate": {
                "threshold": 0.85,  # 85%
                "unit": "%",
                "critical": 0.70,
                "description": "Service worker cache hit rate"
            },
            "websocket_connections": {
                "threshold": 100,  # max concurrent
                "unit": "connections",
                "critical": 200,
                "description": "Concurrent WebSocket connections"
            },
            "prediction_generation_time": {
                "threshold": 50,  # ms
                "unit": "ms",
                "critical": 100,
                "description": "ML prediction generation time"
            },
            "database_connection_pool": {
                "threshold": 0.8,  # 80% utilization
                "unit": "ratio",
                "critical": 0.95,
                "description": "Database connection pool utilization"
            },
            "error_rate": {
                "threshold": 0.01,  # 1%
                "unit": "%",
                "critical": 0.05,
                "description": "Request error rate"
            },
            "offline_users": {
                "threshold": 0.1,  # 10% of users
                "unit": "ratio",
                "critical": 0.3,
                "description": "Users in offline mode"
            }
        }
        self.alerts: Dict[str, Alert] = {}
        self.alert_lock = threading.Lock()
    
    def evaluate_health(self) -> Dict[str, Any]:
        """
        Evaluate overall system health
        
        Returns:
            Health status dictionary with all metrics
        """
        health_status = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "overall_status": "healthy",
            "metrics": {},
            "alerts": [],
            "recommendations": []
        }
        
        for check_name, check_config in self.checks.items():
            latest_metric = self.metrics.get_latest(check_name)
            
            if latest_metric is None:
                health_status["metrics"][check_name] = {
                    "status": "unknown",
                    "message": "No data collected yet"
                }
                continue
            
            value = latest_metric.value
            threshold = check_config["threshold"]
            critical = check_config["critical"]
            
            # Determine status based on check type
            # For cache hit rate and ratios, higher is better
            if check_name in ["cache_hit_rate", "offline_users"]:
                if value < critical:
                    status = "critical"
                    health_status["overall_status"] = "unhealthy"
                elif value < threshold:
                    status = "warning"
                    if health_status["overall_status"] != "unhealthy":
                        health_status["overall_status"] = "degraded"
                else:
                    status = "healthy"
            # For latencies and error rates, lower is better
            else:
                if value > critical:
                    status = "critical"
                    health_status["overall_status"] = "unhealthy"
                elif value > threshold:
                    status = "warning"
                    if health_status["overall_status"] != "unhealthy":
                        health_status["overall_status"] = "degraded"
                else:
                    status = "healthy"
            
            stats = self.metrics.get_stats(check_name, minutes=60)
            
            health_status["metrics"][check_name] = {
                "status": status,
                "current_value": value,
                "unit": check_config["unit"],
                "threshold": threshold,
                "critical_threshold": critical,
                "description": check_config["description"],
                "stats_60m": stats
            }
            
            # Create alert if status is warning or critical
            if status in ["warning", "critical"]:
                severity = AlertSeverity.CRITICAL if status == "critical" else AlertSeverity.WARNING
                alert_id = f"{check_name}_{int(time.time())}"
                
                alert = Alert(
                    id=alert_id,
                    severity=severity,
                    title=f"{check_name.replace('_', ' ').title()} Alert",
                    description=f"{check_config['description']}: {value} {check_config['unit']}",
                    metric_name=check_name,
                    threshold=threshold,
                    current_value=value,
                    timestamp=datetime.utcnow().isoformat() + "Z"
                )
                
                self._add_alert(alert)
                health_status["alerts"].append(alert.to_dict())
                
                # Add recommendation
                if check_name == "websocket_latency":
                    health_status["recommendations"].append(
                        "Consider scaling WebSocket server or optimizing event processing"
                    )
                elif check_name == "cache_hit_rate":
                    health_status["recommendations"].append(
                        "Review cache strategy; consider pre-caching more assets"
                    )
                elif check_name == "error_rate":
                    health_status["recommendations"].append(
                        "Review application logs for error patterns"
                    )
        
        return health_status
    
    def _add_alert(self, alert: Alert):
        """Add a new alert"""
        with self.alert_lock:
            self.alerts[alert.id] = alert
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        with self.alert_lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].resolved = True
                self.alerts[alert_id].resolution_timestamp = datetime.utcnow().isoformat() + "Z"
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active (unresolved) alerts"""
        with self.alert_lock:
            return [
                alert.to_dict() for alert in self.alerts.values()
                if not alert.resolved
            ]


class PerformanceProfiler:
    """Performance profiling for critical operations"""
    
    def __init__(self, metrics: MetricsCollector):
        """Initialize performance profiler"""
        self.metrics = metrics
        self.timers: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
    
    def start_timer(self, operation_name: str) -> 'Timer':
        """Start a timer for an operation"""
        return Timer(self, operation_name)

    def profile(self, operation_name: str) -> 'Timer':
        """Alias for start_timer - convenience method for context manager usage"""
        return self.start_timer(operation_name)

    def record_time(self, operation_name: str, duration_ms: float):
        """Record operation timing"""
        with self.lock:
            if operation_name not in self.timers:
                self.timers[operation_name] = []
            self.timers[operation_name].append(duration_ms)
        
        # Record as metric
        metric = HealthMetric(
            name=operation_name,
            value=duration_ms,
            metric_type=MetricType.TIMER,
            timestamp=datetime.utcnow().isoformat() + "Z",
            unit="ms",
            labels={"operation": operation_name}
        )
        self.metrics.record(metric)
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, float]:
        """Get statistics for an operation"""
        return self.metrics.get_stats(operation_name, minutes=60)


class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, profiler: PerformanceProfiler, operation_name: str):
        """Initialize timer"""
        self.profiler = profiler
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record"""
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.profiler.record_time(self.operation_name, duration_ms)


class MonitoringDashboard:
    """In-memory dashboard for monitoring data"""
    
    def __init__(self, metrics: MetricsCollector, health_checker: HealthChecker):
        """Initialize dashboard"""
        self.metrics = metrics
        self.health_checker = health_checker
        self.last_dashboard_update = None
        self.dashboard_cache = {}
    
    def get_dashboard_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data
        
        Args:
            force_refresh: Force recalculation instead of using cache
            
        Returns:
            Dashboard data dictionary
        """
        now = time.time()
        
        # Use cache if available and fresh (< 5 seconds old)
        if (not force_refresh and 
            self.last_dashboard_update and 
            now - self.last_dashboard_update < 5):
            return self.dashboard_cache
        
        # Evaluate health
        health_status = self.health_checker.evaluate_health()
        
        # Get key metrics
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "health": health_status,
            "websocket_metrics": {
                "current_latency": self._get_metric_value("websocket_latency"),
                "latency_stats": self.metrics.get_stats("websocket_latency", minutes=60),
                "active_connections": self._get_metric_value("websocket_connections"),
                "connection_history": [
                    m.value for m in self.metrics.get_metric_history("websocket_connections", minutes=60)
                ]
            },
            "cache_metrics": {
                "hit_rate": self._get_metric_value("cache_hit_rate"),
                "hit_rate_history": [
                    m.value for m in self.metrics.get_metric_history("cache_hit_rate", minutes=60)
                ]
            },
            "api_metrics": {
                "response_time": self._get_metric_value("api_response_time"),
                "response_time_stats": self.metrics.get_stats("api_response_time", minutes=60),
                "error_rate": self._get_metric_value("error_rate"),
                "error_rate_history": [
                    m.value for m in self.metrics.get_metric_history("error_rate", minutes=60)
                ]
            },
            "ml_metrics": {
                "prediction_generation_time": self._get_metric_value("prediction_generation_time"),
                "prediction_stats": self.metrics.get_stats("prediction_generation_time", minutes=60)
            },
            "database_metrics": {
                "connection_pool_utilization": self._get_metric_value("database_connection_pool"),
                "pool_history": [
                    m.value for m in self.metrics.get_metric_history("database_connection_pool", minutes=60)
                ]
            },
            "alerts": self.health_checker.get_active_alerts()
        }
        
        # Update cache
        self.dashboard_cache = dashboard_data
        self.last_dashboard_update = now
        
        return dashboard_data
    
    def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """Get latest value for a metric"""
        metric = self.metrics.get_latest(metric_name)
        return metric.value if metric else None


# Global instances
_metrics_collector = None
_health_checker = None
_performance_profiler = None
_monitoring_dashboard = None


def initialize_monitoring():
    """Initialize global monitoring instances"""
    global _metrics_collector, _health_checker, _performance_profiler, _monitoring_dashboard
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(max_history=1000)
        _health_checker = HealthChecker(_metrics_collector)
        _performance_profiler = PerformanceProfiler(_metrics_collector)
        _monitoring_dashboard = MonitoringDashboard(_metrics_collector, _health_checker)


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        initialize_monitoring()
    return _metrics_collector


def get_health_checker() -> HealthChecker:
    """Get global health checker"""
    global _health_checker
    if _health_checker is None:
        initialize_monitoring()
    return _health_checker


def get_performance_profiler() -> PerformanceProfiler:
    """Get global performance profiler"""
    global _performance_profiler
    if _performance_profiler is None:
        initialize_monitoring()
    return _performance_profiler


def get_monitoring_dashboard() -> MonitoringDashboard:
    """Get global monitoring dashboard"""
    global _monitoring_dashboard
    if _monitoring_dashboard is None:
        initialize_monitoring()
    return _monitoring_dashboard
