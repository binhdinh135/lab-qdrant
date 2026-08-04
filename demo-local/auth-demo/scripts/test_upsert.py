"""
Script test upsert 1 point vào collection auth_demo.

Sinh 1 vector 384 chiều (dummy) rồi gửi PUT /points.
Dùng để test phân quyền: admin key sẽ thành công, readonly key sẽ bị 403.

Cách dùng:
  D:\\Qdrant\\.venv\\Scripts\\python.exe scripts\\test_upsert.py --key admin-secret-key-2024
  D:\\Qdrant\\.venv\\Scripts\\python.exe scripts\\test_upsert.py --key readonly-key-2024
"""

import argparse
import json
import sys
from urllib import error, request

QDRANT_URL = "http://localhost:6380"
COLLECTION_NAME = "auth_demo"


def generate_dummy_vector(size: int = 384) -> list[float]:
    """Tạo vector dummy 384 chiều."""
    return [round(i * 0.0026, 4) for i in range(1, size + 1)]


def main():
    parser = argparse.ArgumentParser(description="Test upsert với API key")
    parser.add_argument("--key", required=True, help="API key để test")
    parser.add_argument("--id", type=int, default=9999, help="Point ID (default: 9999)")
    args = parser.parse_args()

    vector = generate_dummy_vector()
    body = {
        "points": [
            {
                "id": args.id,
                "vector": {"dense": vector},
                "payload": {
                    "title": f"Test upsert with key: {args.key[:10]}...",
                    "department": "TEST",
                },
            }
        ]
    }

    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points?wait=true"
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "api-key": args.key,
    }

    req = request.Request(url, data=data, headers=headers, method="PUT")

    try:
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"✅ HTTP {response.status}")
            print(json.dumps(result, indent=2))
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP {exc.code}")
        print(body_text)
        sys.exit(1)


if __name__ == "__main__":
    main()
