"""
Script setup data cho Kịch bản 2: JWT per-Collection.

Tạo sample documents cho hr_docs và it_docs, sinh embeddings, rồi upsert.

Cách chạy:
  cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-2-jwt-collection
  D:\Qdrant\.venv\Scripts\python.exe setup_data.py
"""

import json
from pathlib import Path
from urllib import error, request
from fastembed import TextEmbedding, SparseTextEmbedding

QDRANT_URL = "http://localhost:6380"
API_KEY = "admin-secret-key-2024"

# Sample documents cho từng collection
HR_DOCUMENTS = [
    {"id": 1, "title": "Quy chế nghỉ phép 2024", "text": "Nhân viên được nghỉ phép 12 ngày/năm. Nghỉ ốm có giấy bác sĩ không trừ phép.", "department": "NHAN_SU"},
    {"id": 2, "title": "Bảng lương tháng 6", "text": "Lương cơ bản + phụ cấp ăn trưa + thưởng KPI. Chuyển khoản trước ngày 5.", "department": "NHAN_SU"},
    {"id": 3, "title": "Quy trình tuyển dụng", "text": "Nhận CV → phỏng vấn vòng 1 → test kỹ thuật → phỏng vấn vòng 2 → offer.", "department": "NHAN_SU"},
    {"id": 4, "title": "Nội quy công ty", "text": "Giờ làm việc 8h-17h. Đi trễ 3 lần bị cảnh cáo. Trang phục lịch sự.", "department": "NHAN_SU"},
]

IT_DOCUMENTS = [
    {"id": 1, "title": "Hướng dẫn cài đặt VPN", "text": "Tải OpenVPN client, import file .ovpn từ IT. Kết nối bằng tài khoản AD.", "department": "CNTT"},
    {"id": 2, "title": "Chính sách bảo mật", "text": "Password tối thiểu 12 ký tự, đổi mỗi 90 ngày. Bật 2FA cho email.", "department": "CNTT"},
    {"id": 3, "title": "Hướng dẫn Git workflow", "text": "Dùng feature branch → pull request → code review → merge vào main.", "department": "CNTT"},
    {"id": 4, "title": "Cấu hình CI/CD pipeline", "text": "Push code → GitHub Actions build → test → deploy staging → deploy prod.", "department": "CNTT"},
]


def call_qdrant(path: str, method: str = "GET", body=None):
    url = f"{QDRANT_URL}{path}"
    data = None
    headers = {"api-key": API_KEY}

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


def generate_and_upsert(collection_name: str, documents: list):
    """Sinh embeddings và upsert vào collection."""
    print(f"\n  Sinh embeddings cho {len(documents)} documents...")
    
    dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    texts = [f"{doc['title']}. {doc['text']}" for doc in documents]
    dense_embeddings = list(dense_model.embed(texts))
    sparse_embeddings = list(sparse_model.embed(texts))

    points = []
    for i, doc in enumerate(documents):
        point = {
            "id": doc["id"],
            "vector": {
                "dense": [float(x) for x in dense_embeddings[i]],
                "keywords": {
                    "indices": [int(x) for x in sparse_embeddings[i].indices.tolist()],
                    "values": [float(x) for x in sparse_embeddings[i].values.tolist()],
                },
            },
            "payload": {
                "title": doc["title"],
                "text": doc["text"],
                "department": doc["department"],
            },
        }
        points.append(point)

    result = call_qdrant(
        f"/collections/{collection_name}/points?wait=true",
        method="PUT",
        body={"points": points},
    )
    if result and result.get("status") == "ok":
        print(f"  ✅ Upserted {len(points)} points vào {collection_name}")
    else:
        print(f"  ❌ Failed upsert {collection_name}")


def main():
    print("=" * 60)
    print("SETUP DATA CHO KỊCH BẢN 2: JWT PER-COLLECTION")
    print("=" * 60)

    # Tạo indexes cho cả 2 collections
    for collection in ["hr_docs", "it_docs"]:
        print(f"\n[*] Tạo indexes cho {collection}...")
        call_qdrant(
            f"/collections/{collection}/index",
            method="PUT",
            body={"field_name": "department", "field_schema": "keyword"},
        )

    # Sinh embeddings + upsert
    print("\n[1/2] Collection hr_docs...")
    generate_and_upsert("hr_docs", HR_DOCUMENTS)

    print("\n[2/2] Collection it_docs...")
    generate_and_upsert("it_docs", IT_DOCUMENTS)

    # Verify
    print(f"\n{'=' * 60}")
    for col in ["hr_docs", "it_docs"]:
        info = call_qdrant(f"/collections/{col}")
        if info:
            count = info.get("result", {}).get("points_count", 0)
            print(f"  ✅ {col}: {count} points")
    print("=" * 60)


if __name__ == "__main__":
    main()
