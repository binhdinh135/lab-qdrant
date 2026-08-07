"""Keyword (full-text) search against Qdrant — uses admin API key."""

from typing import Any
import httpx

from config import QDRANT_URL, QDRANT_API_KEY


async def keyword_search(
    collection: str,
    query: str,
    field: str,
    limit: int = 10,
    payload_filter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Full-text keyword search using Qdrant scroll + text match filter.
    Uses admin API key. ACL enforced via payload_filter.
    """
    text_condition = {"key": field, "match": {"text": query}}

    filter_obj: dict[str, Any] = {"must": [text_condition]}
    if payload_filter and "must" in payload_filter:
        filter_obj["must"].extend(payload_filter["must"])
    elif payload_filter and "should" in payload_filter:
        filter_obj["must"].append(payload_filter)

    body: dict[str, Any] = {
        "filter": filter_obj,
        "limit": limit,
        "with_payload": True,
    }

    url = f"{QDRANT_URL}/collections/{collection}/points/scroll"
    headers = {
        "Content-Type": "application/json",
        "api-key": QDRANT_API_KEY,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json=body, headers=headers)

    if resp.status_code == 200:
        return resp.json()
    return {"error": True, "status": resp.status_code, "detail": resp.text}
