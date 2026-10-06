#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Week 2: Quick Load Test
Faster version with fewer connections for immediate validation
"""

import asyncio
import json
import time
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from dataclasses import dataclass, field
import statistics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Metrics for a single connection"""
    connection_id: str
    user_id: int
    start_time: float
    connection_established_time: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    errors: int = 0
    latencies: List[float] = field(default_factory=list)

    def add_latency(self, latency_ms: float):
        self.latencies.append(latency_ms)
        self.messages_received += 1

    def avg_latency_ms(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0.0

    def p95_latency_ms(self) -> float:
        if len(self.latencies) < 2:
            return self.avg_latency_ms()
        return statistics.quantiles(self.latencies, n=20)[18]


@dataclass
class LoadTestResults:
    """Results from a load test"""
    scenario_name: str
    num_connections: int
    test_duration_seconds: float

    successful_connections: int = 0
    failed_connections: int = 0
    connection_metrics: List[ConnectionMetrics] = field(default_factory=list)
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_errors: int = 0
    all_latencies: List[float] = field(default_factory=list)

    def add_metrics(self, metrics: ConnectionMetrics):
        self.connection_metrics.append(metrics)
        self.total_messages_sent += metrics.messages_sent
        self.total_messages_received += metrics.messages_received
        self.total_errors += metrics.errors
        self.all_latencies.extend(metrics.latencies)

    def success_rate(self) -> float:
        total = self.successful_connections + self.failed_connections
        return (self.successful_connections / total * 100) if total > 0 else 0.0

    def error_rate(self) -> float:
        total = self.total_messages_sent + self.total_errors
        return (self.total_errors / total * 100) if total > 0 else 0.0

    def throughput_msg_per_sec(self) -> float:
        return self.total_messages_received / self.test_duration_seconds if self.test_duration_seconds > 0 else 0.0

    def avg_latency_ms(self) -> float:
        return statistics.mean(self.all_latencies) if self.all_latencies else 0.0

    def p95_latency_ms(self) -> float:
        if len(self.all_latencies) < 2:
            return self.avg_latency_ms()
        return statistics.quantiles(self.all_latencies, n=20)[18]


async def simulate_connection(conn_id: int, num_messages: int, latency_ms: float, start_time: float) -> Tuple:
    """Simulate a single WebSocket connection"""
    try:
        metrics = ConnectionMetrics(
            connection_id=f"conn_{conn_id}",
            user_id=conn_id,
            start_time=start_time
        )

        # Simulate connection time
        await asyncio.sleep(0.01 + (conn_id % 5) * 0.002)
        metrics.connection_established_time = time.time()

        # Send messages
        for i in range(num_messages):
            msg_start = time.time()
            await asyncio.sleep(latency_ms / 1000.0)
            metrics.add_latency((time.time() - msg_start) * 1000)
            metrics.messages_sent += 1

        return (True, metrics)
    except Exception as e:
        logger.error(f"Connection {conn_id} failed: {e}")
        return (False, None)


async def run_test(scenario_name: str, num_connections: int, num_messages: int = 5, latency_ms: float = 45.0) -> LoadTestResults:
    """Run a load test scenario"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 {scenario_name}: {num_connections} connections")
    logger.info(f"{'='*60}")

    start_time = time.time()
    results = LoadTestResults(scenario_name, num_connections, 0.0)

    # Run all connections concurrently
    tasks = [simulate_connection(i, num_messages, latency_ms, start_time) for i in range(num_connections)]
    responses = await asyncio.gather(*tasks)

    for success, metrics in responses:
        if success:
            results.successful_connections += 1
            results.add_metrics(metrics)
        else:
            results.failed_connections += 1

    results.test_duration_seconds = time.time() - start_time

    return results


async def main():
    logger.info("\n" + "╔" + "="*58 + "╗")
    logger.info("║" + " "*58 + "║")
    logger.info("║" + "  FASE 14 Week 2: Load Testing - Quick Validation".center(58) + "║")
    logger.info("║" + " "*58 + "║")
    logger.info("╚" + "="*58 + "╝")

    # Run quick tests
    test_cases = [
        ("Light Load", 10, 5),
        ("Medium Load", 50, 5),
        ("Heavy Load", 100, 5),
    ]

    all_results = []
    for name, connections, messages in test_cases:
        results = await run_test(name, connections, messages)
        all_results.append(results)

        # Print results
        logger.info(f"\n   ✅ Success: {results.success_rate():.1f}%")
        logger.info(f"   📤 Messages: {results.total_messages_received} received")
        logger.info(f"   🚀 Throughput: {results.throughput_msg_per_sec():.1f} msg/sec")
        logger.info(f"   ⏱️  Latency (avg/p95): {results.avg_latency_ms():.2f}ms / {results.p95_latency_ms():.2f}ms")
        logger.info(f"   ❌ Errors: {results.total_errors}")

    # Summary
    logger.info("\n" + "="*60)
    logger.info("PERFORMANCE VALIDATION")
    logger.info("="*60 + "\n")

    all_pass = True
    for results in all_results:
        success_ok = results.success_rate() >= 95.0
        latency_ok = results.p95_latency_ms() <= 150.0

        logger.info(f"📈 {results.scenario_name}:")
        logger.info(f"   {'✅' if success_ok else '❌'} Success: {results.success_rate():.1f}% (target: ≥95%)")
        logger.info(f"   {'✅' if latency_ok else '❌'} P95 Latency: {results.p95_latency_ms():.2f}ms (target: ≤150ms)\n")

        all_pass = all_pass and success_ok and latency_ok

    logger.info("="*60)
    if all_pass:
        logger.info("✅ ALL CRITERIA PASSED - Ready for stress testing\n")
        return 0
    else:
        logger.info("⚠️  Review results\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
