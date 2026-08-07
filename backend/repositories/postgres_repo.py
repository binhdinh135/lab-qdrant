"""PostgreSQL database repository."""

import json
from typing import Any

from repositories.database import db_connect


def postgres_db_init() -> None:
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    user_type TEXT NOT NULL DEFAULT 'USER',
                    permissions_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cur.execute(
                "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS user_type TEXT NOT NULL DEFAULT 'USER'"
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_audit_log (
                    id BIGSERIAL PRIMARY KEY,
                    admin_username TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    target_type TEXT,
                    target_value TEXT,
                    status TEXT NOT NULL,
                    detail_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
        conn.commit()


def db_users_get_all() -> dict[str, Any]:
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username, password_hash, user_type, permissions_json, created_at FROM app_users ORDER BY username"
            )
            rows = cur.fetchall()

    users: dict[str, Any] = {}
    for username, password_hash, user_type, permissions_json, created_at in rows:
        users[username] = {
            "password_hash": password_hash,
            "user_type": str(user_type or "USER").upper(),
            "permissions": json.loads(permissions_json or "[]"),
            "roles": [],
            "created_at": created_at,
        }
    return users


def db_users_get(username: str) -> dict[str, Any] | None:
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password_hash, user_type, permissions_json, created_at FROM app_users WHERE username = %s",
                (username,),
            )
            row = cur.fetchone()

    if not row:
        return None

    password_hash, user_type, permissions_json, created_at = row
    return {
        "password_hash": password_hash,
        "user_type": str(user_type or "USER").upper(),
        "permissions": json.loads(permissions_json or "[]"),
        "roles": [],
        "created_at": created_at,
    }


def db_users_create(username: str, row: dict[str, Any]) -> bool:
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_users (username, password_hash, user_type, permissions_json, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                """,
                (
                    username,
                    row["password_hash"],
                    row.get("user_type", "USER"),
                    json.dumps(row.get("permissions", [])),
                    row.get("created_at", ""),
                ),
            )
            inserted = cur.rowcount == 1
        conn.commit()
    return inserted


def db_users_update_permissions(username: str, permissions: list[dict[str, str]]) -> bool:
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE app_users SET permissions_json = %s WHERE username = %s",
                (json.dumps(permissions), username),
            )
            updated = cur.rowcount == 1
        conn.commit()
    return updated


def db_users_delete(username: str) -> bool:
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM app_users WHERE username = %s", (username,))
            deleted = cur.rowcount == 1
        conn.commit()
    return deleted
