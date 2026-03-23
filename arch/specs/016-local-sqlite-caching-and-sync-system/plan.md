# Plan: Local SQLite Caching and Sync

**Spec**: arch/specs/016-local-sqlite-caching-and-sync-system/spec.md

## Tech Stack

- Frontend: TypeScript, Svelte 5, `@tauri-apps/plugin-sql` (native SQLite via Tauri)
- Backend: Python, FastAPI, aiosqlite (existing)
- Testing: Vitest (frontend), pytest (backend)

## Architecture

The app reads and writes to a local SQLite database. A background sync engine pushes and pulls changes between local and server. The HTTP API client is used only by the sync engine — stores never call it directly.

```
User ↔ Stores ↔ Local SQLite ↔ Sync Engine ↔ HTTP ↔ Server SQLite
```

## Structure

```
frontend/src/lib/
├── db/
│   ├── connection.ts    — open/close local SQLite, run migrations
│   ├── schema.ts        — CREATE TABLE statements, local schema version
│   ├── nodes.ts         — fs_nodes CRUD (read tree, get node, create, update, delete)
│   └── content.ts       — fs_content CRUD (get body, update body)
├── sync/
│   ├── engine.ts        — pull/push orchestration, polling loop, debounced push
│   ├── pull.ts          — fetch server changes, apply to local DB
│   ├── push.ts          — find dirty rows, send to server, clear dirty flags
│   └── status.ts        — sync state store (synced/pending/syncing/error)
├── stores/
│   └── filesystem.ts    — (modified) reads from db/, not api/
├── api/
│   └── client.ts        — (modified) add sync endpoints, keep for sync engine only
└── components/
    ├── SyncIndicator.svelte  — sync status badge
    └── ConflictModal.svelte  — pick-a-version conflict UI

basidian/server/
├── handlers/
│   └── sync.py          — GET /api/sync/changes, POST /api/sync/push
└── migrations.py        — (modified) add deleted_at to fs_nodes
```

## Local SQLite Schema

Same as server, plus sync tracking columns:

```sql
CREATE TABLE fs_nodes (
    id          TEXT PRIMARY KEY,
    parent_id   TEXT REFERENCES fs_nodes(id) ON DELETE CASCADE,
    type        TEXT NOT NULL CHECK (type IN ('file', 'folder')),
    name        TEXT NOT NULL,
    path        TEXT NOT NULL,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    deleted_at  TEXT,              -- soft delete
    is_dirty    INTEGER DEFAULT 0  -- 1 = changed locally, not yet synced
);

CREATE TABLE fs_content (
    node_id     TEXT PRIMARY KEY REFERENCES fs_nodes(id) ON DELETE CASCADE,
    body        TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL,
    is_dirty    INTEGER DEFAULT 0
);

CREATE TABLE sync_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- Stores: 'last_sync_at' (ISO timestamp), 'device_id' (random hex)
```

## Sync API Endpoints (Backend)

### `GET /api/sync/changes?since=<ISO timestamp>`

Returns all rows changed since the given timestamp. On first sync, `since` is omitted and the server returns everything.

```json
{
  "nodes": [...],       // fs_nodes where updated_at > since OR deleted_at > since
  "content": [...],     // fs_content where updated_at > since
  "server_time": "..."  // use as next 'since' value
}
```

### `POST /api/sync/push`

Client sends locally modified rows. Server applies last-write-wins.

```json
// Request
{
  "nodes": [...],
  "content": [...]
}

// Response
{
  "accepted": ["id1", "id2"],
  "rejected": [{"id": "id3", "server_updated_at": "...", "reason": "newer_on_server"}],
  "server_time": "..."
}
```

## Approach

### Phase 1: Local SQLite foundation

1. Add `@tauri-apps/plugin-sql` to the Tauri app (Rust + JS sides).
2. Create `db/connection.ts` — opens `sqlite:basidian-local.db` in the app data directory. Runs `PRAGMA foreign_keys = ON` and schema migrations.
3. Create `db/schema.ts` — the CREATE TABLE statements above, plus a `schema_version` in `sync_meta` for future migrations.
4. Create `db/nodes.ts` — functions: `getTree()`, `getNode(id)`, `createNode(...)`, `updateNode(id, ...)`, `softDeleteNode(id)`, `moveNode(id, ...)`. All queries filter `WHERE deleted_at IS NULL`.
5. Create `db/content.ts` — functions: `getBody(nodeId)`, `updateBody(nodeId, body)`. Sets `is_dirty = 1` on write.

### Phase 2: Refactor stores to use local DB

6. Change `stores/filesystem.ts` — replace all `api.*` calls with `db.*` calls. `loadTree()` reads from local SQLite. `openFile()` reads body from local SQLite. `updateNode()` writes to local SQLite.
7. The editor's autosave flow stays the same (2.5s debounce), but `save()` now writes to local SQLite instead of HTTP.
8. Snapshots (`api.snapshot()`) still go to the server — version history is server-only. If the server is unreachable, skip the snapshot silently.

### Phase 3: Sync engine — pull

9. Add `deleted_at` column to server's `fs_nodes` table. Update server handlers: `delete_node` sets `deleted_at` instead of DELETE. All server queries add `WHERE deleted_at IS NULL`.
10. Create `handlers/sync.py` with the `GET /api/sync/changes` endpoint. Queries `fs_nodes` and `fs_content` for rows where `updated_at > since` (or `deleted_at > since` for soft-deleted nodes).
11. Create `sync/pull.ts` — calls the sync endpoint, upserts returned rows into local SQLite. For soft-deleted nodes, marks them locally with `deleted_at` and cascades.
12. Create `sync/engine.ts` — on app start, runs initial pull (full download if `last_sync_at` is empty). Then polls every 30 seconds.
13. After each pull, update `sync_meta.last_sync_at` with `server_time` from response.
14. After pull applies changes, notify stores to re-read affected data (emit events or re-call store loaders).

### Phase 4: Sync engine — push

15. Create `sync/push.ts` — queries local DB for rows where `is_dirty = 1`. Sends them to `POST /api/sync/push`.
16. Create `handlers/sync.py` push endpoint. For each incoming row, compare `updated_at` with server's. If client's is newer (or row doesn't exist on server), accept. If server's is newer, reject.
17. On accepted: clear `is_dirty = 0` locally.
18. On rejected: server's version is newer — the next pull will overwrite the local version (last-write-wins). Clear `is_dirty` to avoid re-pushing stale data.
19. Trigger push after each local write — debounced 3 seconds after last change.

### Phase 5: Sync status UI

20. Create `sync/status.ts` — a Svelte store exposing: `state` ('synced' | 'pending' | 'syncing' | 'error'), `pendingCount` (number of dirty rows), `lastError` (string | null), `lastSyncAt` (timestamp).
21. Create `SyncIndicator.svelte` — small badge in the status bar. Shows a checkmark when synced, a count when pending, a spinner when syncing, a warning icon on error. Clicking on error shows detail.
22. The sync engine updates this store at each stage (before pull, after pull, before push, after push, on error).

### Phase 6: Conflict resolution

23. Start with last-write-wins — the sync engine silently applies the newer version. This handles the common case (one user, multiple devices, rarely editing the same file simultaneously).
24. For deleted-on-server + edited-locally: during pull, if a node has `deleted_at` set on server but `is_dirty = 1` locally, don't delete it. Instead, surface a conflict in the sync status store.
25. Create `ConflictModal.svelte` — shows when a delete/edit conflict is detected. Options: "Keep my version" (re-create on server) or "Discard my edits" (accept deletion).
26. Future: add `content_hash` to `fs_content` for detecting true edit conflicts (both sides changed). Not in initial implementation.

## Risks

- **Clock skew between devices**: `updated_at` comparison assumes clocks are roughly in sync. Mitigation: use server time for all sync timestamps, not local time. The `server_time` in sync responses is the reference clock.
- **Tauri plugin availability**: `tauri-plugin-sql` must work on both desktop and mobile Tauri targets. Mitigation: it's an official Tauri plugin with broad platform support.
- **Dev mode without Tauri**: During `npm run dev`, Tauri APIs aren't available. Mitigation: mock `@tauri-apps/plugin-sql` in dev, fall back to in-memory or direct HTTP (existing behavior).
- **Large initial sync**: A vault with thousands of files could make first sync slow. Mitigation: for a personal notes vault, this is unlikely to be a problem. If it is, add progress indication.
- **Race conditions**: User edits while sync is applying pull changes. Mitigation: pull should skip nodes that are `is_dirty = 1` locally — don't overwrite unsaved local changes.
- **Schema drift**: Local and server schemas must match. Mitigation: version the local schema in `sync_meta`, run migrations on connection open.

## Decisions

- **Dev mode**: Always develop in Tauri (`cargo tauri dev`). No browser fallback or SQL plugin mocking.
