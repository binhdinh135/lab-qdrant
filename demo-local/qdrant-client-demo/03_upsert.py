"""
BÀI 3: UPSERT POINTS (Đơn lẻ + Batch)

REST API tương ứng:
  PUT /collections/{name}/points?wait=true → client.upsert()

Luồng:  Text → Embedding Model → Vector → Upsert vào Qdrant

Chạy:
  D:\\Qdrant\\.venv\\Scripts\\python.exe 03_upsert.py
"""

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, SparseVector
from fastembed import TextEmbedding, SparseTextEmbedding
from config import (
    QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME,
    DENSE_MODEL_NAME, SPARSE_MODEL_NAME,
)
from models import Document


# Sample documents
DOCUMENTS = [
    Document(document_id="DOC-001", title="Quy chế nghỉ phép 2024",
             text="Nhân viên được nghỉ phép 12 ngày/năm. Nghỉ ốm có giấy bác sĩ không trừ phép.",
             department="NHAN_SU", domain="nhan_su", doc_type="quy_dinh"),
    Document(document_id="DOC-002", title="Bảng lương tháng 6",
             text="Lương cơ bản + phụ cấp ăn trưa + thưởng KPI. Chuyển khoản trước ngày 5.",
             department="NHAN_SU", domain="nhan_su", doc_type="bao_cao"),
    Document(document_id="DOC-003", title="Hướng dẫn cài đặt VPN",
             text="Tải OpenVPN client từ share drive. Import file .ovpn. Kết nối bằng tài khoản AD.",
             department="CNTT", domain="cong_nghe", doc_type="huong_dan"),
    Document(document_id="DOC-004", title="Chính sách bảo mật password",
             text="Password tối thiểu 12 ký tự, bao gồm chữ hoa, thường, số, ký tự đặc biệt. Đổi 90 ngày.",
             department="CNTT", domain="cong_nghe", doc_type="chinh_sach"),
    Document(document_id="DOC-005", title="Quy trình đề nghị thanh toán",
             text="Điền form đề nghị thanh toán trước ngày 25. Đính kèm hóa đơn gốc. Trưởng phòng ký duyệt.",
             department="KE_TOAN", domain="hanh_chinh", doc_type="quy_trinh"),
    Document(document_id="DOC-006", title="Báo cáo tài chính Q2 2024",
             text="Doanh thu tăng 15% so với Q1. Chi phí vận hành giảm 5%. Lợi nhuận ròng đạt mục tiêu.",
             department="KE_TOAN", domain="hanh_chinh", doc_type="bao_cao"),
]


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # === 1. Load embedding models ===
    print("Loading embedding models...")
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)
    print("  ✅ Dense model: bge-small-en-v1.5 (384 dims)")
    print("  ✅ Sparse model: BM25")

    # === 2. Sinh embeddings cho tất cả documents ===
    print("\nSinh embeddings...")
    texts = [f"{doc.title}. {doc.text}" for doc in DOCUMENTS]

    dense_vectors = list(dense_model.embed(texts))
    sparse_vectors = list(sparse_model.embed(texts))
    print(f"  ✅ {len(texts)} documents → {len(dense_vectors)} dense + {len(sparse_vectors)} sparse vectors")

    # === 3. Tạo PointStruct list ===
    # PointStruct = 1 điểm dữ liệu gồm: id + vector + payload
    points = []
    for i, doc in enumerate(DOCUMENTS):
        point = PointStruct(
            id=i + 1,  # ID kiểu int
            vector={
                "dense": dense_vectors[i].tolist(),
                "keywords": SparseVector(
                    indices=sparse_vectors[i].indices.tolist(),
                    values=sparse_vectors[i].values.tolist(),
                ),
            },
            payload=doc.model_dump(),  # Pydantic → dict
        )
        points.append(point)

    # === 4. Upsert batch ===
    # Tương đương:
    # curl -X PUT "http://localhost:6333/collections/client_demo/points?wait=true"
    #   -d '{"points": [...]}'
    result = client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True,  # Đợi ghi xong mới return
    )
    print(f"\n=== Upsert Result ===")
    print(f"  Status: {result.status}")
    print(f"  Points upserted: {len(points)}")

    # === 5. Verify ===
    info = client.get_collection(COLLECTION_NAME)
    print(f"\n=== Verify ===")
    print(f"  Collection '{COLLECTION_NAME}' có {info.points_count} points")

    # === 6. Upsert đơn lẻ (1 point) ===
    # Ví dụ thêm 1 document mới
    new_text = "Hướng dẫn Git workflow: dùng feature branch, pull request, code review."
    new_dense = list(dense_model.embed([new_text]))[0]
    new_sparse = list(sparse_model.embed([new_text]))[0]

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=100,
                vector={
                    "dense": new_dense.tolist(),
                    "keywords": SparseVector(
                        indices=new_sparse.indices.tolist(),
                        values=new_sparse.values.tolist(),
                    ),
                },
                payload={
                    "document_id": "DOC-100",
                    "title": "Hướng dẫn Git workflow",
                    "text": new_text,
                    "department": "CNTT",
                    "domain": "cong_nghe",
                    "doc_type": "huong_dan",
                    "doc_status": "ACTIVE",
                },
            )
        ],
        wait=True,
    )
    print(f"  ✅ Upsert thêm 1 point (id=100)")

    client.close()
    print("\n✅ Done! Tổng cộng 7 points trong collection.")


if __name__ == "__main__":
    main()
