"""
Config cho Smart Search Assistant POC.
"""

# === Qdrant ===
QDRANT_URL = "http://localhost:6333"
QDRANT_API_KEY = None
COLLECTION_NAME = "internal_docs"

# === Vector Config ===
DENSE_VECTOR_SIZE = 1024  # BGE-M3 output 1024 dims
DENSE_MODEL_NAME = "BAAI/bge-m3"
SPARSE_MODEL_NAME = "Qdrant/bm25"

# BGE-M3 dùng LateInteractionTextEmbedding hoặc TextEmbedding tùy fastembed version
# Nếu fastembed cũ không hỗ trợ, dùng sentence-transformers trực tiếp
USE_SENTENCE_TRANSFORMERS = True  # True = dùng sentence-transformers, False = dùng fastembed

# === LLM Config ===
# Options: "ollama" (local miễn phí) | "openai" (cần API key) | "fake" (demo flow)
LLM_PROVIDER = "ollama"
OPENAI_API_KEY = None
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_BASE_URL = "http://localhost:11434"

# === App Config ===
APP_HOST = "0.0.0.0"
APP_PORT = 8000
