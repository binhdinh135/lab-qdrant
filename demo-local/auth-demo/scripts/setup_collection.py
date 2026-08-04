"""
Script setup: Tạo collection + upsert data cho auth-demo.

Dùng chung cho tất cả kịch bản phân quyền.
Script này dùng ADMIN KEY để:
  1. Tạo collection "auth_demo" (dense 384 + sparse BM25)
  2. Tạo payload indexes
  3. Upsert data từ sample_data (dùng lại points_batch đã generate)

Cách chạy:
  cd /d D:\Qdrant\demo-local\auth-demo
  D:\Qdrant\.venv\Scripts\python.exe scripts\setup_collection.py
"""

import json
import sys
from pathlib import Path
from urllib import error, request

# === CONFIG ===
QDRANT_URL = "http://localhost:6380"
API_KEY = "admin-secret-key-2024"
COLLECTION_NAME = "auth_demo"

# Đường dẫn tới sample_data (dùng lại data đã generate từ demo chính)
SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data"


def call_qdrant(path: str, method: str = "GET", body=None):
    """Gọi Qdrant REST API với Admin Key."""
    url = f"{QDRANT_URL}{path}"
    data = None
    headers = {
        "api-key": API_KEY,
    }

    if body is not None:
        payload = json.dumps(body, ensure_ascii=False)
        data = payload.encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"

    req = request.Request(url, data=data, headers=headers, method=method)

    try:
        with request.urlopen(req) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else {}
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        print(f"  ❌ HTTP {exc.code}: {body_text}")
        return None


def main():
    print("=" * 60)
    print("SETUP COLLECTION CHO AUTH DEMO")
    print("=" * 60)

    # 1. Xóa collection cũ nếu có
    print("\n[1/4] Xóa collection cũ (nếu tồn tại)...")
    call_qdrant(f"/collections/{COLLECTION_NAME}", method="DELETE")
    print("  ✅ Done")

    # 2. Tạo collection mới
    print(f"\n[2/4] Tạo collection '{COLLECTION_NAME}'...")
    body = {
        "vectors": {
            "dense": {
                "size": 384,
                "distance": "Cosine",
            }
        },
        "sparse_vectors": {"keywords": {}},
        "shard_number": 1,
        "replication_factor": 1,
    }
    result = call_qdrant(f"/collections/{COLLECTION_NAME}", method="PUT", body=body)
    if result and result.get("result"):
        print("  ✅ Collection created")
    else:
        print("  ❌ Failed to create collection")
        sys.exit(1)

    # 3. Tạo payload indexes
    print("\n[3/4] Tạo payload indexes...")
    indexes = ["doc_status", "domain", "department", "doc_type"]
    for field in indexes:
        call_qdrant(
            f"/collections/{COLLECTION_NAME}/index",
            method="PUT",
            body={"field_name": field, "field_schema": "keyword"},
        )
        print(f"  ✅ Index: {field}")

    # 4. Upsert data
    print("\n[4/4] Upsert data từ sample_data...")
    total_points = 0
    for batch_file in sorted(SAMPLE_DATA_DIR.glob("points_batch_*.json")):
        data = json.loads(batch_file.read_text(encoding="utf-8"))
        num_points = len(data.get("points", []))
        result = call_qdrant(
            f"/collections/{COLLECTION_NAME}/points?wait=true",
            method="PUT",
            body=data,
        )
        if result and result.get("status") == "ok":
            total_points += num_points
            print(f"  ✅ {batch_file.name}: {num_points} points")
        else:
            print(f"  ❌ Failed: {batch_file.name}")

    # Verify
    print(f"\n{'=' * 60}")
    info = call_qdrant(f"/collections/{COLLECTION_NAME}")
    if info:
        count = info.get("result", {}).get("points_count", 0)
        print(f"✅ HOÀN TẤT! Collection '{COLLECTION_NAME}' có {count} points.")
    print("=" * 60)


if __name__ == "__main__":
    main()
