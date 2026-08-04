r"""
BÀI 1: KẾT NỐI QDRANT

REST API tương ứng:
  curl.exe http://localhost:6333/healthz
  curl.exe http://localhost:6333

Python Client cung cấp 2 loại:
  - QdrantClient      -> sync (dùng trong script, notebook)
  - AsyncQdrantClient -> async (dùng trong FastAPI)
Cài: D:\Qdrant\.venv\Scripts\python.exe -m pip install qdrant-client
Chạy:
  D:\Qdrant\.venv\Scripts\python.exe 01_connection.py
"""

from qdrant_client import QdrantClient
from config import QDRANT_URL, QDRANT_API_KEY


def main():
    # === 1. Kết nối cơ bản (sync) ===
    # Tương đương: curl http://localhost:6333
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,  # None nếu không cần auth
        timeout=30,  # timeout 30s
    )

    # Health check
    # Tương đương: curl http://localhost:6333/healthz
    print("=== Health Check ===")
    print(f"Qdrant is alive: {QDRANT_URL}")

    # Lấy thông tin cluster
    # Tương đương: GET /cluster
    print("\n=== Cluster Info ===")
    cluster_info = client.get_collections()
    print(f"Số collections hiện có: {len(cluster_info.collections)}")
    for col in cluster_info.collections:
        print(f"  - {col.name}")

    # === 2. Kết nối với gRPC (nhanh hơn cho production) ===
    # gRPC nhanh hơn REST ~30% cho batch operations
    client_grpc = QdrantClient(
        url=QDRANT_URL,
        prefer_grpc=True,  # Ưu tiên gRPC (port 6334)
        api_key=QDRANT_API_KEY,
    )
    print(f"\n=== gRPC Client ===")
    print(f"gRPC enabled: prefer_grpc=True")

    # === 3. In-memory client (cho testing, không cần Docker) ===
    memory_client = QdrantClient(":memory:")
    print(f"\n=== In-Memory Client ===")
    print(f"In-memory mode: không cần Qdrant server!")
    print(f"Dùng cho: unit test, prototyping nhanh")

    # Close clients
    client.close()
    client_grpc.close()
    memory_client.close()

    print("\n✅ Kết nối thành công!")


if __name__ == "__main__":
    main()
