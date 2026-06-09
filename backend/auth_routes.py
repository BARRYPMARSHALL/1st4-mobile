"""
Authentication API routes for 1st 4 Mobile Backend.

Prefix: /api/auth
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.deps import get_db
from backend.models import User

logger = logging.getLogger("1st4backend.auth_routes")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ─────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


class RegisterResponse(BaseModel):
    status: str
    user_id: str
    email: str
    message: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    status: str
    access_token: str
    token_type: str
    user: dict


class MeResponse(BaseModel):
    status: str
    user: dict


# ── Routes ──────────────────────────────────────────────────────────


@router.post("/register", response_model=RegisterResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new partner account."""
    # Validate inputs
    email = body.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # Check for existing user
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create user
    user = User(
        email=email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name.strip() or None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"New partner registered: {email}")
    return RegisterResponse(
        status="ok",
        user_id=str(user.id),
        email=user.email,
        message="Account created successfully. You can now log in.",
    )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a partner and return a JWT access token."""
    email = body.email.strip().lower()

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()

    token = create_access_token(data={"sub": user.email})
    logger.info(f"Partner logged in: {email}")

    return LoginResponse(
        status="ok",
        access_token=token,
        token_type="bearer",
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name or "",
        },
    )


@router.get("/me", response_model=MeResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return MeResponse(
        status="ok",
        user={
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name or "",
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        },
    )
