"""Embedding service — BGE-M3 dense + sparse (BM25-like) vectors."""

from typing import Any
from FlagEmbedding import BGEM3FlagModel

_model: BGEM3FlagModel | None = None


def get_model() -> BGEM3FlagModel:
    """Lazy-load BGE-M3 model (first call downloads ~2GB)."""
    global _model
    if _model is None:
        _model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
    return _model


def embed_texts(
    texts: list[str],
    return_sparse: bool = True,
) -> dict[str, Any]:
    """
    Embed texts using BGE-M3.

    Returns:
        {
            "dense": [[float, ...], ...],     # 1024-dim dense vectors
            "sparse": [{index: weight}, ...], # sparse (BM25-like) vectors
        }
    """
    model = get_model()
    output = model.encode(
        texts,
        return_dense=True,
        return_sparse=return_sparse,
        return_colbert_vecs=False,
    )

    result: dict[str, Any] = {
        "dense": output["dense_vecs"].tolist(),
    }

    if return_sparse and "lexical_weights" in output:
        # Convert sparse weights to Qdrant sparse vector format
        sparse_vectors = []
        for weights in output["lexical_weights"]:
            indices = []
            values = []
            for idx, val in weights.items():
                indices.append(int(idx))
                values.append(float(val))
            sparse_vectors.append({"indices": indices, "values": values})
        result["sparse"] = sparse_vectors

    return result
