#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 13 Day 3: WebSocket Routes
Real-time connection handlers and event routes
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Optional
import json
from datetime import datetime

from ..websocket_manager import get_connection_manager, get_event_broadcaster
from ..auth import verify_jwt_token
from ..events import EventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    client_id: Optional[int] = Query(None)
):
    """
    WebSocket endpoint for real-time updates

    Query parameters:
    - token: JWT authentication token (required)
    - client_id: Client ID (optional, for client role connections)
    """

    # Verify token
    try:
        payload = verify_jwt_token(token)
        user_id = payload.get("user_id")
        role = payload.get("role", "client")
    except Exception as e:
        logger.error(f"❌ WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Accept connection
    await websocket.accept()
    logger.info(f"🔗 WebSocket connected: user={user_id}, role={role}")

    # Get connection manager
    manager = get_connection_manager()
    broadcaster = get_event_broadcaster(manager)

    # Register connection
    connection_id = await manager.connect(
        websocket,
        user_id=user_id,
        client_id=client_id,
        role=role
    )

    try:
        # Send initial connection message with stats
        stats = manager.get_connection_stats()
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "user_id": user_id,
            "role": role,
            "stats": stats
        })

        # Send event history for this client (if relevant)
        if client_id and role == "client":
            history = await manager.get_event_history(client_id, limit=20)
            if history:
                await websocket.send_json({
                    "type": "history",
                    "events": history
                })

        # Main message loop
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Update heartbeat
            await manager.heartbeat(connection_id)

            # Process message type
            message_type = data.get("type")

            if message_type == "ping":
                # Heartbeat/ping response
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

            elif message_type == "sync_request":
                # Request for latest stats
                stats = manager.get_connection_stats()
                await websocket.send_json({
                    "type": "sync",
                    "stats": stats
                })

            elif message_type == "subscribe":
                # Subscribe to specific events (admin only)
                if role == "admin":
                    events = data.get("events", [])
                    logger.info(f"🔔 Admin subscribed to: {events}")
                    await websocket.send_json({
                        "type": "subscribed",
                        "events": events
                    })

            else:
                logger.warning(f"⚠️ Unknown message type: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {connection_id}")
        await manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await manager.disconnect(connection_id)


@router.get("/stats")
async def get_websocket_stats(token: str = Query(...)):
    """Get WebSocket connection statistics"""
    try:
        payload = verify_jwt_token(token)
    except Exception as e:
        return {"error": "Authentication failed"}

    manager = get_connection_manager()
    return manager.get_connection_stats()


@router.post("/broadcast/notification")
async def broadcast_notification(
    title: str,
    message: str,
    client_id: Optional[int] = None,
    token: str = Query(...)
):
    """Broadcast notification to clients (admin only)"""
    try:
        payload = verify_jwt_token(token)
        if payload.get("role") != "admin":
            return {"error": "Admin access required"}
    except Exception as e:
        return {"error": "Authentication failed"}

    manager = get_connection_manager()
    broadcaster = get_event_broadcaster(manager)

    if client_id:
        # Send to specific client
        message_data = {
            "type": "notification",
            "title": title,
            "message": message
        }
        await manager.broadcast_to_client(client_id, message_data)
    else:
        # Send to all admins
        message_data = {
            "type": "notification",
            "title": title,
            "message": message
        }
        await manager.broadcast_to_admin(message_data)

    return {"status": "sent"}


@router.get("/connections/user/{user_id}")
async def get_user_connections(user_id: int, token: str = Query(...)):
    """Get connections for a specific user"""
    try:
        payload = verify_jwt_token(token)
        if payload.get("role") != "admin":
            return {"error": "Admin access required"}
    except Exception as e:
        return {"error": "Authentication failed"}

    manager = get_connection_manager()
    connection_ids = list(manager.user_connections.get(user_id, set()))

    connections = []
    for conn_id in connection_ids:
        conn_info = manager.connection_info.get(conn_id)
        if conn_info:
            connections.append({
                "connection_id": conn_id,
                "user_id": conn_info.user_id,
                "client_id": conn_info.client_id,
                "role": conn_info.role,
                "state": conn_info.state.value,
                "connected_at": conn_info.connected_at.isoformat(),
                "last_heartbeat": conn_info.last_heartbeat.isoformat()
            })

    return {"connections": connections}


@router.get("/connections/client/{client_id}")
async def get_client_connections(client_id: int, token: str = Query(...)):
    """Get connections for a specific client"""
    try:
        payload = verify_jwt_token(token)
        # Allow admin or the client themselves
        if payload.get("role") != "admin" and payload.get("client_id") != client_id:
            return {"error": "Access denied"}
    except Exception as e:
        return {"error": "Authentication failed"}

    manager = get_connection_manager()
    connection_count = manager.get_client_connections_count(client_id)

    return {
        "client_id": client_id,
        "active_connections": connection_count
    }


@router.post("/cleanup/stale")
async def cleanup_stale_connections(timeout_seconds: int = 300, token: str = Query(...)):
    """Remove stale connections (admin only)"""
    try:
        payload = verify_jwt_token(token)
        if payload.get("role") != "admin":
            return {"error": "Admin access required"}
    except Exception as e:
        return {"error": "Authentication failed"}

    manager = get_connection_manager()
    await manager.check_stale_connections(timeout_seconds)

    return {
        "status": "cleanup complete",
        "remaining_connections": manager.get_active_connections_count()
    }
