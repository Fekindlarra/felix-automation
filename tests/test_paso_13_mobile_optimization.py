#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 13: Mobile Optimization Testing Suite
Test mobile device detection, heartbeat optimization, and bandwidth reduction
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.websocket_manager import WebSocketConnectionManager
from backend.events import ConnectionInfo, ConnectionState


class TestMobileDetection:
    """Test mobile device detection"""

    def test_detect_iphone(self):
        """Test iPhone detection"""
        manager = WebSocketConnectionManager()
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)"
        assert manager._detect_mobile_device(user_agent) is True

    def test_detect_android(self):
        """Test Android detection"""
        manager = WebSocketConnectionManager()
        user_agent = "Mozilla/5.0 (Linux; Android 11; Pixel 5)"
        assert manager._detect_mobile_device(user_agent) is True

    def test_detect_ipad(self):
        """Test iPad detection"""
        manager = WebSocketConnectionManager()
        user_agent = "Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X)"
        assert manager._detect_mobile_device(user_agent) is True

    def test_detect_desktop_chrome(self):
        """Test desktop Chrome is not detected as mobile"""
        manager = WebSocketConnectionManager()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        assert manager._detect_mobile_device(user_agent) is False

    def test_detect_desktop_safari(self):
        """Test desktop Safari is not detected as mobile"""
        manager = WebSocketConnectionManager()
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        assert manager._detect_mobile_device(user_agent) is False

    def test_detect_none_user_agent(self):
        """Test None user agent"""
        manager = WebSocketConnectionManager()
        assert manager._detect_mobile_device(None) is False

    def test_detect_empty_user_agent(self):
        """Test empty user agent"""
        manager = WebSocketConnectionManager()
        assert manager._detect_mobile_device("") is False


class TestHeartbeatOptimization:
    """Test heartbeat interval optimization"""

    @pytest.mark.asyncio
    async def test_mobile_heartbeat_60_seconds(self):
        """Test mobile connections use 60 second heartbeat"""
        manager = WebSocketConnectionManager()
        ws_mock = AsyncMock()

        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)"
        conn_id = await manager.connect(
            ws_mock,
            user_id=1,
            client_id=1,
            user_agent=user_agent
        )

        heartbeat = manager.get_connection_heartbeat(conn_id)
        assert heartbeat == 60

    @pytest.mark.asyncio
    async def test_desktop_heartbeat_30_seconds(self):
        """Test desktop connections use 30 second heartbeat"""
        manager = WebSocketConnectionManager()
        ws_mock = AsyncMock()

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        conn_id = await manager.connect(
            ws_mock,
            user_id=1,
            client_id=1,
            user_agent=user_agent
        )

        heartbeat = manager.get_connection_heartbeat(conn_id)
        assert heartbeat == 30

    @pytest.mark.asyncio
    async def test_no_user_agent_defaults_to_desktop(self):
        """Test missing user agent defaults to desktop heartbeat"""
        manager = WebSocketConnectionManager()
        ws_mock = AsyncMock()

        conn_id = await manager.connect(ws_mock, user_id=1, client_id=1)

        heartbeat = manager.get_connection_heartbeat(conn_id)
        assert heartbeat == 30

    @pytest.mark.asyncio
    async def test_invalid_connection_id(self):
        """Test getting heartbeat for invalid connection"""
        manager = WebSocketConnectionManager()

        heartbeat = manager.get_connection_heartbeat("invalid_id")
        assert heartbeat is None


class TestConnectionTracking:
    """Test connection tracking and statistics"""

    @pytest.mark.asyncio
    async def test_count_mobile_connections(self):
        """Test counting mobile connections"""
        manager = WebSocketConnectionManager()

        # Add 2 mobile connections
        for i in range(2):
            ws_mock = AsyncMock()
            await manager.connect(
                ws_mock,
                user_id=i,
                client_id=i,
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1)"
            )

        # Add 1 desktop connection
        ws_mock = AsyncMock()
        await manager.connect(
            ws_mock,
            user_id=10,
            client_id=10,
            user_agent="Mozilla/5.0 (Windows NT 10.0)"
        )

        assert manager.get_active_mobile_connections() == 2
        assert manager.get_active_desktop_connections() == 1

    @pytest.mark.asyncio
    async def test_mobile_device_flag_in_connection_info(self):
        """Test is_mobile flag is set in connection info"""
        manager = WebSocketConnectionManager()
        ws_mock = AsyncMock()

        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1)"
        conn_id = await manager.connect(
            ws_mock,
            user_id=1,
            client_id=1,
            user_agent=user_agent
        )

        conn_info = manager.connection_info[conn_id]
        assert conn_info.is_mobile is True
        assert conn_info.user_agent == user_agent


class TestBandwidthOptimization:
    """Test event optimization for mobile"""

    def test_optimize_event_removes_internal_fields(self):
        """Test optimization removes internal fields"""
        manager = WebSocketConnectionManager()

        event_data = {
            "client_id": 1,
            "probability": 0.856789,
            "_internal": "should_be_removed",
            "_debug": "should_be_removed",
            "user_data": "keep_this"
        }

        optimized = manager.optimize_event_for_mobile(event_data, is_mobile=True)

        assert "_internal" not in optimized
        assert "_debug" not in optimized
        assert optimized["user_data"] == "keep_this"

    def test_optimize_event_reduces_float_precision(self):
        """Test optimization reduces float precision"""
        manager = WebSocketConnectionManager()

        event_data = {
            "probability": 0.856789,
            "confidence": 0.923456,
            "score": 42.987654
        }

        optimized = manager.optimize_event_for_mobile(event_data, is_mobile=True)

        assert optimized["probability"] == 0.86
        assert optimized["confidence"] == 0.92
        assert optimized["score"] == 42.99

    def test_optimize_event_removes_none_values(self):
        """Test optimization removes None values on mobile"""
        manager = WebSocketConnectionManager()

        event_data = {
            "client_id": 1,
            "data": None,
            "description": "test"
        }

        optimized = manager.optimize_event_for_mobile(event_data, is_mobile=True)

        assert "data" not in optimized
        assert optimized["description"] == "test"

    def test_no_optimization_for_desktop(self):
        """Test no optimization for desktop clients"""
        manager = WebSocketConnectionManager()

        event_data = {
            "probability": 0.856789,
            "data": None,
            "_internal": "keep_this_on_desktop"
        }

        optimized = manager.optimize_event_for_mobile(event_data, is_mobile=False)

        assert optimized == event_data


class TestConnectionInfoMobileFields:
    """Test ConnectionInfo mobile-related methods"""

    def test_get_heartbeat_interval_mobile(self):
        """Test get_heartbeat_interval for mobile"""
        conn_info = ConnectionInfo(
            connection_id="test_id",
            user_id=1,
            client_id=1,
            state=ConnectionState.CONNECTED,
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            role="client",
            is_mobile=True
        )

        assert conn_info.get_heartbeat_interval() == 60

    def test_get_heartbeat_interval_desktop(self):
        """Test get_heartbeat_interval for desktop"""
        conn_info = ConnectionInfo(
            connection_id="test_id",
            user_id=1,
            client_id=1,
            state=ConnectionState.CONNECTED,
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            role="client",
            is_mobile=False
        )

        assert conn_info.get_heartbeat_interval() == 30


class TestPerformanceMetrics:
    """Test performance of mobile optimization"""

    def test_detect_mobile_performance(self):
        """Test mobile detection is performant"""
        manager = WebSocketConnectionManager()
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)"

        # Should detect quickly
        import time
        start = time.time()
        for _ in range(10000):
            manager._detect_mobile_device(user_agent)
        elapsed = time.time() - start

        # Should complete 10k detections in under 100ms
        assert elapsed < 0.1

    def test_event_optimization_performance(self):
        """Test event optimization is performant"""
        manager = WebSocketConnectionManager()
        event_data = {f"field_{i}": i * 0.123456 for i in range(100)}

        import time
        start = time.time()
        for _ in range(1000):
            manager.optimize_event_for_mobile(event_data, is_mobile=True)
        elapsed = time.time() - start

        # Should optimize 1k events in under 50ms
        assert elapsed < 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
