"""
Database Models for FASE 15
SQLAlchemy ORM models
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Client(Base):
    """Client/Business account"""
    __tablename__ = "clients"

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    business_type = Column(String)
    company_size = Column(String)  # startup, pyme, empresa
    created_at = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    """ML Prediction record"""
    __tablename__ = "predictions"

    id = Column(String, primary_key=True)
    client_id = Column(String, index=True)
    probability = Column(Integer)  # 0-100
    confidence = Column(Float)  # 0-1
    risk_factors = Column(String)  # JSON
    positive_factors = Column(String)  # JSON
    shap_explanation = Column(String)  # JSON SHAP values
    predicted_timeline_days = Column(Integer)
    actual_outcome = Column(Boolean, nullable=True)  # True if converted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Event(Base):
    """WebSocket event record"""
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    type = Column(String)  # prediction:generated, anomaly:detected, etc
    client_id = Column(String)
    payload = Column(String)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)

class ABTest(Base):
    """A/B Testing"""
    __tablename__ = "ab_tests"

    id = Column(String, primary_key=True)
    test_name = Column(String)
    email_type = Column(String)
    variant_a = Column(String)
    variant_b = Column(String)
    active = Column(Boolean, default=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)

class ABTestResult(Base):
    """A/B Test results"""
    __tablename__ = "ab_test_results"

    id = Column(String, primary_key=True)
    test_id = Column(String)
    client_id = Column(String)
    variant = Column(String)  # A or B
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
