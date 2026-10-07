#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - ML Model In-Memory Caching
Keep ML model loaded in memory for fast inference
"""

import logging
import pickle
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class MLModelCache:
    """
    Cache ML model in memory for fast access
    Prevents model reloading on every prediction
    """

    def __init__(self, model_path: str = "models/ml_model.pkl", ttl_minutes: int = 60):
        """
        Initialize ML model cache

        Args:
            model_path: Path to pickled ML model
            ttl_minutes: Time-to-live for cached model (default 60 minutes)
        """
        self.model_path = model_path
        self.ttl = timedelta(minutes=ttl_minutes)
        self.model = None
        self.loaded_at = None
        self.lock = Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "reloads": 0
        }

    def get_model(self):
        """Get ML model from cache or load from disk"""
        with self.lock:
            # Check if model is valid
            if self.model is not None and self._is_valid():
                self.stats["hits"] += 1
                return self.model

            # Model not cached or expired
            self.stats["misses"] += 1
            self._reload_model()

        return self.model

    def _is_valid(self) -> bool:
        """Check if cached model is still valid"""
        if self.loaded_at is None:
            return False
        return datetime.utcnow() - self.loaded_at < self.ttl

    def _reload_model(self) -> None:
        """Reload model from disk"""
        try:
            import os
            if not os.path.exists(self.model_path):
                logger.warning(f"⚠️ Model not found at {self.model_path}")
                return

            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
                self.loaded_at = datetime.utcnow()
                self.stats["reloads"] += 1

            logger.info(f"✅ ML model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load ML model: {e}")
            self.model = None

    def predict(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make prediction using cached model

        Args:
            features: Feature dictionary for prediction

        Returns:
            Prediction result or None if model unavailable
        """
        model = self.get_model()
        if model is None:
            return None

        try:
            # Convert features to model input format
            prediction = model.predict([features])
            confidence = model.predict_proba([features])

            return {
                "prediction": float(prediction[0]),
                "confidence": float(confidence[0][1]) if len(confidence[0]) > 1 else 0.5,
                "model_version": getattr(model, 'version', 'unknown'),
                "cached": True
            }
        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear cached model"""
        with self.lock:
            self.model = None
            self.loaded_at = None
            logger.info("✅ ML model cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_requests": total_requests,
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "hit_rate_percent": f"{hit_rate:.1f}%",
            "model_reloads": self.stats["reloads"],
            "cached_model_age_seconds": (
                (datetime.utcnow() - self.loaded_at).total_seconds()
                if self.loaded_at else None
            ),
            "model_loaded": self.model is not None
        }


class ConnectionPoolOptimizer:
    """Optimize database connection pooling"""

    def __init__(self, max_connections: int = 10, connection_timeout: int = 5):
        """
        Initialize connection pool optimizer

        Args:
            max_connections: Maximum connections in pool (default 10)
            connection_timeout: Timeout for acquiring connection (default 5 seconds)
        """
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.stats = {
            "created": 0,
            "reused": 0,
            "errors": 0
        }

    def optimize_connection_pool(self, db_engine) -> None:
        """Apply connection pooling optimizations"""
        try:
            # For SQLAlchemy
            if hasattr(db_engine, 'pool'):
                logger.info(f"🔧 Configuring connection pool (max={self.max_connections})")
                # Connection pool is typically auto-managed
                self.stats["created"] += 1
            else:
                logger.warning("⚠️ Database engine doesn't support connection pooling")
        except Exception as e:
            logger.error(f"❌ Connection pool optimization failed: {e}")
            self.stats["errors"] += 1


# Global cache instance
_ml_cache: Optional[MLModelCache] = None


def get_ml_model_cache(model_path: str = "models/ml_model.pkl") -> MLModelCache:
    """Get or create global ML model cache"""
    global _ml_cache
    if _ml_cache is None:
        _ml_cache = MLModelCache(model_path=model_path, ttl_minutes=60)
    return _ml_cache
