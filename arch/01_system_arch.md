# System Architecture

## Overview

Basidian is a cross-platform markdown note-taking application. It pairs a Python backend (FastAPI + SQLite) with a Svelte 5 frontend wrapped in Tauri for desktop and mobile builds. A plugin system lets both sides extend functionality without touching core code.

## How It Works

```
┌──────────────────────────────────────────────────────┐
│                    Tauri Shell                        │
│  ┌────────────────────────────────────────────────┐  │
│  │           SvelteKit Frontend (:5173)           │  │
│  │                                                │  │
│  │  ┌──────────┐  ┌────────┐  ┌──────────────┐  │  │
│  │  │ FileTree │  │ Editor │  │ Plugin Panels│  │  │
│  │  └────┬─────┘  └───┬────┘  └──────┬───────┘  │  │
│  │       │             │              │          │  │
│  │       └─────────┬───┘──────────────┘          │  │
│  │                 ▼                             │  │
│  │          Svelte Stores                        │  │
│  │           (filesystem, theme, settings)       │  │
│  │                 │                             │  │
│  │                 ▼                             │  │
│  │          HTTP API Client                      │  │
│  └─────────────────┼────────────────────────────┘  │
└────────────────────┼─────────────────────────────────┘
                     │ REST (JSON)
                     ▼
     ┌───────────────────────────────────┐
     │   FastAPI Backend (:8090)         │
     │                                   │
     │   /api/notes/*   /api/fs/*        │
     │          │              │         │
     │          └──────┬───────┘         │
     │                 ▼                 │
     │          SQLite (aiosqlite)       │
     │          pb_data/data.db          │
     └───────────────────────────────────┘

     ┌───────────────────────────────────┐
     │   CLI Tools                       │
     │   bscli  — file operations        │
     │   basync — bidirectional sync     │
     │          │                        │
     │          ▼                        │
     │   BasidianClient (HTTP)  ─────►  Backend
     └───────────────────────────────────┘
```

**Request lifecycle:**

1. User interacts with a Svelte component.
2. Component calls an action on a Svelte store.
3. Store action calls the HTTP API client.
4. Client sends a REST request to FastAPI at `:8090`.
5. FastAPI handler queries SQLite and returns JSON.
6. Store updates its state; Svelte re-renders reactively.
7. Plugin hooks fire on relevant events (file open, save, etc.).

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/server/main.py` | FastAPI app, CORS, logging middleware, CLI entry |
| `backend/src/server/db.py` | SQLite connection lifecycle and migrations |
| `backend/src/client.py` | Async HTTP client shared by CLI tools |
| `frontend/src/lib/api/client.ts` | Frontend HTTP client to backend |
| `frontend/src/lib/stores/filesystem.ts` | File tree state and actions |
| `frontend/src/routes/+page.svelte` | Main page (routes to desktop or mobile) |
| `frontend/src-tauri/tauri.conf.json` | Tauri window and CSP config |

## Design Decisions

- **SQLite over PocketBase:** The project started with PocketBase (`pb_data/` directory remains) but switched to raw SQLite with aiosqlite for simpler async access and full control over the schema.
- **Static SvelteKit:** SSR is disabled. The frontend builds to static HTML and runs entirely client-side inside Tauri.
- **REST over WebSocket:** All data flows through REST. A WebSocket URL env var exists but is not actively used.
- **Platform detection at build time:** `VITE_PLATFORM` determines mobile vs. desktop layout. This avoids runtime detection complexity.

<!-- manual -->
<!-- /manual -->
