"""
Config cho Smart Search Assistant POC.
"""

# === Qdrant ===
QDRANT_URL = "http://localhost:6333"
QDRANT_API_KEY = None
COLLECTION_NAME = "internal_docs"

# === Vector Config ===
DENSE_VECTOR_SIZE = 384
DENSE_MODEL_NAME = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL_NAME = "Qdrant/bm25"

# === LLM Config ===
# Chọn 1 trong các option:
#   "fake"   → FakeListChatModel (không cần API key, demo flow)
#   "ollama" → Ollama local (cần cài ollama + model)
#   "openai" → OpenAI API (cần OPENAI_API_KEY)
LLM_PROVIDER = "fake"
OPENAI_API_KEY = None
OLLAMA_MODEL = "llama3"
OLLAMA_BASE_URL = "http://localhost:11434"

# === App Config ===
APP_HOST = "0.0.0.0"
APP_PORT = 8000
