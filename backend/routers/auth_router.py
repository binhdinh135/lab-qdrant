"""Authentication routes — /admin/login and /login."""

from fastapi import APIRouter, HTTPException

from models.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    LoginRequest,
    LoginResponse,
)
from services.auth_service import verify_password, encode_admin_token
from services.user_service import users_get
from services.qdrant_service import encode_qdrant_token

router = APIRouter(tags=["auth"])


@router.post("/admin/login", response_model=AdminLoginResponse)
def admin_login(body: AdminLoginRequest) -> AdminLoginResponse:
    row = users_get(body.username)
    if not row:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(body.password, row.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if str(row.get("user_type", "USER")).strip().upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin account required")

    status = str(row.get("status", "ACTIVE")).strip().upper()
    if status and status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Admin account is inactive")

    token, exp = encode_admin_token(body.username)

    # Admin gets global manage access (full rw all collections, no need to list them)
    qdrant_token = encode_qdrant_token(body.username, "manage", ["ADMIN"])

    return AdminLoginResponse(
        admin_token=token,
        qdrant_token=qdrant_token or "",
        expires_at=exp.isoformat() + "Z",
        username=body.username,
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    row = users_get(body.username)
    if not row:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(body.password, row.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if str(row.get("user_type", "USER")).strip().upper() != "USER":
        raise HTTPException(status_code=403, detail="Only USER accounts can use this login endpoint")

    permissions = row.get("permissions", [])
    roles = row.get("roles", [])
    qdrant_token = encode_qdrant_token(body.username, permissions, roles)
    if not qdrant_token:
        raise HTTPException(status_code=500, detail="Cannot mint Qdrant JWT token")
    return LoginResponse(qdrant_token=qdrant_token)
