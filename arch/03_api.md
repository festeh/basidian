# API

## Overview

The backend exposes a REST API over HTTP at port 8090. All endpoints return JSON. There is no authentication.

## How It Works

Two routers handle all requests:

- **Notes router** — CRUD for timestamped notes, plus date filtering and search.
- **Filesystem router** — CRUD for a virtual file/folder tree, plus move and search.

CORS allows all origins. A logging middleware records every request with method, path, status, and duration.

## Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"status": "ok"}` |

### Notes (`/api/notes`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/notes` | List all notes (newest first) |
| POST | `/api/notes` | Create a note |
| GET | `/api/notes/{id}` | Get one note |
| PUT | `/api/notes/{id}` | Update a note |
| DELETE | `/api/notes/{id}` | Delete a note (204) |
| GET | `/api/notes/date/{date}` | Notes for a date (YYYY-MM-DD) |
| GET | `/api/search?q=...` | Search notes by title/content |

### Filesystem (`/api/fs`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/fs/tree` | Get tree (optional `parent_path` filter) |
| GET | `/api/fs/node?path=...` | Get node by path |
| GET | `/api/fs/node/{id}` | Get node by ID |
| POST | `/api/fs/node` | Create file or folder |
| PUT | `/api/fs/node/{id}` | Update node |
| DELETE | `/api/fs/node/{id}` | Delete node (cascades for folders) |
| POST | `/api/fs/move/{id}` | Move or rename node |
| GET | `/api/fs/search?q=...` | Search files by name/content |

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/server/main.py` | App creation, router registration, middleware |
| `backend/src/server/handlers/notes.py` | Notes endpoints |
| `backend/src/server/handlers/filesystem.py` | Filesystem endpoints |
| `backend/src/models.py` | Pydantic request/response models |
| `frontend/src/lib/api/client.ts` | Frontend client that calls these endpoints |

## Design Decisions

- **No versioning.** The API serves a single frontend and CLI tools, all released together.
- **No auth.** The server runs locally on the user's machine. CORS is wide open for dev convenience.
- **Cascade delete.** Deleting a folder removes all children in the same transaction.

<!-- manual -->
<!-- /manual -->
