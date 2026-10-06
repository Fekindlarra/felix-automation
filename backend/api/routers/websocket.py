"""
WebSocket router for real-time prediction updates and events
Handles client connections, authentication, and event broadcasting
"""
import json
import logging
from typing import Set, Dict, List
from datetime import datetime
from fastapi import WebSocket, APIRouter, Query, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import Event, Prediction, Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections with authentication and event broadcasting"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
        self.connection_metadata: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str, user_id: str):
        """Register a new WebSocket connection"""
        await websocket.accept()
        connection_id = f"{user_id}_{client_id}_{datetime.now().timestamp()}"
        self.active_connections[connection_id] = websocket
        self.client_subscriptions[connection_id] = {client_id}
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "client_id": client_id,
            "connected_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now()
        }
        logger.info(f"✅ Client connected: {connection_id} (Total: {len(self.active_connections)})")
        return connection_id

    def disconnect(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            if connection_id in self.client_subscriptions:
                del self.client_subscriptions[connection_id]
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            logger.info(f"❌ Client disconnected: {connection_id} (Total: {len(self.active_connections)})")

    async def broadcast_prediction(self, event: dict):
        """Broadcast prediction event to all subscribed clients"""
        if not self.active_connections:
            return

        disconnected = []
        for conn_id, websocket in self.active_connections.items():
            client_id = self.client_subscriptions.get(conn_id, set())

            # Only send if client is subscribed to this event
            if event.get("client_id") in client_id:
                try:
                    await websocket.send_json({
                        "type": "prediction:generated",
                        "timestamp": datetime.now().isoformat(),
                        "data": event
                    })
                except Exception as e:
                    logger.error(f"Error sending to {conn_id}: {e}")
                    disconnected.append(conn_id)

        # Clean up disconnected clients
        for conn_id in disconnected:
            self.disconnect(conn_id)

    async def broadcast_event(self, event_type: str, payload: dict):
        """Broadcast generic event to all connected clients"""
        if not self.active_connections:
            return

        disconnected = []
        message = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "payload": payload
        }

        for conn_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {conn_id}: {e}")
                disconnected.append(conn_id)

        # Clean up disconnected clients
        for conn_id in disconnected:
            self.disconnect(conn_id)

    async def send_heartbeat(self, connection_id: str):
        """Send heartbeat ping to verify connection is alive"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "connections_online": len(self.active_connections)
                })
                self.connection_metadata[connection_id]["last_heartbeat"] = datetime.now()
            except Exception as e:
                logger.error(f"Heartbeat failed for {connection_id}: {e}")
                self.disconnect(connection_id)

    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "unique_clients": len(set(
                client for clients in self.client_subscriptions.values()
                for client in clients
            )),
            "connections": [
                {
                    "id": conn_id,
                    "user_id": meta.get("user_id"),
                    "client_id": meta.get("client_id"),
                    "connected_at": meta.get("connected_at"),
                    "latency_ms": 0  # Will be calculated from heartbeat
                }
                for conn_id, meta in self.connection_metadata.items()
            ]
        }


# Global connection manager
manager = ConnectionManager()


# WebSocket endpoint for real-time updates
@router.websocket("/predictions/{user_id}/{client_id}")
async def websocket_predictions(
    websocket: WebSocket,
    user_id: str,
    client_id: str,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time prediction updates

    URL: ws://localhost:8000/ws/predictions/{user_id}/{client_id}?token={jwt_token}

    Messages received:
    - {"type": "subscribe", "client_ids": ["client_001", "client_002"]}
    - {"type": "pong"}  (response to heartbeat)

    Messages sent:
    - {"type": "prediction:generated", "data": {...}}
    - {"type": "heartbeat", "timestamp": "..."}
    - {"type": "connection_confirmed", "connection_id": "..."}
    """

    # TODO: Verify JWT token here
    # from backend.api.routers.auth import verify_jwt_token
    # if not verify_jwt_token(token):
    #     await websocket.close(code=4001, reason="Unauthorized")
    #     return

    connection_id = await manager.connect(websocket, client_id, user_id)

    # Send connection confirmation
    await websocket.send_json({
        "type": "connection_confirmed",
        "connection_id": connection_id,
        "timestamp": datetime.now().isoformat()
    })

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "subscribe":
                # Client wants to subscribe to specific clients
                client_ids = message.get("client_ids", [client_id])
                manager.client_subscriptions[connection_id] = set(client_ids)
                await websocket.send_json({
                    "type": "subscription_updated",
                    "subscribed_to": list(client_ids),
                    "timestamp": datetime.now().isoformat()
                })

            elif msg_type == "pong":
                # Client responded to heartbeat
                manager.connection_metadata[connection_id]["last_heartbeat"] = datetime.now()

            elif msg_type == "ping":
                # Client sent ping, send pong
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            else:
                logger.warning(f"Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)


# REST endpoint to broadcast events (for backend use)
@router.post("/broadcast/prediction")
async def broadcast_prediction(event: dict, db: Session = Depends(get_db)):
    """
    Broadcast a prediction event to all subscribed WebSocket clients

    Body:
    {
        "client_id": "client_001",
        "probability": 75.5,
        "confidence": 0.92,
        "risk_factors": ["Low website quality"],
        "positive_factors": ["Good engagement"],
        "timeline_days": 14,
        "shap_explanation": [...]
    }
    """
    await manager.broadcast_prediction(event)
    return {"status": "broadcasted", "recipients": len(manager.active_connections)}


@router.post("/broadcast/event")
async def broadcast_event(event_type: str, payload: dict):
    """Broadcast generic event to all WebSocket clients"""
    await manager.broadcast_event(event_type, payload)
    return {"status": "broadcasted", "type": event_type, "recipients": len(manager.active_connections)}


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return manager.get_stats()


@router.post("/test-broadcast")
async def test_broadcast(client_id: str = "test_client"):
    """Test broadcast - sends sample prediction event"""
    await manager.broadcast_prediction({
        "client_id": client_id,
        "probability": 72.5,
        "confidence": 0.88,
        "risk_factors": ["Low website quality"],
        "positive_factors": ["Growing engagement"],
        "timeline_days": 14
    })
    return {"status": "test message sent"}
