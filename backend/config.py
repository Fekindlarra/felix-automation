#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration - Backend API FASE 12
"""

import os
from pathlib import Path
from datetime import timedelta

# Get project root (parent of backend dir)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 horas

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "pipeline.db"))

# CORS
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

# Admin user (Felipe)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "felipe@enbuenamesa.com")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", None)  # Hash bcrypt

# API Configuration
API_TITLE = "Felix Automation API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Backend API para Dashboard Interno y Portal Cliente"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = str(PROJECT_ROOT / "data" / "logs" / "api.log")

# Server
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
RELOAD = os.getenv("RELOAD", "true").lower() == "true"
