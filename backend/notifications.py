#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 13 Day 4: Sistema de Notificaciones Avanzado
Notificaciones en tiempo real + Email + Alertas
"""

import asyncio
import json
import logging
from typing import Dict, Optional, List
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Tipos de notificación"""
    AUDIT_COMPLETED = "audit_completed"
    PROPOSAL_GENERATED = "proposal_generated"
    PROPOSAL_SENT = "proposal_sent"
    PIPELINE_CHANGED = "pipeline_changed"
    EMAIL_OPENED = "email_opened"
    FOLLOW_UP_DUE = "follow_up_due"
    ALERT_WARNING = "alert_warning"
    ALERT_ERROR = "alert_error"


class NotificationPriority(Enum):
    """Prioridad de notificación"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Notification:
    """Estructura de notificación"""
    id: str
    client_id: int
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    icon: str
    created_at: datetime
    read: bool = False
    action_url: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'client_id': self.client_id,
            'type': self.type.value,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'icon': self.icon,
            'created_at': self.created_at.isoformat(),
            'read': self.read,
            'action_url': self.action_url,
            'metadata': self.metadata or {}
        }


class NotificationService:
    """Servicio centralizado de notificaciones"""

    def __init__(self, event_broadcaster=None):
        self.broadcaster = event_broadcaster
        self.notifications: Dict[str, Notification] = {}
        self.notification_queue: List[Notification] = []
        logger.info("✅ Notification Service inicializado")

    async def notify_audit_completed(self, client_id: int, platform: str,
                                    score: float, audit_id: int):
        """Notificar auditoría completada"""
        notification = Notification(
            id=f"audit_{audit_id}_{datetime.utcnow().timestamp()}",
            client_id=client_id,
            type=NotificationType.AUDIT_COMPLETED,
            priority=NotificationPriority.HIGH,
            title=f"✅ Auditoría {platform.capitalize()} Completada",
            message=f"Tu auditoría de {platform} obtuvo un score de {score}/100. Revisa los detalles en el dashboard.",
            icon="📊",
            created_at=datetime.utcnow(),
            action_url=f"/dashboard/client/{client_id}#audits",
            metadata={
                'platform': platform,
                'score': score,
                'audit_id': audit_id
            }
        )

        await self.send_notification(notification)
        logger.info(f"🔔 Notificación de auditoría: {platform} - {score}/100")

    async def notify_proposal_generated(self, client_id: int, proposal_id: int,
                                       amount: float):
        """Notificar propuesta generada"""
        notification = Notification(
            id=f"proposal_{proposal_id}_{datetime.utcnow().timestamp()}",
            client_id=client_id,
            type=NotificationType.PROPOSAL_GENERATED,
            priority=NotificationPriority.HIGH,
            title="📋 Propuesta Personalizada Lista",
            message=f"Hemos generado tu propuesta personalizada por ${amount:,.0f}. Te la enviaremos por email en breve.",
            icon="📋",
            created_at=datetime.utcnow(),
            action_url=f"/dashboard/client/{client_id}#proposal",
            metadata={
                'proposal_id': proposal_id,
                'amount': amount
            }
        )

        await self.send_notification(notification)
        logger.info(f"🔔 Notificación de propuesta: ${amount:,.0f}")

    async def notify_proposal_sent(self, client_id: int, proposal_id: int,
                                  recipient_email: str):
        """Notificar propuesta enviada"""
        notification = Notification(
            id=f"proposal_sent_{proposal_id}_{datetime.utcnow().timestamp()}",
            client_id=client_id,
            type=NotificationType.PROPOSAL_SENT,
            priority=NotificationPriority.MEDIUM,
            title="📧 Propuesta Enviada",
            message=f"Tu propuesta ha sido enviada a {recipient_email}. Esperamos tu feedback.",
            icon="📧",
            created_at=datetime.utcnow(),
            action_url=f"/dashboard/client/{client_id}#proposal",
            metadata={
                'proposal_id': proposal_id,
                'recipient_email': recipient_email
            }
        )

        await self.send_notification(notification)
        logger.info(f"🔔 Notificación de envío de propuesta")

    async def notify_pipeline_changed(self, client_id: int, old_stage: str,
                                     new_stage: str, client_name: str = ""):
        """Notificar cambio de etapa en pipeline"""
        stage_emojis = {
            'prospecto': '🎯',
            'propuesta': '📋',
            'negociacion': '🤝',
            'cerrado': '✅'
        }

        notification = Notification(
            id=f"pipeline_{client_id}_{datetime.utcnow().timestamp()}",
            client_id=client_id,
            type=NotificationType.PIPELINE_CHANGED,
            priority=NotificationPriority.MEDIUM,
            title=f"{stage_emojis.get(new_stage, '🔄')} Cambio de Etapa",
            message=f"Cliente {client_name} movió de {old_stage} → {new_stage}",
            icon=stage_emojis.get(new_stage, '🔄'),
            created_at=datetime.utcnow(),
            action_url=f"/dashboard/admin#pipeline",
            metadata={
                'old_stage': old_stage,
                'new_stage': new_stage,
                'client_name': client_name
            }
        )

        await self.send_notification(notification)
        logger.info(f"🔔 Notificación de pipeline: {old_stage} → {new_stage}")

    async def notify_follow_up_due(self, client_id: int, client_name: str,
                                  days_since_proposal: int):
        """Alertar que es hora de hacer follow-up"""
        notification = Notification(
            id=f"followup_{client_id}_{datetime.utcnow().timestamp()}",
            client_id=client_id,
            type=NotificationType.FOLLOW_UP_DUE,
            priority=NotificationPriority.HIGH,
            title="📞 Follow-up Pendiente",
            message=f"{client_name} hace {days_since_proposal} días que recibió la propuesta. ¡Es hora de hacer seguimiento!",
            icon="📞",
            created_at=datetime.utcnow(),
            action_url=f"/dashboard/admin#client/{client_id}",
            metadata={
                'days_since_proposal': days_since_proposal,
                'client_name': client_name
            }
        )

        await self.send_notification(notification)
        logger.info(f"🔔 Notificación de follow-up para: {client_name}")

    async def notify_alert(self, title: str, message: str, alert_type: str = "warning",
                          priority: NotificationPriority = NotificationPriority.HIGH,
                          client_id: Optional[int] = None, icon: str = "⚠️"):
        """Enviar alerta general"""
        notification_type = (NotificationType.ALERT_WARNING if alert_type == "warning"
                           else NotificationType.ALERT_ERROR)

        notification = Notification(
            id=f"alert_{datetime.utcnow().timestamp()}",
            client_id=client_id or 0,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            icon=icon,
            created_at=datetime.utcnow()
        )

        await self.send_notification(notification)
        logger.warning(f"🔔 Alerta: {title}")

    async def send_notification(self, notification: Notification):
        """Enviar notificación a través de todos los canales"""
        # Almacenar en caché
        self.notifications[notification.id] = notification
        self.notification_queue.append(notification)

        # Emitir evento WebSocket si está disponible
        if self.broadcaster:
            try:
                await self.broadcaster.emit_notification(
                    client_id=notification.client_id,
                    title=notification.title,
                    message=notification.message,
                    notification_type=notification.type.value
                )
            except Exception as e:
                logger.error(f"Error emitiendo evento WebSocket: {e}")

        logger.info(f"📨 Notificación enviada: {notification.title}")

    def get_notifications(self, client_id: int, limit: int = 50,
                         unread_only: bool = False) -> List[Notification]:
        """Obtener notificaciones de un cliente"""
        notifications = [
            n for n in self.notifications.values()
            if n.client_id == client_id
        ]

        if unread_only:
            notifications = [n for n in notifications if not n.read]

        return sorted(notifications, key=lambda x: x.created_at,
                     reverse=True)[:limit]

    def mark_as_read(self, notification_id: str) -> bool:
        """Marcar notificación como leída"""
        if notification_id in self.notifications:
            self.notifications[notification_id].read = True
            return True
        return False

    def get_unread_count(self, client_id: int) -> int:
        """Obtener cantidad de notificaciones sin leer"""
        return len([
            n for n in self.notifications.values()
            if n.client_id == client_id and not n.read
        ])

    async def get_alerts_summary(self) -> Dict:
        """Resumen de alertas activas del sistema"""
        return {
            'total_notifications': len(self.notifications),
            'queue_size': len(self.notification_queue),
            'critical_alerts': len([
                n for n in self.notifications.values()
                if n.priority == NotificationPriority.CRITICAL
            ]),
            'unread_by_priority': {
                'critical': len([n for n in self.notifications.values()
                               if n.priority == NotificationPriority.CRITICAL and not n.read]),
                'high': len([n for n in self.notifications.values()
                           if n.priority == NotificationPriority.HIGH and not n.read]),
                'medium': len([n for n in self.notifications.values()
                             if n.priority == NotificationPriority.MEDIUM and not n.read])
            }
        }


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service(broadcaster=None) -> NotificationService:
    """Obtener instancia global del servicio de notificaciones"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(broadcaster)
    return _notification_service
