"""
Script sinh query embeddings cho auth-demo.

Tương tự generate_query_embeddings.py của demo chính,
nhưng output vào folder auth-demo/queries/

Cách chạy:
  cd /d D:\Qdrant\demo-local\auth-demo
  D:\Qdrant\.venv\Scripts\python.exe scripts\generate_query.py
"""

import json
from pathlib import Path
from fastembed import TextEmbedding, SparseTextEmbedding

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "queries"


def build_query_body(query: str) -> dict:
    """Sinh dense + sparse embedding cho 1 câu query."""
    dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    dense_vectors = list(dense_model.embed([query]))
    sparse_vectors = list(sparse_model.embed([query]))

    dense_vector = dense_vectors[0]
    sparse_vector = sparse_vectors[0]

    # Hybrid search body (prefetch dense + sparse, fusion RRF)
    return {
        "prefetch": [
            {
                "query": [float(x) for x in dense_vector],
                "using": "dense",
                "limit": 20,
            },
            {
                "query": {
                    "indices": [int(x) for x in sparse_vector.indices.tolist()],
                    "values": [float(x) for x in sparse_vector.values.tolist()],
                },
                "using": "keywords",
                "limit": 20,
            },
        ],
        "query": {"fusion": "rrf"},
        "limit": 5,
        "with_payload": True,
    }


def build_dense_only_query(query: str) -> dict:
    """Sinh chỉ dense embedding (search đơn giản)."""
    dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    dense_vectors = list(dense_model.embed([query]))
    dense_vector = dense_vectors[0]

    return {
        "query": [float(x) for x in dense_vector],
        "using": "dense",
        "limit": 5,
        "with_payload": True,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("SINH QUERY EMBEDDINGS CHO AUTH DEMO")
    print("=" * 50)

    query = input("\nNhập câu hỏi tiếng Việt: ").strip()
    if not query:
        print("Câu hỏi không được để trống.")
        return

    # 1. Hybrid search body
    print("\n[1/2] Sinh Hybrid Search body (dense + sparse + RRF)...")
    hybrid_body = build_query_body(query)
    hybrid_path = OUTPUT_DIR / "query_hybrid.json"
    hybrid_path.write_text(json.dumps(hybrid_body, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ Saved: {hybrid_path.name}")

    # 2. Dense-only search body
    print("[2/2] Sinh Dense Search body...")
    dense_body = build_dense_only_query(query)
    dense_path = OUTPUT_DIR / "query_dense.json"
    dense_path.write_text(json.dumps(dense_body, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ Saved: {dense_path.name}")

    print(f"\n{'=' * 50}")
    print(f"✅ Đã lưu 2 file query vào: {OUTPUT_DIR}")
    print(f"   - query_hybrid.json (hybrid search)")
    print(f"   - query_dense.json  (dense only)")
    print(f"\nCâu hỏi: '{query}'")
    print("=" * 50)


if __name__ == "__main__":
    main()
