"""
Script test upsert với JWT token cho Kịch bản 2.

Sinh 1 vector 384 chiều rồi upsert bằng JWT Bearer token.

Cách dùng:
  D:\Qdrant\.venv\Scripts\python.exe test_upsert_jwt.py --token-file token_hr.txt --collection hr_docs
  D:\Qdrant\.venv\Scripts\python.exe test_upsert_jwt.py --token-file token_it.txt --collection hr_docs
"""

import argparse
import json
import sys
from pathlib import Path
from urllib import error, request

QDRANT_URL = "http://localhost:6380"


def generate_dummy_vector(size: int = 384) -> list[float]:
    return [round(i * 0.0026, 4) for i in range(1, size + 1)]


def main():
    parser = argparse.ArgumentParser(description="Test upsert với JWT token")
    parser.add_argument("--token-file", required=True, help="File chứa JWT token")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--id", type=int, default=999, help="Point ID (default: 999)")
    args = parser.parse_args()

    # Đọc token
    token_path = Path(__file__).parent / args.token_file
    token = token_path.read_text(encoding="utf-8").strip()

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
                    "title": f"Test upsert via JWT into {args.collection}",
                    "department": "TEST",
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
            print(f"✅ HTTP {response.status} - Upsert vào {args.collection} thành công")
            print(json.dumps(result, indent=2))
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP {exc.code} - Upsert vào {args.collection} bị từ chối")
        print(body_text)
        sys.exit(1)


if __name__ == "__main__":
    main()
