"""Application configuration — loaded from environment variables."""

import importlib
import os
from pathlib import Path

from dotenv import load_dotenv

try:
    psycopg = importlib.import_module("psycopg")
except Exception:  # pragma: no cover
    psycopg = None

try:
    oracledb = importlib.import_module("oracledb")
except Exception:  # pragma: no cover
    oracledb = None

if oracledb is not None:
    oracledb.defaults.fetch_lobs = False


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "users.json"
ADMIN_UI_FILE = BASE_DIR / "admin_ui.html"

load_dotenv(BASE_DIR / ".env")

APP_AUTH_TTL_MINUTES = int(os.getenv("APP_AUTH_TTL_MINUTES", "480"))
ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "admin-jwt-secret-demo").strip()
ADMIN_JWT_ISSUER = os.getenv("ADMIN_JWT_ISSUER", "backend").strip() or "backend"
ADMIN_JWT_AUDIENCE = os.getenv("ADMIN_JWT_AUDIENCE", "admin-portal").strip() or "admin-portal"

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6390").rstrip("/")
QDRANT_ADMIN_API_KEY = os.getenv("QDRANT_ADMIN_API_KEY", "admin-secret-key-demo")
QDRANT_READONLY_API_KEY = os.getenv("QDRANT_READONLY_API_KEY", "readonly-key-demo").strip()
QDRANT_JWT_SECRET = os.getenv("QDRANT_JWT_SECRET", "").strip()
QDRANT_TOKEN_TTL_MINUTES = int(os.getenv("QDRANT_TOKEN_TTL_MINUTES", "120"))

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
ORACLE_USER = os.getenv("ORACLE_USER", "").strip()
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_DSN = os.getenv("ORACLE_DSN", "").strip()

ADMIN_BOOTSTRAP_USERNAME = os.getenv("ADMIN_BOOTSTRAP_USERNAME", "admin")
ADMIN_BOOTSTRAP_PASSWORD = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "Admin@123")
