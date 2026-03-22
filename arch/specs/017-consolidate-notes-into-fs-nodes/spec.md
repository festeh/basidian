# Clean Data Model + Smart Backend

## Problem

The data model has three issues:

1. The `notes` table is dead code — the frontend never uses it.
2. `fs_nodes` mixes tree structure with content blobs. Tree queries (sidebar, recent files) physically read content from disk even when only metadata is needed — SQLite stores rows as single blobs on B-tree pages, so there's no way to skip the content column at the storage level.
3. No structured metadata — tags, links, dates are buried in markdown content, queryable only by parsing at runtime. `parent_path` as a string makes moves O(n) with string replacement.

## Target Data Model

Three SQLite tables. Metadata lives in-memory on the backend (the Obsidian approach).

**Prerequisite**: Every connection must run `PRAGMA foreign_keys = ON` — SQLite disables FKs by default, making all REFERENCES and CASCADE clauses decorative without it.

```sql
-- Tree structure only. No content. Rows are small, tree queries are fast.
CREATE TABLE fs_nodes (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
    parent_id   TEXT REFERENCES fs_nodes(id) ON DELETE CASCADE,
    type        TEXT NOT NULL CHECK (type IN ('file', 'folder')),
    name        TEXT NOT NULL,
    path        TEXT NOT NULL,                  -- materialized, updated on move
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE UNIQUE INDEX idx_fs_nodes_path ON fs_nodes (path);
CREATE INDEX idx_fs_nodes_parent_id ON fs_nodes (parent_id);
CREATE INDEX idx_fs_nodes_type ON fs_nodes (type);
-- Root-level uniqueness: UNIQUE(parent_id, name) doesn't work for NULL parent_id
-- (SQL treats NULL != NULL). Use two indexes instead:
CREATE UNIQUE INDEX idx_fs_nodes_unique_name
    ON fs_nodes (parent_id, name) WHERE parent_id IS NOT NULL;
CREATE UNIQUE INDEX idx_fs_nodes_unique_root_name
    ON fs_nodes (name) WHERE parent_id IS NULL;

-- Current content. One row per file node. PK lookup to open a file.
CREATE TABLE fs_content (
    node_id     TEXT PRIMARY KEY REFERENCES fs_nodes(id) ON DELETE CASCADE,
    body        TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL
);

-- Version history. Explicit snapshots, created on inactivity gap.
CREATE TABLE fs_versions (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
    node_id     TEXT NOT NULL REFERENCES fs_nodes(id) ON DELETE CASCADE,
    body        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE INDEX idx_fs_versions_node_id ON fs_versions (node_id);
CREATE INDEX idx_fs_versions_created_at ON fs_versions (created_at);
```

This is the standard production pattern (current state + history as separate tables) used by Notion, Joplin, Django audit plugins, Rails paper_trail, etc.

### Changes from current schema

- `notes` table: **dropped** (dead code)
- `fs_nodes.content`: **moved** to `fs_content.body` (tree queries no longer touch content)
- `fs_nodes.parent_path`: **replaced** by `parent_id` FK with ON DELETE CASCADE (referential integrity, O(1) moves, recursive folder deletion handled by SQLite)
- `fs_nodes.path`: **kept** as materialized column for O(1) lookups by path
- `fs_nodes.type`: **adds** CHECK constraint
- `fs_nodes`: **adds** unique name constraints via partial indexes (two indexes to handle NULL parent_id for root nodes — SQL treats NULL != NULL so a single UNIQUE constraint doesn't work)
- `fs_nodes` column renames: `created` → `created_at`, `updated` → `updated_at` (consistency)
- `file_versions`: **renamed** to `fs_versions`, `content` → `body` (consistency with `fs_content`)
- `db.py`: **must** run `PRAGMA foreign_keys = ON` on connection open (SQLite disables FKs by default)

### What stays the same

- Explicit snapshots in `fs_versions` (not append-only — autosave would flood it)
- Auto-snapshot on inactivity gap before content update
- Version retention policy (7d all, 30d daily, older weekly)
- Frontend snapshot calls on file switch and app close

## In-Memory Metadata Index

On startup, parse all file content and build indexes. Update incrementally on each save/delete. This is how Obsidian does it — fast reads from memory, trivially rebuildable, no extra tables to sync.

```python
class MetadataIndex:
    # tag → set of node IDs
    tags: dict[str, set[str]]

    # source node ID → set of target paths (raw [[wikilink]] text)
    links: dict[str, set[str]]

    # target path → set of source node IDs (reverse of links)
    backlinks: dict[str, set[str]]

    # ISO date string → node ID (for daily notes calendar)
    daily_dates: dict[str, str]

    # node ID → parsed YAML frontmatter dict
    frontmatter: dict[str, dict]
```

### Parsing rules

- **Tags**: `#tag-name` in content (not inside code blocks). Normalized to lowercase.
- **Links**: `[[path]]` and `[[path|display]]` wikilinks. Store raw path, resolve to node ID when possible.
- **Daily dates**: Parse from filename if the file is under the daily notes folder (configurable, default `/daily`). Pattern: `DD-MMM-YYYY.md`.
- **Frontmatter**: YAML between `---` fences at the start of the file.

### New API endpoints

| Method | Endpoint | Returns |
|--------|----------|---------|
| GET | `/api/fs/tags` | `[{tag, count}]` — all tags with usage counts |
| GET | `/api/fs/tags/{tag}` | `[FsNode]` — nodes with this tag (without content) |
| GET | `/api/fs/backlinks` | `[{source_id, source_path, source_name}]` — nodes linking to `?path=...` |
| GET | `/api/fs/links/{node_id}` | `[{target_path, target_id?, target_name?}]` — outgoing links |
| GET | `/api/fs/daily-dates` | `{date: node_id}` — map for calendar view |

### Lifecycle

- **Startup**: Query all `fs_content` rows, parse body, build full index. For a few thousand small markdown files this takes milliseconds.
- **On save** (`PUT /api/fs/node/{id}` with content change): Re-parse the saved content, update its entries in all indexes.
- **On delete**: Remove node from all indexes.
- **On move/rename**: Update path-based index keys (backlinks target paths, daily dates).

## What Changes

### Phase 1: Remove dead code

- Drop `notes` table from migrations
- Delete `basidian/server/handlers/notes.py`
- Delete `Note`, `NoteRequest` from `basidian/models.py`
- Remove `notes_router` from `basidian/server/handlers/__init__.py` and `main.py`
- Drop the `idx_notes_date` index creation

### Phase 2: Schema migration

Migrate `fs_nodes` to the three-table model:

- Create `fs_nodes` with new schema (no content, `parent_id` instead of `parent_path`)
- Create `fs_content` (extract content from old `fs_nodes`)
- Rename `file_versions` → `fs_versions`, `content` → `body`
- Populate `parent_id` from existing `parent_path` (find parent node by path)
- Rename `created` → `created_at`, `updated` → `updated_at`
- Add CHECK constraint on `type`, UNIQUE(parent_id, name)

SQLite doesn't support most ALTER TABLE operations, so this requires the standard recreate-table migration:
1. Create new tables with target schema
2. INSERT into new `fs_nodes` SELECT from old (with `parent_id` computed via subquery, without content)
3. INSERT into `fs_content` SELECT `id, content, updated` from old `fs_nodes` WHERE type = 'file'
4. INSERT into `fs_versions` SELECT from old `file_versions` (rename column)
5. Drop old tables
6. Rename new tables
7. Recreate indexes

### Phase 3: Update backend handlers

- `db.py`: Run `PRAGMA foreign_keys = ON` after opening connection (before migrations). Without this, all FKs and CASCADEs are silently ignored.
- `filesystem.py`:
  - `get_tree`: SELECT from `fs_nodes` only (no content) — rows are small, fast scan
  - `get_node` / `get_node_by_id`: LEFT JOIN `fs_nodes` + `fs_content` (LEFT JOIN because folders have no `fs_content` row — INNER JOIN would 404 on folders)
  - `create_node`: INSERT into `fs_nodes` + INSERT into `fs_content` (for files only, not folders)
  - `update_node`: UPDATE `fs_content.body` + `fs_content.updated_at` for content changes, and also UPDATE `fs_nodes.updated_at` (so `get_recent_files` ordering reflects content edits, not just metadata changes). Auto-snapshot logic checks `fs_content.updated_at` for inactivity gap.
  - `move_node`: UPDATE `parent_id` (O(1) for the node), then recompute `path` for descendants using `WITH RECURSIVE` CTE
  - `delete_node`: With `ON DELETE CASCADE` on `parent_id`, deleting a folder recursively deletes all descendants automatically (SQLite handles recursive cascade on self-referential FKs). `fs_content` and `fs_versions` rows are also cascade-deleted.
  - `get_recent_files`: SELECT from `fs_nodes` only (no content needed for list). Uses `fs_nodes.updated_at` which is kept in sync with content edits.
  - `search_files`: JOIN `fs_nodes` + `fs_content` (need to search body)
- `history.py`: Update table name `file_versions` → `fs_versions`, `content` → `body`. Snapshot reads from `fs_content.body` instead of `fs_nodes.content`.
- Update Pydantic models: `FsNode` response shape adds `parent_id`, `content` becomes optional (absent in tree/list responses, present when a single file is fetched)
- The API still returns `parent_path` in responses (computed from parent's path via join or index lookup)

### Phase 4: Update frontend

- `types/index.ts`: Add `parent_id` to `FsNode` interface, `content` already optional
- `stores/filesystem.ts`: `buildTree` uses `parent_id` for hierarchy (map by id instead of path)
- `api/client.ts`: `createNode` sends `parent_path` (backend resolves to `parent_id`), or switch to `parent_id` if available
- No other frontend changes needed — daily notes, editor, file tree all work the same
- Tree responses are faster (smaller payloads, no content)

### Phase 5: In-memory metadata index

- New module: `basidian/server/metadata.py` — `MetadataIndex` class with parsing + query methods
- Initialize on startup in `main.py` lifespan (after DB init, query all `fs_content`, parse)
- Hook into `update_node` and `delete_node` handlers to update index on changes
- New handler: `basidian/server/handlers/metadata.py` — routes for tags, backlinks, links, daily dates
- Register `metadata_router` in `main.py`

## API Changes

### Modified responses

`FsNode` response adds `parent_id`, keeps `parent_path` (computed). `content` is present only when fetching a single file:

```json
{
  "id": "abc123",
  "parent_id": "def456",
  "parent_path": "/daily",
  "type": "file",
  "name": "22-Mar-2026.md",
  "path": "/daily/22-Mar-2026.md",
  "content": "...",
  "sort_order": 0,
  "created_at": "2026-03-22T10:00:00",
  "updated_at": "2026-03-22T10:00:00"
}
```

Root-level nodes have `parent_id: null` and `parent_path: "/"`.

Tree/list endpoints (`get_tree`, `get_recent_files`, `tags/{tag}`) omit `content`.

### Removed endpoints

All `/api/notes/*` and `/api/search` (replaced by `/api/fs/search` which already exists).

### New endpoints

Tags, backlinks, links, daily-dates (see table above).

## Migration Strategy

- On startup, detect old schema (presence of `parent_path` column, absence of `parent_id`) and run migration automatically
- Migration is idempotent — safe to run multiple times
- No data loss: all `fs_nodes` data is preserved, content moved to `fs_content`, `parent_id` computed from `parent_path`
- `notes` table data is discarded (never user-facing)

## Requirements

- [ ] All notes-related backend code is removed
- [ ] Content separated into `fs_content` table (tree queries don't touch content)
- [ ] `fs_nodes` schema uses `parent_id` FK with materialized `path`
- [ ] `file_versions` renamed to `fs_versions`
- [ ] Tree operations use `parent_id` (move is O(1) for the node itself)
- [ ] In-memory metadata index parses tags, links, frontmatter, daily dates
- [ ] New API endpoints serve metadata from memory
- [ ] Index updates incrementally on save/delete/move
- [ ] Existing frontend functionality unbroken
- [ ] Migration from old schema is automatic on startup
- [ ] Tests pass

## Out of Scope

- Sync system (spec 016 — but this model is sync-ready: three tables, timestamps for conflict resolution, metadata derived not stored)
- Full-text search index (current LIKE queries on `fs_content.body` are fine for now)
- Frontend UI for tags, backlinks, graph view (just the API layer)
- Persisting metadata to SQLite (rebuild from content is fast and avoids sync complexity)
