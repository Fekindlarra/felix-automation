#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Production Hardening & Final Optimizations
Ensures all endpoints are secure, optimized, and production-ready
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Any
import time

logger = logging.getLogger(__name__)

# =============================================================================
# Rate Limiting for Critical Endpoints
# =============================================================================

class RateLimiter:
    """Rate limiter for critical Phase 3 endpoints"""

    def __init__(self, max_calls: int = 10, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = {}  # {endpoint: [(timestamp, count)]}

    def is_allowed(self, endpoint: str) -> bool:
        """Check if endpoint call is within rate limit"""
        now = time.time()

        if endpoint not in self.calls:
            self.calls[endpoint] = []

        # Remove old calls outside time window
        self.calls[endpoint] = [
            ts for ts in self.calls[endpoint]
            if now - ts < self.time_window
        ]

        # Check if under limit
        if len(self.calls[endpoint]) < self.max_calls:
            self.calls[endpoint].append(now)
            return True

        return False

# Global rate limiters for critical endpoints
phase3_activate_limiter = RateLimiter(max_calls=1, time_window=3600)  # 1 per hour
phase3_deactivate_limiter = RateLimiter(max_calls=2, time_window=300)  # 2 per 5 min
kill_switch_limiter = RateLimiter(max_calls=5, time_window=60)  # 5 per minute

def rate_limit(limiter: RateLimiter) -> Callable:
    """Decorator for rate limiting endpoints"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            endpoint_name = func.__name__
            if not limiter.is_allowed(endpoint_name):
                logger.warning(f"⚠️ Rate limit exceeded for {endpoint_name}")
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,  # Too Many Requests
                    detail=f"Rate limit exceeded for {endpoint_name}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# =============================================================================
# Input Validation & Sanitization
# =============================================================================

class InputValidator:
    """Validate and sanitize admin inputs"""

    @staticmethod
    def validate_reason(reason: str = None) -> str:
        """Validate admin action reason"""
        if reason is None:
            return "Auto-triggered by system"

        reason = str(reason).strip()
        if len(reason) > 500:
            reason = reason[:500]

        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
        for char in dangerous_chars:
            reason = reason.replace(char, '')

        return reason

    @staticmethod
    def validate_notify_slack(notify: bool = True) -> bool:
        """Validate Slack notification flag"""
        return bool(notify)

# =============================================================================
# Database Optimization - Indexing
# =============================================================================

def create_phase3_indexes(db_path: str = "fase15.db") -> bool:
    """Create indexes on Phase 3 critical tables for performance"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        indexes_to_create = [
            # ab_tests table indexes
            ("idx_ab_tests_phase3",
             "CREATE INDEX IF NOT EXISTS idx_ab_tests_phase3 ON ab_tests(phase, active, created_at)"),

            # ab_test_ml_predictions indexes
            ("idx_predictions_test_client",
             "CREATE INDEX IF NOT EXISTS idx_predictions_test_client ON ab_test_ml_predictions(test_id, client_id)"),

            ("idx_predictions_accuracy",
             "CREATE INDEX IF NOT EXISTS idx_predictions_accuracy ON ab_test_ml_predictions(test_id, actual_outcome)"),

            # personalization_variants indexes
            ("idx_personalization_rollout",
             "CREATE INDEX IF NOT EXISTS idx_personalization_rollout ON personalization_variants(test_id, rollout_phase)"),

            ("idx_personalization_client",
             "CREATE INDEX IF NOT EXISTS idx_personalization_client ON personalization_variants(client_id, effective_until)"),

            # system_config indexes
            ("idx_system_config_key",
             "CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(key)"),

            # api_logs indexes for monitoring
            ("idx_api_logs_timestamp",
             "CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_logs(timestamp, status_code)"),
        ]

        created_count = 0
        for index_name, index_sql in indexes_to_create:
            try:
                cursor.execute(index_sql)
                created_count += 1
                logger.info(f"✅ Index created: {index_name}")
            except Exception as e:
                logger.warning(f"⚠️ Index {index_name} already exists or failed: {e}")

        conn.commit()
        conn.close()

        logger.info(f"✅ Phase 3 database optimization complete ({created_count} indexes)")
        return True

    except Exception as e:
        logger.error(f"❌ Database optimization failed: {e}")
        return False

# =============================================================================
# WebSocket Optimization - Message Batching
# =============================================================================

class WebSocketBatcher:
    """Batch WebSocket messages for efficient broadcasting"""

    def __init__(self, batch_size: int = 10, batch_timeout: int = 500):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout  # milliseconds
        self.batch = []
        self.last_flush = time.time()

    def add_message(self, message: dict) -> bool:
        """Add message to batch"""
        self.batch.append(message)

        # Flush if batch is full or timeout exceeded
        now = time.time()
        if len(self.batch) >= self.batch_size or (now - self.last_flush) > (self.batch_timeout / 1000):
            return self.should_flush()

        return False

    def should_flush(self) -> bool:
        """Check if batch should be flushed"""
        return len(self.batch) >= self.batch_size or (time.time() - self.last_flush) > (self.batch_timeout / 1000)

    def get_batch(self) -> list:
        """Get current batch and reset"""
        batch = self.batch.copy()
        self.batch = []
        self.last_flush = time.time()
        return batch

# =============================================================================
# ML Model Caching Optimization
# =============================================================================

class MLModelCache:
    """Optimize ML model loading and caching"""

    _instance = None
    _model = None
    _last_load = None
    _cache_ttl = 3600  # 1 hour

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLModelCache, cls).__new__(cls)
        return cls._instance

    def get_model(self):
        """Get cached ML model with TTL"""
        now = time.time()

        # Check if cache is valid
        if self._model is not None and self._last_load is not None:
            if (now - self._last_load) < self._cache_ttl:
                logger.debug("📊 ML model loaded from cache")
                return self._model

        # Load model (would be actual ML model loading here)
        logger.info("📊 Loading ML model (this would load from disk)")
        self._model = None  # Placeholder
        self._last_load = now

        return self._model

    def invalidate_cache(self):
        """Manually invalidate cache"""
        self._model = None
        self._last_load = None
        logger.info("🔄 ML model cache invalidated")

# =============================================================================
# Production Readiness Validation
# =============================================================================

class ProductionValidator:
    """Validate all components are ready for production"""

    @staticmethod
    def validate_all(db_path: str = "fase15.db") -> dict:
        """Run all production readiness checks"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "all_pass": True
        }

        # Check 1: Database connectivity
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            results["checks"]["database_connectivity"] = "✅ PASS"
        except Exception as e:
            results["checks"]["database_connectivity"] = f"❌ FAIL: {e}"
            results["all_pass"] = False

        # Check 2: Required tables exist
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            required_tables = [
                "ab_tests", "ab_test_ml_predictions", "personalization_variants",
                "system_config", "api_logs"
            ]
            missing = []
            for table in required_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    missing.append(table)
            conn.close()

            if missing:
                results["checks"]["required_tables"] = f"❌ FAIL: Missing {missing}"
                results["all_pass"] = False
            else:
                results["checks"]["required_tables"] = "✅ PASS"
        except Exception as e:
            results["checks"]["required_tables"] = f"❌ FAIL: {e}"
            results["all_pass"] = False

        # Check 3: Phase 3 flag exists in system_config
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_config WHERE key='PHASE_3_ACTIVE'")
            if cursor.fetchone():
                results["checks"]["phase3_flag"] = "✅ PASS"
            else:
                results["checks"]["phase3_flag"] = "⚠️  Flag not set (will be set on activation)"
            conn.close()
        except Exception as e:
            results["checks"]["phase3_flag"] = f"⚠️  {e}"

        # Check 4: Backup directory exists
        import os
        if os.path.exists("data/backups/"):
            results["checks"]["backup_directory"] = "✅ PASS"
        else:
            results["checks"]["backup_directory"] = "❌ FAIL: Missing data/backups/"
            results["all_pass"] = False

        # Check 5: Logs directory exists
        if os.path.exists("logs/phase3/"):
            results["checks"]["logs_directory"] = "✅ PASS"
        else:
            results["checks"]["logs_directory"] = "⚠️  Create logs/phase3/ before activation"

        return results

# =============================================================================
# Execution
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*60)
    print("FASE 15 Phase 3 - Production Hardening")
    print("="*60 + "\n")

    # 1. Create database indexes
    print("📊 Creating database indexes for Phase 3...")
    create_phase3_indexes()

    # 2. Validate production readiness
    print("\n🔍 Running production readiness validation...\n")
    validator = ProductionValidator()
    results = validator.validate_all()

    for check, status in results["checks"].items():
        print(f"  {check:30} {status}")

    print(f"\n{'='*60}")
    if results["all_pass"]:
        print("✅ ALL PRODUCTION READINESS CHECKS PASSED")
    else:
        print("⚠️  SOME CHECKS FAILED - REVIEW ABOVE")
    print("="*60 + "\n")

    logger.info("✅ Production hardening complete")
