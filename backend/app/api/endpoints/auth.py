# FILE: backend/app/api/endpoints/auth.py
# PHOENIX PROTOCOL - AUTHENTICATION V2.11 (HAVERI DOMAIN + CORRECT SERVICE CALL)
# 1. FIXED: Cookie domain changed to ".haveri.tech" for haveri instance.
# 2. ADDED: /register endpoint that properly uses user_service.create.
# 3. UPDATED: Log messages to reflect haveri domain.
# 4. STATUS: 100% Pylance Clear.

from datetime import timedelta
from typing import Any
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pymongo.database import Database
from bson import ObjectId

from ...core import security
from ...core.config import settings
from ...core.db import get_db
from ...services import user_service
from ...models.token import Token
from ...models.user import UserInDB, UserLogin, RegisterRequest, UserCreate
from .dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_user_from_refresh_token(request: Request, db: Database = Depends(get_db)) -> UserInDB:
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        logger.warning("Refresh token missing in request cookies")
        raise HTTPException(status_code=401, detail="Refresh token missing")
    try:
        payload = security.decode_token(refresh_token)
        user_id_str = payload.get("sub")
        user = user_service.get_user_by_id(db, ObjectId(user_id_str))
        if not user:
            logger.error(f"User not found for id: {user_id_str}")
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logger.error(f"Invalid refresh token: {e}")
        raise HTTPException(status_code=401, detail="Invalid session")

@router.post("/login", response_model=Token)
async def login_access_token(response: Response, form_data: UserLogin, db: Database = Depends(get_db)) -> Any:
    user = user_service.authenticate(db, username=form_data.username.lower(), password=form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(status_code=401, detail="Identifikim i pasaktë")
    
    access_token = security.create_access_token(data={"id": str(user.id), "role": user.role})
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = security.create_refresh_token(data={"id": str(user.id)}, expires_delta=refresh_token_expires)

    # Set cookie with domain for cross-site access (haveri.tech)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        domain=".haveri.tech",          # Allow subdomains of haveri.tech
        path="/",
        max_age=int(refresh_token_expires.total_seconds())
    )
    
    logger.info(f"Login successful for user {user.id}, cookie set with domain .haveri.tech")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: UserInDB = Depends(get_user_from_refresh_token)) -> Any:
    new_access_token = security.create_access_token(data={"id": str(current_user.id), "role": current_user.role})
    logger.info(f"Token refreshed for user {current_user.id}")
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="none",
        domain=".haveri.tech",
        path="/"
    )
    logger.info("Logout successful, cookie deleted")
    return {"message": "Logged out"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(register_data: RegisterRequest, db: Database = Depends(get_db)):
    # Check if user already exists
    existing = user_service.get_user_by_email(db, register_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Prepare UserCreate object
    # If username is not provided, use email as username
    username = register_data.username if register_data.username else register_data.email
    user_create = UserCreate(
        username=username,
        email=register_data.email,
        password=register_data.password,
        full_name=register_data.full_name
    )
    
    # Create user using the service (which hashes password and sets defaults)
    created_user = user_service.create(db, user_create)
    
    logger.info(f"User registered successfully: {register_data.email} (id: {created_user.id})")
    return {"message": "User created successfully", "user_id": str(created_user.id)}