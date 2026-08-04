r"""
Script ingest tài liệu Markdown vào Qdrant.

Luồng:
  1. Đọc tất cả .md files trong data/documents/
  2. Chunk theo Markdown headers
  3. Sinh embeddings (dense + sparse)
  4. Upsert vào Qdrant collection "internal_docs"

Chạy:
  cd /d D:\Qdrant\demo_chatbot
  D:\Qdrant\.venv\Scripts\python.exe scripts\ingest_documents.py
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, SparseVectorParams, Distance,
    PointStruct, SparseVector, PayloadSchemaType,
)
from fastembed import TextEmbedding, SparseTextEmbedding

from config import (
    QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME,
    DENSE_VECTOR_SIZE, DENSE_MODEL_NAME, SPARSE_MODEL_NAME,
)


DOCS_DIR = Path(__file__).parent.parent / "data" / "documents"


def chunk_markdown(content: str, filename: str) -> list[dict]:
    """
    Chunk Markdown theo headers (##).
    Mỗi chunk = 1 section.
    """
    chunks = []
    current_section = "Intro"
    current_text = []

    for line in content.split("\n"):
        if line.startswith("## "):
            # Save previous chunk
            if current_text:
                text = "\n".join(current_text).strip()
                if text:
                    chunks.append({
                        "document": filename,
                        "section": current_section,
                        "text": text,
                    })
            current_section = line.lstrip("#").strip()
            current_text = []
        elif line.startswith("# "):
            current_section = line.lstrip("#").strip()
        else:
            current_text.append(line)

    # Last chunk
    if current_text:
        text = "\n".join(current_text).strip()
        if text:
            chunks.append({
                "document": filename,
                "section": current_section,
                "text": text,
            })

    return chunks


def main():
    print("=" * 60)
    print("INGEST TÀI LIỆU VÀO QDRANT")
    print("=" * 60)

    # 1. Load models
    print("\n[1/5] Loading embedding models...")
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)
    print("  ✅ Dense: bge-small-en-v1.5 (384 dims)")
    print("  ✅ Sparse: BM25")

    # 2. Connect Qdrant
    print("\n[2/5] Connecting Qdrant...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # 3. Recreate collection
    print(f"\n[3/5] Recreate collection '{COLLECTION_NAME}'...")
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": VectorParams(size=DENSE_VECTOR_SIZE, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "keywords": SparseVectorParams(),
        },
    )
    # Indexes
    for field in ["document", "section"]:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )
    print("  ✅ Collection created + indexes")

    # 4. Read & chunk documents
    print(f"\n[4/5] Reading documents from {DOCS_DIR}...")
    if not DOCS_DIR.exists():
        print(f"  ⚠️  Folder {DOCS_DIR} không tồn tại!")
        print(f"  Tạo folder và thêm file .md vào đó.")
        return

    all_chunks = []
    for md_file in sorted(DOCS_DIR.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        chunks = chunk_markdown(content, md_file.name)
        all_chunks.extend(chunks)
        print(f"  📄 {md_file.name}: {len(chunks)} chunks")

    if not all_chunks:
        print("  ❌ Không tìm thấy tài liệu .md nào!")
        return

    print(f"  Tổng: {len(all_chunks)} chunks")

    # 5. Embed & upsert
    print(f"\n[5/5] Embedding + Upsert...")
    texts = [f"{c['document']} - {c['section']}: {c['text']}" for c in all_chunks]

    dense_vectors = list(dense_model.embed(texts))
    sparse_vectors = list(sparse_model.embed(texts))

    points = []
    for i, chunk in enumerate(all_chunks):
        points.append(PointStruct(
            id=i + 1,
            vector={
                "dense": dense_vectors[i].tolist(),
                "keywords": SparseVector(
                    indices=sparse_vectors[i].indices.tolist(),
                    values=sparse_vectors[i].values.tolist(),
                ),
            },
            payload=chunk,
        ))

    # Batch upsert (max 100 per batch)
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch, wait=True)

    print(f"  ✅ Upserted {len(points)} points")

    # Verify
    info = client.get_collection(COLLECTION_NAME)
    print(f"\n{'=' * 60}")
    print(f"✅ HOÀN TẤT! Collection '{COLLECTION_NAME}' có {info.points_count} points.")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    main()
