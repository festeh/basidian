"""Database schema migrations."""

import aiosqlite


async def run_migrations(db: aiosqlite.Connection) -> None:
    """Create tables and indexes if they don't exist."""

    # Notes table
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

    # fs_nodes table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS fs_nodes (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
            type TEXT DEFAULT '' NOT NULL,
            name TEXT DEFAULT '' NOT NULL,
            path TEXT DEFAULT '' NOT NULL,
            parent_path TEXT DEFAULT '' NOT NULL,
            content TEXT DEFAULT '' NOT NULL,
            sort_order NUMERIC DEFAULT 0 NOT NULL,
            created TEXT DEFAULT '' NOT NULL,
            updated TEXT DEFAULT '' NOT NULL
        )
    """)

    # Indexes
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

    # Drop unused is_daily column from existing databases
    async with db.execute("PRAGMA table_info(fs_nodes)") as cursor:
        columns = [row[1] for row in await cursor.fetchall()]
    if "is_daily" in columns:
        await db.execute("ALTER TABLE fs_nodes DROP COLUMN is_daily")

    await db.commit()
