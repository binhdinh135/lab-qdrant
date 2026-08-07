"""FastAPI application entry point."""

from fastapi import FastAPI

from repositories.database import postgres_enabled, oracle_enabled
from repositories.postgres_repo import postgres_db_init
from repositories.oracle_repo import oracle_db_init
from routers import admin_router, auth_router, debug_router
from services.user_service import bootstrap_admin

app = FastAPI(title="Admin RBAC Demo Backend", version="1.0.0")

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(debug_router.router)


@app.on_event("startup")
def startup() -> None:
    if postgres_enabled():
        postgres_db_init()
    elif oracle_enabled():
        oracle_db_init()
    bootstrap_admin()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
