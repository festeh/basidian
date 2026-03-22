"""Database schema migrations."""

import aiosqlite
from loguru import logger


async def _get_columns(db: aiosqlite.Connection, table: str) -> list[str]:
    """Get column names for a table."""
    async with db.execute(f"PRAGMA table_info({table})") as cursor:
        return [row[1] for row in await cursor.fetchall()]


async def _table_exists(db: aiosqlite.Connection, table: str) -> bool:
    """Check if a table exists."""
    async with db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ) as cursor:
        return await cursor.fetchone() is not None


async def _needs_migration(db: aiosqlite.Connection) -> bool:
    """Detect old schema: fs_nodes has parent_path column."""
    if not await _table_exists(db, "fs_nodes"):
        return False
    columns = await _get_columns(db, "fs_nodes")
    return "parent_path" in columns


async def _migrate_from_old_schema(db: aiosqlite.Connection) -> None:
    """Migrate from old schema (fs_nodes with content/parent_path) to new three-table model."""
    logger.info("Migration: Migrating from old schema to new three-table model")

    # 1. Create new fs_nodes table
    await db.execute("""
        CREATE TABLE fs_nodes_new (
            id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
            parent_id   TEXT REFERENCES fs_nodes_new(id) ON DELETE CASCADE,
            type        TEXT NOT NULL CHECK (type IN ('file', 'folder')),
            name        TEXT NOT NULL,
            path        TEXT NOT NULL,
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)

    # 2. Copy tree data, computing parent_id from parent_path
    await db.execute("""
        INSERT INTO fs_nodes_new (id, parent_id, type, name, path, sort_order, created_at, updated_at)
        SELECT
            old.id,
            parent.id,
            old.type,
            old.name,
            old.path,
            old.sort_order,
            COALESCE(NULLIF(old.created, ''), old.updated, datetime('now')),
            COALESCE(NULLIF(old.updated, ''), old.created, datetime('now'))
        FROM fs_nodes old
        LEFT JOIN fs_nodes parent ON parent.path = old.parent_path
    """)

    # 3. Create fs_content from old fs_nodes (files only)
    await db.execute("""
        CREATE TABLE fs_content (
            node_id     TEXT PRIMARY KEY REFERENCES fs_nodes_new(id) ON DELETE CASCADE,
            body        TEXT NOT NULL DEFAULT '',
            updated_at  TEXT NOT NULL
        )
    """)

    await db.execute("""
        INSERT INTO fs_content (node_id, body, updated_at)
        SELECT id, content, COALESCE(NULLIF(updated, ''), NULLIF(created, ''), datetime('now'))
        FROM fs_nodes old
        WHERE old.type = 'file'
    """)

    # 4. Create fs_versions from old file_versions
    await db.execute("""
        CREATE TABLE fs_versions (
            id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
            node_id     TEXT NOT NULL REFERENCES fs_nodes_new(id) ON DELETE CASCADE,
            body        TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)

    if await _table_exists(db, "file_versions"):
        await db.execute("""
            INSERT INTO fs_versions (id, node_id, body, created_at)
            SELECT id, node_id, content, created_at
            FROM file_versions
        """)
        await db.execute("DROP TABLE file_versions")

    # 5. Drop old tables, rename new
    await db.execute("DROP TABLE fs_nodes")
    await db.execute("ALTER TABLE fs_nodes_new RENAME TO fs_nodes")

    # 6. Drop notes table if it exists (dead code)
    if await _table_exists(db, "notes"):
        await db.execute("DROP TABLE notes")

    # 7. Create indexes
    await _create_indexes(db)

    await db.commit()
    logger.info("Migration: Complete")


async def _create_indexes(db: aiosqlite.Connection) -> None:
    """Create all indexes for the new schema."""
    await db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_fs_nodes_path ON fs_nodes (path)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_fs_nodes_parent_id ON fs_nodes (parent_id)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_fs_nodes_type ON fs_nodes (type)"
    )
    # Two partial indexes for unique name constraint (NULL parent_id needs special handling)
    await db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_fs_nodes_unique_name
        ON fs_nodes (parent_id, name) WHERE parent_id IS NOT NULL
    """)
    await db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_fs_nodes_unique_root_name
        ON fs_nodes (name) WHERE parent_id IS NULL
    """)
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_fs_versions_node_id ON fs_versions (node_id)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_fs_versions_created_at ON fs_versions (created_at)"
    )


async def _create_tables(db: aiosqlite.Connection) -> None:
    """Create tables for a fresh database."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS fs_nodes (
            id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
            parent_id   TEXT REFERENCES fs_nodes(id) ON DELETE CASCADE,
            type        TEXT NOT NULL CHECK (type IN ('file', 'folder')),
            name        TEXT NOT NULL,
            path        TEXT NOT NULL,
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS fs_content (
            node_id     TEXT PRIMARY KEY REFERENCES fs_nodes(id) ON DELETE CASCADE,
            body        TEXT NOT NULL DEFAULT '',
            updated_at  TEXT NOT NULL
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS fs_versions (
            id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
            node_id     TEXT NOT NULL REFERENCES fs_nodes(id) ON DELETE CASCADE,
            body        TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)

    await _create_indexes(db)
    await db.commit()


async def run_migrations(db: aiosqlite.Connection) -> None:
    """Run all migrations. Detects schema version and migrates as needed."""
    # Enable foreign keys (SQLite disables them by default)
    await db.execute("PRAGMA foreign_keys = ON")

    if await _needs_migration(db):
        await _migrate_from_old_schema(db)
    else:
        await _create_tables(db)
