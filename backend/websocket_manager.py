#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 13 Day 3: WebSocket Connection Manager
Real-time event broadcasting and connection management
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Callable
from datetime import datetime
from collections import defaultdict
import uuid

from .events import (
    EventPayload, EventType, ConnectionState, ConnectionInfo,
    get_target_roles
)

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manage WebSocket connections and event broadcasting"""

    def __init__(self):
        # Active connections: connection_id -> websocket
        self.active_connections: Dict[str, any] = {}

        # Connection metadata: connection_id -> ConnectionInfo
        self.connection_info: Dict[str, ConnectionInfo] = {}

        # User connections: user_id -> Set[connection_id]
        self.user_connections: Dict[int, Set[str]] = defaultdict(set)

        # Client connections: client_id -> Set[connection_id]
        self.client_connections: Dict[int, Set[str]] = defaultdict(set)

        # Admin connections (Felipe)
        self.admin_connections: Set[str] = set()

        # Event handlers: event_type -> List[callback]
        self.event_handlers: Dict[EventType, list] = defaultdict(list)

        # Event queue for async processing
        self.event_queue: asyncio.Queue = asyncio.Queue()

        # Event history (for new clients joining)
        self.event_history: Dict[int, list] = defaultdict(list)
        self.max_history_size: int = 100

    async def connect(self, websocket: any, user_id: int,
                     client_id: Optional[int] = None,
                     role: str = "client",
                     user_agent: Optional[str] = None) -> str:
        """Register a new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Detect if client is mobile
        is_mobile = self._detect_mobile_device(user_agent)

        # Store connection
        self.active_connections[connection_id] = websocket

        # Store connection metadata
        conn_info = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            client_id=client_id,
            state=ConnectionState.CONNECTED,
            connected_at=now,
            last_heartbeat=now,
            role=role,
            is_mobile=is_mobile,
            user_agent=user_agent
        )
        self.connection_info[connection_id] = conn_info

        # Index by user and client
        self.user_connections[user_id].add(connection_id)
        if client_id:
            self.client_connections[client_id].add(connection_id)

        # Track admin connections
        if role == "admin":
            self.admin_connections.add(connection_id)

        device_type = "📱 Mobile" if is_mobile else "💻 Desktop"
        logger.info(f"✅ Connection established: {connection_id} ({device_type}, user:{user_id}, role:{role})")

        # Send connection established event with device info
        await self.broadcast_event(
            EventType.CONNECTION_ESTABLISHED,
            connection_id,
            user_id,
            {
                "connection_id": connection_id,
                "is_mobile": is_mobile,
                "heartbeat_interval": conn_info.get_heartbeat_interval()
            }
        )

        return connection_id

    async def disconnect(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id not in self.active_connections:
            return

        # Get connection info
        conn_info = self.connection_info.get(connection_id)
        if not conn_info:
            return

        # Remove from active connections
        del self.active_connections[connection_id]

        # Remove from user connections
        self.user_connections[conn_info.user_id].discard(connection_id)

        # Remove from client connections
        if conn_info.client_id:
            self.client_connections[conn_info.client_id].discard(connection_id)

        # Remove from admin connections
        self.admin_connections.discard(connection_id)

        # Remove metadata
        del self.connection_info[connection_id]

        logger.info(f"❌ Connection closed: {connection_id} (user:{conn_info.user_id})")

    async def send_to_connection(self, connection_id: str, message: dict):
        """Send message to specific connection"""
        if connection_id not in self.active_connections:
            logger.warning(f"Connection not found: {connection_id}")
            return

        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            await self.disconnect(connection_id)

    async def broadcast_event(self, event_type: EventType, connection_id: str,
                             user_id: int, data: dict = None):
        """Broadcast event to eligible connections"""

        # Get target roles for this event
        target_roles = get_target_roles(event_type)

        # Find eligible connections
        eligible_connections = []
        for conn_id, conn_info in self.connection_info.items():
            if conn_info.state != ConnectionState.CONNECTED:
                continue

            # Check role eligibility
            if conn_info.role not in target_roles:
                continue

            # For client events, only send to relevant client or admins
            if event_type.value.startswith("pipeline:") or event_type.value.startswith("audit:"):
                if conn_info.role == "admin" or conn_info.client_id == data.get("client_id"):
                    eligible_connections.append(conn_id)
            else:
                eligible_connections.append(conn_id)

        # Broadcast to eligible connections
        message = {
            "event_type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }

        for conn_id in eligible_connections:
            await self.send_to_connection(conn_id, message)

        # Store in history
        client_id = data.get("client_id") if data else None
        if client_id and len(self.event_history[client_id]) >= self.max_history_size:
            self.event_history[client_id].pop(0)
        if client_id:
            self.event_history[client_id].append(message)

    async def broadcast(self, message: dict, role: str = None, client_id: int = None):
        """
        Generic broadcast method for Phase 3 admin endpoints

        Args:
            message: Message to broadcast
            role: Role to broadcast to ('admin', 'client', None for all)
            client_id: Client ID to broadcast to (only used with role='client')
        """
        if role == "admin":
            await self.broadcast_to_admin(message)
        elif role == "client" and client_id:
            await self.broadcast_to_client(client_id, message)
        else:
            # Broadcast to all connections
            for connection_id in self.active_connections:
                await self.send_to_connection(connection_id, message)

    async def broadcast_to_admin(self, message: dict):
        """Broadcast to all admin connections"""
        for connection_id in self.admin_connections:
            await self.send_to_connection(connection_id, message)

    async def broadcast_to_client(self, client_id: int, message: dict):
        """Broadcast to all connections for a specific client"""
        for connection_id in self.client_connections.get(client_id, set()):
            await self.send_to_connection(connection_id, message)

    def get_active_connections_count(self) -> int:
        """Get total active connections"""
        return len(self.active_connections)

    def get_admin_connections_count(self) -> int:
        """Get admin connections count"""
        return len(self.admin_connections)

    def get_client_connections_count(self, client_id: int) -> int:
        """Get connections for specific client"""
        return len(self.client_connections.get(client_id, set()))

    async def get_event_history(self, client_id: int, limit: int = 50) -> list:
        """Get recent event history for a client"""
        history = self.event_history.get(client_id, [])
        return history[-limit:] if history else []

    async def heartbeat(self, connection_id: str):
        """Update connection heartbeat"""
        if connection_id in self.connection_info:
            self.connection_info[connection_id].last_heartbeat = datetime.utcnow()

    async def check_stale_connections(self, timeout_seconds: int = 300):
        """Remove stale connections (no heartbeat for timeout_seconds)"""
        now = datetime.utcnow()
        stale_connections = []

        for conn_id, conn_info in self.connection_info.items():
            elapsed = (now - conn_info.last_heartbeat).total_seconds()
            if elapsed > timeout_seconds:
                stale_connections.append(conn_id)

        for conn_id in stale_connections:
            logger.warning(f"Removing stale connection: {conn_id}")
            await self.disconnect(conn_id)

    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "admin_connections": len(self.admin_connections),
            "client_connections": len(self.client_connections),
            "active_clients": len([c for c in self.client_connections.values() if c])
        }

    # Mobile Optimization Methods

    def _detect_mobile_device(self, user_agent: Optional[str]) -> bool:
        """Detect if client is a mobile device based on user agent"""
        if not user_agent:
            return False

        mobile_patterns = [
            'Android', 'webOS', 'iPhone', 'iPad', 'iPod',
            'BlackBerry', 'IEMobile', 'Opera Mini',
            'Mobile', 'CriOS'  # Chrome iOS
        ]

        return any(pattern in user_agent for pattern in mobile_patterns)

    def get_connection_heartbeat(self, connection_id: str) -> Optional[int]:
        """Get heartbeat interval for a specific connection (in seconds)"""
        if connection_id not in self.connection_info:
            return None

        conn_info = self.connection_info[connection_id]
        return conn_info.get_heartbeat_interval()

    def get_active_mobile_connections(self) -> int:
        """Count active mobile connections"""
        return sum(
            1 for conn_info in self.connection_info.values()
            if conn_info.is_active() and conn_info.is_mobile
        )

    def get_active_desktop_connections(self) -> int:
        """Count active desktop connections"""
        return sum(
            1 for conn_info in self.connection_info.values()
            if conn_info.is_active() and not conn_info.is_mobile
        )

    def optimize_event_for_mobile(self, event_data: Dict, is_mobile: bool) -> Dict:
        """
        Optimize event payload for mobile clients to reduce bandwidth.
        - Reduce precision of floating point numbers
        - Remove unnecessary fields (any field starting with _)
        - Compress data structures
        """
        if not is_mobile:
            return event_data

        optimized = {}

        for key, value in event_data.items():
            # Skip internal fields (any field starting with underscore)
            if isinstance(key, str) and key.startswith('_'):
                continue

            # Reduce precision of floats
            if isinstance(value, float):
                optimized[key] = round(value, 2)
            # Skip None values on mobile
            elif value is None:
                continue
            else:
                optimized[key] = value

        return optimized


class EventBroadcaster:
    """Broadcast system events to WebSocket clients"""

    def __init__(self, connection_manager: WebSocketConnectionManager):
        self.manager = connection_manager
        self.logger = logging.getLogger(__name__)

    async def emit_pipeline_event(self, client_id: int, old_stage: str,
                                  new_stage: str, user_id: int = None):
        """Emit pipeline stage changed event"""
        message = {
            "event_type": EventType.PIPELINE_STAGE_CHANGED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "old_stage": old_stage,
                "new_stage": new_stage
            }
        }

        await self.manager.broadcast_event(
            EventType.PIPELINE_STAGE_CHANGED,
            "system",
            0,
            message["data"]
        )

        self.logger.info(f"📊 Pipeline event: Client {client_id} moved {old_stage} → {new_stage}")

    async def emit_audit_event(self, client_id: int, platform: str,
                              score: float, audit_id: int):
        """Emit audit completed event"""
        message = {
            "event_type": EventType.AUDIT_COMPLETED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "platform": platform,
                "score": score,
                "audit_id": audit_id
            }
        }

        await self.manager.broadcast_event(
            EventType.AUDIT_COMPLETED,
            "system",
            0,
            message["data"]
        )

        self.logger.info(f"🔍 Audit completed: {platform} score={score}")

    async def emit_proposal_event(self, client_id: int, proposal_id: int,
                                 amount: float):
        """Emit proposal sent event"""
        message = {
            "event_type": EventType.PROPOSAL_SENT.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "proposal_id": proposal_id,
                "amount": amount
            }
        }

        await self.manager.broadcast_event(
            EventType.PROPOSAL_SENT,
            "system",
            0,
            message["data"]
        )

        self.logger.info(f"📋 Proposal sent: ${amount:,.0f}")

    async def emit_email_event(self, client_id: int, email_id: int,
                              event_type: EventType, email_type: str):
        """Emit email tracking event"""
        message = {
            "event_type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "email_id": email_id,
                "email_type": email_type
            }
        }

        await self.manager.broadcast_event(
            event_type,
            "system",
            0,
            message["data"]
        )

        self.logger.info(f"📧 Email event: {event_type.value}")

    async def emit_kpi_update(self, metric_name: str, metric_value: float,
                             metric_unit: str = ""):
        """Emit KPI update event (broadcasts to all admins)"""
        message = {
            "event_type": EventType.KPI_UPDATED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metric_unit": metric_unit
            }
        }

        await self.manager.broadcast_to_admin(message)
        self.logger.info(f"📈 KPI updated: {metric_name}={metric_value} {metric_unit}")

    async def emit_notification(self, client_id: int, title: str, message: str,
                               notification_type: str = "info"):
        """Emit notification event"""
        message_payload = {
            "event_type": EventType.NOTIFICATION_CREATED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "title": title,
                "message": message,
                "notification_type": notification_type
            }
        }

        await self.manager.broadcast_event(
            EventType.NOTIFICATION_CREATED,
            "system",
            0,
            message_payload["data"]
        )

        self.logger.info(f"🔔 Notification: {title}")

    async def emit_prediction(self, client_id: int, probability: float,
                             confidence: float, risk_factors: list,
                             positive_factors: list, recommendation: str,
                             predicted_timeline_days: int):
        """Emit ML prediction event (FASE 14)"""
        message_payload = {
            "event_type": EventType.PREDICTION_GENERATED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "probability": probability,
                "confidence": confidence,
                "risk_factors": risk_factors,
                "positive_factors": positive_factors,
                "recommendation": recommendation,
                "predicted_timeline_days": predicted_timeline_days
            }
        }

        await self.manager.broadcast_event(
            EventType.PREDICTION_GENERATED,
            "system",
            0,
            message_payload["data"]
        )

        self.logger.info(f"🎯 Prediction: Client {client_id} → {probability:.1f}% probability")

    async def emit_anomaly(self, client_id: int, anomaly_type: str,
                          severity: str, description: str, affected_metric: str):
        """Emit anomaly detection event (FASE 14)"""
        message_payload = {
            "event_type": EventType.ANOMALY_DETECTED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "client_id": client_id,
                "anomaly_type": anomaly_type,
                "severity": severity,
                "description": description,
                "affected_metric": affected_metric
            }
        }

        await self.manager.broadcast_event(
            EventType.ANOMALY_DETECTED,
            "system",
            0,
            message_payload["data"]
        )

        self.logger.info(f"⚠️ Anomaly ({severity}): {anomaly_type} - {description}")


# Global connection manager instance
_connection_manager: Optional[WebSocketConnectionManager] = None


def get_connection_manager() -> WebSocketConnectionManager:
    """Get global connection manager (create if needed)"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = WebSocketConnectionManager()
    return _connection_manager


def get_event_broadcaster(manager: Optional[WebSocketConnectionManager] = None) -> EventBroadcaster:
    """Get event broadcaster"""
    if manager is None:
        manager = get_connection_manager()
    return EventBroadcaster(manager)
