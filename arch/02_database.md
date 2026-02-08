# Database

## Overview

Basidian stores all data in a single SQLite database accessed asynchronously through aiosqlite. The database holds two tables: `notes` for timestamped entries and `fs_nodes` for a hierarchical virtual filesystem.

## How It Works

```
FastAPI lifespan
  │
  ├─ startup: open aiosqlite connection → run migrations → store on app.state
  │
  ├─ request: get_db(request) → returns app.state.db connection
  │
  └─ shutdown: close connection
```

IDs are 16-character hex strings generated with `secrets.token_hex(8)`, matching the PocketBase ID format from the project's early days.

## Schema

### notes

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | 16-char hex |
| title | TEXT | Default empty |
| content | TEXT | Default empty |
| date | TEXT | YYYY-MM-DD |
| created | TEXT | ISO timestamp |
| updated | TEXT | ISO timestamp |

Index: `idx_notes_date` on `date`.

### fs_nodes

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | 16-char hex |
| type | TEXT | `file` or `folder` |
| name | TEXT | Display name |
| path | TEXT | Full path (unique) |
| parent_path | TEXT | Parent folder path |
| content | TEXT | File content (empty for folders) |
| is_daily | INTEGER | Daily note flag (unused) |
| sort_order | INTEGER | Custom ordering |
| created | TEXT | ISO timestamp |
| updated | TEXT | ISO timestamp |

Indexes: unique on `path`, on `parent_path`, on `type`.

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/server/db.py` | Connection lifecycle, `get_db()` dependency |
| `backend/src/server/migrations.py` | Table creation and index definitions |
| `backend/src/server/handlers/notes.py` | Notes CRUD queries |
| `backend/src/server/handlers/filesystem.py` | Filesystem CRUD queries, cascade delete/move |

## Design Decisions

- **No ORM.** Raw SQL with aiosqlite keeps the dependency footprint small and queries transparent.
- **Path-based hierarchy.** Folders and files use stored `path` and `parent_path` columns rather than adjacency-list IDs. Moving a folder cascades path updates to all children.
- **Search uses LIKE.** Full-text search is case-insensitive `LIKE '%query%'` on title/content. No FTS5 extension yet.

<!-- manual -->
<!-- /manual -->
