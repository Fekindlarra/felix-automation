"""
FASE 15 FastAPI Application
Track B: Machine Learning Predictions API
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import get_settings
from database import init_db, SessionLocal
from routers import auth, predictions, events, websocket
from routes.phase3_admin_routes import router as phase3_admin_router, init_phase3_admin_routes
import sqlite3

settings = get_settings()
logger = logging.getLogger(__name__)

# Global database connection for Phase 3 admin routes
_db_connection = None
_ws_manager = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events"""
    global _db_connection, _ws_manager

    # Startup
    print("🚀 FASE 15 API Starting (Track B - ML Predictions)")
    try:
        init_db()
        logger.info("✅ Database initialized")

        # Initialize Phase 3 admin routes dependencies
        # Create SQLite connection for Phase 3 admin operations
        try:
            db_path = settings.DATABASE_URL.replace("sqlite:///./", "") if hasattr(settings, 'DATABASE_URL') else "fase15.db"
            _db_connection = sqlite3.connect(db_path, check_same_thread=False)
            logger.info(f"✅ SQLite connection established to {db_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not establish SQLite connection for Phase 3: {e}")

        # Initialize WebSocket manager if available
        try:
            from routers.websocket import ConnectionManager
            _ws_manager = ConnectionManager()
            logger.info("✅ WebSocket manager initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize WebSocket manager: {e}")

        # Initialize Phase 3 admin routes with database and websocket manager
        init_phase3_admin_routes(_db_connection, _ws_manager)

    except Exception as e:
        logger.error(f"❌ Startup initialization failed: {e}")

    yield

    # Shutdown
    print("🛑 FASE 15 API Shutting down")
    if _db_connection:
        try:
            _db_connection.close()
            logger.info("✅ Database connection closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing database: {e}")

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="FASE 15: Real-Time ML Predictions + WebSocket Dashboard",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(phase3_admin_router, tags=["Phase 3 Admin"])

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "🟢 healthy",
        "version": settings.API_VERSION,
        "environment": "production" if not settings.DEBUG else "development",
    }

@app.get("/api/info")
def app_info():
    """API information"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "phase": "FASE 15",
        "track": "Track B: ML Predictions",
        "features": [
            "JWT Authentication",
            "ML-based sales probability predictions",
            "SHAP model explainability",
            "WebSocket real-time updates",
            "Batch prediction jobs",
            "A/B testing framework",
        ],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.DEBUG)
