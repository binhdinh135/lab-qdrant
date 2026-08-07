"""Authentication & authorization service."""

import datetime as dt
import hashlib
import hmac
import os
from typing import Any

import jwt
from fastapi import Header, HTTPException

from config import (
    ADMIN_JWT_SECRET,
    ADMIN_JWT_ISSUER,
    ADMIN_JWT_AUDIENCE,
    APP_AUTH_TTL_MINUTES,
)


def hash_password(password: str, salt_hex: str | None = None) -> str:
    if salt_hex is None:
        salt_hex = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 120000
    ).hex()
    return f"{salt_hex}${digest}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        salt_hex, digest = encoded_hash.split("$", maxsplit=1)
    except ValueError:
        return False
    computed = hash_password(password, salt_hex).split("$", maxsplit=1)[1]
    return hmac.compare_digest(computed, digest)


def encode_admin_token(username: str) -> tuple[str, dt.datetime]:
    now = dt.datetime.utcnow()
    exp = now + dt.timedelta(minutes=APP_AUTH_TTL_MINUTES)
    payload = {
        "iss": ADMIN_JWT_ISSUER,
        "aud": ADMIN_JWT_AUDIENCE,
        "sub": username,
        "kind": "admin",
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(payload, ADMIN_JWT_SECRET, algorithm="HS256"), exp


def decode_admin_token(token: str) -> dict[str, Any]:
    try:
        data = jwt.decode(
            token,
            ADMIN_JWT_SECRET,
            algorithms=["HS256"],
            issuer=ADMIN_JWT_ISSUER,
            audience=ADMIN_JWT_AUDIENCE,
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid admin token")

    if str(data.get("kind", "")).lower() != "admin":
        raise HTTPException(status_code=401, detail="Invalid admin token kind")
    return data


def require_admin(authorization: str = Header(default="")) -> dict[str, Any]:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", maxsplit=1)[1].strip()
        return decode_admin_token(token)
    raise HTTPException(status_code=401, detail="Missing or invalid admin Bearer token")
