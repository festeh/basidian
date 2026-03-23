# Sync Implementation Notes

Design decisions made during the 017 data model work that affect how sync (016) should be built.

## What to sync

Three tables, nothing else:

```
fs_nodes    — tree structure (id, parent_id, type, name, path, sort_order, timestamps)
fs_content  — file bodies (node_id, body, updated_at)
fs_versions — version history (id, node_id, body, created_at)
```

**Metadata is NOT synced.** Tags, links, backlinks, daily dates, frontmatter — all derived in-memory from content. Each device rebuilds its own `MetadataIndex` on startup and updates it incrementally on each save. This eliminates an entire class of sync conflicts (two devices can't disagree about derived data).

## Conflict resolution: timestamps, not hashes

Use `updated_at` for last-write-wins. No content hashing needed.

**Why timestamps are fine for this app:**
- One user, 2-3 devices
- Rarely editing the same note on two devices before syncing
- Modern devices with NTP are accurate to within seconds
- Obsidian Sync uses the same approach

**If you later want conflict detection** (show both versions instead of silently overwriting): add a `content_hash` column to `fs_content`. Compare hash on sync — if both sides changed from the same base hash to different new hashes, that's a conflict. This is a non-breaking addition.

## Sync granularity

Sync is per-row, not per-table:

- **Tree changes** (`fs_nodes`): creates, deletes, moves/renames. Compare `updated_at` per node.
- **Content changes** (`fs_content`): body edits. Compare `updated_at` per node. Content is the heavy payload — only transfer when `updated_at` differs.
- **Version history** (`fs_versions`): append-only, sync by pushing new rows. No conflicts possible (versions are immutable once created).

The tree/content split matters here: when syncing "what changed," you can compare tree metadata without touching content blobs. A rename or move only changes `fs_nodes` — no content transfer needed. A content edit only changes `fs_content` — no tree transfer needed.

## Sync protocol sketch

### Pull (server → device)

1. Device sends its last sync timestamp (or per-table high-water marks)
2. Server returns rows where `updated_at > last_sync` for `fs_nodes` and `fs_content`
3. Server returns `fs_versions` rows where `created_at > last_sync`
4. Device applies changes to local SQLite, rebuilds `MetadataIndex`

### Push (device → server)

1. Device tracks locally modified rows (dirty flag or changelog table)
2. On sync, send dirty rows to server with their `updated_at`
3. Server compares `updated_at` — if server's is newer, reject (conflict) or last-write-wins
4. Server applies accepted changes, returns confirmed timestamps

### Ordering matters

Pull before push. This way the device has the latest server state before deciding what to push, reducing false conflicts.

## What the current model gives you for free

- **`fs_nodes.updated_at`** is kept in sync with content changes (the handler updates both `fs_content.updated_at` AND `fs_nodes.updated_at` on save). So you can check "did anything change for this node" with a single column on `fs_nodes`.
- **ON DELETE CASCADE** means deleting a node on one side and syncing the delete is clean — just delete from `fs_nodes`, cascade handles content and versions.
- **`parent_id` FK** means you can sync tree structure relationally (sync parent before children) rather than relying on path string manipulation.
- **`fs_versions` is append-only** — no update conflicts, just "push new rows."

## Local cache (spec 016)

The local device should have its own SQLite with the exact same schema. The app reads/writes to local SQLite, and sync pushes/pulls between local and remote. This means:

- Offline editing works (local SQLite is always available)
- File opens are instant (local read, no network)
- Sync is background, non-blocking
- The `MetadataIndex` is built from local SQLite content

## Open questions

- **Deleted file tracking**: When a file is deleted, the row disappears. How does the other device know to delete it? Options: soft delete (add `deleted_at` column), or a separate `sync_tombstones` table that records deletions with timestamps.
- **Version history sync direction**: Spec 016 says "File version history is stored on the server only, not in the local cache." If so, `fs_versions` doesn't need to be in the local SQLite at all — version history is a server-side feature only, and the local cache only has `fs_nodes` + `fs_content`.
- **Initial sync**: First device connection needs to pull the full vault. Subsequent syncs are incremental. Consider a "full sync" mode vs "incremental sync" mode.
- **Sync frequency**: Spec 016 says "within a few seconds of a local change." A simple approach: debounce saves (wait 2-3 seconds after last edit), then push. Pull on a timer (every 30 seconds) or via server-sent events / WebSocket for push notifications.
