"""Oracle database repository — all Oracle SQL operations."""

from typing import Any

from fastapi import HTTPException

from repositories.database import oracle_connect


def oracle_get_collection_id(cur: Any, collection_name: str) -> int | None:
    cur.execute(
        "SELECT COLLECTION_ID FROM COLLECTIONS WHERE COLLECTION_NAME = :1",
        (collection_name,),
    )
    row = cur.fetchone()
    if row:
        return int(row[0])
    return None


def oracle_get_role_id(cur: Any, role_name: str) -> int | None:
    cur.execute("SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME = :1", (role_name,))
    row = cur.fetchone()
    if not row:
        return None
    return int(row[0])


def oracle_get_or_create_role_id(cur: Any, role_name: str) -> int:
    cur.execute("SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME = :1", (role_name,))
    row = cur.fetchone()
    if row:
        return int(row[0])
    try:
        cur.execute("INSERT INTO ROLES (ROLE_NAME) VALUES (:1)", (role_name,))
    except Exception as exc:
        err = getattr(exc, "args", [None])[0]
        if not (hasattr(err, "code") and getattr(err, "code", None) == 1):
            raise
    cur.execute("SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME = :1", (role_name,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Cannot resolve role id for {role_name}")
    return int(row[0])


def oracle_ensure_user_role_link(cur: Any, user_id: int, role_id: int) -> None:
    cur.execute(
        "SELECT ID FROM USER_ROLE WHERE USER_ID = :1 AND ROLE_ID = :2",
        (user_id, role_id),
    )
    if cur.fetchone():
        return
    cur.execute(
        "INSERT INTO USER_ROLE (USER_ID, ROLE_ID) VALUES (:1, :2)",
        (user_id, role_id),
    )


def oracle_replace_role_permissions(cur: Any, role_id: int, permissions: list[dict[str, str]]) -> None:
    cur.execute("DELETE FROM ROLE_PERMISSION WHERE ROLE_ID = :1", (role_id,))
    for perm in permissions:
        collection_name = perm.get("collection", "").strip()
        access = perm.get("access", "").strip()
        if not collection_name or access not in {"r", "rw"}:
            continue
        collection_id = oracle_get_collection_id(cur, collection_name)
        if collection_id is None:
            raise HTTPException(
                status_code=404,
                detail=f"Collection not found in Oracle metadata: {collection_name}. Sync collections first.",
            )
        cur.execute(
            """
            INSERT INTO ROLE_PERMISSION (ROLE_ID, COLLECTION_ID, PERMISSION)
            VALUES (:1, :2, :3)
            """,
            (role_id, collection_id, access),
        )


def oracle_managed_role_name(username: str) -> str:
    normalized = "".join(ch for ch in username.upper() if ch.isalnum() or ch == "_")
    if not normalized:
        normalized = "USER"
    return ("ROLE_" + normalized)[:100]


def oracle_normalize_role_names(role_names: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw in role_names:
        name = str(raw).strip().upper()
        if not name:
            continue
        if name not in normalized:
            normalized.append(name)
    return normalized


def oracle_users_get_all() -> dict[str, Any]:
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.USERNAME,
                    u.PASSWORD_HASH,
                    u.USER_TYPE,
                    u.CREATED_AT,
                    r.ROLE_NAME,
                    c.COLLECTION_NAME,
                    rp.PERMISSION
                FROM USERS u
                LEFT JOIN USER_ROLE ur ON ur.USER_ID = u.USER_ID
                LEFT JOIN ROLES r ON r.ROLE_ID = ur.ROLE_ID
                LEFT JOIN ROLE_PERMISSION rp ON rp.ROLE_ID = ur.ROLE_ID
                LEFT JOIN COLLECTIONS c ON c.COLLECTION_ID = rp.COLLECTION_ID
                ORDER BY u.USERNAME, r.ROLE_NAME, c.COLLECTION_NAME
                """
            )
            rows = cur.fetchall()

    users: dict[str, Any] = {}
    for username, password_hash, user_type, created_at, role_name, collection_name, permission in rows:
        if username not in users:
            users[username] = {
                "password_hash": password_hash,
                "user_type": str(user_type or "USER").upper(),
                "permissions": [],
                "roles": [],
                "created_at": created_at,
            }
        if role_name and role_name not in users[username]["roles"]:
            users[username]["roles"].append(role_name)
        if collection_name and permission:
            perm_item = {"collection": collection_name, "access": permission}
            if perm_item not in users[username]["permissions"]:
                users[username]["permissions"].append(perm_item)
    return users


def oracle_users_get(username: str) -> dict[str, Any] | None:
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.PASSWORD_HASH,
                    u.USER_TYPE,
                    u.CREATED_AT,
                    r.ROLE_NAME,
                    c.COLLECTION_NAME,
                    rp.PERMISSION
                FROM USERS u
                LEFT JOIN USER_ROLE ur ON ur.USER_ID = u.USER_ID
                LEFT JOIN ROLES r ON r.ROLE_ID = ur.ROLE_ID
                LEFT JOIN ROLE_PERMISSION rp ON rp.ROLE_ID = ur.ROLE_ID
                LEFT JOIN COLLECTIONS c ON c.COLLECTION_ID = rp.COLLECTION_ID
                WHERE u.USERNAME = :1
                ORDER BY r.ROLE_NAME, c.COLLECTION_NAME
                """,
                (username,),
            )
            rows = cur.fetchall()

    if not rows:
        return None

    password_hash, user_type, created_at, _, _, _ = rows[0]
    permissions: list[dict[str, str]] = []
    roles: list[str] = []
    for _, _, _, role_name, collection_name, permission in rows:
        if role_name and role_name not in roles:
            roles.append(role_name)
        if collection_name and permission:
            permissions.append({"collection": collection_name, "access": permission})

    return {
        "password_hash": password_hash,
        "user_type": str(user_type or "USER").upper(),
        "permissions": permissions,
        "roles": roles,
        "created_at": created_at,
    }


def oracle_users_create(username: str, row: dict[str, Any]) -> bool:
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO USERS (USERNAME, PASSWORD_HASH, USER_TYPE, STATUS, CREATED_AT)
                    VALUES (:1, :2, :3, :4, :5)
                    """,
                    (
                        username,
                        row["password_hash"],
                        row.get("user_type", "USER"),
                        "ACTIVE",
                        row.get("created_at", ""),
                    ),
                )
            except Exception as exc:
                err = getattr(exc, "args", [None])[0]
                if hasattr(err, "code") and getattr(err, "code", None) == 1:
                    conn.rollback()
                    return False
                else:
                    raise
        conn.commit()
    return True


def oracle_users_delete(username: str) -> bool:
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM USERS WHERE USERNAME = :1", (username,))
            deleted = cur.rowcount == 1
        conn.commit()
    return deleted


def oracle_users_update_permissions(username: str, permissions: list[dict[str, str]]) -> bool:
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT USER_ID FROM USERS WHERE USERNAME = :1", (username,))
            row = cur.fetchone()
            if not row:
                return False

            user_id = int(row[0])
            managed_role = oracle_managed_role_name(username)
            role_id = oracle_get_or_create_role_id(cur, managed_role)
            oracle_ensure_user_role_link(cur, user_id, role_id)
            oracle_replace_role_permissions(cur, role_id, permissions)
        conn.commit()
    return True


def oracle_sync_collections(collection_names: list[str]) -> list[str]:
    synced: list[str] = []
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            for raw_name in collection_names:
                collection_name = str(raw_name).strip()
                if not collection_name:
                    continue
                collection_id = oracle_get_collection_id(cur, collection_name)
                if collection_id is not None:
                    continue
                cur.execute(
                    "INSERT INTO COLLECTIONS (COLLECTION_NAME) VALUES (:1)",
                    (collection_name,),
                )
                synced.append(collection_name)
        conn.commit()
    return synced


def oracle_delete_collection_metadata(collection_name: str) -> bool:
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            collection_id = oracle_get_collection_id(cur, collection_name)
            if collection_id is None:
                return False
            cur.execute("DELETE FROM ROLE_PERMISSION WHERE COLLECTION_ID = :1", (collection_id,))
            cur.execute("DELETE FROM COLLECTIONS WHERE COLLECTION_ID = :1", (collection_id,))
        conn.commit()
    return True


def oracle_create_role(role_name: str, description: str, permissions: list[dict[str, str]]) -> bool:
    role_name = role_name.strip().upper()
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO ROLES (ROLE_NAME, DESCRIPTION) VALUES (:1, :2)",
                    (role_name, description.strip()),
                )
            except Exception as exc:
                err = getattr(exc, "args", [None])[0]
                if hasattr(err, "code") and getattr(err, "code", None) == 1:
                    conn.rollback()
                    return False
                raise

            role_id = oracle_get_role_id(cur, role_name)
            if role_id is None:
                raise RuntimeError(f"Cannot resolve ROLE_ID for {role_name}")
            oracle_replace_role_permissions(cur, role_id, permissions)
        conn.commit()
    return True


def oracle_update_role_permissions(role_name: str, permissions: list[dict[str, str]]) -> bool:
    role_name = role_name.strip().upper()
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            role_id = oracle_get_role_id(cur, role_name)
            if role_id is None:
                return False
            oracle_replace_role_permissions(cur, role_id, permissions)
        conn.commit()
    return True


def oracle_delete_role(role_name: str) -> bool:
    role_name = role_name.strip().upper()
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ROLES WHERE ROLE_NAME = :1", (role_name,))
            deleted = cur.rowcount == 1
        conn.commit()
    return deleted


def oracle_list_roles() -> list[dict[str, Any]]:
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.ROLE_NAME,
                    r.DESCRIPTION,
                    c.COLLECTION_NAME,
                    rp.PERMISSION
                FROM ROLES r
                LEFT JOIN ROLE_PERMISSION rp ON rp.ROLE_ID = r.ROLE_ID
                LEFT JOIN COLLECTIONS c ON c.COLLECTION_ID = rp.COLLECTION_ID
                ORDER BY r.ROLE_NAME, c.COLLECTION_NAME
                """
            )
            rows = cur.fetchall()

    role_map: dict[str, dict[str, Any]] = {}
    for role_name, description, collection_name, permission in rows:
        if role_name not in role_map:
            role_map[role_name] = {
                "role_name": role_name,
                "description": description or "",
                "permissions": [],
            }
        if collection_name and permission:
            item = {"collection": collection_name, "access": permission}
            if item not in role_map[role_name]["permissions"]:
                role_map[role_name]["permissions"].append(item)

    return [role_map[k] for k in sorted(role_map.keys())]


def oracle_set_user_roles(username: str, roles: list[str]) -> bool:
    role_names = oracle_normalize_role_names(roles)
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT USER_ID FROM USERS WHERE USERNAME = :1", (username,))
            user_row = cur.fetchone()
            if not user_row:
                return False
            user_id = int(user_row[0])

            role_ids: list[int] = []
            for role_name in role_names:
                role_id = oracle_get_role_id(cur, role_name)
                if role_id is None:
                    raise HTTPException(status_code=404, detail=f"Role not found: {role_name}")
                role_ids.append(role_id)

            cur.execute("DELETE FROM USER_ROLE WHERE USER_ID = :1", (user_id,))
            for role_id in role_ids:
                cur.execute(
                    "INSERT INTO USER_ROLE (USER_ID, ROLE_ID) VALUES (:1, :2)",
                    (user_id, role_id),
                )
        conn.commit()
    return True


def oracle_get_user_roles(username: str) -> list[str] | None:
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT USER_ID FROM USERS WHERE USERNAME = :1", (username,))
            user_row = cur.fetchone()
            if not user_row:
                return None
            user_id = int(user_row[0])

            cur.execute(
                """
                SELECT r.ROLE_NAME
                FROM USER_ROLE ur
                JOIN ROLES r ON r.ROLE_ID = ur.ROLE_ID
                WHERE ur.USER_ID = :1
                ORDER BY r.ROLE_NAME
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    return [str(r[0]) for r in rows]


def oracle_bootstrap_admin_if_missing(bootstrap_username: str, password_hash: str) -> None:
    import datetime as dt

    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT USER_ID FROM USERS WHERE USERNAME = :1", (bootstrap_username,))
            row = cur.fetchone()
            if not row:
                cur.execute(
                    """
                    INSERT INTO USERS (USERNAME, PASSWORD_HASH, USER_TYPE, STATUS, CREATED_AT)
                    VALUES (:1, :2, :3, :4, :5)
                    """,
                    (
                        bootstrap_username,
                        password_hash,
                        "ADMIN",
                        "ACTIVE",
                        dt.datetime.utcnow().isoformat() + "Z",
                    ),
                )
            else:
                cur.execute(
                    "UPDATE USERS SET USER_TYPE = 'ADMIN', STATUS = 'ACTIVE' WHERE USER_ID = :1",
                    (int(row[0]),),
                )
        conn.commit()


def oracle_db_init() -> None:
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            for legacy_table in ("USER_PERMISSION", "USERPERMISSION"):
                try:
                    cur.execute(f"DROP TABLE {legacy_table} CASCADE CONSTRAINTS PURGE")
                except Exception as exc:
                    err = getattr(exc, "args", [None])[0]
                    if not hasattr(err, "code") or getattr(err, "code", None) != 942:
                        raise

            _create_table_ignore_exists(cur, """
                CREATE TABLE USERS (
                    USER_ID NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    USERNAME VARCHAR2(100) UNIQUE NOT NULL,
                    FULL_NAME VARCHAR2(200),
                    PASSWORD_HASH VARCHAR2(500) NOT NULL,
                    USER_TYPE VARCHAR2(20) DEFAULT 'USER' NOT NULL,
                    STATUS VARCHAR2(20) DEFAULT 'ACTIVE',
                    CREATED_AT VARCHAR2(64) NOT NULL
                )
            """)

            try:
                cur.execute("ALTER TABLE USERS ADD USER_TYPE VARCHAR2(20) DEFAULT 'USER' NOT NULL")
            except Exception as exc:
                err = getattr(exc, "args", [None])[0]
                if not hasattr(err, "code") or getattr(err, "code", None) != 1430:
                    raise

            _create_table_ignore_exists(cur, """
                CREATE TABLE ADMIN_AUDIT_LOG (
                    LOG_ID NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    ADMIN_USERNAME VARCHAR2(100) NOT NULL,
                    ACTION_NAME VARCHAR2(100) NOT NULL,
                    TARGET_TYPE VARCHAR2(100),
                    TARGET_VALUE VARCHAR2(200),
                    STATUS VARCHAR2(20) NOT NULL,
                    DETAIL_JSON CLOB,
                    CREATED_AT VARCHAR2(64) NOT NULL
                )
            """)

            _create_table_ignore_exists(cur, """
                CREATE TABLE COLLECTIONS (
                    COLLECTION_ID NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    COLLECTION_NAME VARCHAR2(100) UNIQUE NOT NULL,
                    DESCRIPTION VARCHAR2(200)
                )
            """)

            _create_table_ignore_exists(cur, """
                CREATE TABLE ROLES (
                    ROLE_ID NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    ROLE_NAME VARCHAR2(100) UNIQUE NOT NULL,
                    DESCRIPTION VARCHAR2(200)
                )
            """)

            _create_table_ignore_exists(cur, """
                CREATE TABLE USER_ROLE (
                    ID NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    USER_ID NUMBER NOT NULL,
                    ROLE_ID NUMBER NOT NULL,
                    CONSTRAINT FK_USER_ROLE_USER
                        FOREIGN KEY(USER_ID)
                        REFERENCES USERS(USER_ID)
                        ON DELETE CASCADE,
                    CONSTRAINT FK_USER_ROLE_ROLE
                        FOREIGN KEY(ROLE_ID)
                        REFERENCES ROLES(ROLE_ID)
                        ON DELETE CASCADE,
                    CONSTRAINT UK_USER_ROLE UNIQUE (USER_ID, ROLE_ID)
                )
            """)

            _create_table_ignore_exists(cur, """
                CREATE TABLE ROLE_PERMISSION (
                    ID NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    ROLE_ID NUMBER NOT NULL,
                    COLLECTION_ID NUMBER NOT NULL,
                    PERMISSION VARCHAR2(5),
                    CONSTRAINT FK_ROLE_PERMISSION_ROLE
                        FOREIGN KEY(ROLE_ID)
                        REFERENCES ROLES(ROLE_ID)
                        ON DELETE CASCADE,
                    CONSTRAINT FK_ROLE_PERMISSION_COLLECTION
                        FOREIGN KEY(COLLECTION_ID)
                        REFERENCES COLLECTIONS(COLLECTION_ID),
                    CONSTRAINT UK_ROLE_COLLECTION UNIQUE (ROLE_ID, COLLECTION_ID)
                )
            """)
        conn.commit()


def _create_table_ignore_exists(cur: Any, ddl: str) -> None:
    try:
        cur.execute(ddl)
    except Exception as exc:
        err = getattr(exc, "args", [None])[0]
        if not hasattr(err, "code") or getattr(err, "code", None) != 955:
            raise
