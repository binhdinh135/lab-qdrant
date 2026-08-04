"""
Script upsert 1 doc CNTT moi vào company_docs bằng Admin Key.
Dùng để test isolation: sau khi upsert, token NHAN_SU vẫn không thấy doc này.

Cách dùng:
  cd /d D:\\Qdrant\\demo-local\\auth-demo\\kich-ban-3-jwt-multitenant
  D:\\Qdrant\\.venv\\Scripts\\python.exe test_upsert_admin.py
"""

import json
import sys
from urllib import error, request

QDRANT_URL = "http://localhost:6380"
API_KEY = "admin-secret-key-2024"
COLLECTION = "company_docs"


def generate_dummy_vector(size: int = 384) -> list[float]:
    return [round(i * 0.0026, 4) for i in range(1, size + 1)]


def main():
    vector = generate_dummy_vector()
    body = {
        "points": [
            {
                "id": 100,
                "vector": {
                    "dense": vector,
                    "keywords": {"indices": [], "values": []},
                },
                "payload": {
                    "title": "Huong dan Docker (admin added)",
                    "department": "CNTT",
                    "text": "Docker compose cho microservices - upsert boi admin",
                },
            }
        ]
    }

    url = f"{QDRANT_URL}/collections/{COLLECTION}/points?wait=true"
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }

    req = request.Request(url, data=data, headers=headers, method="PUT")

    try:
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"✅ HTTP {response.status} - Admin upsert doc CNTT vào {COLLECTION}")
            print(json.dumps(result, indent=2))
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP {exc.code}")
        print(body_text)
        sys.exit(1)


if __name__ == "__main__":
    main()
