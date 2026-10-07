#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Enhanced Monitoring with Optimizations
Integrates memory monitoring, database optimization, and checkpoint tracking
"""

import asyncio
import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from backend.phase3_optimizations import (
    DatabaseOptimizer, MemoryMonitor, MLModelCache, QueryOptimizer
)
from backend.rollback_manager import RollbackManager
from backend.circuit_breaker import CircuitBreakerRegistry

logger = logging.getLogger(__name__)


class EnhancedPhase3Monitor:
    """Monitor Phase 3 with performance optimizations and memory tracking"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection
        self.db.row_factory = sqlite3.Row
        
        # Initialize components
        self.db_optimizer = DatabaseOptimizer(db_connection)
        self.memory_monitor = MemoryMonitor(alert_threshold_percent=80.0)
        self.ml_cache = MLModelCache()
        self.query_optimizer = QueryOptimizer()
        self.rollback_manager = RollbackManager(db_connection)
        
        # Monitoring state
        self.checkpoints_run = 0
        self.memory_warnings = []
        self.query_times = {}

    async def initialize(self):
        """Initialize optimizations before Phase 3 starts"""
        logger.info("🚀 Initializing Phase 3 with optimizations...")
        
        # Step 1: Create database indices
        indices = self.db_optimizer.create_phase3_indices()
        indices_ok = sum(1 for v in indices.values() if v)
        logger.info(f"✅ Database indices: {indices_ok}/{len(indices)} created")
        
        # Step 2: Enable query optimization
        self.db_optimizer.enable_query_optimization()
        logger.info("✅ Query optimization enabled (WAL, cache, sync)")
        
        # Step 3: Analyze table statistics
        tables = self.db_optimizer.analyze_table_stats()
        logger.info(f"✅ Table statistics analyzed for {len(tables)} tables")
        
        # Step 4: Pre-load ML model
        model = self.ml_cache.get_model()
        logger.info(f"✅ ML model pre-loaded: {model is not None}")
        
        # Step 5: Check initial memory
        health = self.memory_monitor.check_memory_health()
        logger.info(f"✅ Initial memory health: {health['healthy']}")
        
        return {
            "indices_created": indices_ok,
            "tables_analyzed": len(tables),
            "model_cached": model is not None,
            "memory_healthy": health['healthy'],
            "timestamp": datetime.utcnow().isoformat()
        }

    async def run_optimized_checkpoint(self, checkpoint_number: int) -> Dict[str, Any]:
        """
        Run checkpoint with performance monitoring.
        Returns full report with metrics, memory, and optimizations applied.
        """
        start_time = datetime.utcnow()
        
        try:
            # Collect metrics (optimized queries with indices)
            metrics = self._collect_metrics_optimized()
            
            # Check memory health
            memory_health = self.memory_monitor.check_memory_health()
            if not memory_health['healthy']:
                self.memory_warnings.append({
                    "checkpoint": checkpoint_number,
                    "alert": memory_health.get('alert'),
                    "timestamp": datetime.utcnow().isoformat()
                })
                logger.warning(f"⚠️  Memory warning at checkpoint {checkpoint_number}")
            
            # Get circuit breaker states
            cb_states = CircuitBreakerRegistry.get_all_metrics()
            cb_open = [name for name, metrics in cb_states.items() 
                      if metrics['state'] == 'OPEN']
            
            # Determine health status
            healthy_metrics = sum(1 for k, v in metrics.items() if v)
            health_status = "GREEN" if healthy_metrics >= 5 else "YELLOW" if healthy_metrics >= 5 else "RED"
            
            # Build checkpoint report
            checkpoint = {
                "checkpoint_number": checkpoint_number,
                "hora": 48 + (checkpoint_number * 2),
                "timestamp": start_time.isoformat(),
                "metrics": metrics,
                "health_status": health_status,
                "healthy_metric_count": healthy_metrics,
                "circuit_breakers": {
                    "total": len(cb_states),
                    "open": len(cb_open),
                    "open_services": cb_open
                },
                "memory": {
                    "process_mb": memory_health['stats'].get('process_rss_mb'),
                    "system_percent": memory_health['stats'].get('system_percent'),
                    "healthy": memory_health['healthy']
                },
                "query_performance": self.query_times,
                "decision": self._make_checkpoint_decision(metrics, cb_open, memory_health)
            }
            
            # Save to database
            self._save_checkpoint(checkpoint)
            
            # Log timing
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"✅ Checkpoint {checkpoint_number} completed in {elapsed_ms:.1f}ms")
            
            return checkpoint
            
        except Exception as e:
            logger.error(f"❌ Error in checkpoint {checkpoint_number}: {e}")
            return {
                "checkpoint_number": checkpoint_number,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _collect_metrics_optimized(self) -> Dict[str, bool]:
        """Collect health metrics using optimized queries"""
        metrics = {}
        
        try:
            # ML Accuracy (threshold: >= 0.78)
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT AVG(ml_accuracy) FROM comparison_reports
                WHERE generated_at > datetime('now', '-1 hour')
            """)
            result = cursor.fetchone()
            ml_acc = result[0] if result[0] else 0.75
            metrics['ml_accuracy'] = ml_acc >= 0.78
            
            # Error Rate (threshold: < 0.0008)
            cursor.execute("""
                SELECT error_rate FROM backend_metrics_collector
                WHERE collected_at > datetime('now', '-5 minutes')
                ORDER BY collected_at DESC LIMIT 1
            """)
            result = cursor.fetchone()
            error_rate = result[0] if result else 0.001
            metrics['error_rate'] = error_rate < 0.0008
            
            # WebSocket Latency (threshold: < 95ms)
            cursor.execute("""
                SELECT AVG(latency_ms) FROM websocket_metrics
                WHERE recorded_at > datetime('now', '-5 minutes')
            """)
            result = cursor.fetchone()
            latency = result[0] if result[0] else 8.0
            metrics['latency'] = latency < 95
            
            # Predictions/Hour (threshold: >= 42)
            cursor.execute("""
                SELECT COUNT(*) FROM ab_test_ml_predictions
                WHERE created_at > datetime('now', '-1 hour')
            """)
            result = cursor.fetchone()
            predictions = result[0] if result else 48
            metrics['predictions'] = predictions >= 42
            
            # Personalization Active (threshold: >= 140)
            cursor.execute("""
                SELECT COUNT(*) FROM personalization_variants
                WHERE applied_date > datetime('now', '-24 hours')
            """)
            result = cursor.fetchone()
            personalization = result[0] if result else 150
            metrics['personalization'] = personalization >= 140
            
            # Active Tests (threshold: >= 8)
            cursor.execute("""
                SELECT COUNT(*) FROM ab_tests WHERE active = 1
            """)
            result = cursor.fetchone()
            tests = result[0] if result else 9
            metrics['active_tests'] = tests >= 8
            
        except Exception as e:
            logger.error(f"❌ Error collecting metrics: {e}")
        
        return metrics

    def _make_checkpoint_decision(self, metrics: Dict, open_breakers: list, 
                                 memory_health: Dict) -> str:
        """
        Decide if Phase 3 should continue, caution, or rollback.
        
        Rules:
        - 6/6 metrics GREEN + no open breakers = CONTINUE
        - 5/6 metrics or 1 open breaker = CAUTION
        - <5/6 metrics or >1 open breaker = ALERT/ROLLBACK
        - Memory unhealthy = CAUTION
        """
        healthy_count = sum(1 for v in metrics.values() if v)
        
        if healthy_count >= 6 and not open_breakers and memory_health['healthy']:
            return "CONTINUE"
        elif healthy_count == 5 and len(open_breakers) <= 1 and memory_health['healthy']:
            return "CAUTION"
        else:
            return "ALERT/ROLLBACK"

    def _save_checkpoint(self, checkpoint: Dict):
        """Save checkpoint to database and JSON log"""
        try:
            cursor = self.db.cursor()
            
            # Save to database
            cursor.execute("""
                INSERT INTO phase3_checkpoints
                (checkpoint_number, hora, metrics, health_status, healthy_metric_count,
                 circuit_breaker_states, memory_usage, decision, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                checkpoint['checkpoint_number'],
                checkpoint['hora'],
                json.dumps(checkpoint['metrics']),
                checkpoint['health_status'],
                checkpoint['healthy_metric_count'],
                json.dumps(checkpoint['circuit_breakers']),
                json.dumps(checkpoint['memory']),
                checkpoint['decision']
            ))
            
            self.db.commit()
            
            # Save to JSON log
            log_file = f"/home/claude/felix-automation/logs/phase3/checkpoint_HORA_{checkpoint['hora']:02d}.json"
            with open(log_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            logger.info(f"✅ Checkpoint {checkpoint['checkpoint_number']} saved")
            
        except Exception as e:
            logger.error(f"❌ Error saving checkpoint: {e}")

    def get_phase3_status(self) -> Dict[str, Any]:
        """Get current Phase 3 status with optimization metrics"""
        return {
            "checkpoints_completed": self.checkpoints_run,
            "memory_warnings": len(self.memory_warnings),
            "memory_health": self.memory_monitor.check_memory_health(),
            "ml_model_cached": self.ml_cache._model is not None,
            "database_optimized": True,
            "query_performance": self.query_times,
            "timestamp": datetime.utcnow().isoformat()
        }


async def run_phase3_monitoring_loop(db_path: str, checkpoints: int = 13):
    """
    Main Phase 3 monitoring loop with optimizations.
    Runs checkpoints every 2 hours for 24 hours (13 total).
    """
    db = sqlite3.connect(db_path)
    monitor = EnhancedPhase3Monitor(db)
    
    # Initialize optimizations
    init_result = await monitor.initialize()
    logger.info(f"Initialization: {init_result}")
    
    # Run checkpoint loop
    for checkpoint_num in range(1, checkpoints + 1):
        logger.info(f"\n🕐 Running checkpoint {checkpoint_num}/13...")
        
        # Run checkpoint with optimizations
        result = await monitor.run_optimized_checkpoint(checkpoint_num)
        
        # Check if rollback needed
        if result.get('decision') == "ALERT/ROLLBACK":
            logger.error(f"🚨 Rollback triggered at checkpoint {checkpoint_num}")
            await monitor.rollback_manager.execute_rollback(
                trigger=None,
                reason=f"Checkpoint {checkpoint_num} failed health checks"
            )
            break
        
        # Wait 2 hours before next checkpoint (or less for testing)
        if checkpoint_num < checkpoints:
            wait_time = 7200  # 2 hours
            logger.info(f"⏳ Waiting {wait_time}s until next checkpoint...")
            await asyncio.sleep(wait_time)
    
    db.close()
    logger.info("✅ Phase 3 monitoring complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_phase3_monitoring_loop("/home/claude/felix-automation/data/phase3.sqlite"))
