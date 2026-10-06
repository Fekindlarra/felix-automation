"""
Error Tracking System - FASE 14 Production Monitoring
Aggregates, tracks, and analyzes system errors with automatic severity detection
"""

import logging
import time
import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import traceback

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    DATABASE = "database"
    API = "api"
    SHOPIFY = "shopify"
    PREDICTIONS = "predictions"
    AB_TESTING = "ab_testing"
    WEBSOCKET = "websocket"
    AUTH = "auth"
    VALIDATION = "validation"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Single error record"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    error_type: str  # e.g., "ValueError", "ConnectionError"
    stack_trace: str
    context: Dict[str, Any] = field(default_factory=dict)
    component: str = ""
    timestamp: str = ""
    resolved: bool = False
    resolution_notes: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'error_id': self.error_id,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'error_type': self.error_type,
            'stack_trace': self.stack_trace,
            'context': self.context,
            'component': self.component,
            'timestamp': self.timestamp,
            'resolved': self.resolved,
            'resolution_notes': self.resolution_notes
        }


@dataclass
class ErrorAggregate:
    """Aggregated error statistics"""
    category: ErrorCategory
    severity: ErrorSeverity
    error_type: str
    count: int
    first_occurrence: str
    last_occurrence: str
    avg_frequency_per_hour: float
    is_recurring: bool
    trend: str  # "increasing", "decreasing", "stable"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'error_type': self.error_type,
            'count': self.count,
            'first_occurrence': self.first_occurrence,
            'last_occurrence': self.last_occurrence,
            'avg_frequency_per_hour': round(self.avg_frequency_per_hour, 2),
            'is_recurring': self.is_recurring,
            'trend': self.trend
        }


class ErrorTracker:
    """Comprehensive error tracking and analysis system"""

    def __init__(self, database_path: str = "database.sqlite", config: Dict = None):
        """
        Initialize error tracker

        Args:
            database_path: Path to SQLite database
            config: Configuration dictionary with thresholds
        """
        self.database_path = database_path
        self.config = config or {}
        self.error_buffer: List[ErrorRecord] = []
        self.error_history: List[ErrorRecord] = []
        self.aggregates: Dict[str, ErrorAggregate] = {}

        # Thresholds
        self.critical_error_threshold = self.config.get('critical_error_threshold', 5)  # Errors/hour
        self.recurring_threshold = self.config.get('recurring_threshold', 3)  # Same error N times
        self.buffer_flush_interval = self.config.get('buffer_flush_interval', 60)  # seconds
        self.last_flush = time.time()

    def record_error(
        self,
        category: ErrorCategory,
        severity: ErrorSeverity,
        message: str,
        error_type: str,
        component: str = "",
        context: Dict[str, Any] = None,
        stack_trace: str = ""
    ) -> str:
        """
        Record an error

        Args:
            category: Error category
            severity: Error severity level
            message: Error message
            error_type: Exception type (e.g., "ValueError")
            component: Component that generated the error
            context: Additional context data
            stack_trace: Full stack trace

        Returns:
            Error ID
        """
        error_id = f"{int(time.time() * 1000)}"
        timestamp = datetime.utcnow().isoformat()

        error = ErrorRecord(
            error_id=error_id,
            category=category,
            severity=severity,
            message=message,
            error_type=error_type,
            component=component,
            context=context or {},
            stack_trace=stack_trace,
            timestamp=timestamp
        )

        self.error_buffer.append(error)
        self.error_history.append(error)

        # Keep history limited
        if len(self.error_history) > 10000:
            self.error_history = self.error_history[-10000:]

        # Log locally
        logger.log(
            getattr(logging, severity.value.upper(), logging.INFO),
            f"[{component}] {error_type}: {message}"
        )

        # Auto-flush if buffer growing
        if len(self.error_buffer) > 100 or \
           (time.time() - self.last_flush) > self.buffer_flush_interval:
            self.flush_to_database()

        return error_id

    def record_exception(
        self,
        exception: Exception,
        category: ErrorCategory,
        component: str = "",
        context: Dict[str, Any] = None
    ) -> str:
        """
        Record an exception with automatic stack trace extraction

        Args:
            exception: The exception object
            category: Error category
            component: Component name
            context: Additional context

        Returns:
            Error ID
        """
        severity = self._determine_severity_from_exception(exception)
        stack_trace = traceback.format_exc()

        return self.record_error(
            category=category,
            severity=severity,
            message=str(exception),
            error_type=exception.__class__.__name__,
            component=component,
            context=context,
            stack_trace=stack_trace
        )

    def _determine_severity_from_exception(self, exception: Exception) -> ErrorSeverity:
        """Auto-determine severity from exception type"""
        exception_type = exception.__class__.__name__

        # Critical
        if exception_type in ['SystemExit', 'MemoryError', 'DatabaseLockedError']:
            return ErrorSeverity.CRITICAL

        # Error
        if exception_type in ['ValueError', 'TypeError', 'KeyError', 'ConnectionError',
                             'TimeoutError', 'HTTPError', 'DatabaseError']:
            return ErrorSeverity.ERROR

        # Warning
        return ErrorSeverity.WARNING

    def flush_to_database(self) -> int:
        """Flush buffered errors to database"""
        if not self.error_buffer:
            return 0

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            for error in self.error_buffer:
                cursor.execute("""
                    INSERT INTO error_log (
                        error_id, category, severity, message, error_type,
                        component, stack_trace, context_json, timestamp, resolved
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    error.error_id,
                    error.category.value,
                    error.severity.value,
                    error.message,
                    error.error_type,
                    error.component,
                    error.stack_trace,
                    json.dumps(error.context),
                    error.timestamp,
                    0
                ))

            conn.commit()
            conn.close()

            flushed_count = len(self.error_buffer)
            self.error_buffer = []
            self.last_flush = time.time()

            logger.info(f"Flushed {flushed_count} errors to database")
            return flushed_count

        except Exception as e:
            logger.error(f"Failed to flush errors to database: {e}")
            return 0

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            e for e in self.error_history
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]

        if not recent_errors:
            return {
                'total_errors': 0,
                'by_severity': {},
                'by_category': {},
                'critical_count': 0,
                'is_critical': False
            }

        # Count by severity
        by_severity = defaultdict(int)
        for error in recent_errors:
            by_severity[error.severity.value] += 1

        # Count by category
        by_category = defaultdict(int)
        for error in recent_errors:
            by_category[error.category.value] += 1

        critical_count = len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL])
        is_critical = critical_count > 0 or by_severity['error'] > self.critical_error_threshold

        return {
            'total_errors': len(recent_errors),
            'by_severity': dict(by_severity),
            'by_category': dict(by_category),
            'critical_count': critical_count,
            'is_critical': is_critical,
            'hours_covered': hours
        }

    def get_aggregates(self, hours: int = 24) -> List[ErrorAggregate]:
        """Get aggregated error statistics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            e for e in self.error_history
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]

        if not recent_errors:
            return []

        # Group by (category, severity, error_type)
        groups = defaultdict(list)
        for error in recent_errors:
            key = (error.category, error.severity, error.error_type)
            groups[key].append(error)

        aggregates = []
        for (category, severity, error_type), errors in groups.items():
            if len(errors) >= self.recurring_threshold:
                times = [datetime.fromisoformat(e.timestamp) for e in errors]
                first = min(times)
                last = max(times)
                duration_hours = (last - first).total_seconds() / 3600
                avg_freq = len(errors) / max(duration_hours, 1)

                # Determine trend
                if len(errors) >= 3:
                    recent_third = len([e for e in errors if datetime.fromisoformat(e.timestamp) > last - timedelta(hours=duration_hours/3)])
                    older_third = len([e for e in errors if datetime.fromisoformat(e.timestamp) < first + timedelta(hours=duration_hours/3)])
                    if recent_third > older_third * 1.2:
                        trend = "increasing"
                    elif recent_third < older_third * 0.8:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"

                aggregate = ErrorAggregate(
                    category=category,
                    severity=severity,
                    error_type=error_type,
                    count=len(errors),
                    first_occurrence=first.isoformat(),
                    last_occurrence=last.isoformat(),
                    avg_frequency_per_hour=avg_freq,
                    is_recurring=True,
                    trend=trend
                )
                aggregates.append(aggregate)

        # Sort by severity then count
        severity_order = {ErrorSeverity.CRITICAL: 0, ErrorSeverity.ERROR: 1, ErrorSeverity.WARNING: 2, ErrorSeverity.INFO: 3}
        aggregates.sort(
            key=lambda x: (severity_order.get(x.severity, 4), -x.count)
        )

        return aggregates

    def resolve_error(self, error_id: str, resolution_notes: str = ""):
        """Mark error as resolved"""
        for error in self.error_history:
            if error.error_id == error_id:
                error.resolved = True
                error.resolution_notes = resolution_notes
                break

        # Also update in database
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE error_log SET resolved=1, resolution_notes=?
                WHERE error_id=?
            """, (resolution_notes, error_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update error resolution: {e}")

    def get_error_by_id(self, error_id: str) -> Optional[ErrorRecord]:
        """Get specific error"""
        for error in self.error_history:
            if error.error_id == error_id:
                return error
        return None

    def get_errors_by_component(self, component: str, hours: int = 24) -> List[ErrorRecord]:
        """Get all errors from specific component"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            e for e in self.error_history
            if e.component == component and
            datetime.fromisoformat(e.timestamp) > cutoff_time
        ]

    def get_critical_errors(self, hours: int = 1) -> List[ErrorRecord]:
        """Get all critical errors in time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            e for e in self.error_history
            if e.severity == ErrorSeverity.CRITICAL and
            datetime.fromisoformat(e.timestamp) > cutoff_time
        ]


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None


def get_error_tracker(database_path: str = "database.sqlite", config: Dict = None) -> ErrorTracker:
    """Get or create global error tracker"""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker(database_path, config)
    return _error_tracker


# Convenience functions for quick error recording
def log_error(
    category: ErrorCategory,
    message: str,
    component: str = "",
    context: Dict = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR
) -> str:
    """Convenience function to log an error"""
    tracker = get_error_tracker()
    return tracker.record_error(
        category=category,
        severity=severity,
        message=message,
        error_type="LoggedError",
        component=component,
        context=context
    )


def log_exception(exception: Exception, category: ErrorCategory, component: str = "", context: Dict = None) -> str:
    """Convenience function to log an exception"""
    tracker = get_error_tracker()
    return tracker.record_exception(exception, category, component, context)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    tracker = ErrorTracker("database.sqlite")

    # Record some example errors
    tracker.record_error(
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        message="Connection timeout to database",
        error_type="ConnectionError",
        component="database_module",
        context={'retry_count': 3, 'timeout_seconds': 30}
    )

    tracker.record_error(
        category=ErrorCategory.API,
        severity=ErrorSeverity.WARNING,
        message="Rate limit approaching",
        error_type="RateLimitWarning",
        component="shopify_client",
        context={'requests_remaining': 5, 'reset_time': '2026-10-06T20:00:00'}
    )

    # Get summary
    summary = tracker.get_error_summary(hours=24)
    print("\n" + "="*60)
    print("ERROR TRACKING SUMMARY")
    print("="*60)
    print(json.dumps(summary, indent=2))

    # Get aggregates
    aggregates = tracker.get_aggregates(hours=24)
    print("\n" + "="*60)
    print("RECURRING ERRORS")
    print("="*60)
    for agg in aggregates:
        print(f"\n{agg.category.value} - {agg.error_type}")
        print(f"  Severity: {agg.severity.value}")
        print(f"  Count: {agg.count}")
        print(f"  Trend: {agg.trend}")
        print(f"  Avg Frequency: {agg.avg_frequency_per_hour:.2f} errors/hour")

    # Flush to database
    tracker.flush_to_database()
