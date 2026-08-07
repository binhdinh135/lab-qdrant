"""User service — abstraction over database backends."""

import datetime as dt
from typing import Any

from repositories.database import postgres_enabled, oracle_enabled
from repositories.postgres_repo import (
    db_users_get_all,
    db_users_get,
    db_users_create,
    db_users_update_permissions,
    db_users_delete,
)
from repositories.oracle_repo import (
    oracle_users_get_all,
    oracle_users_get,
    oracle_users_create,
    oracle_users_update_permissions,
    oracle_users_delete,
    oracle_bootstrap_admin_if_missing,
)
from services.auth_service import hash_password
from config import ADMIN_BOOTSTRAP_USERNAME, ADMIN_BOOTSTRAP_PASSWORD


def users_get_all() -> dict[str, Any]:
    if postgres_enabled():
        return db_users_get_all()
    if oracle_enabled():
        return oracle_users_get_all()
    raise RuntimeError("Unsupported backend")


def users_get(username: str) -> dict[str, Any] | None:
    if postgres_enabled():
        return db_users_get(username)
    if oracle_enabled():
        return oracle_users_get(username)
    raise RuntimeError("Unsupported backend")


def users_create(username: str, row: dict[str, Any]) -> bool:
    if postgres_enabled():
        return db_users_create(username, row)
    if oracle_enabled():
        return oracle_users_create(username, row)
    raise RuntimeError("Unsupported backend")


def users_update_permissions(username: str, permissions: list[dict[str, str]]) -> bool:
    if postgres_enabled():
        return db_users_update_permissions(username, permissions)
    if oracle_enabled():
        return oracle_users_update_permissions(username, permissions)
    raise RuntimeError("Unsupported backend")


def users_delete(username: str) -> bool:
    if postgres_enabled():
        return db_users_delete(username)
    if oracle_enabled():
        return oracle_users_delete(username)
    raise RuntimeError("Unsupported backend")


def bootstrap_admin() -> None:
    if oracle_enabled():
        oracle_bootstrap_admin_if_missing(
            ADMIN_BOOTSTRAP_USERNAME, hash_password(ADMIN_BOOTSTRAP_PASSWORD)
        )
        return

    row = users_get(ADMIN_BOOTSTRAP_USERNAME)
    if row:
        if str(row.get("user_type", "USER")).upper() != "ADMIN":
            raise RuntimeError("Bootstrap admin exists but is not ADMIN.")
        return

    users_create(
        ADMIN_BOOTSTRAP_USERNAME,
        {
            "password_hash": hash_password(ADMIN_BOOTSTRAP_PASSWORD),
            "user_type": "ADMIN",
            "permissions": [],
            "created_at": dt.datetime.utcnow().isoformat() + "Z",
        },
    )


def to_public_user(username: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "username": username,
        "user_type": row.get("user_type", "USER"),
        "permissions": row.get("permissions", []),
        "created_at": row.get("created_at"),
    }
