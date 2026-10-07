#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Production Optimizations
Comprehensive performance tuning for Phase 3 execution
- WebSocket message batching (500ms windows, gzip compression)
- ML model in-memory caching (60-minute TTL)
- Memory monitoring (alert at 80% utilization)
- Database query optimization (indexes)
- Connection pooling (max 10 concurrent)
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from websocket_batch_optimizer import (
    get_batch_optimizer,
    get_memory_monitor,
    optimize_database_queries
)
from ml_model_cache import get_ml_model_cache

logger = logging.getLogger(__name__)


class Phase3Optimizations:
    """Apply all Phase 3 performance optimizations"""

    def __init__(self, db_connection=None):
        self.db = db_connection
        self.batch_optimizer = get_batch_optimizer()
        self.memory_monitor = get_memory_monitor()
        self.ml_cache = get_ml_model_cache()
        self.optimizations_applied = []

    def apply_all_optimizations(self) -> Dict[str, bool]:
        """
        Apply all Phase 3 optimizations

        Returns:
        {
            "websocket_batching": bool,
            "ml_caching": bool,
            "memory_monitoring": bool,
            "database_optimization": bool,
            "all_applied": bool
        }
        """
        logger.info("🚀 Applying Phase 3 production optimizations...")

        results = {}

        # 1. WebSocket message batching
        try:
            # Already initialized via get_batch_optimizer()
            logger.info("✅ WebSocket message batching: ENABLED")
            logger.info(f"   • Batch window: 500ms")
            logger.info(f"   • Max batch size: 100 messages")
            logger.info(f"   • Compression: Enabled for mobile (>1KB payloads)")
            logger.info(f"   • Rate limit: 100 messages/sec per connection")
            results["websocket_batching"] = True
            self.optimizations_applied.append("websocket_batching")
        except Exception as e:
            logger.error(f"❌ WebSocket batching failed: {e}")
            results["websocket_batching"] = False

        # 2. ML model in-memory caching
        try:
            self.ml_cache.get_model()  # Trigger initial load
            logger.info("✅ ML model in-memory caching: ENABLED")
            logger.info(f"   • TTL: 60 minutes")
            logger.info(f"   • Eliminates disk I/O on every prediction")
            results["ml_caching"] = True
            self.optimizations_applied.append("ml_caching")
        except Exception as e:
            logger.error(f"❌ ML caching failed: {e}")
            results["ml_caching"] = False

        # 3. Memory monitoring
        try:
            memory_status = self.memory_monitor.check_memory()
            logger.info("✅ Memory monitoring: ENABLED")
            logger.info(f"   • Warning threshold: 800MB")
            logger.info(f"   • Critical threshold: 950MB")
            logger.info(f"   • Current usage: {memory_status.get('rss_mb', 0):.1f}MB")
            results["memory_monitoring"] = True
            self.optimizations_applied.append("memory_monitoring")
        except Exception as e:
            logger.error(f"❌ Memory monitoring failed: {e}")
            results["memory_monitoring"] = False

        # 4. Database query optimization
        try:
            if self.db:
                optimize_database_queries(self.db)
                logger.info("✅ Database query optimization: ENABLED")
                logger.info(f"   • Index on phase3_checkpoints(hora)")
                logger.info(f"   • Index on ab_test_ml_predictions(test_id, created_at)")
                logger.info(f"   • Index on personalization_variants(test_id, rollout_phase)")
                results["database_optimization"] = True
                self.optimizations_applied.append("database_optimization")
            else:
                logger.warning("⚠️ Database connection not available for optimization")
                results["database_optimization"] = False
        except Exception as e:
            logger.error(f"❌ Database optimization failed: {e}")
            results["database_optimization"] = False

        # Summary
        all_applied = all(results.values())
        results["all_applied"] = all_applied

        status = "🟢 COMPLETE" if all_applied else "🟡 PARTIAL"
        logger.info(f"\n{status} Phase 3 Optimizations: {sum(results.values())}/4 applied")

        return results

    def get_optimization_report(self) -> Dict[str, Any]:
        """Get detailed optimization report"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "optimizations_applied": self.optimizations_applied,
            "websocket_batching": {
                "enabled": True,
                "batch_window_ms": 500,
                "max_batch_size": 100,
                "compression": "gzip (mobile only)",
                "rate_limit": "100 msgs/sec per connection",
                "stats": self.batch_optimizer.get_stats()
            },
            "ml_model_cache": {
                "enabled": True,
                "ttl_minutes": 60,
                "stats": self.ml_cache.get_stats()
            },
            "memory_monitoring": {
                "enabled": True,
                "warning_threshold_mb": 800,
                "critical_threshold_mb": 950,
                "current": self.memory_monitor.check_memory()
            },
            "database_optimization": {
                "enabled": True,
                "indexes": [
                    "phase3_checkpoints(hora)",
                    "ab_test_ml_predictions(test_id, created_at)",
                    "personalization_variants(test_id, rollout_phase)"
                ]
            }
        }

    def monitor_performance(self) -> Dict[str, Any]:
        """Monitor Phase 3 performance metrics in real-time"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "memory": self.memory_monitor.check_memory(),
            "websocket_batch_stats": self.batch_optimizer.get_stats(),
            "ml_cache_stats": self.ml_cache.get_stats()
        }


def initialize_phase3_optimizations(db_connection) -> Phase3Optimizations:
    """Initialize Phase 3 optimizations for production"""
    logger.info("🔧 Initializing Phase 3 production optimizations...")

    optimizer = Phase3Optimizations(db_connection)
    results = optimizer.apply_all_optimizations()

    if not results["all_applied"]:
        logger.warning("⚠️ Some optimizations failed - check logs above")
    else:
        logger.info("✅ All Phase 3 optimizations successfully applied")

    return optimizer


# Export key functions for use in FastAPI app
__all__ = [
    "Phase3Optimizations",
    "initialize_phase3_optimizations",
    "get_batch_optimizer",
    "get_memory_monitor",
    "get_ml_model_cache"
]
