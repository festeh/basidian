# Plan: Decompose Server Into Server Code and CLI Apps

## Tech Stack

- Language: Python 3.12+
- Build system: uv (pyproject.toml)
- CLI framework: Click
- Server framework: FastAPI + uvicorn
- Storage: SQLite (aiosqlite)

## Current State

Everything lives in one flat package `basidian_server`:

```
backend/src/basidian_server/
├── __init__.py
├── main.py              # FastAPI server + Click CLI entry point
├── database.py          # SQLite async wrapper (global state)
├── models.py            # Pydantic models
├── bscli.py             # CLI: direct DB file operations
├── basync.py            # CLI: push/pull sync via HTTP
├── basync_client.py     # HTTP client for basync
├── basync_config.py     # Config loader for basync
└── handlers/
    ├── __init__.py
    ├── notes.py
    └── filesystem.py
```

Problems:
- `bscli` duplicates business logic from handlers (path parsing, INSERT, etc.) without the validation.
- `bscli` accesses the DB directly while `basync` uses HTTP -- inconsistent protocols.
- Three apps and shared code are tangled in one package.
- Database connection is a module-level global variable. Handlers use `db.db` (module.variable). Hard to test, hidden coupling.

## Target Structure

```
backend/src/
├── basidian/
│   ├── __init__.py
│   ├── client.py              # HTTP client for Basidian API (shared by both CLIs)
│   └── models.py              # Pydantic models (shared by server + CLIs)
├── basidian_server/
│   ├── __init__.py
│   ├── main.py                # FastAPI app + Click serve command
│   ├── db.py                  # init_db(), close_db(), get_db dependency
│   ├── migrations.py          # Table creation DDL
│   └── handlers/
│       ├── __init__.py
│       ├── notes.py
│       └── filesystem.py
├── bscli/
│   ├── __init__.py
│   └── main.py                # Click CLI for file operations (via HTTP)
└── basync/
    ├── __init__.py
    ├── main.py                # Click CLI for push/pull sync (via HTTP)
    └── config.py              # Config loader
```

### Package Responsibilities

**`basidian`** (shared library) -- HTTP client and models. Both CLI apps import from here.
- `basidian.client`: `BasidianClient` async HTTP client wrapping the server API.
- `basidian.models`: Pydantic models (`Note`, `NoteRequest`, `FsNode`, `FsNodeRequest`, `MoveRequest`).

**`basidian_server`** -- HTTP server only. Owns the database layer. Contains FastAPI app, handlers, logging, and the `serve` CLI command.
- `basidian_server.db`: Connection lifecycle (`init_db`, `close_db`), `get_db` FastAPI dependency, `generate_id()`.
- `basidian_server.migrations`: `run_migrations()` — DDL for tables and indexes. Separate concern from connection management; grows as schema evolves.

**`bscli`** -- CLI for file operations. Uses `basidian.client` to talk to the server over HTTP. No direct DB access.

**`basync`** -- CLI for push/pull file sync. Uses `basidian.client` to talk to the server over HTTP. No direct DB access.

### Dependency Graph

```
basidian (models + HTTP client)
    ^            ^
    |            |
basidian_server  |  (also has db.py + migrations.py)
    bscli -------+
    basync ------+
```

All CLI tools are thin HTTP clients. The server is the single owner of database access and business logic.

## Approach

### 1. Create the shared `basidian` package

- Move `models.py` to `basidian/models.py`
- Move and expand `basync_client.py` to `basidian/client.py` as the shared HTTP client
  - Replace the duplicate `FsNode` dataclass with `basidian.models.FsNode`
  - Add methods needed by `bscli` (search, get node by path, etc.) if not already present
- The client already has: `get_tree`, `get_node`, `create_node`, `update_node`, `delete_node`
- Add: `search_files`, `get_node_by_id`, `move_node` to match handler endpoints

### 2. Restructure `basidian_server`

- Split `database.py` into two files:
  - `db.py`: Connection lifecycle + FastAPI dependency injection + `generate_id()`
  - `migrations.py`: `run_migrations()` with all DDL
- Remove the global `db` variable. Instead:
  - Store the `aiosqlite.Connection` on `app.state.db` during lifespan
  - Create a `get_db` dependency that reads from `request.app.state.db`
  - Handlers receive the connection via `db: aiosqlite.Connection = Depends(get_db)`
- Update `main.py`:
  - Lifespan calls `init_db(app, db_path)` and `close_db(app)`
  - Import models from `basidian.models`
- Update all handlers:
  - Add `db: aiosqlite.Connection = Depends(get_db)` parameter
  - Remove `assert db.db is not None` checks (dependency guarantees it)
  - Replace `db.db.execute(...)` with `db.execute(...)`
  - Import `generate_id` from `basidian_server.db`
  - Import models from `basidian.models`

### 3. Rewrite `bscli` as an HTTP client

- Create `bscli/main.py` with the same Click CLI interface (`files list`, `files tree`, `files create`, etc.)
- Replace all direct DB calls with `basidian.client.BasidianClient` HTTP calls
- Drop all async DB helper functions (`_list_files`, `_get_tree`, `_create_node`, etc.)
- Add `--url` option (default `http://localhost:8090`) instead of `--db` option

### 4. Extract `basync` into its own package

- Move `basync.py` to `basync/main.py`
- Move `basync_config.py` to `basync/config.py`
- Update imports to use `basidian.client.BasidianClient` (shared client)
- Remove `basync_client.py` (absorbed into `basidian/client.py`)

### 5. Update `pyproject.toml`

Entry points:

```toml
[project.scripts]
basidian-server = "basidian_server.main:cli"
bscli = "bscli.main:cli"
basync = "basync.main:cli"
```

Dependencies: keep all deps together since it's one project.

### 6. Clean up

- Delete `basidian_server/bscli.py`
- Delete `basidian_server/basync.py`
- Delete `basidian_server/basync_client.py`
- Delete `basidian_server/basync_config.py`
- Delete `basidian_server/models.py` (moved to `basidian/models.py`)
- Delete `basidian_server/database.py` (replaced by `db.py` + `migrations.py`)

### 7. Verify

- `uv run basidian-server serve` starts the HTTP server
- `uv run bscli --url http://localhost:8090 files list` works over HTTP
- `uv run basync push` works over HTTP
- No package imports the database directly except `basidian_server`
- No global mutable state in any module

## Risks

- **Server must be running for CLI tools**: This is the intended tradeoff. Document it.
- **uv package discovery**: Multiple packages under `src/`. May need explicit package config in `pyproject.toml`.
- **Client method coverage**: `BasidianClient` needs methods for all endpoints that `bscli` uses. Current client is missing `search_files`, `move_node`, `get_node_by_id`. These need to be added.

## Open Questions

None -- all resolved.
