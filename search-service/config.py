"""Search service configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6390").rstrip("/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "admin-secret-key-demo")
SEARCH_SERVICE_PORT = int(os.getenv("SEARCH_SERVICE_PORT", "8001"))
