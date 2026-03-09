# Plan: File History

**Spec**: arch/specs/012-file-history-tracking/spec.md

## Tech Stack

- Language: Python (backend), TypeScript + Svelte 5 (frontend)
- Framework: FastAPI, SvelteKit
- Storage: SQLite (new `file_versions` table alongside existing `fs_nodes`)
- Diffing: `diff` (jsdiff) library on the frontend for line-level diffs
- Testing: vitest (frontend), pytest (backend, if tests exist)

## Structure

New and changed files:

```
basidian/server/
├── migrations.py               # Add file_versions table
├── handlers/
│   ├── filesystem.py           # Modify update_node, add snapshot on inactivity
│   └── history.py              # New: version list, get version, restore, cleanup
├── main.py                     # Register history router

frontend/src/lib/
├── api/
│   └── client.ts               # New methods: getVersions, snapshot, restoreVersion
├── stores/
│   └── history.ts              # New: version list state, selected version
├── types/
│   └── index.ts                # Add FileVersion type
├── components/
│   ├── Editor.svelte           # Call snapshot on file switch / destroy
│   └── HistoryPanel.svelte     # New: version list + diff view + restore button
```

## Approach

### 1. New `file_versions` table

Add to `migrations.py`:

```sql
CREATE TABLE IF NOT EXISTS file_versions (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (node_id) REFERENCES fs_nodes(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_versions_node_id ON file_versions(node_id);
CREATE INDEX IF NOT EXISTS idx_versions_created_at ON file_versions(created_at);
```

Full content snapshots, not diffs. Simpler to implement, and note files are small (a few KB each).

### 2. Session-end version capture

Two triggers for creating a version:

**a) Explicit snapshot (file switch / app close):**
New endpoint `POST /api/fs/node/{id}/snapshot`. The frontend calls this whenever the user navigates away from a file. Backend checks if content differs from the most recent version (or if no versions exist yet) and creates one if needed. This is idempotent — calling it twice won't create duplicates.

**b) Inactivity detection (10-minute gap):**
In the existing `update_node()` handler, before overwriting content: if `now - node.updated > 10 minutes` and the content is changing, snapshot the OLD content as a version. This catches the case where the user returns to a file after a break and starts typing again — the previous session's final state is preserved.

### 3. History API endpoints

New `history_router` in `handlers/history.py`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/fs/node/{id}/versions` | GET | List versions (id, created_at, summary). Most recent first. |
| `/api/fs/node/{id}/versions/{vid}` | GET | Get full version content |
| `/api/fs/node/{id}/snapshot` | POST | Create version snapshot if content changed |
| `/api/fs/node/{id}/restore/{vid}` | POST | Replace file content with version content |

The list endpoint returns lightweight summaries (no full content) with a change summary like "+3 / -1 lines" computed by comparing each version to its predecessor.

Restore works by: reading the old version's content, calling the normal `update_node` logic to set it as the current content, then creating a new version snapshot. This way restore itself is undoable.

### 4. Frontend: snapshot calls

Modify `Editor.svelte`:
- On file switch (`$effect` that detects file change): call `api.snapshot(fileId)` after flush save. Call it even if no pending save exists, in case the last autosave already persisted the content.
- On `onDestroy`: same — call snapshot for the current file.

These are fire-and-forget calls (don't block the UI).

### 5. Frontend: API client additions

Add to `client.ts`:
- `getVersions(nodeId): Promise<FileVersionSummary[]>`
- `getVersion(nodeId, versionId): Promise<FileVersion>`
- `snapshot(nodeId): Promise<void>`
- `restoreVersion(nodeId, versionId): Promise<FsNode>`

### 6. Frontend: history store

New `stores/history.ts`:
- `versions` — list of version summaries for the current file
- `selectedVersion` — the version being viewed (full content loaded)
- `isOpen` — whether history panel is showing
- Actions: `loadVersions(nodeId)`, `selectVersion(vid)`, `restore(vid)`, `close()`

### 7. Frontend: HistoryPanel component

A side panel (similar pattern to ChatPane) with:
- **Version list**: scrollable list, each entry showing relative time ("2 hours ago") and change summary ("+3 / -1 lines"). Use `Intl.RelativeTimeFormat` or a small helper — no new dependency needed.
- **Diff view**: when a version is selected, show a side-by-side or unified diff. Use the `diff` npm package for line-level diffing. Render added lines in green, removed in red (CSS only, no CodeMirror needed for the read-only diff).
- **Restore button**: "Restore this version" button. Calls restore endpoint, refreshes editor content.

### 8. Version cleanup

Run cleanup on app startup (in the FastAPI lifespan handler). The cleanup logic:

```
For each file with versions:
  - Keep all versions from the last 7 days
  - For versions 7-30 days old: keep one per day (the latest that day)
  - For versions older than 30 days: keep one per week (the latest that week)
  - Delete the rest
```

This runs once at server start. No background scheduler needed — the app restarts often enough (dev server, Tauri app launches) to keep versions tidy.

## Implementation Order

1. Backend: migration + snapshot endpoint + update_node inactivity check
2. Backend: list/get/restore endpoints + cleanup
3. Frontend: API client + store
4. Frontend: Editor.svelte snapshot calls
5. Frontend: HistoryPanel component (list + diff + restore)

Each step is independently testable.

## Risks

- **Storage growth**: Full content snapshots for every session end. Mitigated by cleanup policy and the fact that notes are small text files. A 10KB note with 100 versions = 1MB — manageable.
- **Snapshot spam on rapid file switching**: User clicks through multiple files quickly. Mitigated by the "only if content changed from last version" check in the snapshot endpoint.
- **Race between flush save and snapshot**: Flush save is fire-and-forget, snapshot call follows immediately. If flush hasn't completed, snapshot might capture stale content. Mitigation: make the frontend `await` the flush save before calling snapshot, or have the snapshot endpoint accept optional content to snapshot directly.
- **Cleanup deleting too aggressively**: Fixed retention policy might not suit all users. Acceptable for now (out of scope to configure), and the policy is conservative (keeps everything for 7 days).
