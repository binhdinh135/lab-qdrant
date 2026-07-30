import json
from pathlib import Path
from typing import Any

from fastembed import SparseTextEmbedding, TextEmbedding

BASE_DIR = Path(__file__).resolve().parent


def to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "numpy"):
        return value.numpy().tolist()
    return list(value)


def build_sparse_payload(sparse_embedding: Any) -> dict[str, list[Any]]:
    if isinstance(sparse_embedding, dict):
        return {
            "indices": to_list(sparse_embedding.get("indices", [])),
            "values": to_list(sparse_embedding.get("values", [])),
        }

    if hasattr(sparse_embedding, "indices") and hasattr(sparse_embedding, "values"):
        return {
            "indices": to_list(sparse_embedding.indices),
            "values": to_list(sparse_embedding.values),
        }

    return {"indices": [], "values": []}


def build_point(document: dict[str, Any], dense_vector: Any, sparse_vector: Any) -> dict[str, Any]:
    payload = {
        "document_id": document["document_id"],
        "title": document["title"],
        "domain": document["domain"],
        "department": document["department"],
        "doc_type": document["doc_type"],
        "doc_status": document["doc_status"],
        "text": document["text"],
    }

    return {
        "id": document["id"],
        "vector": {
            "dense": to_list(dense_vector),
            "keywords": build_sparse_payload(sparse_vector),
        },
        "payload": payload,
    }


def generate_batch(input_path: Path, output_path: Path) -> None:
    documents = json.loads(input_path.read_text(encoding="utf-8"))
    texts = [f"{doc['title']}. {doc['text']}" for doc in documents]

    dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    dense_embeddings = list(dense_model.embed(texts))
    sparse_embeddings = list(sparse_model.embed(texts))

    points = [
        build_point(document, dense_embeddings[index], sparse_embeddings[index])
        for index, document in enumerate(documents)
    ]

    output_path.write_text(json.dumps({"points": points}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    for batch_number in [1, 2]:
        input_path = BASE_DIR / f"documents_batch_{batch_number:02d}.json"
        output_path = BASE_DIR / f"points_batch_{batch_number:02d}.json"
        generate_batch(input_path, output_path)
        print(f"Generated {output_path.name} from {input_path.name}")
