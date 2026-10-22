#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoints para gestionar auditorías programadas
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from backend.services.audit_scheduler import get_scheduler

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# MODELOS
# ═══════════════════════════════════════════════════════════════════════════

class ScheduleAuditRequest(BaseModel):
    """Request para programar una auditoría"""
    cliente_id: str
    cliente_nombre: str
    cliente_email: EmailStr
    day_of_week: int = 0  # 0=Monday, 6=Sunday
    hour: int = 9
    minute: int = 0

class AuditScheduleInfo(BaseModel):
    """Información de auditoría programada"""
    cliente_id: str
    cliente_nombre: str
    cliente_email: str
    day_of_week: int
    hour: int
    minute: int
    next_run: Optional[str]
    creado: str

class SchedulerStats(BaseModel):
    """Estadísticas del scheduler"""
    total_programadas: int
    proximas_ejecuciones: List[Dict[str, Any]]
    activo: bool

# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/schedule", status_code=status.HTTP_201_CREATED)
async def schedule_audit(request: ScheduleAuditRequest):
    """Programa una auditoría semanal automática"""
    
    try:
        scheduler = get_scheduler()
        
        # Aquí iría la lógica real de callback
        from backend.services.audit_scheduler import default_audit_callback
        
        job_id = scheduler.schedule_weekly_audit(
            cliente_id=request.cliente_id,
            cliente_nombre=request.cliente_nombre,
            cliente_email=request.cliente_email,
            audit_callback=default_audit_callback,
            day_of_week=request.day_of_week,
            hour=request.hour,
            minute=request.minute
        )
        
        logger.info(f"✅ Auditoría programada: {request.cliente_nombre}")
        
        return {
            "status": "programada",
            "job_id": job_id,
            "cliente": request.cliente_nombre,
            "mensaje": f"Auditoría programada para cada {['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][request.day_of_week]} a las {request.hour:02d}:{request.minute:02d}"
        }
    
    except Exception as e:
        logger.error(f"Error programando auditoría: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al programar auditoría: {str(e)}"
        )

@router.get("/list", response_model=List[AuditScheduleInfo])
async def list_scheduled_audits():
    """Listar todas las auditorías programadas"""
    
    try:
        scheduler = get_scheduler()
        audits = scheduler.get_scheduled_audits()
        
        return [
            AuditScheduleInfo(
                cliente_id=k,
                cliente_nombre=v["cliente_nombre"],
                cliente_email=v["cliente_email"],
                day_of_week=v["day_of_week"],
                hour=v["hour"],
                minute=v["minute"],
                next_run=v.get("next_run"),
                creado=v["creado"]
            )
            for k, v in audits.items()
        ]
    
    except Exception as e:
        logger.error(f"Error listando auditorías programadas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar auditorías programadas"
        )

@router.get("/{cliente_id}", response_model=AuditScheduleInfo)
async def get_scheduled_audit(cliente_id: str):
    """Obtener detalles de una auditoría programada"""
    
    try:
        scheduler = get_scheduler()
        audit = scheduler.get_audit_status(cliente_id)
        
        if not audit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Auditoría programada no encontrada"
            )
        
        return AuditScheduleInfo(
            cliente_id=cliente_id,
            cliente_nombre=audit["cliente_nombre"],
            cliente_email=audit["cliente_email"],
            day_of_week=audit["day_of_week"],
            hour=audit["hour"],
            minute=audit["minute"],
            next_run=audit.get("next_run"),
            creado=audit["creado"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo auditoría programada: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener auditoría programada"
        )

@router.delete("/{cliente_id}")
async def cancel_scheduled_audit(cliente_id: str):
    """Cancela una auditoría programada"""
    
    try:
        scheduler = get_scheduler()
        
        if not scheduler.cancel_audit(cliente_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Auditoría programada no encontrada"
            )
        
        logger.info(f"✅ Auditoría cancelada: {cliente_id}")
        
        return {
            "status": "cancelada",
            "cliente_id": cliente_id,
            "mensaje": "Auditoría programada cancelada exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelando auditoría: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cancelar auditoría"
        )

@router.get("/stats", response_model=SchedulerStats)
async def get_scheduler_stats():
    """Obtener estadísticas del scheduler"""
    
    try:
        scheduler = get_scheduler()
        audits = scheduler.get_scheduled_audits()
        
        proximas = [
            {
                "cliente": v["cliente_nombre"],
                "next_run": v.get("next_run"),
                "frecuencia": f"Cada {['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][v['day_of_week']]}"
            }
            for v in audits.values()
        ]
        
        return SchedulerStats(
            total_programadas=len(audits),
            proximas_ejecuciones=proximas,
            activo=scheduler.scheduler.running
        )
    
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estadísticas del scheduler"
        )

