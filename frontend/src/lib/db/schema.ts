/**
 * Local SQLite schema for offline caching.
 * Mirrors the server's fs_nodes + fs_content tables,
 * with added sync tracking columns (deleted_at, is_dirty).
 * No fs_versions — version history is server-only.
 */

export const SCHEMA_VERSION = 1;

export const CREATE_TABLES: string[] = [
	`CREATE TABLE IF NOT EXISTS sync_meta (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )`,

	`CREATE TABLE IF NOT EXISTS fs_nodes (
        id          TEXT PRIMARY KEY,
        parent_id   TEXT REFERENCES fs_nodes(id) ON DELETE CASCADE,
        type        TEXT NOT NULL CHECK (type IN ('file', 'folder')),
        name        TEXT NOT NULL,
        path        TEXT NOT NULL,
        sort_order  INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT NOT NULL,
        updated_at  TEXT NOT NULL,
        deleted_at  TEXT,
        is_dirty    INTEGER NOT NULL DEFAULT 0
    )`,

	`CREATE TABLE IF NOT EXISTS fs_content (
        node_id     TEXT PRIMARY KEY REFERENCES fs_nodes(id) ON DELETE CASCADE,
        body        TEXT NOT NULL DEFAULT '',
        updated_at  TEXT NOT NULL,
        is_dirty    INTEGER NOT NULL DEFAULT 0
    )`,

	'CREATE UNIQUE INDEX IF NOT EXISTS idx_fs_nodes_path ON fs_nodes (path)',
	'CREATE INDEX IF NOT EXISTS idx_fs_nodes_parent_id ON fs_nodes (parent_id)',
	'CREATE INDEX IF NOT EXISTS idx_fs_nodes_type ON fs_nodes (type)',
	`CREATE UNIQUE INDEX IF NOT EXISTS idx_fs_nodes_unique_name
        ON fs_nodes (parent_id, name) WHERE parent_id IS NOT NULL`,
	`CREATE UNIQUE INDEX IF NOT EXISTS idx_fs_nodes_unique_root_name
        ON fs_nodes (name) WHERE parent_id IS NULL`,
	'CREATE INDEX IF NOT EXISTS idx_fs_nodes_dirty ON fs_nodes (is_dirty) WHERE is_dirty = 1',
	'CREATE INDEX IF NOT EXISTS idx_fs_content_dirty ON fs_content (is_dirty) WHERE is_dirty = 1'
];
