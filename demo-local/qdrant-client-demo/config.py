"""
Config chung cho project qdrant-client-demo.
"""

# Qdrant connection
QDRANT_URL = "http://localhost:6333"
QDRANT_API_KEY = None  # None nếu không dùng auth, hoặc "admin-secret-key-2024"

# Collection name dùng xuyên suốt project
COLLECTION_NAME = "client_demo"

# Vector config
DENSE_VECTOR_SIZE = 384  # bge-small-en-v1.5
DENSE_MODEL_NAME = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL_NAME = "Qdrant/bm25"
