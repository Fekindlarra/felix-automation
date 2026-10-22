#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Scheduler - Programar auditorías automáticas semanales
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from typing import Callable, Optional, Dict, Any

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER GLOBAL
# ═══════════════════════════════════════════════════════════════════════════

_scheduler: Optional[BackgroundScheduler] = None
_scheduled_audits: Dict[str, Dict[str, Any]] = {}

class AuditScheduler:
    """Gestor de auditorías programadas"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduled_audits = {}
    
    def start(self):
        """Inicia el scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Audit Scheduler iniciado")
    
    def stop(self):
        """Detiene el scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Audit Scheduler detenido")
    
    def schedule_weekly_audit(
        self,
        cliente_id: str,
        cliente_nombre: str,
        cliente_email: str,
        audit_callback: Callable,
        day_of_week: int = 0,  # 0=Monday, 6=Sunday
        hour: int = 9,
        minute: int = 0
    ):
        """
        Programa una auditoría semanal automática
        
        Args:
            cliente_id: ID del cliente
            cliente_nombre: Nombre del cliente
            cliente_email: Email para enviar reporte
            audit_callback: Función a llamar para ejecutar auditoría
            day_of_week: Día de la semana (0=lunes)
            hour: Hora de ejecución (0-23)
            minute: Minuto de ejecución (0-59)
        """
        
        job_id = f"audit_{cliente_id}_weekly"
        
        # Crear trigger cron para semanal
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute
        )
        
        # Registrar job
        job = self.scheduler.add_job(
            audit_callback,
            trigger=trigger,
            id=job_id,
            name=f"Weekly audit for {cliente_nombre}",
            args=[cliente_id, cliente_nombre, cliente_email],
            replace_existing=True
        )
        
        # Guardar registro
        self.scheduled_audits[cliente_id] = {
            "job_id": job_id,
            "cliente_nombre": cliente_nombre,
            "cliente_email": cliente_email,
            "day_of_week": day_of_week,
            "hour": hour,
            "minute": minute,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "creado": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📅 Auditoría programada: {cliente_nombre} (cada lunes a {hour:02d}:{minute:02d})")
        
        return job_id
    
    def cancel_audit(self, cliente_id: str):
        """Cancela una auditoría programada"""
        
        job_id = f"audit_{cliente_id}_weekly"
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            del self.scheduled_audits[cliente_id]
            logger.info(f"❌ Auditoría cancelada: {cliente_id}")
            return True
        
        return False
    
    def get_scheduled_audits(self):
        """Obtiene lista de auditorías programadas"""
        return self.scheduled_audits
    
    def get_audit_status(self, cliente_id: str):
        """Obtiene estado de una auditoría programada"""
        
        if cliente_id not in self.scheduled_audits:
            return None
        
        job_id = f"audit_{cliente_id}_weekly"
        job = self.scheduler.get_job(job_id)
        
        if not job:
            return None
        
        audit = self.scheduled_audits[cliente_id]
        audit["next_run"] = job.next_run_time.isoformat() if job.next_run_time else None
        
        return audit

# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON GLOBAL
# ═══════════════════════════════════════════════════════════════════════════

_global_scheduler = None

def get_scheduler() -> AuditScheduler:
    """Obtiene o crea el scheduler global"""
    global _global_scheduler
    
    if _global_scheduler is None:
        _global_scheduler = AuditScheduler()
    
    return _global_scheduler

def start_scheduler():
    """Inicia el scheduler global"""
    scheduler = get_scheduler()
    scheduler.start()

def stop_scheduler():
    """Detiene el scheduler global"""
    scheduler = get_scheduler()
    scheduler.stop()

# ═══════════════════════════════════════════════════════════════════════════
# CALLBACK DE EJEMPLO
# ═══════════════════════════════════════════════════════════════════════════

async def default_audit_callback(
    cliente_id: str,
    cliente_nombre: str,
    cliente_email: str
):
    """
    Callback de auditoría por defecto
    En producción, esto llamaría al pipeline de Hermes
    """
    
    logger.info(f"🔄 Ejecutando auditoría programada para {cliente_nombre}")
    
    # Aquí iría la lógica real:
    # 1. Extraer datos de Instagram via Make.com
    # 2. Llamar a Hermes para análisis
    # 3. Generar PDF
    # 4. Enviar por email
    # 5. Guardar resultado en BD

if __name__ == "__main__":
    # Test del scheduler
    import asyncio
    
    scheduler = get_scheduler()
    scheduler.start()
    
    # Programar una auditoría de prueba
    scheduler.schedule_weekly_audit(
        cliente_id="test-001",
        cliente_nombre="Test Cliente",
        cliente_email="test@example.com",
        audit_callback=default_audit_callback,
        day_of_week=0,  # Lunes
        hour=9,
        minute=0
    )
    
    print("📅 Scheduler de prueba iniciado")
    print("Auditorías programadas:")
    for cliente_id, audit in scheduler.get_scheduled_audits().items():
        print(f"  • {audit['cliente_nombre']}: {audit['next_run']}")

