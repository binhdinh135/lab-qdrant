"""
BÀI 5: SEARCH + FILTER PAYLOAD

REST API tương ứng:
  POST /collections/{name}/points/query
    với body có "filter": {"must": [...]}

Filter giúp thu hẹp phạm vi search theo metadata (department, status, ...)
mà KHÔNG ảnh hưởng tốc độ (nhờ payload index).

Chạy:
  D:\\Qdrant\\.venv\\Scripts\\python.exe 05_search_filter.py
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
from fastembed import TextEmbedding
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME, DENSE_MODEL_NAME


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)

    query = "Hướng dẫn quy trình"
    query_vector = list(dense_model.embed([query]))[0].tolist()
    print(f"Câu hỏi: '{query}'\n")

    # === 1. Filter: department = NHAN_SU ===
    # Tương đương JSON:
    # "filter": {"must": [{"key": "department", "match": {"value": "NHAN_SU"}}]}
    print("=== Filter: department = NHAN_SU ===")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using="dense",
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="department",
                    match=MatchValue(value="NHAN_SU"),
                )
            ]
        ),
        limit=5,
        with_payload=True,
    )
    for point in results.points:
        print(f"  [{point.score:.4f}] [{point.payload['department']}] {point.payload['title']}")

    # === 2. Filter: department = CNTT ===
    print("\n=== Filter: department = CNTT ===")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using="dense",
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="department",
                    match=MatchValue(value="CNTT"),
                )
            ]
        ),
        limit=5,
        with_payload=True,
    )
    for point in results.points:
        print(f"  [{point.score:.4f}] [{point.payload['department']}] {point.payload['title']}")

    # === 3. Multi-filter: department = CNTT AND doc_type = huong_dan ===
    # Tương đương: "must": [cond1, cond2] → AND logic
    print("\n=== Multi-filter: CNTT + huong_dan ===")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using="dense",
        query_filter=Filter(
            must=[
                FieldCondition(key="department", match=MatchValue(value="CNTT")),
                FieldCondition(key="doc_type", match=MatchValue(value="huong_dan")),
            ]
        ),
        limit=5,
        with_payload=True,
    )
    for point in results.points:
        print(f"  [{point.score:.4f}] [{point.payload['doc_type']}] {point.payload['title']}")

    # === 4. must_not: loại bỏ KE_TOAN ===
    # Tương đương: "must_not": [{"key": "department", "match": {"value": "KE_TOAN"}}]
    print("\n=== must_not: loại bỏ KE_TOAN ===")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using="dense",
        query_filter=Filter(
            must_not=[
                FieldCondition(key="department", match=MatchValue(value="KE_TOAN")),
            ]
        ),
        limit=5,
        with_payload=True,
    )
    for point in results.points:
        print(f"  [{point.score:.4f}] [{point.payload['department']}] {point.payload['title']}")

    # === 5. should: NHAN_SU HOẶC CNTT (OR logic) ===
    print("\n=== should: NHAN_SU hoặc CNTT ===")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using="dense",
        query_filter=Filter(
            should=[
                FieldCondition(key="department", match=MatchValue(value="NHAN_SU")),
                FieldCondition(key="department", match=MatchValue(value="CNTT")),
            ]
        ),
        limit=5,
        with_payload=True,
    )
    for point in results.points:
        print(f"  [{point.score:.4f}] [{point.payload['department']}] {point.payload['title']}")

    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
