#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 11: White-Box Audit API Routes
REST endpoints para auditorías profundas con acceso a credenciales
(Shopify, Jumpseller, Code Analysis)
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, Dict
from pydantic import BaseModel

from orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from whitebox.credentials_manager import CredentialsManager

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances
credentials_manager = None
auditor_agent = None


def get_credentials_manager() -> CredentialsManager:
    """Get or create credentials manager instance"""
    global credentials_manager
    if credentials_manager is None:
        credentials_manager = CredentialsManager()
    return credentials_manager


def get_auditor_agent(orchestrator: FelixAutomationOrchestrator) -> MultiPlatformAuditorAgent:
    """Get or create auditor agent instance"""
    global auditor_agent
    if auditor_agent is None:
        auditor_agent = MultiPlatformAuditorAgent(orchestrator)
    return auditor_agent


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class ShopifyCredentials(BaseModel):
    """Credenciales de Shopify"""
    store_domain: str
    access_token: str


class JumpsellerCredentials(BaseModel):
    """Credenciales de Jumpseller"""
    store_name: str
    api_key: str
    api_secret: str


class CodeCredentials(BaseModel):
    """Credenciales para auditoría de código"""
    repository_url: str
    ssh_host: Optional[str] = None
    ssh_user: Optional[str] = None
    ssh_key: Optional[str] = None
    ftp_host: Optional[str] = None
    ftp_user: Optional[str] = None
    ftp_password: Optional[str] = None


class WhiteBoxAuditRequest(BaseModel):
    """Request para white-box audit"""
    client_id: int
    platform: str  # shopify, jumpseller, code
    credentials: Dict


# ============================================================================
# ENDPOINTS: CREDENCIALES
# ============================================================================

@router.post("/api/whitebox/credentials/store")
async def store_credentials(
    token: str,
    client_id: int,
    platform: str,
    credentials_data: Dict,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Almacenar credenciales de forma segura con encriptación.

    Args:
        token: Admin authentication token
        client_id: Client ID
        platform: Plataforma (shopify, jumpseller, code)
        credentials_data: Datos de credenciales

    Returns:
        Status y confirmación de almacenamiento
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        cred_manager = get_credentials_manager()

        # Validar plataforma
        if platform not in ["shopify", "jumpseller", "code"]:
            raise ValueError(f"Platform {platform} not supported")

        # Encriptar y almacenar
        cred_manager.store_credentials(platform, credentials_data)

        logger.info(f"✅ Credenciales almacenadas para {platform} - Cliente {client_id}")

        return {
            "status": "success",
            "message": f"Credenciales de {platform} almacenadas de forma segura",
            "client_id": client_id,
            "platform": platform,
            "expires_in_seconds": 3600
        }

    except Exception as e:
        logger.error(f"❌ Error almacenando credenciales: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/whitebox/credentials/validate")
async def validate_credentials(
    token: str,
    platform: str,
    credentials_data: Dict,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Validar credenciales antes de almacenarlas.

    Args:
        token: Admin authentication token
        platform: Plataforma
        credentials_data: Datos de credenciales

    Returns:
        Status de validación
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        cred_manager = get_credentials_manager()

        # Validar según plataforma
        if platform == "shopify":
            is_valid = cred_manager.validate_shopify_token(credentials_data.get("access_token", ""))
        elif platform == "jumpseller":
            is_valid = cred_manager.validate_jumpseller_key(credentials_data.get("api_key", ""))
        else:
            is_valid = True  # Code audits are more flexible

        return {
            "status": "success",
            "platform": platform,
            "is_valid": is_valid,
            "message": "Credenciales válidas" if is_valid else "Credenciales inválidas"
        }

    except Exception as e:
        logger.error(f"❌ Error validando credenciales: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: SHOPIFY WHITE-BOX AUDIT
# ============================================================================

@router.post("/api/whitebox/audit/shopify")
async def audit_shopify_whitebox(
    token: str,
    client_id: int,
    credentials: ShopifyCredentials,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Ejecutar white-box audit de Shopify.

    Args:
        token: Admin authentication token
        client_id: Client ID
        credentials: Shopify credentials

    Returns:
        Audit results con scores y hallazgos detallados
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        agent = get_auditor_agent(orch)
        cred_manager = get_credentials_manager()

        # Almacenar credenciales temporalmente
        cred_manager.store_credentials("shopify", credentials.dict())

        # Ejecutar auditoría
        audit_result = agent.audit_client_whitebox(
            client_id=client_id,
            platform="shopify",
            credentials=credentials.dict()
        )

        # Limpiar credenciales después de auditoría
        cred_manager.cleanup_expired_credentials()

        logger.info(f"✅ Shopify white-box audit completado - Score: {audit_result.get('score', 0)}")

        return {
            "status": "success",
            "client_id": client_id,
            "platform": "shopify",
            **audit_result
        }

    except Exception as e:
        logger.error(f"❌ Error en Shopify white-box audit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: JUMPSELLER WHITE-BOX AUDIT
# ============================================================================

@router.post("/api/whitebox/audit/jumpseller")
async def audit_jumpseller_whitebox(
    token: str,
    client_id: int,
    credentials: JumpsellerCredentials,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Ejecutar white-box audit de Jumpseller.

    Args:
        token: Admin authentication token
        client_id: Client ID
        credentials: Jumpseller credentials

    Returns:
        Audit results con scores y hallazgos detallados
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        agent = get_auditor_agent(orch)
        cred_manager = get_credentials_manager()

        # Almacenar credenciales temporalmente
        cred_manager.store_credentials("jumpseller", credentials.dict())

        # Ejecutar auditoría
        audit_result = agent.audit_client_whitebox(
            client_id=client_id,
            platform="jumpseller",
            credentials=credentials.dict()
        )

        # Limpiar credenciales
        cred_manager.cleanup_expired_credentials()

        logger.info(f"✅ Jumpseller white-box audit completado - Score: {audit_result.get('score', 0)}")

        return {
            "status": "success",
            "client_id": client_id,
            "platform": "jumpseller",
            **audit_result
        }

    except Exception as e:
        logger.error(f"❌ Error en Jumpseller white-box audit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: CODE WHITE-BOX AUDIT
# ============================================================================

@router.post("/api/whitebox/audit/code")
async def audit_code_whitebox(
    token: str,
    client_id: int,
    credentials: CodeCredentials,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Ejecutar white-box audit de código/infraestructura.

    Args:
        token: Admin authentication token
        client_id: Client ID
        credentials: Code repository credentials

    Returns:
        Audit results con análisis de seguridad, arquitectura, performance
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        agent = get_auditor_agent(orch)
        cred_manager = get_credentials_manager()

        # Almacenar credenciales temporalmente
        cred_manager.store_credentials("code", credentials.dict())

        # Ejecutar auditoría
        audit_result = agent.audit_client_whitebox(
            client_id=client_id,
            platform="code",
            credentials=credentials.dict()
        )

        # Limpiar credenciales
        cred_manager.cleanup_expired_credentials()

        logger.info(f"✅ Code white-box audit completado - Score: {audit_result.get('score', 0)}")

        return {
            "status": "success",
            "client_id": client_id,
            "platform": "code",
            **audit_result
        }

    except Exception as e:
        logger.error(f"❌ Error en Code white-box audit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: AUDITORÍA COMPLETA (Multi-Plataforma)
# ============================================================================

@router.post("/api/whitebox/audit/complete")
async def audit_complete_whitebox(
    token: str,
    client_id: int,
    platforms: list,  # ["shopify", "jumpseller", "code"]
    credentials_map: Dict,  # {"shopify": {...}, "jumpseller": {...}, "code": {...}}
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Ejecutar auditorías white-box completas en múltiples plataformas.

    Args:
        token: Admin authentication token
        client_id: Client ID
        platforms: Lista de plataformas a auditar
        credentials_map: Mapa de credenciales por plataforma

    Returns:
        Resultados consolidados de todas las auditorías
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        agent = get_auditor_agent(orch)
        cred_manager = get_credentials_manager()

        results = {}

        for platform in platforms:
            if platform not in credentials_map:
                logger.warning(f"⚠️  No credentials provided for {platform}")
                continue

            try:
                # Almacenar credenciales
                cred_manager.store_credentials(platform, credentials_map[platform])

                # Ejecutar auditoría
                audit_result = agent.audit_client_whitebox(
                    client_id=client_id,
                    platform=platform,
                    credentials=credentials_map[platform]
                )

                results[platform] = audit_result
                logger.info(f"✅ {platform} audit completado - Score: {audit_result.get('score', 0)}")

            except Exception as e:
                logger.error(f"❌ Error en {platform} audit: {str(e)}")
                results[platform] = {
                    "status": "error",
                    "error": str(e),
                    "score": 0
                }

        # Limpiar todas las credenciales
        cred_manager.cleanup_expired_credentials()

        # Calcular score promedio
        valid_scores = [r.get('score', 0) for r in results.values() if r.get('status') != 'error']
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

        return {
            "status": "success",
            "client_id": client_id,
            "platforms_audited": list(results.keys()),
            "average_score": round(avg_score, 1),
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ Error en auditoría completa: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: HISTORIAL Y REPORTES
# ============================================================================

@router.get("/api/whitebox/audit/history")
async def get_whitebox_history(
    token: str,
    client_id: int = None,
    platform: str = None,
    limit: int = 50,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Obtener historial de auditorías white-box.

    Args:
        token: Admin authentication token
        client_id: Filtro por cliente
        platform: Filtro por plataforma
        limit: Máximo de registros

    Returns:
        Lista de auditorías white-box con scores y timestamps
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        limit = min(limit, 500)  # Cap at 500

        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        # Query audits from database
        query = "SELECT * FROM audits WHERE platform IN ('shopify', 'jumpseller', 'code')"
        params = []

        if client_id:
            query += " AND client_id = ?"
            params.append(client_id)

        if platform:
            query += " AND platform = ?"
            params.append(platform)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = orch.db.execute(query, params)
        audits = cursor.fetchall()

        import json
        results = []
        for audit in audits:
            results.append({
                "id": audit[0],
                "client_id": audit[1],
                "platform": audit[2],
                "score": audit[3],
                "status": audit[4],
                "audit_type": audit[5],
                "created_at": audit[6],
                "details": json.loads(audit[7]) if audit[7] else None
            })

        return {
            "status": "success",
            "total": len(results),
            "client_id": client_id,
            "platform": platform,
            "audits": results
        }

    except Exception as e:
        logger.error(f"❌ Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/whitebox/audit/{audit_id}")
async def get_whitebox_audit_details(
    audit_id: int,
    token: str,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Obtener detalles completos de una auditoría white-box.

    Args:
        audit_id: Audit ID
        token: Admin authentication token

    Returns:
        Detalles completos con hallazgos y recomendaciones
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        cursor = orch.db.execute(
            "SELECT * FROM audits WHERE id = ? AND platform IN ('shopify', 'jumpseller', 'code')",
            (audit_id,)
        )
        audit = cursor.fetchone()

        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")

        import json
        return {
            "status": "success",
            "id": audit[0],
            "client_id": audit[1],
            "platform": audit[2],
            "score": audit[3],
            "audit_status": audit[4],
            "audit_type": audit[5],
            "created_at": audit[6],
            "details": json.loads(audit[7]) if audit[7] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching audit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: SEGURIDAD Y MANEJO DE CREDENCIALES
# ============================================================================

@router.get("/api/whitebox/credentials/status")
async def get_credentials_status(
    token: str,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Obtener estado de credenciales almacenadas.

    Args:
        token: Admin authentication token

    Returns:
        Estado de credenciales, TTL, etc.
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        cred_manager = get_credentials_manager()
        status_info = cred_manager.get_credentials_status()

        return {
            "status": "success",
            "credentials_status": status_info
        }

    except Exception as e:
        logger.error(f"❌ Error getting credentials status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/whitebox/credentials/cleanup")
async def cleanup_credentials(
    token: str,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Limpiar todas las credenciales almacenadas (liberación manual).

    Args:
        token: Admin authentication token

    Returns:
        Confirmación de limpieza
    """
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        cred_manager = get_credentials_manager()
        count = cred_manager.cleanup_expired_credentials()

        logger.info(f"🗑️  {count} credenciales eliminadas manualmente")

        return {
            "status": "success",
            "message": f"{count} credenciales eliminadas",
            "cleaned_platforms": count
        }

    except Exception as e:
        logger.error(f"❌ Error cleaning credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
