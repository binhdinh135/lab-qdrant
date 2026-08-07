"""Audit logging service."""

import datetime as dt
import json
from typing import Any

from repositories.database import postgres_enabled, oracle_enabled, db_connect, oracle_connect


def audit_admin_action(
    claims: dict[str, Any],
    action_name: str,
    target_type: str = "",
    target_value: str = "",
    status: str = "SUCCESS",
    detail: dict[str, Any] | None = None,
) -> None:
    admin_username = str(claims.get("sub", "unknown")).strip() or "unknown"
    detail_json = json.dumps(detail or {}, ensure_ascii=False)
    created_at = dt.datetime.utcnow().isoformat() + "Z"

    try:
        if postgres_enabled():
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO admin_audit_log
                            (admin_username, action_name, target_type, target_value, status, detail_json, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (admin_username, action_name, target_type, target_value, status, detail_json, created_at),
                    )
                conn.commit()
            return

        if oracle_enabled():
            with oracle_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO ADMIN_AUDIT_LOG
                            (ADMIN_USERNAME, ACTION_NAME, TARGET_TYPE, TARGET_VALUE, STATUS, DETAIL_JSON, CREATED_AT)
                        VALUES (:1, :2, :3, :4, :5, :6, :7)
                        """,
                        (admin_username, action_name, target_type, target_value, status, detail_json, created_at),
                    )
                conn.commit()
    except Exception:
        return
