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
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Email/Password Login Endpoint

    Returns JWT token for authenticated user
    """
    if not request.email or not request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Lookup user in database
    user_db = db.query(Client).filter(Client.email == request.email).first()

    if not user_db:
        logger.warning(f"⚠️ Login attempt with non-existent email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Return user data from database
    user = {
        "id": user_db.id,
        "email": user_db.email,
        "name": user_db.name,
        "business_type": user_db.business_type,
        "company_size": user_db.company_size
    }

    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"], "role": "client"}
    )

    logger.info(f"✅ User logged in: {request.email}")

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
