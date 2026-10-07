#!/usr/bin/env python3
# ====================================================================
# FASE 14 - WebSocket Load Testing & Performance Benchmarks
# Tests: Concurrent Connections, Event Throughput, Latency
# ====================================================================

import asyncio
import websockets
import json
import time
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List
import statistics

@dataclass
class TestResult:
    """Store individual test metrics"""
    connection_time: float
    message_latency: float
    disconnect_time: float

class LoadTestRunner:
    """Simulate concurrent WebSocket connections and measure performance"""

    def __init__(self, host: str = "localhost", port: int = 8001, num_connections: int = 100):
        self.host = host
        self.port = port
        self.num_connections = num_connections
        self.ws_uri = f"ws://{host}:{port}/ws"
        self.results: List[TestResult] = []
        self.total_events_sent = 0
        self.total_events_received = 0
        self.start_time = None
        self.end_time = None

    async def connect_and_test(self, client_id: int) -> TestResult:
        """
        Establish WebSocket connection and send test events
        """
        connection_start = time.time()

        try:
            # Generate JWT token for testing
            jwt_token = self._generate_test_token(client_id)

            # Connect to WebSocket
            async with websockets.connect(self.ws_uri, ping_interval=None) as websocket:
                connection_time = time.time() - connection_start

                # Authenticate
                auth_message = {
                    "type": "auth",
                    "token": jwt_token
                }

                # Measure message send latency
                latency_start = time.time()
                await websocket.send(json.dumps(auth_message))

                # Wait for auth response with timeout
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=5.0
                    )
                    latency = time.time() - latency_start
                    self.total_events_received += 1
                except asyncio.TimeoutError:
                    latency = 5000.0  # Timeout

                # Send test event
                test_message = {
                    "type": "test:event",
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat()
                }

                await websocket.send(json.dumps(test_message))
                self.total_events_sent += 1

                # Keep connection open for a short duration
                await asyncio.sleep(2)

                disconnect_start = time.time()

            disconnect_time = time.time() - disconnect_start

            return TestResult(
                connection_time=connection_time,
                message_latency=latency,
                disconnect_time=disconnect_time
            )

        except Exception as e:
            print(f"  ✗ Client {client_id} error: {str(e)}")
            return TestResult(
                connection_time=float('inf'),
                message_latency=float('inf'),
                disconnect_time=float('inf')
            )

    def _generate_test_token(self, user_id: int) -> str:
        """Generate a simple JWT token for testing (without real signing)"""
        import base64
        import json

        # This is a mock token - in real scenario would use proper JWT signing
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": f"test_user_{user_id}",
            "user_id": user_id,
            "role": "test",
            "exp": int(time.time()) + 3600
        }

        header_b64 = base64.b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip('=')

        # Mock signature (in production, would be HMAC-SHA256)
        signature = "mock_signature_123"

        token = f"{header_b64}.{payload_b64}.{signature}"
        return token

    async def run_load_test(self):
        """
        Run concurrent WebSocket connections and collect metrics
        """
        print(f"\n🚀 Starting WebSocket Load Test")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Target: {self.num_connections} concurrent connections")
        print(f"Server: {self.ws_uri}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        self.start_time = time.time()

        # Create tasks for all connections
        tasks = [
            self.connect_and_test(i)
            for i in range(self.num_connections)
        ]

        # Run all connections concurrently with progress
        print(f"Launching {self.num_connections} concurrent connections...")
        results = await asyncio.gather(*tasks, return_exceptions=False)

        self.end_time = time.time()
        self.results = [r for r in results if isinstance(r, TestResult)]

        # Filter out failed connections (infinity values)
        successful_results = [
            r for r in self.results
            if r.connection_time != float('inf') and r.message_latency != float('inf')
        ]

        self._print_results(successful_results)

    def _print_results(self, successful_results: List[TestResult]):
        """Print detailed test results and metrics"""
        print(f"\n📊 LOAD TEST RESULTS")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        total_duration = self.end_time - self.start_time
        success_rate = (len(successful_results) / self.num_connections) * 100

        print(f"\n✓ Connections Successful: {len(successful_results)}/{self.num_connections} ({success_rate:.1f}%)")
        print(f"✓ Total Duration: {total_duration:.2f} seconds")
        print(f"✓ Events Sent: {self.total_events_sent}")
        print(f"✓ Events Received: {self.total_events_received}")

        if successful_results:
            conn_times = [r.connection_time * 1000 for r in successful_results]  # ms
            latencies = [r.message_latency * 1000 for r in successful_results]   # ms

            print(f"\n⏱️  CONNECTION TIMING METRICS (milliseconds)")
            print(f"   ├─ Mean: {statistics.mean(conn_times):.2f}ms")
            print(f"   ├─ Median: {statistics.median(conn_times):.2f}ms")
            print(f"   ├─ Min: {min(conn_times):.2f}ms")
            print(f"   └─ Max: {max(conn_times):.2f}ms")

            print(f"\n⏱️  MESSAGE LATENCY METRICS (milliseconds)")
            print(f"   ├─ Mean: {statistics.mean(latencies):.2f}ms")
            print(f"   ├─ Median: {statistics.median(latencies):.2f}ms")
            print(f"   ├─ Min: {min(latencies):.2f}ms")
            print(f"   ├─ Max: {max(latencies):.2f}ms")
            print(f"   └─ P95: {sorted(latencies)[int(len(latencies)*0.95)]:.2f}ms")

            # Throughput
            events_per_second = self.total_events_sent / total_duration
            print(f"\n📈 THROUGHPUT METRICS")
            print(f"   ├─ Events/Second: {events_per_second:.1f}")
            print(f"   └─ Connections/Second: {len(successful_results)/total_duration:.1f}")

        print(f"\n🎯 PERFORMANCE TARGETS vs ACTUAL")
        print(f"   ├─ Target WebSocket Latency: <100ms (P95)")
        if successful_results:
            p95_latency = sorted([r.message_latency * 1000 for r in successful_results])[
                int(len(successful_results)*0.95)
            ]
            status = "✅ PASS" if p95_latency < 100 else "❌ FAIL"
            print(f"   ├─ Actual P95 Latency: {p95_latency:.2f}ms {status}")

        print(f"   ├─ Target Concurrent Connections: 100+")
        print(f"   └─ Actual: {len(successful_results)} {('✅ PASS' if len(successful_results) >= 100 else '⚠ PARTIAL')}")

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    """Main entry point"""

    # Parse arguments
    num_connections = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    host = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8001

    # Run load test
    tester = LoadTestRunner(host=host, port=port, num_connections=num_connections)

    try:
        await tester.run_load_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Load test interrupted by user")
    except Exception as e:
        print(f"\n❌ Load test error: {str(e)}")
        print(f"\nNote: WebSocket server must be running on {host}:{port}")
        print(f"Start with: python3 backend/main.py")


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║      FASE 14 - WebSocket Load Testing Framework                ║
    ║      Concurrent Connections, Throughput & Latency Analysis     ║
    ╚════════════════════════════════════════════════════════════════╝

    Usage: python3 load_testing.py [num_connections] [host] [port]
    Example: python3 load_testing.py 100 localhost 8001

    Targets:
    - Concurrent connections: 100+
    - WebSocket latency (P95): <100ms
    - Success rate: 95%+
    """)

    asyncio.run(main())
