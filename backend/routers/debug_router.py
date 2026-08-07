"""Debug routes — test access tokens."""

from typing import Any

from fastapi import APIRouter, Header, HTTPException

from models.schemas import AccessTokenTestRequest
from services.qdrant_service import qdrant_scroll_probe, qdrant_write_probe

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/test-access-token")
def debug_test_access_token(
    body: AccessTokenTestRequest,
    authorization: str = Header(default=""),
) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token")

    qdrant_token = authorization.split(" ", maxsplit=1)[1].strip()
    if not qdrant_token:
        raise HTTPException(status_code=401, detail="Empty Bearer token")

    if body.action == "write":
        qdrant_status, qdrant_response = qdrant_write_probe(body.collection, qdrant_token)
    else:
        qdrant_status, qdrant_response = qdrant_scroll_probe(body.collection, qdrant_token)

    verdict = "allowed" if qdrant_status == 200 else "forbidden" if qdrant_status == 403 else "unknown"

    return {
        "collection": body.collection,
        "action": body.action,
        "qdrant_status": qdrant_status,
        "verdict": verdict,
        "qdrant_response": qdrant_response,
        "mode": "qdrant-jwt-direct",
    }
