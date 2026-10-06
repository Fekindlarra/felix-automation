"""
FASE 14 - Lead Capture Routes (FastAPI)
Rutas para captar auditorías desde landing page
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime
import re
import logging
import asyncio

from backend.email_service import send_email
from backend.routes.lead_prediction_integration import (
    process_lead_prediction,
    broadcast_lead_event,
    initialize_prediction_system
)

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/leads", tags=["Lead Capture"])


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class LeadInput(BaseModel):
    """Modelo para captar lead desde landing page"""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: str
    audit_type: str  # quick, complete, deep
    message: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Nombre debe tener al menos 2 caracteres')
        return v.strip()

    @validator('company')
    def validate_company(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Nombre de empresa es requerido')
        return v.strip()

    @validator('audit_type')
    def validate_audit_type(cls, v):
        if v not in ['quick', 'complete', 'deep']:
            raise ValueError('Tipo de auditoría no es válido')
        return v


class LeadResponse(BaseModel):
    """Response al captar lead"""
    success: bool
    message: str
    lead_id: str = "pending"
    confirmation_email: bool


class AuditTypeInfo(BaseModel):
    """Información sobre tipo de auditoría"""
    id: str
    name: str
    price: int
    description: str
    delivery: str
    popular: Optional[bool] = False


class AuditTypesResponse(BaseModel):
    """Response de tipos de auditoría"""
    success: bool
    audit_types: List[AuditTypeInfo]


class LeadStatusResponse(BaseModel):
    """Response de estado del lead"""
    success: bool
    status: str  # pending, contacted, scheduled, completed
    next_step: str
    audit_date: Optional[str] = None


# ============================================================================
# VALIDADORES
# ============================================================================

class LeadValidator:
    """Validar datos de lead antes de capturar"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validar formato de teléfono"""
        if not phone:
            return True  # Opcional
        # Acepta: +56912345678, (56) 9 1234 5678, 912345678, etc
        clean_phone = re.sub(r'\D', '', phone)
        return len(clean_phone) >= 8

    @staticmethod
    def validate(data: dict) -> tuple[bool, List[str]]:
        """Validar todos los campos"""
        errors = []

        # Nombre
        if not data.get('name') or len(data['name'].strip()) < 2:
            errors.append('Nombre debe tener al menos 2 caracteres')

        # Email
        if not data.get('email'):
            errors.append('Email es requerido')
        elif not LeadValidator.validate_email(data['email']):
            errors.append('Email no es válido')

        # Teléfono
        if data.get('phone') and not LeadValidator.validate_phone(data['phone']):
            errors.append('Teléfono no es válido')

        # Empresa
        if not data.get('company') or len(data['company'].strip()) < 2:
            errors.append('Nombre de empresa es requerido')

        # Tipo de auditoría
        valid_types = ['quick', 'complete', 'deep']
        if not data.get('audit_type') or data['audit_type'] not in valid_types:
            errors.append('Tipo de auditoría no es válido')

        return len(errors) == 0, errors


# ============================================================================
# SERVICIOS
# ============================================================================

class LeadService:
    """Servicio para gestionar leads"""

    # Audit type mappings
    AUDIT_NAMES = {
        'quick': 'Auditoría Rápida ($250)',
        'complete': 'Auditoría Completa ($600)',
        'deep': 'Auditoría Profunda ($1,200)'
    }

    @staticmethod
    def create_lead(data: dict) -> dict:
        """Crear lead en base de datos"""
        try:
            lead = {
                'name': data['name'].strip(),
                'email': data['email'].lower().strip(),
                'phone': data.get('phone', '').strip(),
                'company': data['company'].strip(),
                'audit_type': data['audit_type'],
                'message': data.get('message', '').strip(),
                'created_at': datetime.now().isoformat(),
                'status': 'pending',  # pending, contacted, scheduled, completed
                'source': 'landing_page'
            }
            logger.info(f"✅ Lead created: {lead['email']} - {lead['company']}")
            return lead
        except Exception as e:
            logger.error(f"❌ Error creating lead: {str(e)}")
            raise Exception(f'Error creando lead: {str(e)}')

    @staticmethod
    def send_confirmation_email(lead: dict) -> bool:
        """Enviar email de confirmación al cliente"""
        try:
            subject = '✅ Tu Auditoría Online Está en Proceso'

            body = f"""
Hola {lead['name']},

¡Gracias por solicitar tu auditoría online!

**Detalles de tu solicitud:**
- Empresa: {lead['company']}
- Plan: {LeadService.AUDIT_NAMES.get(lead['audit_type'], lead['audit_type'])}
- Teléfono: {lead['phone'] or 'No proporcionado'}

**¿Qué sigue?**
1. Nuestro equipo revisará tu solicitud (24 horas)
2. Te contactaremos para agendar una llamada breve
3. En 48 horas tendrás tu reporte completo en PDF

**Mientras tanto:**
- Puedes ver ejemplos de reportes en: https://tudominio.com/ejemplos
- Lee casos de éxito: https://tudominio.com/casos
- Preguntas frecuentes: https://tudominio.com/faq

Si tienes alguna pregunta urgente, responde este email.

¡Vamos a encontrar qué está frenando tus ventas! 🎯

---
Auditoría Online | En Buena Mesa
felipe@enbuenamesa.com
            """

            success = send_email(
                to=lead['email'],
                subject=subject,
                body=body,
                html=False
            )

            if success:
                logger.info(f"✅ Confirmation email sent to {lead['email']}")
            else:
                logger.warning(f"⚠️ Confirmation email failed for {lead['email']}")

            return success
        except Exception as e:
            logger.error(f"Error sending confirmation email: {str(e)}")
            return False

    @staticmethod
    def send_internal_notification(lead: dict) -> bool:
        """Enviar notificación interna al equipo"""
        try:
            subject = f"🔔 NUEVO LEAD: {lead['company']} - {lead['audit_type'].upper()}"

            body = f"""
NUEVO LEAD CAPTURADO

Nombre: {lead['name']}
Email: {lead['email']}
Teléfono: {lead['phone'] or 'N/A'}
Empresa: {lead['company']}
Tipo: {lead['audit_type']}
Mensaje: {lead['message'] or 'N/A'}

Hora: {lead['created_at']}

ACCIÓN REQUERIDA:
1. Revisar el sitio de {lead['company']}
2. Contactar en 24 horas
3. Agendar auditoría

Dashboard: https://tudominio.com/admin/leads
            """

            # Enviar a email interno
            success = send_email(
                to='felipe@enbuenamesa.com',
                subject=subject,
                body=body,
                html=False
            )

            if success:
                logger.info(f"✅ Internal notification sent for {lead['company']}")
            else:
                logger.warning(f"⚠️ Internal notification failed for {lead['company']}")

            return success
        except Exception as e:
            logger.error(f"Error sending internal notification: {str(e)}")
            return False


# ============================================================================
# RUTAS
# ============================================================================

@router.post('/submit', response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def submit_lead(lead_data: LeadInput):
    """
    Captar lead desde landing page

    POST /api/leads/submit
    {
        "name": "Juan García",
        "email": "juan@empresa.com",
        "phone": "+56912345678",
        "company": "Mi Negocio Online",
        "audit_type": "complete",
        "message": "Me interesa mejorar mis conversiones"
    }
    """
    try:
        # Convertir a dict para validación adicional
        data = {
            'name': lead_data.name,
            'email': lead_data.email,
            'phone': lead_data.phone,
            'company': lead_data.company,
            'audit_type': lead_data.audit_type,
            'message': lead_data.message
        }

        # Validar datos
        is_valid, errors = LeadValidator.validate(data)
        if not is_valid:
            logger.warning(f"❌ Validation failed: {errors}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'success': False,
                    'error': 'Validación fallida',
                    'errors': errors
                }
            )

        # Crear lead
        lead = LeadService.create_lead(data)

        # Enviar emails
        confirmation_sent = LeadService.send_confirmation_email(lead)
        notification_sent = LeadService.send_internal_notification(lead)

        # 🆕 FASE 14: Emitir evento de lead capturado
        await broadcast_lead_event(lead)

        # 🆕 FASE 14: Generar predicción ML en background
        # Ejecutar predicción en background sin bloquear la respuesta
        try:
            prediction_result = await process_lead_prediction(lead_data=lead)
            logger.info(f"✅ Prediction generated in background for {lead['company']}")
        except Exception as e:
            logger.warning(f"⚠️ Prediction generation failed (non-blocking): {e}")

        return LeadResponse(
            success=True,
            message='Lead capturado exitosamente',
            lead_id=lead.get('id', 'pending'),
            confirmation_email=confirmation_sent
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in submit_lead: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'success': False,
                'error': str(e)
            }
        )


@router.get('/audit-types', response_model=AuditTypesResponse)
async def get_audit_types():
    """
    Obtener tipos de auditoría disponibles
    GET /api/leads/audit-types
    """
    return AuditTypesResponse(
        success=True,
        audit_types=[
            AuditTypeInfo(
                id='quick',
                name='Auditoría Rápida',
                price=250,
                description='Web + Tienda',
                delivery='48 horas'
            ),
            AuditTypeInfo(
                id='complete',
                name='Auditoría Completa',
                price=600,
                description='Web + Anuncios + Tienda',
                delivery='48 horas',
                popular=True
            ),
            AuditTypeInfo(
                id='deep',
                name='Auditoría Profunda',
                price=1200,
                description='Todo incluido + Código + Asesoría',
                delivery='72 horas'
            )
        ]
    )


@router.get('/status/{lead_id}', response_model=LeadStatusResponse)
async def get_lead_status(lead_id: str):
    """
    Obtener estado de un lead
    GET /api/leads/status/{lead_id}
    """
    try:
        # Buscar lead en base de datos
        # lead = db.leads.find_one({'id': lead_id})
        # Por ahora, respuesta simulada

        return LeadStatusResponse(
            success=True,
            status='contacted',  # pending, contacted, scheduled, completed
            next_step='Llamada programada para mañana a las 10 AM',
            audit_date='2026-10-07'
        )

    except Exception as e:
        logger.error(f"Error getting lead status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'success': False,
                'error': str(e)
            }
        )


@router.get('/health')
async def health_check():
    """Health check para lead capture service"""
    return {
        'status': 'healthy',
        'service': 'lead_capture',
        'timestamp': datetime.now().isoformat()
    }
