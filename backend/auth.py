#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication - JWT Token Management
FASE 12: Backend API
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Callable
from functools import wraps
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-fase12")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 horas


class AuthManager:
    """Gestor de autenticación JWT"""

    @staticmethod
    def create_access_token(
        data: Dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Crear JWT token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        logger.info(f"✅ JWT token created para: {data.get('sub')}")
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict:
        """Verificar y decodificar JWT token"""
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )

            sub: str = payload.get("sub")
            if sub is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except JWTError as e:
            logger.error(f"❌ JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashear contraseña"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return pwd_context.verify(plain_password, hashed_password)


# Usuario admin por defecto
ADMIN_USER = {
    "email": "felipe@enbuenamesa.com",
    "password": "admin123",  # Cambiar en producción
    "role": "admin"
}

# Token válido para portal cliente
PORTAL_TOKEN_EXPIRE_MINUTES = 60  # 1 hora para portal cliente


def create_admin_token(email: str = ADMIN_USER["email"]) -> str:
    """Crear token para admin (Felipe)"""
    return AuthManager.create_access_token(
        data={
            "sub": email,
            "role": "admin",
            "type": "internal"
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_client_portal_token(client_id: int, client_email: str) -> str:
    """Crear token para portal cliente"""
    return AuthManager.create_access_token(
        data={
            "sub": client_email,
            "client_id": client_id,
            "role": "client",
            "type": "portal"
        },
        expires_delta=timedelta(minutes=PORTAL_TOKEN_EXPIRE_MINUTES)
    )


def verify_admin_token(token: str) -> Dict:
    """Verificar token de admin"""
    payload = AuthManager.verify_token(token)

    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado - se requiere rol admin"
        )

    return payload


def verify_client_token(token: str) -> Dict:
    """Verificar token de cliente"""
    payload = AuthManager.verify_token(token)

    if payload.get("role") != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado - token inválido"
        )

    return payload


def generate_jwt_token(user_id: int, role: str = "client",
                       expires_delta: Optional[timedelta] = None) -> str:
    """
    Generar JWT token con user_id y role.
    Función standalone para facilitar generación de tokens.

    Args:
        user_id: ID del usuario
        role: Rol del usuario (client, admin)
        expires_delta: Tiempo de expiración personalizado

    Returns:
        JWT token string
    """
    return AuthManager.create_access_token(
        data={
            "sub": f"user_{user_id}",
            "user_id": user_id,
            "role": role
        },
        expires_delta=expires_delta
    )


def verify_jwt_token(token: str) -> Optional[Dict]:
    """
    Verificar y decodificar JWT token sin lanzar excepciones.
    Utilizado por WebSocket que maneja errores internamente.

    Args:
        token: JWT token string

    Returns:
        Payload decodificado si el token es válido, None si no lo es
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        sub: str = payload.get("sub")
        if sub is None:
            logger.warning("⚠️ JWT token sin 'sub' claim")
            return None

        logger.debug(f"✅ JWT token verificado para: {sub}")
        return payload

    except JWTError as e:
        logger.warning(f"⚠️ JWT verification failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error in JWT verification: {str(e)}")
        return None


def verify_request_admin_role(request: Request) -> None:
    """
    Verify that request comes from an admin user
    Extracts token from Authorization header and verifies admin role

    Raises HTTPException with 401 or 403 if not authenticated or not admin

    Usage in FastAPI route:
        from auth import verify_request_admin_role

        @router.post("/admin-endpoint")
        async def admin_endpoint(request: Request):
            verify_request_admin_role(request)
            # ... rest of handler
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization", "")

    if not auth_header:
        logger.warning("❌ Admin access attempt without Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token from "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("❌ Invalid Authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = parts[1]

    # Verify token and check admin role
    try:
        payload = AuthManager.verify_token(token)
        role = payload.get("role")

        if role != "admin":
            logger.warning(f"❌ Non-admin access attempt (role: {role})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for this operation"
            )

        logger.info(f"✅ Admin access verified for {payload.get('sub')}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Admin verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"}
        )
