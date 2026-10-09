"""
Database initialization and session management for FASE 15
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.api.config import get_settings

settings = get_settings()

# Database URL - use SQLite for development
DATABASE_URL = settings.DATABASE_URL or "sqlite:///./fase15.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


def init_db():
    """Initialize database - create all tables"""
    # Import explícito del módulo de modelos de esta app. "from models import Base"
    # resolvía al directorio raíz models/ (sin Base) y fallaba al importar backend.api.main.
    from backend.api.models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database on import
if not os.path.exists(DATABASE_URL.replace("sqlite:///./", "")):
    init_db()
