"""
BÀI 9: KẾT NỐI VỚI API KEY / JWT

Khi Qdrant bật auth (QDRANT__SERVICE__API_KEY), client phải truyền key.

Chạy (cần Qdrant auth-demo đang chạy ở port 6380):
  D:\\Qdrant\\.venv\\Scripts\\python.exe 09_auth.py
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue


# === Auth Demo server (port 6380) ===
AUTH_URL = "http://localhost:6380"
ADMIN_KEY = "admin-secret-key-2024"
READONLY_KEY = "readonly-key-2024"


def test_admin():
    """Test kết nối với Admin Key — full quyền."""
    print("=== Admin Key ===")
    client = QdrantClient(url=AUTH_URL, api_key=ADMIN_KEY)

    collections = client.get_collections()
    print(f"  Collections: {[c.name for c in collections.collections]}")

    client.close()
    print("  ✅ Admin: đọc OK")


def test_readonly():
    """Test kết nối với Read-only Key — chỉ đọc."""
    print("\n=== Read-only Key ===")
    client = QdrantClient(url=AUTH_URL, api_key=READONLY_KEY)

    # Đọc OK
    collections = client.get_collections()
    print(f"  Collections: {[c.name for c in collections.collections]}")
    print("  ✅ Read-only: đọc OK")

    # Ghi → bị lỗi
    try:
        from qdrant_client.models import VectorParams, Distance
        client.create_collection(
            collection_name="hack_test",
            vectors_config=VectorParams(size=4, distance=Distance.COSINE),
        )
        print("  ❌ BUG: Read-only không nên tạo được collection!")
    except Exception as e:
        print(f"  ✅ Read-only: ghi bị chặn đúng ({type(e).__name__})")

    client.close()


def test_jwt():
    """Test kết nối bằng JWT token."""
    print("\n=== JWT Token ===")

    # Đọc token từ file (nếu đã chạy generate_tokens.py)
    import os
    token_path = os.path.join(
        os.path.dirname(__file__), "..", "auth-demo",
        "kich-ban-2-jwt-collection", "token_hr.txt"
    )

    if not os.path.exists(token_path):
        print("  ⚠️  Chưa có token_hr.txt (chạy generate_tokens.py trước)")
        return

    token = open(token_path).read().strip()

    # JWT token được truyền qua api_key parameter
    client = QdrantClient(url=AUTH_URL, api_key=token)

    # Search collection hr_docs
    try:
        collections = client.get_collections()
        print(f"  Collections visible: {[c.name for c in collections.collections]}")
        print("  ✅ JWT: kết nối OK")
    except Exception as e:
        print(f"  ❌ JWT error: {e}")

    client.close()


def test_no_key():
    """Test kết nối không có key — bị 401."""
    print("\n=== No Key ===")
    client = QdrantClient(url=AUTH_URL)  # Không truyền api_key

    try:
        client.get_collections()
        print("  ❌ BUG: Không key mà vẫn truy cập được!")
    except Exception as e:
        print(f"  ✅ No key: bị chặn đúng ({type(e).__name__})")

    client.close()


def main():
    print("=" * 50)
    print("TEST KẾT NỐI VỚI AUTH (port 6380)")
    print("=" * 50)
    print("⚠️  Cần auth-demo đang chạy: docker compose up -d")
    print()

    try:
        test_admin()
        test_readonly()
        test_jwt()
        test_no_key()
    except Exception as e:
        if "10061" in str(e) or "ConnectError" in str(e) or "ResponseHandling" in str(e):
            print(f"\n❌ Không kết nối được port 6380!")
            print(f"   Hãy chạy trước: cd /d D:\\Qdrant\\demo-local\\auth-demo && docker compose up -d")
            return
        raise

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
