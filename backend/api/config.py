"""
FASE 15 Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings from environment variables"""

    # API
    API_TITLE: str = "FASE 15 API"
    API_VERSION: str = "15.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./fase15.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # WebSocket
    WEBSOCKET_URL: str = "ws://localhost:8000/ws"
    HEARTBEAT_INTERVAL: int = 30  # seconds

    # ML Models
    ML_MODEL_PATH: str = "./models/predictor_model.pkl"
    FEATURE_SCALER_PATH: str = "./models/feature_scaler.pkl"

    # Redis (for WebSocket broadcast)
    REDIS_URL: str = "redis://localhost:6379"

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8081",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
