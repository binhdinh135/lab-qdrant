"""
BÀI 10: FASTAPI ENDPOINTS (/search, /upsert)

Đây là bước cuối: tích hợp qdrant-client vào web API.

Cài thêm:
  D:\\Qdrant\\.venv\\Scripts\\pip.exe install fastapi uvicorn

Chạy server:
  D:\\Qdrant\\.venv\\Scripts\\python.exe -m uvicorn 10_fastapi_endpoint:app --reload --port 8000

Test:
  curl http://localhost:8000/health
  curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d "{\"query\":\"nghỉ phép\",\"limit\":3}"
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.models import (
    SparseVector, Prefetch, FusionQuery, Fusion,
    Filter, FieldCondition, MatchValue, PointStruct,
)
from fastembed import TextEmbedding, SparseTextEmbedding

from config import (
    QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME,
    DENSE_MODEL_NAME, SPARSE_MODEL_NAME,
)
from models import SearchRequest, SearchResult, UpsertRequest


# === Global resources ===
client: QdrantClient = None
dense_model: TextEmbedding = None
sparse_model: SparseTextEmbedding = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo resources khi start, cleanup khi stop."""
    global client, dense_model, sparse_model

    # Startup
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)
    print("✅ Qdrant client + embedding models loaded")

    yield

    # Shutdown
    client.close()
    print("🔒 Qdrant client closed")


app = FastAPI(
    title="Qdrant Client Demo API",
    description="Demo tích hợp qdrant-client với FastAPI",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok", "qdrant": QDRANT_URL, "collection": COLLECTION_NAME}


@app.post("/search", response_model=list[SearchResult])
def search(request: SearchRequest):
    """
    Hybrid Search (dense + sparse + RRF).

    Tương đương REST:
      POST /collections/{name}/points/query
        body: {"prefetch": [...], "query": {"fusion": "rrf"}}
    """
    # Sinh embeddings
    query_dense = list(dense_model.embed([request.query]))[0].tolist()
    query_sparse_raw = list(sparse_model.embed([request.query]))[0]
    query_sparse = SparseVector(
        indices=query_sparse_raw.indices.tolist(),
        values=query_sparse_raw.values.tolist(),
    )

    # Build filter
    query_filter = None
    if request.department:
        query_filter = Filter(
            must=[FieldCondition(key="department", match=MatchValue(value=request.department))]
        )

    # Hybrid search
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            Prefetch(query=query_dense, using="dense", limit=20),
            Prefetch(query=query_sparse, using="keywords", limit=20),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        query_filter=query_filter,
        limit=request.limit,
        with_payload=True,
    )

    # Map to response model
    return [
        SearchResult(
            id=point.id,
            score=point.score,
            title=point.payload.get("title", ""),
            text=point.payload.get("text", ""),
            department=point.payload.get("department", ""),
        )
        for point in results.points
    ]


@app.post("/upsert")
def upsert(request: UpsertRequest):
    """
    Upsert 1 document.

    Luồng: text → embedding → upsert vào Qdrant.
    """
    text = f"{request.title}. {request.text}"

    # Sinh embeddings
    dense_vec = list(dense_model.embed([text]))[0].tolist()
    sparse_raw = list(sparse_model.embed([text]))[0]

    # Tạo point ID từ hash document_id
    point_id = abs(hash(request.document_id)) % (10**8)

    # Upsert
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector={
                    "dense": dense_vec,
                    "keywords": SparseVector(
                        indices=sparse_raw.indices.tolist(),
                        values=sparse_raw.values.tolist(),
                    ),
                },
                payload={
                    "document_id": request.document_id,
                    "title": request.title,
                    "text": request.text,
                    "department": request.department,
                    "domain": request.domain,
                    "doc_type": request.doc_type,
                    "doc_status": "ACTIVE",
                },
            )
        ],
        wait=True,
    )

    return {"status": "ok", "point_id": point_id, "document_id": request.document_id}


@app.get("/collections")
def list_collections():
    """Liệt kê collections."""
    result = client.get_collections()
    return {"collections": [c.name for c in result.collections]}


@app.get("/count")
def count(department: str = None):
    """Đếm points, có thể filter theo department."""
    count_filter = None
    if department:
        count_filter = Filter(
            must=[FieldCondition(key="department", match=MatchValue(value=department))]
        )
    result = client.count(collection_name=COLLECTION_NAME, count_filter=count_filter, exact=True)
    return {"count": result.count, "department": department}
