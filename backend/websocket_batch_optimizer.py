#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - WebSocket Message Batch Optimizer
Optimizations for real-time event broadcasting:
- Message batching every 500ms
- Payload compression for mobile
- Rate limiting per connection
- Memory efficient event history
"""

import asyncio
import json
import logging
import gzip
import io
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BatchedMessage:
    """Represents a batched WebSocket message"""
    messages: List[Dict[str, Any]]
    timestamp: str
    batch_size: int
    compressed: bool = False
    compressed_size: Optional[int] = None


class WebSocketBatchOptimizer:
    """Optimize WebSocket broadcasting with message batching and compression"""

    def __init__(self, batch_window_ms: int = 500, max_batch_size: int = 100):
        """
        Initialize batch optimizer

        Args:
            batch_window_ms: Time window for batching messages (default 500ms)
            max_batch_size: Maximum messages per batch before force-send (default 100)
        """
        self.batch_window_ms = batch_window_ms / 1000.0  # Convert to seconds
        self.max_batch_size = max_batch_size

        # Message queues per connection: connection_id -> List[message]
        self.message_queues: Dict[str, List[Dict]] = defaultdict(list)

        # Batch timers: connection_id -> asyncio.Task
        self.batch_timers: Dict[str, asyncio.Task] = {}

        # Rate limiting: connection_id -> timestamp of last sent
        self.rate_limiters: Dict[str, float] = {}

        # Statistics
        self.stats = {
            "total_messages": 0,
            "total_batches": 0,
            "compression_ratio": 0.0,
            "messages_batched": 0,
            "messages_compressed": 0,
        }

    async def queue_message(self, connection_id: str, message: Dict[str, Any], 
                           send_callback, is_mobile: bool = False) -> None:
        """
        Queue a message for batching

        Args:
            connection_id: Target connection ID
            message: Message payload
            send_callback: Async function(compressed_message, is_compressed) to send
            is_mobile: Whether client is mobile (for compression)
        """
        # Add message to queue
        self.message_queues[connection_id].append(message)
        self.stats["total_messages"] += 1

        # Check if batch should be sent immediately
        if len(self.message_queues[connection_id]) >= self.max_batch_size:
            await self._send_batch(connection_id, send_callback, is_mobile)
            return

        # Schedule batch send if not already scheduled
        if connection_id not in self.batch_timers or self.batch_timers[connection_id].done():
            self.batch_timers[connection_id] = asyncio.create_task(
                self._schedule_batch_send(connection_id, send_callback, is_mobile)
            )

    async def _schedule_batch_send(self, connection_id: str, send_callback, is_mobile: bool) -> None:
        """Schedule batch send after window expires"""
        await asyncio.sleep(self.batch_window_ms)
        await self._send_batch(connection_id, send_callback, is_mobile)

    async def _send_batch(self, connection_id: str, send_callback, is_mobile: bool) -> None:
        """Send batched messages"""
        # Get queued messages
        messages = self.message_queues.get(connection_id, [])

        if not messages:
            return

        # Clear queue
        del self.message_queues[connection_id]
        if connection_id in self.batch_timers:
            del self.batch_timers[connection_id]

        # Create batch payload
        batch_payload = {
            "batch": True,
            "count": len(messages),
            "timestamp": datetime.utcnow().isoformat(),
            "messages": messages
        }

        # Serialize to JSON
        json_data = json.dumps(batch_payload)

        # Compress if mobile (save ~60% bandwidth)
        compressed_data = None
        is_compressed = False

        if is_mobile and len(json_data) > 1024:  # Only compress if >1KB
            try:
                compressed = gzip.compress(json_data.encode('utf-8'), compresslevel=6)
                compression_ratio = len(compressed) / len(json_data)

                if compression_ratio < 0.9:  # Only use if saves >10%
                    compressed_data = compressed
                    is_compressed = True
                    self.stats["messages_compressed"] += len(messages)
                    self.stats["compression_ratio"] = compression_ratio
            except Exception as e:
                logger.warning(f"Compression failed: {e}")

        # Rate limit check
        now = datetime.utcnow().timestamp()
        last_sent = self.rate_limiters.get(connection_id, 0)

        if (now - last_sent) < 0.01:  # Max 100 messages/sec = 10ms per message
            # Rate limited, delay slightly
            await asyncio.sleep(0.01)

        self.rate_limiters[connection_id] = now

        # Send via callback
        try:
            await send_callback(compressed_data or json_data, is_compressed)
            self.stats["total_batches"] += 1
            self.stats["messages_batched"] += len(messages)

            logger.debug(f"✅ Batch sent ({len(messages)} msgs, compressed={is_compressed})")
        except Exception as e:
            logger.error(f"❌ Failed to send batch: {e}")

    async def flush_all(self, send_callback, is_mobile: bool = False) -> None:
        """Flush all pending batches (call on shutdown)"""
        for connection_id in list(self.message_queues.keys()):
            await self._send_batch(connection_id, send_callback, is_mobile)

    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        return {
            "total_messages": self.stats["total_messages"],
            "total_batches": self.stats["total_batches"],
            "average_batch_size": (self.stats["messages_batched"] / max(1, self.stats["total_batches"])),
            "messages_compressed": self.stats["messages_compressed"],
            "compression_ratio": f"{self.stats['compression_ratio']*100:.1f}%",
            "batching_efficiency": f"{(self.stats['messages_batched'] / max(1, self.stats['total_messages']))*100:.1f}%"
        }


class MemoryMonitor:
    """Monitor memory usage and alert if exceeding thresholds"""

    def __init__(self, warning_threshold_mb: int = 800, critical_threshold_mb: int = 950):
        """
        Initialize memory monitor

        Args:
            warning_threshold_mb: Warn if memory usage exceeds this (default 800MB)
            critical_threshold_mb: Error if memory usage exceeds this (default 950MB)
        """
        self.warning_threshold = warning_threshold_mb * 1024 * 1024
        self.critical_threshold = critical_threshold_mb * 1024 * 1024
        self.last_alert = None

    def check_memory(self) -> Dict[str, Any]:
        """Check current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            return {
                "rss_bytes": memory_info.rss,
                "rss_mb": memory_info.rss / (1024 * 1024),
                "percent": memory_percent,
                "status": self._get_status(memory_info.rss),
                "timestamp": datetime.utcnow().isoformat()
            }
        except ImportError:
            logger.warning("psutil not installed, memory monitoring disabled")
            return {"status": "unavailable"}

    def _get_status(self, rss_bytes: int) -> str:
        """Determine memory status"""
        if rss_bytes > self.critical_threshold:
            logger.critical(f"🔴 CRITICAL: Memory usage {rss_bytes/(1024*1024):.1f}MB exceeds threshold")
            return "CRITICAL"
        elif rss_bytes > self.warning_threshold:
            logger.warning(f"🟡 WARNING: Memory usage {rss_bytes/(1024*1024):.1f}MB approaching limit")
            return "WARNING"
        return "OK"


def optimize_database_queries(db_connection) -> None:
    """Create indexes to optimize Phase 3 database queries"""
    logger.info("🔧 Optimizing database indexes for Phase 3...")

    try:
        cursor = db_connection.cursor()

        # Index on phase3_checkpoints for temporal queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phase3_checkpoints_hora
            ON phase3_checkpoints(hora)
        """)

        # Index on ab_test_ml_predictions for test-based queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ab_test_ml_predictions_test_id
            ON ab_test_ml_predictions(test_id, created_at)
        """)

        # Index on personalization_variants for rollout queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_personalization_variants_test_id
            ON personalization_variants(test_id, rollout_phase)
        """)

        db_connection.commit()
        logger.info("✅ Database indexes created successfully")
    except Exception as e:
        logger.warning(f"⚠️ Index optimization failed: {e}")


# Global optimizer instance
_batch_optimizer: Optional[WebSocketBatchOptimizer] = None
_memory_monitor: Optional[MemoryMonitor] = None


def get_batch_optimizer() -> WebSocketBatchOptimizer:
    """Get or create global batch optimizer"""
    global _batch_optimizer
    if _batch_optimizer is None:
        _batch_optimizer = WebSocketBatchOptimizer(batch_window_ms=500, max_batch_size=100)
    return _batch_optimizer


def get_memory_monitor() -> MemoryMonitor:
    """Get or create global memory monitor"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor(warning_threshold_mb=800, critical_threshold_mb=950)
    return _memory_monitor
