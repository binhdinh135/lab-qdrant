"""Hybrid search — combine vector + keyword with RRF fusion."""

from typing import Any

from services.vector_search import semantic_search
from services.keyword_search import keyword_search


def _rrf_score(rank: int, k: int = 60) -> float:
    """Reciprocal Rank Fusion score."""
    return 1.0 / (k + rank)


async def hybrid_search(
    collection: str,
    vector: list[float],
    query: str,
    query_field: str,
    limit: int = 10,
    score_threshold: float | None = None,
    payload_filter: dict[str, Any] | None = None,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
    with_payload: bool = True,
) -> dict[str, Any]:
    """
    Hybrid search using Reciprocal Rank Fusion (RRF).
    1. Run semantic search
    2. Run keyword search
    3. Fuse with weighted RRF
    """
    candidate_limit = min(limit * 3, 100)

    vector_results = await semantic_search(
        collection=collection,
        vector=vector,
        limit=candidate_limit,
        score_threshold=score_threshold,
        payload_filter=payload_filter,
        with_payload=with_payload,
    )

    keyword_results = await keyword_search(
        collection=collection,
        query=query,
        field=query_field,
        limit=candidate_limit,
        payload_filter=payload_filter,
    )

    if vector_results.get("error"):
        return vector_results
    if keyword_results.get("error"):
        return keyword_results

    vector_points = vector_results.get("result", [])
    keyword_points = keyword_results.get("result", {}).get("points", [])

    scores: dict[int | str, dict[str, Any]] = {}

    for rank, point in enumerate(vector_points, start=1):
        point_id = point["id"]
        scores[point_id] = {
            "id": point_id,
            "payload": point.get("payload"),
            "rrf_score": vector_weight * _rrf_score(rank),
            "vector_rank": rank,
            "keyword_rank": None,
        }

    for rank, point in enumerate(keyword_points, start=1):
        point_id = point["id"]
        if point_id in scores:
            scores[point_id]["rrf_score"] += keyword_weight * _rrf_score(rank)
            scores[point_id]["keyword_rank"] = rank
        else:
            scores[point_id] = {
                "id": point_id,
                "payload": point.get("payload"),
                "rrf_score": keyword_weight * _rrf_score(rank),
                "vector_rank": None,
                "keyword_rank": rank,
            }

    fused = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)[:limit]

    return {
        "result": fused,
        "vector_count": len(vector_points),
        "keyword_count": len(keyword_points),
        "fused_count": len(fused),
    }
