"""Data ingestion pipeline — chunk + embed + upload to Qdrant.

Luồng:
1. Nhận document text + metadata (ACL fields)
2. Chunking (chia nhỏ theo đoạn)
3. Embedding (BGE-M3: dense 1024d + sparse BM25)
4. Upload vào Qdrant (dense vector + sparse vector + payload)
"""

from typing import Any
import httpx
import time

from config import QDRANT_URL, QDRANT_API_KEY
from services.chunking import chunk_text
from services.embedding import embed_texts


async def upsert_points_raw(
    collection: str,
    points: list[dict[str, Any]],
) -> dict[str, Any]:
    """Upload pre-built points to Qdrant."""
    url = f"{QDRANT_URL}/collections/{collection}/points"
    headers = {
        "Content-Type": "application/json",
        "api-key": QDRANT_API_KEY,
    }
    body = {"points": points}

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.put(url, json=body, headers=headers)

    if resp.status_code == 200:
        return resp.json()
    return {"error": True, "status": resp.status_code, "detail": resp.text}


async def ingest_document(
    collection: str,
    text: str,
    metadata: dict[str, Any],
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    id_prefix: str = "",
) -> dict[str, Any]:
    """
    Full pipeline: chunk → embed → upload.

    Args:
        collection: Target Qdrant collection.
        text: Full document text.
        metadata: ACL metadata (department, owner, tags, etc.)
                  Will be attached to every chunk.
        chunk_size: Characters per chunk.
        chunk_overlap: Overlap between chunks.
        id_prefix: Prefix for point IDs (e.g. "doc1_").

    Returns:
        Upload result with chunk count.
    """
    # 1. Chunk
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        return {"error": True, "detail": "No chunks generated from text"}

    # 2. Embed (dense + sparse)
    embeddings = embed_texts(chunks, return_sparse=True)
    dense_vectors = embeddings["dense"]
    sparse_vectors = embeddings.get("sparse", [])

    # 3. Build points
    base_id = int(time.time() * 1000)
    points: list[dict[str, Any]] = []

    for i, chunk in enumerate(chunks):
        point_id = f"{id_prefix}{base_id + i}" if id_prefix else base_id + i
        payload = {
            **metadata,
            "text": chunk,
            "chunk_index": i,
            "total_chunks": len(chunks),
        }

        point: dict[str, Any] = {
            "id": point_id if isinstance(point_id, int) else hash(point_id) % (2**63),
            "vector": dense_vectors[i],
            "payload": payload,
        }

        points.append(point)

    # 4. Upload
    result = await upsert_points_raw(collection, points)
    if result.get("error"):
        return result

    return {
        "ok": True,
        "chunks": len(chunks),
        "collection": collection,
        "qdrant_result": result,
    }
