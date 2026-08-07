"""Qdrant HTTP client and JWT minting."""

import datetime as dt
import json
from typing import Any
from urllib import error, request

import jwt
from fastapi import HTTPException

from config import (
    QDRANT_URL,
    QDRANT_ADMIN_API_KEY,
    QDRANT_READONLY_API_KEY,
    QDRANT_JWT_SECRET,
    QDRANT_TOKEN_TTL_MINUTES,
)
from models.schemas import CreateCollectionRequest

_qdrant_signing_key_cache: str | None = None


def _fetch_qdrant_secret() -> str:
    req = request.Request(
        f"{QDRANT_URL}/cluster/secret-key",
        headers={"api-key": QDRANT_ADMIN_API_KEY},
        method="GET",
    )
    with request.urlopen(req, timeout=5) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Unexpected status from /cluster/secret-key: {resp.status}")
        data = json.loads(resp.read().decode("utf-8"))

    if isinstance(data, dict):
        result = data.get("result")
        if isinstance(result, str) and result.strip():
            return result.strip()
    raise RuntimeError("Invalid /cluster/secret-key response format")


def get_qdrant_signing_key() -> str | None:
    global _qdrant_signing_key_cache

    if QDRANT_JWT_SECRET:
        return QDRANT_JWT_SECRET
    if _qdrant_signing_key_cache:
        return _qdrant_signing_key_cache

    try:
        _qdrant_signing_key_cache = _fetch_qdrant_secret()
        return _qdrant_signing_key_cache
    except Exception:
        if QDRANT_ADMIN_API_KEY.strip():
            _qdrant_signing_key_cache = QDRANT_ADMIN_API_KEY
            return _qdrant_signing_key_cache
        return None


def encode_qdrant_token(username: str, permissions: list[dict[str, str]] | str, roles: list[str] | None = None) -> str:
    now = dt.datetime.utcnow()
    exp = now + dt.timedelta(minutes=QDRANT_TOKEN_TTL_MINUTES)
    signing_key = get_qdrant_signing_key()
    if not signing_key:
        return ""

    # "manage" = global full access, no need to list collections
    if isinstance(permissions, str):
        access_claim = permissions[0]  # "m" from "manage", or "r" from "read"
    else:
        access_claim = permissions

    payload = {
        "sub": username,
        "roles": roles or [],
        "iat": now,
        "exp": exp,
        "access": access_claim,
    }
    return jwt.encode(payload, signing_key, algorithm="HS256")


def qdrant_request_json(
    path: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    use_readonly: bool = False,
) -> dict[str, Any]:
    url = f"{QDRANT_URL}{path}"
    headers: dict[str, str] = {}
    api_key = QDRANT_READONLY_API_KEY if use_readonly and QDRANT_READONLY_API_KEY else QDRANT_ADMIN_API_KEY
    if api_key:
        headers["api-key"] = api_key
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            if not raw:
                return {}
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            return {"raw": parsed}
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(
            status_code=502,
            detail=f"Qdrant {method} {path} failed: HTTP {exc.code} - {body_text}",
        )
    except error.URLError as exc:
        raise HTTPException(status_code=502, detail=f"Qdrant unavailable: {exc.reason}")


def fetch_qdrant_collections() -> list[str]:
    data = qdrant_request_json("/collections", method="GET", use_readonly=True)

    collections: list[str] = []
    result = data.get("result") if isinstance(data, dict) else None
    if isinstance(result, dict):
        raw_items = result.get("collections")
        if isinstance(raw_items, list):
            for item in raw_items:
                if isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        collections.append(name.strip())

    return sorted(set(collections))


def qdrant_create_collection(body: CreateCollectionRequest) -> dict[str, Any]:
    payload = {
        "vectors": {
            "size": body.vector_size,
            "distance": body.distance,
        },
        "shard_number": body.shard_number,
        "replication_factor": body.replication_factor,
        "write_consistency_factor": body.write_consistency_factor,
        "on_disk_payload": body.on_disk_payload,
    }
    return qdrant_request_json(f"/collections/{body.collection_name}", method="PUT", body=payload)


def qdrant_get_collection_info(collection_name: str) -> dict[str, Any]:
    return qdrant_request_json(f"/collections/{collection_name}", method="GET", use_readonly=True)


def qdrant_delete_collection(collection_name: str) -> dict[str, Any]:
    return qdrant_request_json(f"/collections/{collection_name}", method="DELETE")


def qdrant_update_collection(collection_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return qdrant_request_json(f"/collections/{collection_name}", method="PATCH", body=payload)


def qdrant_scroll_probe(collection: str, bearer_token: str | None = None) -> tuple[int, str]:
    url = f"{QDRANT_URL}/collections/{collection}/points/scroll"
    body_bytes = json.dumps({"limit": 1}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    req = request.Request(url, data=body_bytes, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=8) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        if hasattr(exc, "code") and hasattr(exc, "read"):
            code = int(getattr(exc, "code"))
            raw = exc.read().decode("utf-8", errors="replace")
            return code, raw
        raise


def qdrant_write_probe(collection: str, bearer_token: str | None = None) -> tuple[int, str]:
    url = f"{QDRANT_URL}/collections/{collection}/points"
    test_id = int(dt.datetime.utcnow().timestamp())
    body_bytes = json.dumps(
        {
            "points": [
                {
                    "id": test_id,
                    "vector": [0.0, 0.0, 0.0, 0.0],
                    "payload": {
                        "__rbac_test__": True,
                        "source": "debug-test-access-token",
                        "created_at": dt.datetime.utcnow().isoformat() + "Z",
                    },
                }
            ]
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    req = request.Request(url, data=body_bytes, headers=headers, method="PUT")

    try:
        with request.urlopen(req, timeout=8) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        if hasattr(exc, "code") and hasattr(exc, "read"):
            code = int(getattr(exc, "code"))
            raw = exc.read().decode("utf-8", errors="replace")
            return code, raw
        raise
