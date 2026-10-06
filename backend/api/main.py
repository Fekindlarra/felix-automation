"""
FASE 15 FastAPI Application
Track B: Machine Learning Predictions API
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import get_settings
from database import init_db
from routers import auth, predictions, events, websocket

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events"""
    # Startup
    print("🚀 FASE 15 API Starting (Track B - ML Predictions)")
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    yield
    # Shutdown
    print("🛑 FASE 15 API Shutting down")

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
