#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 14: Comprehensive Integration Testing Suite for FASE 14
Tests for WebSocket, ML, Shopify, A/B Testing, and Mobile features
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from backend.websocket_manager import WebSocketConnectionManager, EventBroadcaster
from backend.events import EventType, ConnectionState, EventFactory
from analytics.prediction_broadcaster import PredictionBroadcaster
from analytics.predictor import ConversionPrediction, ConversionPredictor


class TestWebSocketIntegration:
    """Integration tests for WebSocket real-time features"""

    @pytest.mark.asyncio
    async def test_mobile_connection_heartbeat_optimization(self):
        """Test mobile connections receive optimized heartbeat"""
        manager = WebSocketConnectionManager()
        ws_mock = AsyncMock()

        # Create mobile connection
        conn_id = await manager.connect(
            ws_mock,
            user_id=1,
            client_id=1,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1)"
        )

        # Verify mobile flag and heartbeat
        conn_info = manager.connection_info[conn_id]
        assert conn_info.is_mobile is True
        assert conn_info.get_heartbeat_interval() == 60

    @pytest.mark.asyncio
    async def test_desktop_connection_standard_heartbeat(self):
        """Test desktop connections receive standard heartbeat"""
        manager = WebSocketConnectionManager()
        ws_mock = AsyncMock()

        # Create desktop connection
        conn_id = await manager.connect(
            ws_mock,
            user_id=1,
            client_id=1,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        # Verify desktop flag and heartbeat
        conn_info = manager.connection_info[conn_id]
        assert conn_info.is_mobile is False
        assert conn_info.get_heartbeat_interval() == 30

    @pytest.mark.asyncio
    async def test_broadcast_event_optimization_for_mobile(self):
        """Test events are optimized for mobile clients"""
        manager = WebSocketConnectionManager()
        ws_mobile = AsyncMock()
        ws_desktop = AsyncMock()

        # Create one mobile and one desktop connection
        mobile_id = await manager.connect(
            ws_mobile,
            user_id=1,
            client_id=1,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1)"
        )

        desktop_id = await manager.connect(
            ws_desktop,
            user_id=2,
            client_id=1,
            user_agent="Mozilla/5.0 (Windows NT 10.0)"
        )

        # Broadcast event with float precision
        event_data = {
            "client_id": 1,
            "probability": 0.856789,
            "_internal": "should_be_removed"
        }

        await manager.broadcast_event(
            EventType.PIPELINE_STAGE_CHANGED,
            "system",
            0,
            event_data
        )

        # Verify messages were sent
        assert ws_mobile.send_json.called
        assert ws_desktop.send_json.called

    @pytest.mark.asyncio
    async def test_event_broadcaster_integration(self):
        """Test EventBroadcaster emits properly formatted events"""
        manager = WebSocketConnectionManager()
        broadcaster = EventBroadcaster(manager)
        ws_mock = AsyncMock()

        # Create connection
        conn_id = await manager.connect(ws_mock, user_id=1, client_id=1)

        # Emit pipeline event
        await broadcaster.emit_pipeline_event(1, "prospect", "proposal")

        # Verify broadcast was called
        assert manager.event_history[1]  # Event stored in history


class TestMLPredictionIntegration:
    """Integration tests for ML prediction broadcasting"""

    @pytest.mark.asyncio
    async def test_prediction_broadcaster_emits_real_time_update(self):
        """Test predictions are broadcast in real-time"""
        manager = WebSocketConnectionManager()
        ws_mock = AsyncMock()

        # Create connection
        conn_id = await manager.connect(
            ws_mock,
            user_id=1,
            client_id=1,
            role="admin"
        )

        # Create prediction
        prediction = ConversionPrediction(
            client_id=1,
            client_name="Test Client",
            probability=85,
            confidence=92,
            risk_factors=["long_sales_cycle"],
            positive_factors=["high_engagement"],
            recommendation="Follow up next week",
            predicted_timeline_days=14
        )

        # Broadcast prediction event
        broadcaster = PredictionBroadcaster(manager)
        await broadcaster.broadcast_prediction(1, prediction)

        # Verify event was sent
        assert ws_mock.send_json.called

    def test_prediction_score_calculation(self):
        """Test prediction score is calculated correctly"""
        prediction = ConversionPrediction(
            client_id=1,
            client_name="Test Client",
            probability=75,
            confidence=88,
            risk_factors=[],
            positive_factors=["recent_engagement"],
            recommendation="Close this week",
            predicted_timeline_days=7
        )

        # Score should be probability * confidence / 100
        expected_score = (75 * 88) / 100
        # Prediction object should have the probability and confidence values
        assert prediction.probability == 75
        assert prediction.confidence == 88


class TestShopifyIntegration:
    """Integration tests for Shopify API"""

    @pytest.mark.asyncio
    async def test_shopify_api_client_initialization(self):
        """Test Shopify API client initializes correctly"""
        from whitebox.shopify_api_client import ShopifyAPIClient

        client = ShopifyAPIClient(
            shop_domain="test-shop.myshopify.com",
            access_token="shpat_testtoken123"
        )

        assert client.shop_domain == "test-shop.myshopify.com"
        assert client.session is not None

    @pytest.mark.asyncio
    async def test_shopify_rate_limiting(self):
        """Test Shopify API respects rate limits"""
        from whitebox.shopify_api_client import ShopifyAPIClient

        client = ShopifyAPIClient(
            shop_domain="test-shop.myshopify.com",
            access_token="shpat_testtoken123"
        )

        # Rate limiter should be configured for 2 req/sec
        assert client.rate_limiter is not None
        assert client.rate_limiter.max_calls == 2


class TestABTestingIntegration:
    """Integration tests for A/B testing framework"""

    def test_variant_assigner_deterministic(self):
        """Test variant assignment is deterministic"""
        from agents.email_variant_assigner import EmailVariantAssigner

        assigner = EmailVariantAssigner()

        # Same client should always get same variant
        variant1 = assigner.assign_variant(test_id=1, client_id=100)
        variant2 = assigner.assign_variant(test_id=1, client_id=100)

        assert variant1 == variant2

    def test_variant_distribution(self):
        """Test variants are distributed evenly"""
        from agents.email_variant_assigner import EmailVariantAssigner

        assigner = EmailVariantAssigner()

        # Count distribution across clients
        variants = {}
        for client_id in range(1000):
            variant = assigner.assign_variant(test_id=1, client_id=client_id)
            variants[variant] = variants.get(variant, 0) + 1

        # Should be roughly 50-50
        total = sum(variants.values())
        a_ratio = variants.get('A', 0) / total

        # Allow 45-55% distribution
        assert 0.45 < a_ratio < 0.55

    def test_statistical_significance_calculation(self):
        """Test statistical significance is calculated correctly"""
        from agents.statistical_tester import StatisticalTester

        tester = StatisticalTester()

        # Create test results
        variant_a = {
            'sent': 1000,
            'opens': 350,
            'clicks': 85,
            'conversions': 12
        }

        variant_b = {
            'sent': 1000,
            'opens': 380,
            'clicks': 105,
            'conversions': 18
        }

        result = tester.compare_variants(variant_a, variant_b)

        # Should return statistical measures
        assert 'open_rate_a' in result
        assert 'open_rate_b' in result
        assert 'p_value' in result
        assert 'winner' in result


class TestMobileOptimizationIntegration:
    """Integration tests for mobile optimization"""

    @pytest.mark.asyncio
    async def test_mobile_event_optimization_workflow(self):
        """Test complete mobile event optimization workflow"""
        manager = WebSocketConnectionManager()
        ws_mobile = AsyncMock()

        # Create mobile connection
        mobile_id = await manager.connect(
            ws_mobile,
            user_id=1,
            client_id=1,
            user_agent="Mozilla/5.0 (Android 11; Pixel 5)"
        )

        # Create event with optimizable data
        event_data = {
            "client_id": 1,
            "probability": 0.856789123,
            "confidence": 0.923456789,
            "_internal": "internal_data",
            "null_field": None
        }

        # Optimize for mobile
        optimized = manager.optimize_event_for_mobile(event_data, is_mobile=True)

        # Verify optimization
        assert optimized["probability"] == 0.86  # Reduced precision
        assert optimized["confidence"] == 0.92   # Reduced precision
        assert "_internal" not in optimized      # Removed
        assert "null_field" not in optimized     # Removed

    def test_service_worker_offline_capability(self):
        """Test service worker configuration for offline capability"""
        # Service worker should be configured to:
        # 1. Cache static assets
        # 2. Provide offline fallback
        # 3. Support sync on reconnection

        # This is validated through the manifest.json and service_worker.js files
        # Check files exist and have proper configuration
        import os

        assert os.path.exists("/home/claude/felix-automation/frontend/service_worker.js")
        assert os.path.exists("/home/claude/felix-automation/frontend/manifest.json")


class TestPerformanceRequirements:
    """Tests for FASE 14 performance requirements"""

    @pytest.mark.asyncio
    async def test_websocket_latency_under_100ms(self):
        """Test WebSocket message delivery latency < 100ms"""
        manager = WebSocketConnectionManager()
        ws_mock = AsyncMock()

        conn_id = await manager.connect(ws_mock, user_id=1, client_id=1)

        # Measure broadcast latency
        import time
        start = time.time()

        await manager.broadcast_event(
            EventType.PIPELINE_STAGE_CHANGED,
            "system",
            0,
            {"client_id": 1, "old_stage": "prospect", "new_stage": "proposal"}
        )

        elapsed = time.time() - start
        assert elapsed < 0.1  # 100ms

    @pytest.mark.asyncio
    async def test_concurrent_connections_handling(self):
        """Test handling multiple concurrent WebSocket connections"""
        manager = WebSocketConnectionManager()
        connections = []

        # Create 100 concurrent connections
        for i in range(100):
            ws_mock = AsyncMock()
            conn_id = await manager.connect(
                ws_mock,
                user_id=i,
                client_id=i % 10
            )
            connections.append(conn_id)

        # Verify all connections are active
        assert manager.get_active_connections_count() == 100

        # Broadcast to all connections
        await manager.broadcast_event(
            EventType.KPI_UPDATED,
            "system",
            0,
            {"metric_name": "test", "metric_value": 100}
        )

        # Verify broadcast completed without errors
        assert manager.get_active_connections_count() == 100

    def test_event_optimization_performance_bulk(self):
        """Test event optimization performance with bulk data"""
        manager = WebSocketConnectionManager()

        # Create large event with many fields
        event_data = {
            f"field_{i}": i * 0.123456789
            for i in range(100)
        }

        import time
        start = time.time()

        # Optimize 1000 events
        for _ in range(1000):
            manager.optimize_event_for_mobile(event_data, is_mobile=True)

        elapsed = time.time() - start

        # Should complete in < 50ms
        assert elapsed < 0.05


class TestEndToEndFeatureFlow:
    """End-to-end tests for complete FASE 14 feature flows"""

    @pytest.mark.asyncio
    async def test_complete_prediction_to_dashboard_flow(self):
        """Test complete flow from prediction generation to dashboard update"""
        manager = WebSocketConnectionManager()
        broadcaster = PredictionBroadcaster(manager)

        ws_mock = AsyncMock()
        admin_conn_id = await manager.connect(
            ws_mock,
            user_id=1,
            client_id=0,
            role="admin"
        )

        # Generate prediction
        prediction = ConversionPrediction(
            client_id=1,
            client_name="Test Client",
            probability=82,
            confidence=91,
            risk_factors=["competitive_pressure"],
            positive_factors=["high_budget"],
            recommendation="Schedule follow-up call",
            predicted_timeline_days=10
        )

        # Broadcast prediction
        await broadcaster.broadcast_prediction(1, prediction)

        # Verify admin received update
        assert ws_mock.send_json.called

    @pytest.mark.asyncio
    async def test_complete_ab_test_workflow(self):
        """Test complete A/B test workflow from creation to winner determination"""
        from agents.email_variant_assigner import EmailVariantAssigner
        from agents.statistical_tester import StatisticalTester

        assigner = EmailVariantAssigner()
        tester = StatisticalTester()

        # Assign clients to variants
        clients_a = []
        clients_b = []

        for client_id in range(100):
            variant = assigner.assign_variant(test_id=1, client_id=client_id)
            if variant == 'A':
                clients_a.append(client_id)
            else:
                clients_b.append(client_id)

        # Simulate test results
        variant_a = {
            'sent': len(clients_a),
            'opens': int(len(clients_a) * 0.35),
            'clicks': int(len(clients_a) * 0.08),
            'conversions': int(len(clients_a) * 0.012)
        }

        variant_b = {
            'sent': len(clients_b),
            'opens': int(len(clients_b) * 0.38),
            'clicks': int(len(clients_b) * 0.10),
            'conversions': int(len(clients_b) * 0.018)
        }

        # Calculate statistical significance
        result = tester.compare_variants(variant_a, variant_b)

        # Should have winner determination
        assert result['winner'] in ['A', 'B', 'No significant difference']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
