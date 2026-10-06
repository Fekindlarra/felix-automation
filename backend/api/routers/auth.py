"""
Authentication Router
JWT token generation and validation
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
from config import get_settings

router = APIRouter()
settings = get_settings()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class BiometricLoginRequest(BaseModel):
    client_id: str

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Email/Password Login Endpoint

    Returns JWT token for authenticated user
    """
    # TODO: Validate against database
    if not request.email or not request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Mock user (replace with DB lookup)
    user = {
        "id": "user_001",
        "email": request.email,
        "role": "admin"
    }

    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]}
    )

    return TokenResponse(
        access_token=access_token,
        user=user
    )

@router.post("/biometric", response_model=TokenResponse)
async def biometric_login(request: BiometricLoginRequest):
    """
    Biometric Authentication Endpoint

    For Face ID / Touch ID login
    """
    # TODO: Validate biometric signature
    user = {
        "id": request.client_id,
        "email": f"{request.client_id}@enbuenamesa.com",
        "role": "user"
    }

    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]}
    )

    return TokenResponse(
        access_token=access_token,
        user=user
    )

@router.post("/verify")
async def verify_token(token: str):
    """
    Verify JWT Token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return {"valid": True, "payload": payload}
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
