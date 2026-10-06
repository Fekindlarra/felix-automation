"""
Load Testing Framework - FASE 14 Phase 3
Concurrent connection testing, stress testing, and performance benchmarking
"""

import asyncio
import time
import json
import random
from datetime import datetime
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import statistics


class TestScenario(Enum):
    """Load test scenarios"""
    GRADUAL_RAMP_UP = "gradual_ramp_up"
    SPIKE = "spike"
    SUSTAINED_LOAD = "sustained_load"
    BURST = "burst"


@dataclass
class ConnectionMetrics:
    """Metrics for a single WebSocket connection"""
    connection_id: str
    start_time: float
    end_time: float
    total_events_sent: int
    total_events_received: int
    total_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    connection_failures: int
    reconnection_attempts: int
    total_duration_ms: float
    avg_latency_ms: float
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class TestResults:
    """Results from a load test"""
    scenario: str
    start_time: str
    end_time: str
    duration_seconds: float
    total_connections: int
    successful_connections: int
    failed_connections: int
    total_events_sent: int
    total_events_received: int
    
    # Latency statistics (milliseconds)
    min_latency_ms: float
    max_latency_ms: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    
    # Throughput
    events_per_second: float
    connections_per_second: float
    
    # Reliability
    success_rate: float
    error_rate: float
    reconnection_rate: float
    
    # System metrics
    memory_usage_mb: float
    cpu_usage_percent: float
    
    connection_metrics: List[Dict[str, Any]]
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)


class MockWebSocketLoadTester:
    """Mock load testing for WebSocket connections (for testing without real websockets)"""
    
    def __init__(self, uri: str, auth_token: str = None):
        """
        Initialize load tester
        
        Args:
            uri: WebSocket URI
            auth_token: Optional JWT authentication token
        """
        self.uri = uri
        self.auth_token = auth_token
        self.connections: Dict[str, asyncio.Task] = {}
        self.metrics: Dict[str, ConnectionMetrics] = {}
        self.start_time = None
        self.end_time = None
    
    async def connect_client(self, client_id: str):
        """
        Simulate a WebSocket client connection
        
        Args:
            client_id: Unique client identifier
        """
        start_time = time.time()
        
        connection_metrics = ConnectionMetrics(
            connection_id=client_id,
            start_time=start_time,
            end_time=None,
            total_events_sent=0,
            total_events_received=0,
            total_latency_ms=0,
            min_latency_ms=float('inf'),
            max_latency_ms=0,
            connection_failures=0,
            reconnection_attempts=0,
            total_duration_ms=0,
            avg_latency_ms=0,
            errors=[]
        )
        
        try:
            # Simulate connection
            await asyncio.sleep(0.01)
            connection_metrics.total_events_sent += 1
            
            # Simulate receiving events
            for i in range(random.randint(5, 20)):
                await asyncio.sleep(random.uniform(0.1, 0.5))
                latency = random.uniform(10, 150)
                connection_metrics.total_events_received += 1
                connection_metrics.total_latency_ms += latency
                connection_metrics.min_latency_ms = min(connection_metrics.min_latency_ms, latency)
                connection_metrics.max_latency_ms = max(connection_metrics.max_latency_ms, latency)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            connection_metrics.connection_failures += 1
            connection_metrics.errors.append(str(e))
        
        finally:
            connection_metrics.end_time = time.time()
            connection_metrics.total_duration_ms = (connection_metrics.end_time - connection_metrics.start_time) * 1000
            
            if connection_metrics.total_events_received > 0:
                connection_metrics.avg_latency_ms = connection_metrics.total_latency_ms / connection_metrics.total_events_received
            
            self.metrics[client_id] = connection_metrics
    
    async def run_gradual_ramp_up(self, max_connections: int, duration_seconds: int, 
                                   ramp_up_rate: int = 10) -> TestResults:
        """Run gradual ramp-up load test"""
        return await self._run_scenario("gradual_ramp_up", max_connections, duration_seconds, ramp_up_rate)
    
    async def run_spike_test(self, base_connections: int, spike_connections: int,
                            duration_seconds: int) -> TestResults:
        """Run spike load test"""
        return await self._run_scenario("spike", base_connections + spike_connections, duration_seconds, base_connections)
    
    async def run_sustained_load(self, num_connections: int, duration_seconds: int) -> TestResults:
        """Run sustained load test"""
        return await self._run_scenario("sustained_load", num_connections, duration_seconds, num_connections)
    
    async def _run_scenario(self, scenario: str, max_connections: int,
                           duration_seconds: int, ramp_up_rate: int) -> TestResults:
        """Run a load test scenario"""
        self.start_time = time.time()
        self.metrics = {}
        self.connections = {}
        
        start_time_str = datetime.utcnow().isoformat() + "Z"
        
        # Create connections gradually
        connections_created = 0
        start = time.time()
        
        while connections_created < max_connections and (time.time() - start) < duration_seconds:
            connections_to_add = min(ramp_up_rate, max_connections - connections_created)
            
            for i in range(connections_to_add):
                client_id = f"{scenario}_{connections_created}_{i}"
                task = asyncio.create_task(self.connect_client(client_id))
                self.connections[client_id] = task
                connections_created += 1
            
            await asyncio.sleep(1)
        
        # Wait for connections to complete
        remaining_time = duration_seconds - (time.time() - start)
        if remaining_time > 0:
            await asyncio.sleep(min(remaining_time, 5))
        
        # Cancel remaining tasks
        for task in self.connections.values():
            task.cancel()
        
        await asyncio.gather(*self.connections.values(), return_exceptions=True)
        
        self.end_time = time.time()
        return self._calculate_results(scenario, start_time_str)
    
    def _calculate_results(self, scenario: str, start_time_str: str) -> TestResults:
        """Calculate test results"""
        duration_seconds = self.end_time - self.start_time
        successful_connections = sum(1 for m in self.metrics.values() if m.connection_failures == 0)
        failed_connections = len(self.metrics) - successful_connections
        
        latencies = []
        total_events_sent = 0
        total_events_received = 0
        total_reconnections = 0
        
        for metrics in self.metrics.values():
            total_events_sent += metrics.total_events_sent
            total_events_received += metrics.total_events_received
            total_reconnections += metrics.reconnection_attempts
            
            if metrics.avg_latency_ms > 0:
                latencies.append(metrics.avg_latency_ms)
        
        latencies_sorted = sorted(latencies) if latencies else [0]
        
        return TestResults(
            scenario=scenario,
            start_time=start_time_str,
            end_time=datetime.utcnow().isoformat() + "Z",
            duration_seconds=duration_seconds,
            total_connections=len(self.metrics),
            successful_connections=successful_connections,
            failed_connections=failed_connections,
            total_events_sent=total_events_sent,
            total_events_received=total_events_received,
            min_latency_ms=min(latencies_sorted) if latencies_sorted else 0,
            max_latency_ms=max(latencies_sorted) if latencies_sorted else 0,
            avg_latency_ms=statistics.mean(latencies_sorted) if latencies_sorted else 0,
            p50_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.50)] if len(latencies_sorted) > 1 else 0,
            p95_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.95)] if len(latencies_sorted) > 1 else 0,
            p99_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.99)] if len(latencies_sorted) > 1 else 0,
            events_per_second=total_events_received / duration_seconds if duration_seconds > 0 else 0,
            connections_per_second=len(self.metrics) / duration_seconds if duration_seconds > 0 else 0,
            success_rate=(successful_connections / len(self.metrics)) if self.metrics else 0,
            error_rate=1 - ((successful_connections / len(self.metrics)) if self.metrics else 0),
            reconnection_rate=(total_reconnections / len(self.metrics)) if self.metrics else 0,
            memory_usage_mb=0,
            cpu_usage_percent=0,
            connection_metrics=[m.to_dict() for m in self.metrics.values()],
            errors=[]
        )
