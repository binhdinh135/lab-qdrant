"""
Script setup data cho Kịch bản 3: Multi-tenant.

Tạo collection company_docs với data từ 3 phòng ban,
sinh embeddings bằng fastembed rồi upsert.

Cách chạy:
  cd /d D:\Qdrant\demo-local\auth-demo\kich-ban-3-jwt-multitenant
  D:\Qdrant\.venv\Scripts\python.exe setup_data.py
"""

import json
from pathlib import Path
from urllib import error, request
from fastembed import TextEmbedding, SparseTextEmbedding

QDRANT_URL = "http://localhost:6380"
API_KEY = "admin-secret-key-2024"
COLLECTION_NAME = "company_docs"

# 6 documents, 3 phòng ban (2 docs mỗi phòng)
DOCUMENTS = [
    {
        "id": 1,
        "title": "Quy chế nghỉ phép 2024",
        "text": "Nhân viên chính thức được nghỉ phép 12 ngày/năm. Nghỉ ốm có giấy bác sĩ không trừ phép.",
        "department": "NHAN_SU",
    },
    {
        "id": 2,
        "title": "Bảng lương tháng 6",
        "text": "Lương cơ bản + phụ cấp ăn trưa + thưởng KPI hàng quý. Chuyển khoản trước ngày 5.",
        "department": "NHAN_SU",
    },
    {
        "id": 3,
        "title": "Hướng dẫn cài đặt VPN",
        "text": "Tải OpenVPN client từ share drive. Import file .ovpn. Kết nối bằng tài khoản Active Directory.",
        "department": "CNTT",
    },
    {
        "id": 4,
        "title": "Chính sách bảo mật password",
        "text": "Password tối thiểu 12 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt. Đổi mỗi 90 ngày.",
        "department": "CNTT",
    },
    {
        "id": 5,
        "title": "Quy trình đề nghị thanh toán",
        "text": "Điền form đề nghị thanh toán trước ngày 25. Đính kèm hóa đơn gốc. Trưởng phòng ký duyệt.",
        "department": "KE_TOAN",
    },
    {
        "id": 6,
        "title": "Báo cáo tài chính Q2 2024",
        "text": "Doanh thu tăng 15% so với Q1. Chi phí vận hành giảm 5%. Lợi nhuận ròng đạt mục tiêu.",
        "department": "KE_TOAN",
    },
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


def main():
    print("=" * 60)
    print("SETUP DATA CHO KỊCH BẢN 3: MULTI-TENANT")
    print("=" * 60)

    # 1. Xóa + tạo collection
    print(f"\n[1/3] Tạo collection {COLLECTION_NAME}...")
    call_qdrant(f"/collections/{COLLECTION_NAME}", method="DELETE")
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
        print("  ✅ Created")
    else:
        print("  ❌ Failed")
        return

    # 2. Indexes
    print("\n[2/3] Tạo indexes...")
    call_qdrant(
        f"/collections/{COLLECTION_NAME}/index",
        method="PUT",
        body={"field_name": "department", "field_schema": "keyword"},
    )
    print("  ✅ department (keyword)")

    # 3. Sinh embeddings + upsert
    print(f"\n[3/3] Sinh embeddings + upsert {len(DOCUMENTS)} documents (3 phòng ban)...")

    dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    texts = [f"{doc['title']}. {doc['text']}" for doc in DOCUMENTS]
    dense_embeddings = list(dense_model.embed(texts))
    sparse_embeddings = list(sparse_model.embed(texts))

    points = []
    for i, doc in enumerate(DOCUMENTS):
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
        f"/collections/{COLLECTION_NAME}/points?wait=true",
        method="PUT",
        body={"points": points},
    )
    if result and result.get("status") == "ok":
        print(f"  ✅ {len(points)} points upserted")
    else:
        print("  ❌ Upsert failed")

    # Verify
    print(f"\n{'=' * 60}")
    info = call_qdrant(f"/collections/{COLLECTION_NAME}")
    if info:
        count = info.get("result", {}).get("points_count", 0)
        print(f"✅ HOÀN TẤT! Collection '{COLLECTION_NAME}' có {count} points (3 phòng ban).")
    print("=" * 60)


if __name__ == "__main__":
    main()
