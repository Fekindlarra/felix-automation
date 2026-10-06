"""
Metrics Collection System - FASE 14 Production Monitoring
Collects performance metrics, calculates aggregates, and detects anomalies
"""

import logging
import time
import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    LATENCY_MS = "latency_ms"  # Response time
    THROUGHPUT = "throughput"  # Requests per second
    ERROR_RATE = "error_rate"  # Percentage (0-100)
    RESOURCE_USAGE = "resource_usage"  # CPU, memory, disk
    CUSTOM = "custom"  # User-defined


@dataclass
class MetricPoint:
    """Single metric data point"""
    metric_name: str
    metric_type: MetricType
    value: float
    unit: str
    component: str
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'metric_name': self.metric_name,
            'metric_type': self.metric_type.value,
            'value': round(self.value, 2),
            'unit': self.unit,
            'component': self.component,
            'timestamp': self.timestamp,
            'tags': self.tags
        }


@dataclass
class MetricAggregate:
    """Aggregated metric statistics"""
    metric_name: str
    component: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    p50_value: float  # Median
    p95_value: float  # 95th percentile
    p99_value: float  # 99th percentile
    std_dev: float
    time_window_seconds: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'metric_name': self.metric_name,
            'component': self.component,
            'count': self.count,
            'min': round(self.min_value, 2),
            'max': round(self.max_value, 2),
            'avg': round(self.avg_value, 2),
            'p50': round(self.p50_value, 2),
            'p95': round(self.p95_value, 2),
            'p99': round(self.p99_value, 2),
            'std_dev': round(self.std_dev, 2),
            'time_window_seconds': self.time_window_seconds
        }


@dataclass
class AnomalyDetection:
    """Detected anomaly in metrics"""
    metric_name: str
    component: str
    anomaly_type: str  # "spike", "drop", "sustained_high", "sustained_low"
    current_value: float
    baseline_value: float
    deviation_percent: float
    severity: str  # "minor", "significant", "critical"
    timestamp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'metric_name': self.metric_name,
            'component': self.component,
            'anomaly_type': self.anomaly_type,
            'current_value': round(self.current_value, 2),
            'baseline_value': round(self.baseline_value, 2),
            'deviation_percent': round(self.deviation_percent, 1),
            'severity': self.severity,
            'timestamp': self.timestamp
        }


class MetricsCollector:
    """Comprehensive metrics collection and analysis system"""

    def __init__(self, database_path: str = "database.sqlite", config: Dict = None):
        """
        Initialize metrics collector

        Args:
            database_path: Path to SQLite database
            config: Configuration dictionary with thresholds
        """
        self.database_path = database_path
        self.config = config or {}

        # In-memory metric storage (rolling window)
        self.metric_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.baselines: Dict[str, Dict[str, float]] = {}  # Baseline values for anomaly detection
        self.anomalies: List[AnomalyDetection] = []

        # Thresholds
        self.anomaly_deviation_threshold = self.config.get('anomaly_deviation_threshold', 30)  # %
        self.spike_threshold = self.config.get('spike_threshold', 50)  # % above baseline
        self.buffer_flush_interval = self.config.get('buffer_flush_interval', 300)  # 5 minutes
        self.baseline_window = self.config.get('baseline_window', 3600)  # 1 hour
        self.last_flush = time.time()

    def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: MetricType = MetricType.CUSTOM,
        unit: str = "",
        component: str = "",
        tags: Dict[str, str] = None
    ) -> str:
        """
        Record a metric point

        Args:
            metric_name: Name of the metric
            value: Metric value
            metric_type: Type of metric
            unit: Unit of measurement
            component: Component generating metric
            tags: Additional tags for filtering

        Returns:
            Metric ID
        """
        timestamp = datetime.utcnow().isoformat()
        metric_id = f"{metric_name}_{int(time.time() * 1000)}"

        metric = MetricPoint(
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            component=component,
            timestamp=timestamp,
            tags=tags or {}
        )

        # Store in buffer
        key = f"{component}:{metric_name}"
        self.metric_buffer[key].append(metric)

        # Detect anomalies
        self._detect_anomaly(metric)

        # Auto-flush if needed
        total_metrics = sum(len(v) for v in self.metric_buffer.values())
        if total_metrics > 50000 or (time.time() - self.last_flush) > self.buffer_flush_interval:
            self.flush_to_database()

        return metric_id

    def _detect_anomaly(self, metric: MetricPoint) -> Optional[AnomalyDetection]:
        """Detect anomalies in metric data"""
        key = f"{metric.component}:{metric.metric_name}"

        # Calculate baseline if not exists
        if key not in self.baselines:
            self._calculate_baseline(key)
            return None

        baseline = self.baselines[key].get('value')
        if baseline is None or baseline == 0:
            return None

        # Calculate deviation
        deviation_percent = abs(value := metric.value - baseline) / baseline * 100

        # Check for anomaly
        if deviation_percent > self.anomaly_deviation_threshold:
            # Determine type
            if metric.value > baseline * 1.5:
                anomaly_type = "spike"
                severity = "significant" if deviation_percent > 100 else "minor"
            elif metric.value < baseline * 0.5:
                anomaly_type = "drop"
                severity = "significant" if deviation_percent > 100 else "minor"
            else:
                anomaly_type = "sustained_high" if metric.value > baseline else "sustained_low"
                severity = "critical" if deviation_percent > 200 else "significant"

            anomaly = AnomalyDetection(
                metric_name=metric.metric_name,
                component=metric.component,
                anomaly_type=anomaly_type,
                current_value=metric.value,
                baseline_value=baseline,
                deviation_percent=deviation_percent,
                severity=severity,
                timestamp=metric.timestamp
            )

            self.anomalies.append(anomaly)

            # Keep history limited
            if len(self.anomalies) > 1000:
                self.anomalies = self.anomalies[-1000:]

            logger.warning(f"Anomaly detected: {metric.metric_name} = {metric.value} ({anomaly_type})")
            return anomaly

        return None

    def _calculate_baseline(self, key: str):
        """Calculate baseline for a metric"""
        if key not in self.metric_buffer or len(self.metric_buffer[key]) < 10:
            self.baselines[key] = {'value': None, 'updated_at': datetime.utcnow().isoformat()}
            return

        # Use average of recent values
        recent_points = list(self.metric_buffer[key])[-100:]
        values = [p.value for p in recent_points]

        # Remove outliers (values > 2 std devs)
        if len(values) > 5:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            values = [v for v in values if abs(v - mean) <= 2 * stdev]

        baseline_value = statistics.mean(values) if values else None

        self.baselines[key] = {
            'value': baseline_value,
            'count': len(values),
            'updated_at': datetime.utcnow().isoformat()
        }

    def get_aggregate(self, metric_name: str, component: str, seconds: int = 300) -> Optional[MetricAggregate]:
        """Get aggregated statistics for a metric"""
        key = f"{component}:{metric_name}"

        if key not in self.metric_buffer:
            return None

        # Filter by time window
        cutoff_time = datetime.utcnow() - timedelta(seconds=seconds)
        recent_points = [
            p for p in self.metric_buffer[key]
            if datetime.fromisoformat(p.timestamp) > cutoff_time
        ]

        if not recent_points:
            return None

        values = [p.value for p in recent_points]
        values_sorted = sorted(values)

        try:
            std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        except:
            std_dev = 0.0

        return MetricAggregate(
            metric_name=metric_name,
            component=component,
            count=len(values),
            min_value=min(values),
            max_value=max(values),
            avg_value=statistics.mean(values),
            p50_value=statistics.median(values),
            p95_value=values_sorted[int(len(values_sorted) * 0.95)] if len(values_sorted) > 1 else values[0],
            p99_value=values_sorted[int(len(values_sorted) * 0.99)] if len(values_sorted) > 1 else values[0],
            std_dev=std_dev,
            time_window_seconds=seconds
        )

    def get_anomalies(self, hours: int = 24) -> List[AnomalyDetection]:
        """Get anomalies detected in time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            a for a in self.anomalies
            if datetime.fromisoformat(a.timestamp) > cutoff_time
        ]

    def get_component_health(self, component: str, seconds: int = 300) -> Dict[str, Any]:
        """Get overall health metrics for a component"""
        # Find all metrics for this component
        component_metrics = [
            (metric_name.split(':')[1], component)
            for metric_name in self.metric_buffer.keys()
            if metric_name.startswith(f"{component}:")
        ]

        if not component_metrics:
            return {'status': 'unknown', 'metrics': []}

        aggregates = []
        for metric_name, _ in component_metrics:
            agg = self.get_aggregate(metric_name, component, seconds)
            if agg:
                aggregates.append(agg)

        # Detect if any metrics are concerning
        has_anomalies = any(
            a.component == component
            for a in self.get_anomalies(hours=1)
        )

        status = "anomalies_detected" if has_anomalies else "normal"

        return {
            'component': component,
            'status': status,
            'metrics': [a.to_dict() for a in aggregates],
            'timestamp': datetime.utcnow().isoformat()
        }

    def flush_to_database(self) -> int:
        """Flush buffered metrics to database"""
        total_flushed = 0

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            for key, metrics in self.metric_buffer.items():
                for metric in metrics:
                    try:
                        cursor.execute("""
                            INSERT INTO metrics_log (
                                metric_name, metric_type, value, unit,
                                component, tags_json, timestamp
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            metric.metric_name,
                            metric.metric_type.value,
                            metric.value,
                            metric.unit,
                            metric.component,
                            json.dumps(metric.tags),
                            metric.timestamp
                        ))
                        total_flushed += 1
                    except Exception as e:
                        logger.error(f"Error inserting metric: {e}")

            # Flush anomalies
            for anomaly in self.anomalies:
                try:
                    cursor.execute("""
                        INSERT INTO anomalies_log (
                            metric_name, component, anomaly_type,
                            current_value, baseline_value, deviation_percent,
                            severity, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        anomaly.metric_name,
                        anomaly.component,
                        anomaly.anomaly_type,
                        anomaly.current_value,
                        anomaly.baseline_value,
                        anomaly.deviation_percent,
                        anomaly.severity,
                        anomaly.timestamp
                    ))
                except Exception as e:
                    logger.error(f"Error inserting anomaly: {e}")

            conn.commit()
            conn.close()

            # Clear buffers (but keep one window for baseline)
            for key in self.metric_buffer:
                # Keep last 500 for baseline calculation
                if len(self.metric_buffer[key]) > 500:
                    self.metric_buffer[key] = deque(
                        list(self.metric_buffer[key])[-500:],
                        maxlen=10000
                    )

            self.last_flush = time.time()
            logger.info(f"Flushed {total_flushed} metrics to database")

        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")

        return total_flushed

    def get_metric_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get summary of all metrics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        all_metrics = []

        for key, metrics in self.metric_buffer.items():
            for metric in metrics:
                if datetime.fromisoformat(metric.timestamp) > cutoff_time:
                    all_metrics.append(metric)

        # Group by component
        by_component = defaultdict(list)
        for metric in all_metrics:
            by_component[metric.component].append(metric)

        return {
            'total_metrics_recorded': len(all_metrics),
            'components': len(by_component),
            'by_component': {
                comp: len(metrics) for comp, metrics in by_component.items()
            },
            'anomalies_in_period': len(self.get_anomalies(hours=hours)),
            'time_window_hours': hours
        }


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(database_path: str = "database.sqlite", config: Dict = None) -> MetricsCollector:
    """Get or create global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(database_path, config)
    return _metrics_collector


# Convenience functions
def record_latency(component: str, latency_ms: float, operation: str = "") -> str:
    """Record operation latency"""
    collector = get_metrics_collector()
    return collector.record_metric(
        metric_name=f"latency_{operation}" if operation else "latency",
        value=latency_ms,
        metric_type=MetricType.LATENCY_MS,
        unit="ms",
        component=component
    )


def record_throughput(component: str, requests_per_sec: float, endpoint: str = "") -> str:
    """Record throughput"""
    collector = get_metrics_collector()
    return collector.record_metric(
        metric_name=f"throughput_{endpoint}" if endpoint else "throughput",
        value=requests_per_sec,
        metric_type=MetricType.THROUGHPUT,
        unit="req/s",
        component=component
    )


def record_error_rate(component: str, error_percent: float) -> str:
    """Record error rate"""
    collector = get_metrics_collector()
    return collector.record_metric(
        metric_name="error_rate",
        value=error_percent,
        metric_type=MetricType.ERROR_RATE,
        unit="%",
        component=component
    )


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    collector = MetricsCollector("database.sqlite")

    # Record some example metrics
    for i in range(100):
        collector.record_metric(
            metric_name="api_latency",
            value=50 + (i % 30),
            metric_type=MetricType.LATENCY_MS,
            unit="ms",
            component="api_server"
        )

    # Get aggregate
    agg = collector.get_aggregate("api_latency", "api_server", seconds=300)
    if agg:
        print("\n" + "="*60)
        print("METRICS AGGREGATE")
        print("="*60)
        print(json.dumps(agg.to_dict(), indent=2))

    # Get summary
    summary = collector.get_metric_summary(hours=1)
    print("\n" + "="*60)
    print("METRICS SUMMARY")
    print("="*60)
    print(json.dumps(summary, indent=2))
