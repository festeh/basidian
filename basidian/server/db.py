"""Database connection lifecycle and FastAPI dependency."""

import secrets
from pathlib import Path

import aiosqlite
from fastapi import FastAPI, Request

from .migrations import run_migrations


async def init_db(app: FastAPI, db_path: str) -> None:
    """Open the database connection and run migrations."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    await run_migrations(db)
    app.state.db = db


async def close_db(app: FastAPI) -> None:
    """Close the database connection."""
    db: aiosqlite.Connection = app.state.db
    await db.close()


async def get_db(request: Request) -> aiosqlite.Connection:
    """FastAPI dependency that provides the database connection."""
    return request.app.state.db


def generate_id() -> str:
    """Generate random ID similar to PocketBase format (16-char hex string)."""
    return secrets.token_hex(8)
