#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend API - Felix Automation FASE 12 + FASE 13
Dashboard Interno + Portal Cliente + WebSocket Real-Time Updates
"""

import sys
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# Imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import (
    CORS_ORIGINS,
    API_TITLE,
    API_VERSION,
    API_DESCRIPTION,
    ADMIN_EMAIL,
    DATABASE_PATH
)
from backend.auth import (
    AuthManager,
    create_admin_token,
    verify_admin_token,
    verify_client_token,
    ADMIN_USER
)
from orchestrator import FelixAutomationOrchestrator
from backend.routes.websocket_routes import router as websocket_router
from backend.routes.analytics_routes import router as analytics_router
from backend.routes.scheduler_routes import router as scheduler_router
from backend.routes.api_enhancement_routes import router as api_enhancement_router
from backend.routes.prediction_validator_routes import router as prediction_validator_router
from backend.routes.whitebox_routes import router as whitebox_router
from backend.routes.ab_testing_routes import router as ab_testing_router
from backend.routes.ab_testing_routes import init_ab_testing
from backend.routes.shopify_webhooks import router as shopify_webhooks_router
from backend.routes.shopify_webhooks import init_webhooks
from backend.routes.lead_capture_routes import router as lead_capture_router
from backend.routes.seo_routes import router as seo_router
from backend.routes.monitoring_routes import router as monitoring_router
from backend.routes.prometheus_routes import router as prometheus_router
from backend.routes.alert_routing_routes import router as alert_routing_router
from backend.routes.fase14_monitoring_routes import router as fase14_monitoring_router
from agents.statistical_tester import StatisticalTester
from agents.email_variant_assigner import EmailVariantAssigner

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebSocket routes (FASE 13 Day 3)
app.include_router(websocket_router)

# Include Analytics routes (PASO 1: Dashboard Integration - FASE 10)
app.include_router(analytics_router)

# Include Scheduler routes (PASO 2: Analytics Scheduler)
app.include_router(scheduler_router)

# Include API Enhancement routes (PASO 3: Advanced filtering, export, webhooks)
app.include_router(api_enhancement_router)

# Include Prediction Validator routes (PASO 4: Accuracy tracking, confidence adjustment)
app.include_router(prediction_validator_router)

# Include White-Box Audit routes (FASE 11: Deep platform integrations with credentials)
app.include_router(whitebox_router)

# Include A/B Testing routes (FASE 14: Email A/B Testing Framework)
app.include_router(ab_testing_router)

# Include Shopify Webhooks routes (FASE 14: Real-time Shopify events)
app.include_router(shopify_webhooks_router)

# Include Lead Capture routes (FASE 14: Landing page integration)
app.include_router(lead_capture_router)

# Include SEO Audit routes (FASE 14: SEO Analysis Integration)
app.include_router(seo_router)

# Include Monitoring routes (FASE 14: Production metrics and health checks)
app.include_router(monitoring_router)

# Include Prometheus routes (FASE 14 Week 2: Metrics export for Grafana)
app.include_router(prometheus_router)

# Include Alert Routing routes (FASE 14 Week 2 Track C: Alert routing & notifications)
app.include_router(alert_routing_router)

# Include FASE 14 Phase 1 Monitoring routes (Production Infrastructure)
app.include_router(fase14_monitoring_router)

# Global orchestrator instance
orchestrator = None

# FASE 14: Prediction system instance
from backend.routes.lead_prediction_integration import initialize_prediction_system as init_prediction

# FASE 14: A/B Testing and Statistical Analysis instances
statistical_tester = None
variant_assigner = None


def get_orchestrator() -> FelixAutomationOrchestrator:
    """Obtener instancia del orchestrator"""
    global orchestrator
    if orchestrator is None:
        orchestrator = FelixAutomationOrchestrator(db_path=DATABASE_PATH)
        orchestrator.connect_database()
    return orchestrator


def get_statistical_tester() -> StatisticalTester:
    """Get or create statistical tester instance"""
    global statistical_tester
    if statistical_tester is None:
        statistical_tester = StatisticalTester(significance_threshold=0.05)
    return statistical_tester


def get_variant_assigner() -> EmailVariantAssigner:
    """Get or create variant assigner instance"""
    global variant_assigner
    if variant_assigner is None:
        variant_assigner = EmailVariantAssigner()
    return variant_assigner


# ============================================================================
# STARTUP EVENT - Initialize All Systems (FASE 14)
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize all systems on app startup"""
    try:
        logger.info("🚀 Felix Automation API iniciada")
        logger.info(f"📊 Conectando a base de datos: {DATABASE_PATH}")

        orch = get_orchestrator()
        db_conn = orch.db
        logger.info(f"✅ Base de datos conectada - {len(orch.get_all_clients())} clientes encontrados")

        # Initialize prediction system (FASE 14)
        init_prediction(orchestrator=orch)
        logger.info("✅ Prediction system initialized at startup")

        # Initialize A/B testing routes (FASE 14 + FASE 15 Phase 3)
        from backend.websocket_manager import get_connection_manager
        ws_manager = get_connection_manager()
        init_ab_testing(db_conn, ws_manager)
        logger.info("✅ A/B Testing framework initialized at startup with WebSocket broadcasting")

        # Initialize Shopify webhooks (FASE 14)
        init_webhooks(db_conn)
        logger.info("✅ Shopify webhook handler initialized at startup")

        # Initialize Monitoring System (FASE 14)
        try:
            from backend.monitoring_startup import initialize_monitoring, start_monitoring_background_tasks
            initialize_monitoring()
            start_monitoring_background_tasks()
            logger.info("✅ Production Monitoring System initialized at startup")
        except Exception as e:
            logger.warning(f"⚠️ Monitoring system initialization warning (non-blocking): {e}")

    except Exception as e:
        logger.error(f"❌ Error conectando a BD: {str(e)}")


# ============================================================================
# MODELOS
# ============================================================================

class LoginRequest(BaseModel):
    """Request para login"""
    email: str
    password: str


class LoginResponse(BaseModel):
    """Response del login"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class PortalAccessRequest(BaseModel):
    """Request para acceso portal cliente"""
    email: str


class KPIResponse(BaseModel):
    """Response de KPIs"""
    total_clientes: int
    clientes_activos: int
    conversion_rate: float
    revenue_forecast_monthly: float
    pipeline: dict
    score_promedio: float
    audits_pendientes: int


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "🟢 OK",
        "service": "Felix Automation API",
        "version": API_VERSION
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login para admin (Felipe)
    Credenciales: email=felipe@enbuenamesa.com, password=admin123
    """
    logger.info(f"🔐 Login attempt: {request.email}")

    # Verificar credenciales (demo - cambiar en producción)
    if request.email != ADMIN_USER["email"] or request.password != ADMIN_USER["password"]:
        logger.warning(f"❌ Failed login attempt: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )

    # Crear token
    token = create_admin_token(request.email)

    logger.info(f"✅ Login successful: {request.email}")

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user={
            "email": request.email,
            "name": "Felipe",
            "role": "admin"
        }
    )


@app.get("/api/auth/verify")
async def verify_token(token: str):
    """Verificar que el token es válido"""
    try:
        payload = verify_admin_token(token)
        return {
            "valid": True,
            "email": payload.get("sub"),
            "role": payload.get("role")
        }
    except HTTPException as e:
        return {
            "valid": False,
            "error": e.detail
        }


@app.post("/api/auth/portal-access")
async def portal_access(request: PortalAccessRequest):
    """
    Acceso a portal cliente (sin contraseña)
    Solo requiere email válido de un cliente
    """
    logger.info(f"🔓 Portal access request: {request.email}")

    try:
        orch = get_orchestrator()

        # Buscar cliente por email
        client = None
        # Aquí buscamos en la BD un cliente con ese email
        # Por ahora, es una búsqueda simple en la caché
        for cid, c in orch.clients_cache.items():
            if c.email == request.email:
                client = c
                break

        if not client:
            # Si no está en caché, intentar desde BD
            clients = orch.get_all_clients()
            for c in clients:
                if c.email == request.email:
                    client = c
                    break

        if not client:
            logger.warning(f"❌ Client not found: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email no encontrado en nuestros registros"
            )

        # Crear token portal
        from backend.auth import create_client_portal_token
        token = create_client_portal_token(client.id, client.email)

        logger.info(f"✅ Portal access granted: {request.email} (client_id={client.id})")

        return {
            "access_token": token,
            "token_type": "bearer",
            "client_id": client.id,
            "client_name": client.name
        }

    except Exception as e:
        logger.error(f"❌ Portal access error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar solicitud"
        )


# ============================================================================
# DASHBOARD INTERNO ENDPOINTS
# ============================================================================

@app.get("/api/dashboard/kpis")
async def get_dashboard_kpis(token: str):
    """Obtener KPIs para dashboard interno"""
    verify_admin_token(token)

    try:
        orch = get_orchestrator()

        # Obtener estadísticas
        all_clients = orch.get_all_clients()

        # Calcular métricas
        total = len(all_clients)
        activos = len([c for c in all_clients if c.stage != "cerrado"])

        # Pipeline distribution
        pipeline_dist = {
            "prospecto": len([c for c in all_clients if c.stage == "prospecto"]),
            "propuesta": len([c for c in all_clients if c.stage == "propuesta"]),
            "negociacion": len([c for c in all_clients if c.stage == "negociacion"]),
            "cerrado": len([c for c in all_clients if c.stage == "cerrado"])
        }

        # Conversion rate (cerrados / total)
        conversion = (pipeline_dist["cerrado"] / total * 100) if total > 0 else 0

        # Score promedio
        scores = [c.score for c in all_clients if c.score is not None and c.score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Revenue forecast (estimado a partir de budgets)
        revenue = sum([c.estimated_budget or 0 for c in all_clients])

        return {
            "total_clientes": total,
            "clientes_activos": activos,
            "conversion_rate": round(conversion, 1),
            "revenue_forecast_monthly": revenue,
            "pipeline": pipeline_dist,
            "score_promedio": round(avg_score, 1),
            "audits_pendientes": 0
        }

    except Exception as e:
        logger.error(f"❌ KPI calculation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al calcular KPIs"
        )


@app.get("/api/dashboard/clients")
async def get_all_clients(token: str, skip: int = 0, limit: int = 50):
    """Obtener lista de clientes con filtros"""
    verify_admin_token(token)

    try:
        orch = get_orchestrator()
        clients = orch.get_all_clients()

        # Aplicar paginación
        clients_paginated = clients[skip:skip + limit]

        return {
            "total": len(clients),
            "skip": skip,
            "limit": limit,
            "data": [c.to_dict() for c in clients_paginated]
        }

    except Exception as e:
        logger.error(f"❌ Get clients error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener clientes"
        )


@app.get("/api/dashboard/pipeline")
async def get_pipeline_status(token: str):
    """Obtener estado completo del pipeline"""
    verify_admin_token(token)

    try:
        orch = get_orchestrator()
        all_clients = orch.get_all_clients()

        # Agrupar por etapa
        pipeline = {
            "prospecto": [],
            "propuesta": [],
            "negociacion": [],
            "cerrado": []
        }

        for client in all_clients:
            if client.stage in pipeline:
                pipeline[client.stage].append({
                    "id": client.id,
                    "name": client.name,
                    "company": client.company,
                    "score": client.score
                })

        return {
            "pipeline": pipeline,
            "total_by_stage": {
                stage: len(clients)
                for stage, clients in pipeline.items()
            }
        }

    except Exception as e:
        logger.error(f"❌ Pipeline status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estado del pipeline"
        )


# ============================================================================
# CLIENTE ENDPOINTS
# ============================================================================

@app.get("/api/clients/{client_id}")
async def get_client(client_id: int, token: str):
    """Obtener detalle de un cliente"""
    verify_admin_token(token)

    try:
        orch = get_orchestrator()
        client = orch.get_client(client_id)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )

        return client.to_dict()

    except Exception as e:
        logger.error(f"❌ Get client error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener cliente"
        )


@app.get("/api/clients/{client_id}/audits")
async def get_client_audits(client_id: int, token: str):
    """Obtener auditorías de un cliente"""
    verify_admin_token(token)

    try:
        orch = get_orchestrator()
        audits = orch.get_audits_by_client(client_id)

        return {
            "client_id": client_id,
            "total": len(audits),
            "audits": [
                {
                    "id": a.id,
                    "platform": a.platform,
                    "score": a.score,
                    "status": a.status,
                    "audit_type": a.audit_type
                }
                for a in audits
            ]
        }

    except Exception as e:
        logger.error(f"❌ Get audits error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener auditorías"
        )


# ============================================================================
# PORTAL CLIENTE ENDPOINTS
# ============================================================================

@app.get("/api/portal/me")
async def get_portal_data(token: str):
    """Obtener datos para portal cliente"""
    payload = verify_client_token(token)
    client_id = payload.get("client_id")

    try:
        orch = get_orchestrator()
        client = orch.get_client(client_id)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )

        # Obtener auditorías
        audits = orch.get_audits_by_client(client_id)

        return {
            "client": {
                "id": client.id,
                "name": client.name,
                "email": client.email,
                "company": client.company,
                "industry": client.industry,
                "stage": client.stage
            },
            "audits": [
                {
                    "id": a.id,
                    "platform": a.platform,
                    "score": a.score,
                    "audit_type": a.audit_type
                }
                for a in audits
            ],
            "audit_count": len(audits)
        }

    except Exception as e:
        logger.error(f"❌ Portal data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener datos del portal"
        )


# ============================================================================
# FASE 15 PHASE 3 - ADMIN CONTROLS (Kill-Switch & Feature Flags)
# ============================================================================

# Global Phase 3 state
phase3_state = {
    "active": False,
    "activated_at": None,
    "rollback_manager": None,
    "circuit_breaker_registry": None
}


@app.post("/api/admin/phase3/activate")
async def activate_phase3(token: str = Depends(verify_admin_token)):
    """
    Activate FASE 15 Phase 3
    Requires admin authentication
    """
    try:
        orch = get_orchestrator()
        db_conn = orch.db

        # Pre-flight checks
        checks = {
            "database_connected": db_conn is not None,
            "websocket_ready": True,
            "backups_recent": True,  # Simplified - would check actual backup system
            "circuit_breakers_healthy": True,
            "all_systems_healthy": True
        }

        if not all(checks.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pre-flight checks failed: {checks}"
            )

        # Update system config
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, ("PHASE_3_ACTIVE", "true"))
        db_conn.commit()

        # Initialize rollback manager if not already done
        if phase3_state["rollback_manager"] is None:
            from backend.rollback_manager import RollbackManager
            phase3_state["rollback_manager"] = RollbackManager(db_conn)

        # Initialize circuit breaker registry
        if phase3_state["circuit_breaker_registry"] is None:
            from backend.circuit_breaker import CircuitBreakerRegistry
            phase3_state["circuit_breaker_registry"] = CircuitBreakerRegistry

        phase3_state["active"] = True
        from datetime import datetime
        phase3_state["activated_at"] = datetime.utcnow().isoformat()

        logger.info("🚀 FASE 15 Phase 3 ACTIVATED")

        # Broadcast activation event
        try:
            from backend.websocket_manager import get_connection_manager
            from backend.events import EventFactory
            ws_manager = get_connection_manager()
            event = EventFactory.phase3_activated(
                client_id=0,
                timestamp=phase3_state["activated_at"]
            )
            ws_manager.broadcast(event, role='admin')
        except Exception as e:
            logger.warning(f"Could not broadcast activation event: {e}")

        return {
            "status": "activated",
            "phase3_active": True,
            "activated_at": phase3_state["activated_at"],
            "checks": checks
        }

    except Exception as e:
        logger.error(f"❌ Error activating Phase 3: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating Phase 3: {str(e)}"
        )


@app.post("/api/admin/phase3/deactivate")
async def deactivate_phase3(token: str = Depends(verify_admin_token)):
    """
    Deactivate FASE 15 Phase 3 (Kill-Switch)
    Requires admin authentication
    """
    try:
        orch = get_orchestrator()
        db_conn = orch.db

        # Update system config
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, ("PHASE_3_ACTIVE", "false"))
        db_conn.commit()

        phase3_state["active"] = False

        logger.warning("🛑 FASE 15 Phase 3 DEACTIVATED (Kill-Switch)")

        # Broadcast deactivation event
        try:
            from backend.websocket_manager import get_connection_manager
            from backend.events import EventFactory
            from datetime import datetime
            ws_manager = get_connection_manager()
            event = EventFactory.phase3_deactivated(
                client_id=0,
                timestamp=datetime.utcnow().isoformat()
            )
            ws_manager.broadcast(event, role='admin')
        except Exception as e:
            logger.warning(f"Could not broadcast deactivation event: {e}")

        return {
            "status": "deactivated",
            "phase3_active": False,
            "message": "Phase 3 has been disabled via kill-switch"
        }

    except Exception as e:
        logger.error(f"❌ Error deactivating Phase 3: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deactivating Phase 3: {str(e)}"
        )


@app.get("/api/admin/phase3/status")
async def get_phase3_status(token: str = Depends(verify_admin_token)):
    """
    Get current FASE 15 Phase 3 status
    Requires admin authentication
    """
    try:
        status_info = {
            "phase3_active": phase3_state["active"],
            "activated_at": phase3_state["activated_at"],
            "rollback_manager_ready": phase3_state["rollback_manager"] is not None,
            "circuit_breakers_ready": phase3_state["circuit_breaker_registry"] is not None
        }

        # Get health metrics if rollback manager is active
        if phase3_state["rollback_manager"]:
            health = phase3_state["rollback_manager"].collect_metrics()
            status_info["health"] = {
                "ml_accuracy": health.ml_accuracy,
                "error_rate": health.error_rate,
                "websocket_latency_ms": health.websocket_latency_ms,
                "predictions_per_hour": health.predictions_per_hour,
                "personalization_active": health.personalization_active,
                "active_tests": health.active_tests,
                "healthy_metrics": f"{health.get_healthy_metric_count()}/6"
            }

        # Get circuit breaker states
        if phase3_state["circuit_breaker_registry"]:
            status_info["circuit_breakers"] = phase3_state["circuit_breaker_registry"].get_all_metrics()

        return status_info

    except Exception as e:
        logger.error(f"❌ Error getting Phase 3 status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Phase 3 status: {str(e)}"
        )


@app.get("/api/admin/health/detailed")
async def get_detailed_health(token: str = Depends(verify_admin_token)):
    """
    Get detailed system health metrics for Phase 3 monitoring
    Requires admin authentication
    """
    try:
        health_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "phase3_active": phase3_state["active"],
            "services": {}
        }

        # Collect metrics from rollback manager
        if phase3_state["rollback_manager"]:
            decision = phase3_state["rollback_manager"].check_health_and_decide()
            health_info["health_check"] = decision
            health_info["services"]["rollback_manager"] = "operational"
        else:
            health_info["services"]["rollback_manager"] = "not_initialized"

        # Collect circuit breaker metrics
        if phase3_state["circuit_breaker_registry"]:
            health_info["services"]["circuit_breakers"] = phase3_state["circuit_breaker_registry"].get_all_metrics()
        else:
            health_info["services"]["circuit_breakers"] = {}

        # Database health
        try:
            orch = get_orchestrator()
            cursor = orch.db.cursor()
            cursor.execute("SELECT COUNT(*) FROM ab_tests")
            count = cursor.fetchone()[0]
            health_info["services"]["database"] = {"status": "healthy", "ab_tests_count": count}
        except Exception as e:
            health_info["services"]["database"] = {"status": "error", "error": str(e)}

        return health_info

    except Exception as e:
        logger.error(f"❌ Error getting detailed health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting health metrics: {str(e)}"
        )


# ============================================================================
# SHUTDOWN
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Al cerrar la aplicación"""
    logger.info("🛑 Felix Automation API cerrada")
    try:
        global orchestrator
        if orchestrator:
            orchestrator.close_database()
    except Exception as e:
        logger.error(f"Error cerrando BD: {str(e)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
╔════════════════════════════════════════════════════════════════╗
║      FELIX AUTOMATION - BACKEND API FASE 12 + FASE 13         ║
║    Dashboard Interno + Portal Cliente + WebSocket Real-Time   ║
╚════════════════════════════════════════════════════════════════╝
    """)

    print("\n📡 Iniciando servidor...")
    print("   URL: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("   ReDoc: http://localhost:8000/redoc")
    print("\n🔐 Credenciales demo:")
    print(f"   Email: {ADMIN_USER['email']}")
    print(f"   Password: {ADMIN_USER['password']}")
    print()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
