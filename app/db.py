"""Connessione al database e helper di esecuzione query.

Usiamo SQLAlchemy solo come connection pool: le query restano SQL scritto a
mano e parametrizzato (niente ORM che nasconde cosa gira sul DB).
"""
from __future__ import annotations

import os
import time
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError


def _build_url() -> str:
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "foodhoreca")
    user = os.getenv("DB_USER", "app")
    pwd = os.getenv("DB_PASS", "apppw")
    return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{name}?charset=utf8mb4"


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(_build_url(), pool_pre_ping=True, pool_recycle=1800)
    return _engine


def wait_for_db(retries: int = 30, delay: float = 2.0) -> None:
    """Attende che il DB sia pronto (utile al primo avvio di docker compose)."""
    last_err: Exception | None = None
    for _ in range(retries):
        try:
            with get_engine().connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError as exc:  # pragma: no cover - dipende dall'ambiente
            last_err = exc
            time.sleep(delay)
    raise RuntimeError(f"Database non raggiungibile: {last_err}")


def query_all(sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), params or {})
        return [dict(r) for r in rows.mappings()]


def query_one(sql: str, params: dict[str, Any] | None = None) -> dict | None:
    with get_engine().connect() as conn:
        row = conn.execute(text(sql), params or {}).mappings().first()
        return dict(row) if row else None


def execute(sql: str, params: dict[str, Any] | None = None) -> int:
    """Esegue una scrittura in transazione e ritorna lastrowid (se presente)."""
    with get_engine().begin() as conn:
        result = conn.execute(text(sql), params or {})
        return int(result.lastrowid or 0)
