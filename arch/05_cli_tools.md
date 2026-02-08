# CLI Tools

## Overview

Three CLI tools ship with Basidian. All are Python packages managed with uv and use Click for argument parsing.

## How It Works

```
User
 │
 ├─ basidian-server serve       → Starts FastAPI on :8090
 │
 ├─ bscli files list/tree/...   → File operations via HTTP
 │
 └─ basync push/pull            → Bidirectional file sync via HTTP
```

All CLI tools talk to the backend through `BasidianClient`, the shared async HTTP client. None access the database directly.

### basidian-server

Starts the FastAPI application with Uvicorn.

```bash
basidian-server serve --http :8090 --db ./pb_data/data.db
```

### bscli

File and folder operations against the running server.

```bash
bscli files list [--path PATH]
bscli files tree
bscli files create PATH [--type file|folder]
bscli files read PATH
bscli files delete PATH [-f]
bscli files move SOURCE DEST
bscli search QUERY
bscli recent [-n LIMIT]
```

### basync

Bidirectional file sync between local filesystem and Basidian's virtual filesystem.

```bash
basync push [PATH] [--local DIR] [--remote PATH] [--include PAT] [--exclude PAT] [--dry-run]
basync pull [PATH] [--local DIR] [--remote PATH] [--include PAT] [--exclude PAT] [--dry-run]
basync config
```

Reads `.basync.toml` for defaults. Skips binary files, files over 1 MB, and common junk (`.git`, `node_modules`, `__pycache__`).

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/server/main.py` | `basidian-server` entry point |
| `backend/src/bscli/main.py` | `bscli` commands |
| `backend/src/basync/main.py` | `basync` push/pull logic |
| `backend/src/basync/config.py` | TOML config loading |
| `backend/src/client.py` | Shared HTTP client used by all CLI tools |
| `backend/pyproject.toml` | Entry point definitions |

## Design Decisions

- **HTTP-only access.** CLI tools never import the server or database modules. This keeps them decoupled and lets them run against any Basidian server.
- **Dry-run by default mindset.** basync supports `--dry-run` to preview changes before applying.

<!-- manual -->
<!-- /manual -->
