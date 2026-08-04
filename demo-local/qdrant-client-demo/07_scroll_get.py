"""
BÀI 7: SCROLL, GET BY ID, COUNT

REST API tương ứng:
  POST /collections/{name}/points/scroll  → client.scroll()
  POST /collections/{name}/points         → client.retrieve()
  POST /collections/{name}/points/count   → client.count()

Scroll = phân trang qua toàn bộ data (không cần vector query).
Get = lấy point theo ID cụ thể.

Chạy:
  D:\\Qdrant\\.venv\\Scripts\\python.exe 07_scroll_get.py
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # === 1. Count tổng số points ===
    # Tương đương: POST /points/count -d '{"exact": true}'
    count = client.count(
        collection_name=COLLECTION_NAME,
        exact=True,
    )
    print(f"=== Count ===")
    print(f"  Tổng points: {count.count}")

    # === 2. Count với filter ===
    count_hr = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(
            must=[FieldCondition(key="department", match=MatchValue(value="NHAN_SU"))]
        ),
        exact=True,
    )
    print(f"  Points NHAN_SU: {count_hr.count}")

    # === 3. Scroll (phân trang) ===
    # Tương đương: POST /points/scroll -d '{"limit": 3, "with_payload": true}'
    print(f"\n=== Scroll (page 1, limit=3) ===")
    scroll_result, next_offset = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=3,
        with_payload=True,
        with_vectors=False,
    )
    for point in scroll_result:
        print(f"  id={point.id} | {point.payload['title']}")
    print(f"  → next_offset: {next_offset}")

    # Page 2
    if next_offset:
        print(f"\n=== Scroll (page 2, offset={next_offset}) ===")
        scroll_result2, next_offset2 = client.scroll(
            collection_name=COLLECTION_NAME,
            offset=next_offset,
            limit=3,
            with_payload=True,
            with_vectors=False,
        )
        for point in scroll_result2:
            print(f"  id={point.id} | {point.payload['title']}")
        print(f"  → next_offset: {next_offset2}")

    # === 4. Scroll với filter ===
    print(f"\n=== Scroll (chỉ CNTT) ===")
    scroll_cntt, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="department", match=MatchValue(value="CNTT"))]
        ),
        limit=10,
        with_payload=True,
    )
    for point in scroll_cntt:
        print(f"  id={point.id} | [{point.payload['department']}] {point.payload['title']}")

    # === 5. Get by IDs ===
    # Tương đương: POST /points -d '{"ids": [1, 3, 5]}'
    print(f"\n=== Get by IDs [1, 3, 5] ===")
    points = client.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[1, 3, 5],
        with_payload=True,
        with_vectors=False,
    )
    for point in points:
        print(f"  id={point.id} | {point.payload['title']}")

    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
