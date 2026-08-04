"""
BÀI 2: QUẢN LÝ COLLECTION

REST API tương ứng:
  PUT    /collections/{name}  → create_collection()
  GET    /collections/{name}  → get_collection()
  DELETE /collections/{name}  → delete_collection()
  GET    /collections         → get_collections()

Chạy:
  D:\\Qdrant\\.venv\\Scripts\\python.exe 02_collection.py
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    SparseVectorParams,
    PayloadSchemaType,
)
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME, DENSE_VECTOR_SIZE


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # === 1. Xóa collection cũ nếu có ===
    # Tương đương: DELETE /collections/client_demo
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        print(f"🗑️  Đã xóa collection cũ: {COLLECTION_NAME}")

    # === 2. Tạo collection mới ===
    # Tương đương:
    # curl -X PUT "http://localhost:6333/collections/client_demo" \
    #   -H "Content-Type: application/json" \
    #   -d '{"vectors":{"dense":{"size":384,"distance":"Cosine"}}, "sparse_vectors":{"keywords":{}}}'
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": VectorParams(
                size=DENSE_VECTOR_SIZE,
                distance=Distance.COSINE,
            )
        },
        sparse_vectors_config={
            "keywords": SparseVectorParams()
        },
    )
    print(f"✅ Tạo collection: {COLLECTION_NAME}")

    # === 3. Tạo payload indexes ===
    # Tương đương: PUT /collections/client_demo/index
    #   -d '{"field_name":"department","field_schema":"keyword"}'
    for field in ["department", "domain", "doc_type", "doc_status"]:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )
    print("✅ Tạo payload indexes: department, domain, doc_type, doc_status")

    # === 4. Xem thông tin collection ===
    # Tương đương: GET /collections/client_demo
    info = client.get_collection(COLLECTION_NAME)
    print(f"\n=== Collection Info ===")
    print(f"  Name: {COLLECTION_NAME}")
    print(f"  Status: {info.status}")
    print(f"  Points count: {info.points_count}")
    print(f"  Vectors config: {info.config.params.vectors}")
    print(f"  Sparse vectors: {info.config.params.sparse_vectors}")

    # === 5. Liệt kê tất cả collections ===
    # Tương đương: GET /collections
    all_collections = client.get_collections()
    print(f"\n=== All Collections ===")
    for col in all_collections.collections:
        print(f"  - {col.name}")

    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
