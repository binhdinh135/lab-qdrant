"""
BÀI 8: UPDATE PAYLOAD & DELETE POINTS

REST API tương ứng:
  POST /collections/{name}/points/payload  → client.set_payload()
  POST /collections/{name}/points/delete   → client.delete()

Chạy:
  D:\\Qdrant\\.venv\\Scripts\\python.exe 08_update_delete.py
"""

from qdrant_client import QdrantClient
from qdrant_client.models import PointIdsList, Filter, FieldCondition, MatchValue
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # === 1. Set payload (update metadata) ===
    # Tương đương: POST /points/payload -d '{"payload": {...}, "points": [1]}'
    print("=== Update payload point id=1 ===")
    client.set_payload(
        collection_name=COLLECTION_NAME,
        payload={"doc_status": "ARCHIVED", "updated_by": "admin"},
        points=[1],
    )
    # Verify
    points = client.retrieve(collection_name=COLLECTION_NAME, ids=[1], with_payload=True)
    print(f"  Point 1 status: {points[0].payload['doc_status']}")
    print(f"  Point 1 updated_by: {points[0].payload.get('updated_by')}")

    # === 2. Overwrite payload (thay thế toàn bộ) ===
    print("\n=== Overwrite payload point id=1 (set lại status) ===")
    client.overwrite_payload(
        collection_name=COLLECTION_NAME,
        payload={
            "document_id": "DOC-001",
            "title": "Quy chế nghỉ phép 2024 (updated)",
            "text": "Nhân viên được nghỉ phép 15 ngày/năm (tăng từ 12).",
            "department": "NHAN_SU",
            "domain": "nhan_su",
            "doc_type": "quy_dinh",
            "doc_status": "ACTIVE",
        },
        points=[1],
    )
    points = client.retrieve(collection_name=COLLECTION_NAME, ids=[1], with_payload=True)
    print(f"  Title mới: {points[0].payload['title']}")
    print(f"  Text mới: {points[0].payload['text']}")

    # === 3. Delete payload key ===
    print("\n=== Delete payload key 'updated_by' khỏi point 1 ===")
    client.delete_payload(
        collection_name=COLLECTION_NAME,
        keys=["updated_by"],
        points=[1],
    )
    points = client.retrieve(collection_name=COLLECTION_NAME, ids=[1], with_payload=True)
    print(f"  'updated_by' còn tồn tại: {'updated_by' in points[0].payload}")

    # === 4. Delete points by IDs ===
    # Tương đương: POST /points/delete -d '{"points": [100]}'
    print("\n=== Delete point id=100 ===")
    count_before = client.count(collection_name=COLLECTION_NAME, exact=True).count
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=PointIdsList(points=[100]),
    )
    count_after = client.count(collection_name=COLLECTION_NAME, exact=True).count
    print(f"  Before: {count_before} points")
    print(f"  After:  {count_after} points")

    # === 5. Delete points by filter ===
    # Xóa tất cả points có doc_status = "ARCHIVED"
    print("\n=== Delete by filter (doc_status=ARCHIVED) ===")
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="doc_status", match=MatchValue(value="ARCHIVED"))]
        ),
    )
    count_final = client.count(collection_name=COLLECTION_NAME, exact=True).count
    print(f"  Points còn lại: {count_final}")

    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
