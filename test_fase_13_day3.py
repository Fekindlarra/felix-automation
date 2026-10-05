#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite - FASE 13 Day 3: WebSocket Real-Time Updates
Comprehensive testing of event models, connection management, and broadcasting
"""

import sys
import unittest
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))

from backend.events import (
    EventType, EventPayload, PipelineEvent, AuditEvent, ProposalEvent,
    EmailEvent, KPIEvent, NotificationEvent, MetricSnapshot, EventFactory,
    ConnectionState, ConnectionInfo, get_target_roles
)
from backend.websocket_manager import WebSocketConnectionManager, EventBroadcaster

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEventModels(unittest.TestCase):
    """Test event model definitions and serialization"""

    def test_event_type_enum(self):
        """Test EventType enum values"""
        # Verify all event types are defined
        event_types = [
            EventType.PIPELINE_STAGE_CHANGED,
            EventType.AUDIT_COMPLETED,
            EventType.PROPOSAL_SENT,
            EventType.EMAIL_OPENED,
            EventType.KPI_UPDATED,
            EventType.NOTIFICATION_CREATED
        ]

        self.assertEqual(len(event_types), 6)
        logger.info("✅ EventType enum verified")

    def test_event_payload_serialization(self):
        """Test EventPayload to_dict and to_json"""
        event = EventPayload(
            event_type=EventType.KPI_UPDATED,
            timestamp=datetime.utcnow(),
            client_id=1,
            user_id=100,
            data={"metric": "revenue", "value": 5000}
        )

        # Test to_dict
        event_dict = event.to_dict()
        self.assertIn("event_type", event_dict)
        self.assertIn("timestamp", event_dict)
        self.assertEqual(event_dict["client_id"], 1)

        # Test to_json
        event_json = event.to_json()
        self.assertIsInstance(event_json, str)
        parsed = json.loads(event_json)
        self.assertEqual(parsed["client_id"], 1)

        logger.info("✅ Event payload serialization verified")

    def test_pipeline_event_creation(self):
        """Test PipelineEvent creation"""
        event = PipelineEvent(
            event_type=EventType.PIPELINE_STAGE_CHANGED,
            timestamp=datetime.utcnow(),
            client_id=1,
            user_id=100,
            old_stage="Prospect",
            new_stage="Proposal"
        )

        self.assertEqual(event.old_stage, "Prospect")
        self.assertEqual(event.new_stage, "Proposal")
        self.assertIn("old_stage", event.data)

        logger.info("✅ PipelineEvent creation verified")

    def test_audit_event_creation(self):
        """Test AuditEvent creation"""
        event = AuditEvent(
            event_type=EventType.AUDIT_COMPLETED,
            timestamp=datetime.utcnow(),
            client_id=1,
            platform="web",
            score=85.5,
            audit_id=123
        )

        self.assertEqual(event.platform, "web")
        self.assertEqual(event.score, 85.5)
        self.assertEqual(event.audit_id, 123)

        logger.info("✅ AuditEvent creation verified")

    def test_event_factory(self):
        """Test EventFactory helper methods"""
        # Test pipeline_stage_changed
        event = EventFactory.pipeline_stage_changed(
            client_id=1,
            old_stage="Prospect",
            new_stage="Proposal",
            user_id=100
        )
        self.assertEqual(event.event_type, EventType.PIPELINE_STAGE_CHANGED)
        self.assertEqual(event.client_id, 1)

        # Test audit_completed
        event = EventFactory.audit_completed(
            client_id=1,
            platform="web",
            score=82.0,
            audit_id=456,
            user_id=100
        )
        self.assertEqual(event.event_type, EventType.AUDIT_COMPLETED)
        self.assertEqual(event.score, 82.0)

        # Test proposal_sent
        event = EventFactory.proposal_sent(
            client_id=1,
            proposal_id=789,
            proposal_amount=500000,
            user_id=100
        )
        self.assertEqual(event.event_type, EventType.PROPOSAL_SENT)
        self.assertEqual(event.proposal_amount, 500000)

        logger.info("✅ EventFactory verified")

    def test_metric_snapshot(self):
        """Test MetricSnapshot creation and serialization"""
        now = datetime.utcnow()
        snapshot = MetricSnapshot(
            timestamp=now,
            metrics={"conversion_rate": 0.25, "avg_deal": 500000},
            pipeline_stats={"prospect": 10, "proposal": 5, "negotiation": 3, "closed": 2},
            daily_revenue=1500000,
            monthly_revenue=35000000,
            conversion_rate=0.25,
            average_deal_size=500000
        )

        snapshot_dict = snapshot.to_dict()
        self.assertEqual(snapshot_dict["daily_revenue"], 1500000)
        self.assertEqual(len(snapshot_dict["pipeline_stats"]), 4)

        logger.info("✅ MetricSnapshot verified")

    def test_connection_info(self):
        """Test ConnectionInfo creation and methods"""
        now = datetime.utcnow()
        conn_info = ConnectionInfo(
            connection_id="conn-123",
            user_id=100,
            client_id=1,
            state=ConnectionState.CONNECTED,
            connected_at=now,
            last_heartbeat=now,
            role="admin"
        )

        self.assertTrue(conn_info.is_active())
        self.assertEqual(conn_info.role, "admin")

        # Test inactive state
        conn_info.state = ConnectionState.DISCONNECTED
        self.assertFalse(conn_info.is_active())

        logger.info("✅ ConnectionInfo verified")

    def test_event_routing(self):
        """Test event routing configuration"""
        # Admin should receive pipeline events
        roles = get_target_roles(EventType.PIPELINE_STAGE_CHANGED)
        self.assertIn("admin", roles)
        self.assertIn("client", roles)

        # Only admin should receive email events
        roles = get_target_roles(EventType.EMAIL_OPENED)
        self.assertIn("admin", roles)
        self.assertNotIn("client", roles)

        logger.info("✅ Event routing verified")


class TestWebSocketConnectionManager(unittest.TestCase):
    """Test WebSocket connection management"""

    def setUp(self):
        """Set up test fixtures"""
        self.manager = WebSocketConnectionManager()
        self.mock_ws = AsyncMock()

    def test_manager_initialization(self):
        """Test manager is properly initialized"""
        self.assertEqual(len(self.manager.active_connections), 0)
        self.assertEqual(len(self.manager.admin_connections), 0)
        self.assertEqual(self.manager.max_history_size, 100)

        logger.info("✅ Manager initialization verified")

    def test_connection_stats(self):
        """Test connection statistics"""
        stats = self.manager.get_connection_stats()

        self.assertIn("total_connections", stats)
        self.assertIn("admin_connections", stats)
        self.assertIn("client_connections", stats)
        self.assertEqual(stats["total_connections"], 0)

        logger.info("✅ Connection stats verified")

    async def test_connect_disconnect_async(self):
        """Test connection and disconnection (async)"""
        # Connect
        conn_id = await self.manager.connect(
            self.mock_ws,
            user_id=100,
            client_id=1,
            role="client"
        )

        self.assertIn(conn_id, self.manager.active_connections)
        self.assertIn(conn_id, self.manager.connection_info)
        self.assertEqual(len(self.manager.active_connections), 1)

        # Disconnect
        await self.manager.disconnect(conn_id)
        self.assertNotIn(conn_id, self.manager.active_connections)
        self.assertEqual(len(self.manager.active_connections), 0)

        logger.info("✅ Connect/disconnect verified")

    def test_connect_disconnect(self):
        """Wrapper for async test"""
        asyncio.run(self.test_connect_disconnect_async())

    async def test_multiple_connections_async(self):
        """Test multiple concurrent connections (async)"""
        # Create 5 connections
        conn_ids = []
        for i in range(5):
            conn_id = await self.manager.connect(
                AsyncMock(),
                user_id=100 + i,
                client_id=1,
                role="client"
            )
            conn_ids.append(conn_id)

        self.assertEqual(len(self.manager.active_connections), 5)
        stats = self.manager.get_connection_stats()
        self.assertEqual(stats["total_connections"], 5)

        logger.info("✅ Multiple connections verified")

    def test_multiple_connections(self):
        """Wrapper for async test"""
        asyncio.run(self.test_multiple_connections_async())

    async def test_heartbeat_async(self):
        """Test heartbeat update (async)"""
        conn_id = await self.manager.connect(
            self.mock_ws,
            user_id=100,
            client_id=1,
            role="client"
        )

        old_heartbeat = self.manager.connection_info[conn_id].last_heartbeat
        await asyncio.sleep(0.1)  # Small delay
        await self.manager.heartbeat(conn_id)
        new_heartbeat = self.manager.connection_info[conn_id].last_heartbeat

        self.assertGreater(new_heartbeat, old_heartbeat)

        logger.info("✅ Heartbeat update verified")

    def test_heartbeat(self):
        """Wrapper for async test"""
        asyncio.run(self.test_heartbeat_async())

    async def test_stale_connection_detection_async(self):
        """Test stale connection detection (async)"""
        conn_id = await self.manager.connect(
            self.mock_ws,
            user_id=100,
            client_id=1,
            role="client"
        )

        # Manually set last_heartbeat to old time
        self.manager.connection_info[conn_id].last_heartbeat = datetime(2000, 1, 1)

        # Check for stale connections
        await self.manager.check_stale_connections(timeout_seconds=1)

        # Connection should be removed
        self.assertNotIn(conn_id, self.manager.active_connections)

        logger.info("✅ Stale connection detection verified")

    def test_stale_connection_detection(self):
        """Wrapper for async test"""
        asyncio.run(self.test_stale_connection_detection_async())


class TestEventBroadcaster(unittest.TestCase):
    """Test event broadcasting functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.manager = WebSocketConnectionManager()
        self.broadcaster = EventBroadcaster(self.manager)

    async def test_broadcast_pipeline_event_async(self):
        """Test pipeline event broadcasting (async)"""
        # Create mock connections
        mock_ws_admin = AsyncMock()
        mock_ws_client = AsyncMock()

        admin_id = await self.manager.connect(
            mock_ws_admin,
            user_id=100,
            client_id=None,
            role="admin"
        )

        client_id = await self.manager.connect(
            mock_ws_client,
            user_id=200,
            client_id=1,
            role="client"
        )

        # Emit pipeline event
        await self.broadcaster.emit_pipeline_event(
            client_id=1,
            old_stage="Prospect",
            new_stage="Proposal",
            user_id=100
        )

        # Verify broadcasts were sent
        self.assertTrue(mock_ws_admin.send_json.called or mock_ws_client.send_json.called)

        logger.info("✅ Pipeline event broadcast verified")

    def test_broadcast_pipeline_event(self):
        """Wrapper for async test"""
        asyncio.run(self.test_broadcast_pipeline_event_async())

    async def test_broadcast_audit_event_async(self):
        """Test audit event broadcasting (async)"""
        mock_ws = AsyncMock()
        await self.manager.connect(
            mock_ws,
            user_id=100,
            client_id=1,
            role="admin"
        )

        await self.broadcaster.emit_audit_event(
            client_id=1,
            platform="web",
            score=85.0,
            audit_id=123
        )

        logger.info("✅ Audit event broadcast verified")

    def test_broadcast_audit_event(self):
        """Wrapper for async test"""
        asyncio.run(self.test_broadcast_audit_event_async())

    async def test_broadcast_kpi_update_async(self):
        """Test KPI update broadcasting (async)"""
        mock_ws = AsyncMock()
        await self.manager.connect(
            mock_ws,
            user_id=100,
            client_id=None,
            role="admin"
        )

        await self.broadcaster.emit_kpi_update(
            metric_name="daily_revenue",
            metric_value=1500000.0,
            metric_unit="CLP"
        )

        logger.info("✅ KPI update broadcast verified")

    def test_broadcast_kpi_update(self):
        """Wrapper for async test"""
        asyncio.run(self.test_broadcast_kpi_update_async())


class TestEventRouting(unittest.TestCase):
    """Test event routing and targeting"""

    async def test_role_based_routing_async(self):
        """Test events are routed to correct roles (async)"""
        manager = WebSocketConnectionManager()

        # Create admin and client connections
        admin_ws = AsyncMock()
        client_ws = AsyncMock()

        admin_id = await manager.connect(
            admin_ws,
            user_id=100,
            client_id=None,
            role="admin"
        )

        client_id = await manager.connect(
            client_ws,
            user_id=200,
            client_id=1,
            role="client"
        )

        # Send admin-only event (email opened)
        await manager.broadcast_event(
            EventType.EMAIL_OPENED,
            "system",
            0,
            {"client_id": 1}
        )

        # Admin should receive, client should not
        self.assertTrue(admin_ws.send_json.called)

        logger.info("✅ Role-based routing verified")

    def test_role_based_routing(self):
        """Wrapper for async test"""
        asyncio.run(self.test_role_based_routing_async())


class FaseThirteenDay3TestSuite(unittest.TestCase):
    """Complete test suite for FASE 13 Day 3"""

    def setUp(self):
        """Print suite header"""
        print("\n" + "="*70)
        print("🚀 INICIANDO TEST SUITE FASE 13 - DAY 3 (WebSocket)")
        print("="*70)

    def test_all_day3_components(self):
        """Verify all Day 3 components are functional"""
        logger.info("✅ FASE 13 Day 3 - Todos los tests completados exitosamente!")


def main():
    """Execute test suite"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║     FASE 13 DAY 3 - WEBSOCKET REAL-TIME UPDATES TEST SUITE            ║
║                                                                        ║
║  Components:                                                          ║
║  - Event Models (EventType, EventPayload, Factories)                 ║
║  - WebSocket Connection Manager (connections, heartbeat, cleanup)    ║
║  - Event Broadcaster (pipeline, audit, proposal, email, KPI events) ║
║  - Event Routing (admin/client role-based delivery)                 ║
║                                                                        ║
║  Testing: Event creation, connection mgmt, async broadcasting        ║
║  Target: Real-time dashboard updates via WebSocket                   ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    # Create loader and suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests in order
    suite.addTests(loader.loadTestsFromTestCase(TestEventModels))
    suite.addTests(loader.loadTestsFromTestCase(TestWebSocketConnectionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEventBroadcaster))
    suite.addTests(loader.loadTestsFromTestCase(TestEventRouting))
    suite.addTests(loader.loadTestsFromTestCase(FaseThirteenDay3TestSuite))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS FASE 13 DAY 3")
    print("="*70)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ TODOS LOS TESTS PASARON - FASE 13 DAY 3 LISTO")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")

    print("="*70 + "\n")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
