"""
BÀI 6: HYBRID SEARCH (Dense + Sparse + RRF Fusion)

REST API tương ứng:
  POST /collections/{name}/points/query
    với body: {"prefetch": [...], "query": {"fusion": "rrf"}}

Hybrid = Dense (semantic) + Sparse (keyword BM25) → Fusion (RRF)

Chạy:
  D:\\Qdrant\\.venv\\Scripts\\python.exe 06_hybrid_search.py
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    SparseVector, Prefetch, FusionQuery, Fusion,
    Filter, FieldCondition, MatchValue,
)
from fastembed import TextEmbedding, SparseTextEmbedding
from config import (
    QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME,
    DENSE_MODEL_NAME, SPARSE_MODEL_NAME,
)


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)

    query = "Hướng dẫn nghỉ phép"
    print(f"Câu hỏi: '{query}'")

    # Sinh cả dense + sparse embedding cho query
    query_dense = list(dense_model.embed([query]))[0].tolist()
    query_sparse_raw = list(sparse_model.embed([query]))[0]
    query_sparse = SparseVector(
        indices=query_sparse_raw.indices.tolist(),
        values=query_sparse_raw.values.tolist(),
    )

    # === 1. Dense-only search (so sánh) ===
    print("\n=== Dense Only ===")
    dense_results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_dense,
        using="dense",
        limit=5,
        with_payload=["title", "department"],
    )
    for point in dense_results.points:
        print(f"  [{point.score:.4f}] {point.payload['title']}")

    # === 2. Sparse-only search (BM25 keyword) ===
    print("\n=== Sparse Only (BM25) ===")
    sparse_results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_sparse,
        using="keywords",
        limit=5,
        with_payload=["title", "department"],
    )
    for point in sparse_results.points:
        print(f"  [{point.score:.4f}] {point.payload['title']}")

    # === 3. HYBRID SEARCH (Dense + Sparse + RRF) ===
    # Tương đương REST:
    # {"prefetch": [
    #   {"query": [dense_vector], "using": "dense", "limit": 20},
    #   {"query": {"indices": [...], "values": [...]}, "using": "keywords", "limit": 20}
    # ], "query": {"fusion": "rrf"}, "limit": 5}
    print("\n=== HYBRID (Dense + Sparse + RRF Fusion) ===")
    hybrid_results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            Prefetch(query=query_dense, using="dense", limit=20),
            Prefetch(query=query_sparse, using="keywords", limit=20),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=5,
        with_payload=True,
    )
    for point in hybrid_results.points:
        print(f"  [{point.score:.4f}] [{point.payload['department']}] {point.payload['title']}")

    # === 4. Hybrid + Filter ===
    print("\n=== HYBRID + Filter (chỉ NHAN_SU) ===")
    hybrid_filtered = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            Prefetch(query=query_dense, using="dense", limit=20),
            Prefetch(query=query_sparse, using="keywords", limit=20),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        query_filter=Filter(
            must=[FieldCondition(key="department", match=MatchValue(value="NHAN_SU"))]
        ),
        limit=5,
        with_payload=True,
    )
    for point in hybrid_filtered.points:
        print(f"  [{point.score:.4f}] [{point.payload['department']}] {point.payload['title']}")

    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
