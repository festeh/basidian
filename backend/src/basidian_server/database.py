import secrets
from typing import Optional

import aiosqlite

db: Optional[aiosqlite.Connection] = None


async def init(db_path: str) -> None:
    """Initialize database connection and run migrations."""
    global db
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    await run_migrations()


async def close() -> None:
    """Close database connection."""
    global db
    if db:
        await db.close()
        db = None


async def run_migrations() -> None:
    """Create tables and indexes if they don't exist."""
    assert db is not None

    # Notes table (exact schema from Go)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
            title TEXT DEFAULT '' NOT NULL,
            content TEXT DEFAULT '' NOT NULL,
            date TEXT DEFAULT '' NOT NULL,
            created TEXT DEFAULT '' NOT NULL,
            updated TEXT DEFAULT '' NOT NULL
        )
    """)

    # fs_nodes table (exact schema from Go)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS fs_nodes (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
            type TEXT DEFAULT '' NOT NULL,
            name TEXT DEFAULT '' NOT NULL,
            path TEXT DEFAULT '' NOT NULL,
            parent_path TEXT DEFAULT '' NOT NULL,
            content TEXT DEFAULT '' NOT NULL,
            is_daily BOOLEAN DEFAULT FALSE NOT NULL,
            sort_order NUMERIC DEFAULT 0 NOT NULL,
            created TEXT DEFAULT '' NOT NULL,
            updated TEXT DEFAULT '' NOT NULL
        )
    """)

    # Indexes (same as Go)
    await db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_fs_nodes_path ON fs_nodes (path)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_fs_nodes_parent_path ON fs_nodes (parent_path)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_fs_nodes_type ON fs_nodes (type)"
    )
    await db.execute("CREATE INDEX IF NOT EXISTS idx_notes_date ON notes (date)")
    await db.commit()


def generate_id() -> str:
    """Generate random ID similar to PocketBase format (16-char hex string)."""
    return secrets.token_hex(8)
