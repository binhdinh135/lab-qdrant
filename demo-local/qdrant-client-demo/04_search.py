"""
BÀI 4: SEARCH VECTOR (Dense Search)

REST API tương ứng:
  POST /collections/{name}/points/query → client.query_points()

Luồng:  Câu hỏi → Embedding → Query Vector → Qdrant Search → Top K results

Chạy:
  D:\\Qdrant\\.venv\\Scripts\\python.exe 04_search.py
"""

from qdrant_client import QdrantClient
from fastembed import TextEmbedding
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME, DENSE_MODEL_NAME


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)

    # === 1. Sinh embedding cho câu hỏi ===
    query = "Hướng dẫn nghỉ phép"
    print(f"Câu hỏi: '{query}'")
    print("Sinh embedding...")

    query_vector = list(dense_model.embed([query]))[0].tolist()
    print(f"  Vector size: {len(query_vector)}")

    # === 2. Search (dense only) ===
    # Tương đương:
    # curl -X POST ".../points/query" -d '{"query": [...], "using": "dense", "limit": 5}'
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using="dense",
        limit=5,
        with_payload=True,
    )

    # === 3. In kết quả ===
    print(f"\n=== Search Results (top 5) ===")
    print(f"{'#':<3} {'Score':<8} {'Department':<10} {'Title'}")
    print("-" * 60)
    for i, point in enumerate(results.points, 1):
        print(f"{i:<3} {point.score:<8.4f} {point.payload['department']:<10} {point.payload['title']}")

    # === 4. Search với limit khác ===
    print(f"\n=== Search top 3 ===")
    results_3 = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using="dense",
        limit=3,
        with_payload=["title", "department"],  # Chỉ lấy 1 số fields
    )
    for point in results_3.points:
        print(f"  [{point.score:.4f}] {point.payload['title']}")

    # === 5. Search với score threshold ===
    print(f"\n=== Search với score > 0.7 ===")
    results_threshold = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using="dense",
        limit=10,
        score_threshold=0.7,  # Chỉ lấy kết quả score >= 0.7
        with_payload=True,
    )
    print(f"  Số kết quả score >= 0.7: {len(results_threshold.points)}")
    for point in results_threshold.points:
        print(f"  [{point.score:.4f}] {point.payload['title']}")

    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
