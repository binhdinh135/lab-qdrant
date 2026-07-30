import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib import error, request

LOG_PATH = BASE_DIR = Path(__file__).resolve().parent / "upload_result.log"

BASE_DIR = Path(__file__).resolve().parent
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "smart_search_demo"


def write_log(message: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")
    print(message)


def call_qdrant(path: str, method: str = "GET", body: Any = None) -> Any:
    url = f"{QDRANT_URL}{path}"
    data = None
    headers = {}

    if body is not None:
        payload = json.dumps(body, ensure_ascii=False)
        data = payload.encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"

    req = request.Request(url, data=data, headers=headers, method=method)

    try:
        with request.urlopen(req) as response:
            text = response.read().decode("utf-8")
            if not text:
                return {}
            return json.loads(text)
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Qdrant request failed: {exc.code} {exc.reason}\n{body_text}") from exc


def recreate_collection() -> None:
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
    call_qdrant(f"/collections/{COLLECTION_NAME}", method="PUT", body=body)

    for field in ["doc_status", "domain", "department", "doc_type"]:
        call_qdrant(
            f"/collections/{COLLECTION_NAME}/index",
            method="PUT",
            body={"field_name": field, "field_schema": "keyword"},
        )


def upsert_points(file_name: str) -> None:
    file_path = BASE_DIR / file_name
    raw_text = file_path.read_text(encoding="utf-8")
    payload = json.loads(raw_text)
    call_qdrant(
        f"/collections/{COLLECTION_NAME}/points?wait=true",
        method="PUT",
        body=payload,
    )


def verify_payload(limit: int = 3) -> None:
    result = call_qdrant(
        f"/collections/{COLLECTION_NAME}/points/scroll",
        method="POST",
        body={"limit": limit, "with_payload": True, "with_vector": True},
    )
    points = result.get("result", {}).get("points", [])
    for point in points:
        record = {
            "id": point.get("id"),
            "payload": point.get("payload", {}),
            "vector": point.get("vector", {}),
        }
        write_log(json.dumps(record, ensure_ascii=False, indent=2))
        write_log("---")


if __name__ == "__main__":
    LOG_PATH.write_text("", encoding="utf-8")
    recreate_collection()
    upsert_points("points_batch_01.json")
    upsert_points("points_batch_02.json")
    verify_payload()
    write_log("Upload completed successfully.")
