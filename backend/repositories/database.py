"""Database connection helpers and backend detection."""

from config import (
    DATABASE_URL,
    ORACLE_USER,
    ORACLE_PASSWORD,
    ORACLE_DSN,
    psycopg,
    oracledb,
)


def db_backend() -> str:
    if ORACLE_USER and ORACLE_DSN:
        return "oracle"
    if DATABASE_URL:
        return "postgres"
    raise RuntimeError(
        "No database backend configured. Set ORACLE_USER/ORACLE_DSN or DATABASE_URL."
    )


def postgres_enabled() -> bool:
    return db_backend() == "postgres"


def oracle_enabled() -> bool:
    return db_backend() == "oracle"


def db_connect():
    if psycopg is None:
        raise RuntimeError("psycopg is not installed")
    return psycopg.connect(DATABASE_URL)


def oracle_connect():
    if oracledb is None:
        raise RuntimeError("oracledb is not installed")
    return oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)
