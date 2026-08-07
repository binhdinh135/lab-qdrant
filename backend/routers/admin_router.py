"""Admin routes — user, role, and collection management."""

import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from config import ADMIN_UI_FILE
from models.schemas import (
    CreateUserRequest,
    CreateRoleRequest,
    UpdateRolePermissionsRequest,
    AssignUserRolesRequest,
    CreateCollectionRequest,
    UpdateCollectionConfigRequest,
)
from repositories.database import oracle_enabled
from repositories.oracle_repo import (
    oracle_sync_collections,
    oracle_delete_collection_metadata,
    oracle_create_role,
    oracle_update_role_permissions,
    oracle_delete_role,
    oracle_list_roles,
    oracle_set_user_roles,
    oracle_get_user_roles,
)
from services.auth_service import require_admin, hash_password
from services.audit_service import audit_admin_action
from services.user_service import users_get_all, users_get, users_create, users_delete, to_public_user
from services.qdrant_service import (
    fetch_qdrant_collections,
    qdrant_create_collection,
    qdrant_get_collection_info,
    qdrant_delete_collection,
    qdrant_update_collection,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ui")
def admin_ui() -> FileResponse:
    if not ADMIN_UI_FILE.exists():
        raise HTTPException(status_code=404, detail="Admin UI file not found")
    return FileResponse(str(ADMIN_UI_FILE))


@router.get("/users", dependencies=[Depends(require_admin)])
def list_users() -> dict[str, Any]:
    users = users_get_all()
    items = [to_public_user(name, row) for name, row in users.items()]
    return {"users": items}


@router.get("/collections", dependencies=[Depends(require_admin)])
def list_collections() -> dict[str, Any]:
    return {"collections": fetch_qdrant_collections()}


@router.get("/collections/{collection_name}", dependencies=[Depends(require_admin)])
def get_collection(collection_name: str) -> dict[str, Any]:
    info = qdrant_get_collection_info(collection_name)
    return {"collection": collection_name, "info": info}


@router.post("/collections")
def create_collection(
    body: CreateCollectionRequest,
    admin_claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    qdrant_result = qdrant_create_collection(body)
    synced: list[str] = []
    if oracle_enabled():
        synced = oracle_sync_collections([body.collection_name])

    result = {
        "ok": True,
        "collection": {
            "collection_name": body.collection_name,
            "vector_size": body.vector_size,
            "distance": body.distance,
            "shard_number": body.shard_number,
            "replication_factor": body.replication_factor,
            "write_consistency_factor": body.write_consistency_factor,
            "on_disk_payload": body.on_disk_payload,
        },
        "qdrant_result": qdrant_result,
        "synced": synced,
    }
    audit_admin_action(admin_claims, "CREATE_COLLECTION", "collection", body.collection_name, "SUCCESS")
    return result


@router.patch("/collections/{collection_name}")
def update_collection(
    collection_name: str,
    body: UpdateCollectionConfigRequest,
    admin_claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if body.indexing_threshold is not None:
        payload.setdefault("optimizers_config", {})["indexing_threshold"] = body.indexing_threshold
    if body.hnsw_ef_construct is not None:
        payload.setdefault("hnsw_config", {})["ef_construct"] = body.hnsw_ef_construct
    if body.hnsw_m is not None:
        payload.setdefault("hnsw_config", {})["m"] = body.hnsw_m
    if body.write_consistency_factor is not None:
        payload.setdefault("params", {})["write_consistency_factor"] = body.write_consistency_factor
    if body.strict_mode_enabled is not None:
        payload["strict_mode_config"] = {"enabled": body.strict_mode_enabled}

    if not payload:
        raise HTTPException(status_code=400, detail="No collection config fields provided")

    result = qdrant_update_collection(collection_name, payload)
    audit_admin_action(admin_claims, "UPDATE_COLLECTION_CONFIG", "collection", collection_name, "SUCCESS", {"payload": payload})
    return {"ok": True, "collection": collection_name, "payload": payload, "qdrant_result": result}


@router.delete("/collections/{collection_name}")
def delete_collection(
    collection_name: str,
    admin_claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    result = qdrant_delete_collection(collection_name)
    synced_deleted = False
    if oracle_enabled():
        synced_deleted = oracle_delete_collection_metadata(collection_name)
    audit_admin_action(admin_claims, "DELETE_COLLECTION", "collection", collection_name, "SUCCESS", {"oracle_deleted": synced_deleted})
    return {"ok": True, "collection": collection_name, "qdrant_result": result, "oracle_deleted": synced_deleted}


@router.post("/collections/sync")
def sync_collections(admin_claims: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    if not oracle_enabled():
        raise HTTPException(status_code=501, detail="Collection sync is implemented for Oracle backend")

    qdrant_collections = fetch_qdrant_collections()
    synced = oracle_sync_collections(qdrant_collections)
    audit_admin_action(admin_claims, "SYNC_COLLECTIONS", "collections", ",".join(qdrant_collections), "SUCCESS", {"synced_count": len(synced)})
    return {"ok": True, "collections": qdrant_collections, "synced": synced}


@router.post("/users")
def create_user(
    body: CreateUserRequest,
    admin_claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    if oracle_enabled() and body.permissions:
        raise HTTPException(
            status_code=400,
            detail="Oracle role-first mode does not accept direct user permissions. Create role and assign role to user.",
        )

    row = {
        "password_hash": hash_password(body.password),
        "user_type": "USER",
        "permissions": [p.model_dump() for p in body.permissions],
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }

    if not users_create(body.username, row):
        raise HTTPException(status_code=409, detail="Username already exists")

    audit_admin_action(admin_claims, "CREATE_USER", "user", body.username, "SUCCESS", {"user_type": "USER"})
    return {"ok": True, "user": to_public_user(body.username, row)}


@router.delete("/users/{username}")
def delete_user(
    username: str,
    admin_claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    if not users_delete(username):
        raise HTTPException(status_code=404, detail="User not found")
    audit_admin_action(admin_claims, "DELETE_USER", "user", username, "SUCCESS")
    return {"ok": True}


@router.get("/roles", dependencies=[Depends(require_admin)])
def list_roles() -> dict[str, Any]:
    if not oracle_enabled():
        raise HTTPException(status_code=501, detail="Role APIs are implemented for Oracle backend")
    return {"roles": oracle_list_roles()}


@router.post("/roles")
def create_role(
    body: CreateRoleRequest,
    admin_claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    if not oracle_enabled():
        raise HTTPException(status_code=501, detail="Role APIs are implemented for Oracle backend")

    permissions = [p.model_dump() for p in body.permissions]
    if not oracle_create_role(body.role_name, body.description, permissions):
        raise HTTPException(status_code=409, detail="Role already exists")

    audit_admin_action(admin_claims, "CREATE_ROLE", "role", body.role_name.strip().upper(), "SUCCESS")
    return {
        "ok": True,
        "role": {
            "role_name": body.role_name.strip().upper(),
            "description": body.description,
            "permissions": permissions,
        },
    }


@router.put("/roles/{role_name}/permissions")
def update_role_permissions(
    role_name: str,
    body: UpdateRolePermissionsRequest,
    admin_claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    if not oracle_enabled():
        raise HTTPException(status_code=501, detail="Role APIs are implemented for Oracle backend")

    permissions = [p.model_dump() for p in body.permissions]
    if not oracle_update_role_permissions(role_name, permissions):
        raise HTTPException(status_code=404, detail="Role not found")

    audit_admin_action(admin_claims, "UPDATE_ROLE_PERMISSIONS", "role", role_name.strip().upper(), "SUCCESS", {"permission_count": len(permissions)})
    return {"ok": True, "role": {"role_name": role_name.strip().upper(), "permissions": permissions}}


@router.delete("/roles/{role_name}")
def delete_role(
    role_name: str,
    admin_claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    if not oracle_enabled():
        raise HTTPException(status_code=501, detail="Role APIs are implemented for Oracle backend")

    if not oracle_delete_role(role_name):
        raise HTTPException(status_code=404, detail="Role not found")

    audit_admin_action(admin_claims, "DELETE_ROLE", "role", role_name.strip().upper(), "SUCCESS")
    return {"ok": True}


@router.get("/users/{username}/roles", dependencies=[Depends(require_admin)])
def get_user_roles(username: str) -> dict[str, Any]:
    if not oracle_enabled():
        raise HTTPException(status_code=501, detail="Role APIs are implemented for Oracle backend")

    roles = oracle_get_user_roles(username)
    if roles is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": username, "roles": roles}


@router.put("/users/{username}/roles")
def set_user_roles(
    username: str,
    body: AssignUserRolesRequest,
    admin_claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    if not oracle_enabled():
        raise HTTPException(status_code=501, detail="Role APIs are implemented for Oracle backend")

    if not oracle_set_user_roles(username, body.roles):
        raise HTTPException(status_code=404, detail="User not found")

    roles = oracle_get_user_roles(username) or []
    row = users_get(username)
    audit_admin_action(admin_claims, "ASSIGN_USER_ROLES", "user", username, "SUCCESS", {"roles": roles})
    return {"ok": True, "user": to_public_user(username, row or {}), "roles": roles}
