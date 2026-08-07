"""Search Service — FastAPI entry point (port 8001).

All Qdrant calls use admin API key. No auth/role logic here.
Focuses purely on search: semantic, keyword, hybrid, multi-collection.
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from models.schemas import (
    SemanticSearchRequest,
    KeywordSearchRequest,
    HybridSearchRequest,
    MultiSearchRequest,
    UpsertRequest,
    IngestDocumentRequest,
    SemanticSearchResponse,
    KeywordSearchResponse,
    HybridSearchResponse,
    MultiSearchResponse,
    IngestResponse,
    EmbedResponse,
    CollectionsResponse,
)
from services.vector_search import semantic_search
from services.keyword_search import keyword_search
from services.hybrid_search import hybrid_search
from services.ingest import upsert_points_raw, ingest_document
from services.embedding import embed_texts

app = FastAPI(title="Search Service", version="1.0.0")


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "search-service"}


@app.get("/")
def ui():
    return FileResponse(str(STATIC_DIR / "index.html"))


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1)


@app.post("/embed", response_model=EmbedResponse)
def api_embed(body: EmbedRequest) -> dict[str, Any]:
    """Embed texts using BGE-M3, returns dense vectors."""
    result = embed_texts(body.texts, return_sparse=False)
    return {"dense": result["dense"]}


@app.post("/search/semantic", response_model=SemanticSearchResponse)
async def api_semantic_search(body: SemanticSearchRequest) -> dict[str, Any]:
    result = await semantic_search(
        collection=body.collection,
        vector=body.vector,
        limit=body.limit,
        offset=body.offset,
        score_threshold=body.score_threshold,
        payload_filter=body.filter,
        with_payload=body.with_payload,
        with_vectors=body.with_vectors,
    )
    if result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["detail"])
    return result


@app.post("/search/keyword", response_model=KeywordSearchResponse)
async def api_keyword_search(body: KeywordSearchRequest) -> dict[str, Any]:
    result = await keyword_search(
        collection=body.collection,
        query=body.query,
        field=body.field,
        limit=body.limit,
        payload_filter=body.filter,
    )
    if result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["detail"])
    return result


@app.post("/search/hybrid", response_model=HybridSearchResponse)
async def api_hybrid_search(body: HybridSearchRequest) -> dict[str, Any]:
    result = await hybrid_search(
        collection=body.collection,
        vector=body.vector,
        query=body.query,
        query_field=body.query_field,
        limit=body.limit,
        score_threshold=body.score_threshold,
        payload_filter=body.filter,
        vector_weight=body.vector_weight,
        keyword_weight=body.keyword_weight,
        with_payload=body.with_payload,
    )
    if result.get("error"):
        raise HTTPException(status_code=result.get("status", 500), detail=result.get("detail", ""))
    return result


@app.post("/search/multi", response_model=MultiSearchResponse)
async def api_multi_search(body: MultiSearchRequest) -> dict[str, Any]:
    """Search across multiple collections, merge by score."""
    all_results: list[dict[str, Any]] = []
    for collection in body.collections:
        result = await semantic_search(
            collection=collection,
            vector=body.vector,
            limit=body.limit,
            payload_filter=body.filter,
            with_payload=body.with_payload,
        )
        if not result.get("error"):
            points = result.get("result", [])
            for p in points:
                p["_collection"] = collection
            all_results.extend(points)

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {
        "results": all_results[:body.limit],
        "total_candidates": len(all_results),
        "collections_searched": body.collections,
    }


@app.post("/ingest", response_model=IngestResponse)
async def api_upsert(body: UpsertRequest) -> dict[str, Any]:
    """
    Upload points with ACL metadata into a collection.
    Points must have pre-computed vectors.
    """
    points = [
        {
            "id": p.id,
            "vector": p.vector,
            "payload": p.payload.model_dump(),
        }
        for p in body.points
    ]
    result = await upsert_points_raw(body.collection, points)
    if result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["detail"])
    return {"ok": True, "upserted": len(points), "qdrant_result": result}


@app.post("/ingest/document", response_model=IngestResponse)
async def api_ingest_document(body: IngestDocumentRequest) -> dict[str, Any]:
    """
    Full pipeline: text → chunking → BGE-M3 embedding → upload to Qdrant.

    Metadata (ACL fields) is attached to every chunk's payload.
    Example metadata: {"department": "HR", "owner": "tuan", "tags": ["salary"]}
    """
    result = await ingest_document(
        collection=body.collection,
        text=body.text,
        metadata=body.metadata,
        chunk_size=body.chunk_size,
        chunk_overlap=body.chunk_overlap,
        id_prefix=body.id_prefix,
    )
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status", 500),
            detail=result.get("detail", "Ingest failed"),
        )
    return result


@app.get("/collections", response_model=CollectionsResponse)
async def api_list_collections() -> dict[str, Any]:
    """List all collections from Qdrant."""
    import httpx
    from config import QDRANT_URL, QDRANT_API_KEY
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.get(
            f"{QDRANT_URL}/collections",
            headers={"api-key": QDRANT_API_KEY},
        )
    if resp.status_code != 200:
        return {"collections": []}
    data = resp.json()
    result = data.get("result", {})
    collections = [c["name"] for c in result.get("collections", []) if "name" in c]
    return {"collections": sorted(collections)}


from fastapi import UploadFile, File, Form
import fitz  # pymupdf


def _extract_text_from_file(filename: str, content: bytes) -> str:
    """Extract text from uploaded file (txt, md, pdf)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        doc = fitz.open(stream=content, filetype="pdf")
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    # txt, md, or any text file
    return content.decode("utf-8", errors="replace")


@app.post("/ingest/file")
async def api_ingest_file(
    file: UploadFile = File(...),
    collection: str = Form(...),
    metadata_json: str = Form(default="{}"),
    chunk_size: int = Form(default=512),
    chunk_overlap: int = Form(default=50),
) -> dict[str, Any]:
    """
    Upload a file (txt/md/pdf) → extract text → chunk → embed → store.
    metadata_json: JSON string with any fields you want as payload.
    """
    import json as _json

    content = await file.read()
    text = _extract_text_from_file(file.filename or "file.txt", content)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    try:
        metadata = _json.loads(metadata_json)
    except Exception:
        metadata = {}

    # Add source filename to metadata
    metadata.setdefault("source_file", file.filename)

    result = await ingest_document(
        collection=collection,
        text=text,
        metadata=metadata,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status", 500),
            detail=result.get("detail", "Ingest failed"),
        )
    return result
