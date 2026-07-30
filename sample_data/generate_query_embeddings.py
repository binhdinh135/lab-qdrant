import json
from pathlib import Path
from fastembed import TextEmbedding, SparseTextEmbedding

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "queries" / "query_embeddings.json"


def build_query_embeddings(query: str):
    dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    dense_vectors = list(dense_model.embed([query]))
    sparse_vectors = list(sparse_model.embed([query]))

    dense_vector = dense_vectors[0]
    sparse_vector = sparse_vectors[0]

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
        "query": {
            "fusion": "rrf"
        },
        "limit": 5,
        "with_payload": True,
    }


def main():
    query = input("Nhập câu hỏi tiếng Việt: ").strip()
    if not query:
        print("Câu hỏi không được để trống.")
        return

    result = build_query_embeddings(query)
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nĐã lưu vào: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
