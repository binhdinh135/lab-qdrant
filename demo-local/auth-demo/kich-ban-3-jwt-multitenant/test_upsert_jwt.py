"""
Script test upsert với JWT token cho Kịch bản 3 (multi-tenant).

Sinh 1 vector 384 chiều rồi upsert bằng JWT Bearer token.
Payload có department để test filter hoạt động đúng.

Cách dùng:
  D:\\Qdrant\\.venv\\Scripts\\python.exe test_upsert_jwt.py --token-file token_cntt.txt --collection company_docs
"""

import argparse
import json
import sys
from pathlib import Path
from urllib import error, request

QDRANT_URL = "http://localhost:6380"

# Map token file → department (để upsert đúng department)
TOKEN_DEPT_MAP = {
    "token_nhansu.txt": "NHAN_SU",
    "token_cntt.txt": "CNTT",
    "token_ketoan.txt": "KE_TOAN",
}


def generate_dummy_vector(size: int = 384) -> list[float]:
    return [round(i * 0.0026, 4) for i in range(1, size + 1)]


def main():
    parser = argparse.ArgumentParser(description="Test upsert với JWT token (multi-tenant)")
    parser.add_argument("--token-file", required=True, help="File chứa JWT token")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--id", type=int, default=100, help="Point ID (default: 100)")
    args = parser.parse_args()

    # Đọc token
    token_path = Path(__file__).parent / args.token_file
    token = token_path.read_text(encoding="utf-8").strip()

    # Xác định department từ token file
    department = TOKEN_DEPT_MAP.get(args.token_file, "UNKNOWN")

    vector = generate_dummy_vector()
    body = {
        "points": [
            {
                "id": args.id,
                "vector": {
                    "dense": vector,
                    "keywords": {"indices": [], "values": []},
                },
                "payload": {
                    "title": f"Doc moi tu {department} (test upsert)",
                    "department": department,
                    "text": f"Document test upsert qua JWT token {department}",
                },
            }
        ]
    }

    url = f"{QDRANT_URL}/collections/{args.collection}/points?wait=true"
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    req = request.Request(url, data=data, headers=headers, method="PUT")

    try:
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"✅ HTTP {response.status} - Upsert vào {args.collection} (dept={department})")
            print(json.dumps(result, indent=2))
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP {exc.code} - Upsert bị từ chối")
        print(body_text)
        sys.exit(1)


if __name__ == "__main__":
    main()
