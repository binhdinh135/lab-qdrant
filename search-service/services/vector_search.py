"""Semantic (vector) search against Qdrant — uses admin API key."""

from typing import Any
import httpx

from config import QDRANT_URL, QDRANT_API_KEY


async def semantic_search(
    collection: str,
    vector: list[float],
    limit: int = 10,
    offset: int = 0,
    score_threshold: float | None = None,
    payload_filter: dict[str, Any] | None = None,
    with_payload: bool = True,
    with_vectors: bool = False,
) -> dict[str, Any]:
    """
    Vector similarity search. Uses admin API key for full access.
    ACL is enforced via payload_filter (metadata-based).
    """
    body: dict[str, Any] = {
        "vector": vector,
        "limit": limit,
        "offset": offset,
        "with_payload": with_payload,
        "with_vectors": with_vectors,
    }
    if score_threshold is not None:
        body["score_threshold"] = score_threshold
    if payload_filter:
        body["filter"] = payload_filter

    url = f"{QDRANT_URL}/collections/{collection}/points/search"
    headers = {
        "Content-Type": "application/json",
        "api-key": QDRANT_API_KEY,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json=body, headers=headers)

    if resp.status_code == 200:
        return resp.json()
    return {"error": True, "status": resp.status_code, "detail": resp.text}
