# Local SQLite Caching and Sync

## Problem

Every user action hits the backend over HTTP. If the backend is slow, unreachable, or on another machine, the app stalls. There is no local copy of vault data, so the frontend cannot work independently.

## What Users Can Do

### 1. Work without the backend running

- **Scenario: Backend is down**
  - **Given:** The user has opened the app at least once before (local cache exists)
  - **When:** The backend is unreachable
  - **Then:** The app loads from the local cache. The user can browse, search, and edit files normally.

- **Scenario: First launch, no backend**
  - **Given:** No local cache exists and the backend is unreachable
  - **When:** The user opens the app
  - **Then:** The app shows a clear message: "Connect to your vault server to get started."

### 2. Experience instant file loading

- **Scenario: Opening a cached file**
  - **Given:** The file has been synced to the local cache
  - **When:** The user opens the file
  - **Then:** Content appears immediately from the local cache. No loading spinner. If a fresher version exists on the server, it replaces the local content silently (unless the user has made local edits — see conflict handling).

- **Scenario: Browsing the file tree**
  - **When:** The user expands folders or scrolls through the file tree
  - **Then:** The tree renders from the local cache. No network requests block the UI.

### 3. See sync status

- **Scenario: All synced**
  - **Given:** Local cache matches the server
  - **When:** The user looks at the status indicator
  - **Then:** It shows "synced" (or equivalent quiet state).

- **Scenario: Unsynced local changes**
  - **Given:** The user edited files while offline (or the server hasn't confirmed yet)
  - **When:** The user looks at the status indicator
  - **Then:** It shows the number of pending changes (e.g., "3 unsynced").

- **Scenario: Sync in progress**
  - **When:** The app is actively pushing or pulling changes
  - **Then:** The indicator shows sync activity.

- **Scenario: Sync error**
  - **When:** Sync fails (server unreachable, conflict, etc.)
  - **Then:** The indicator shows an error state. The user can tap it for details.

### 4. Resolve conflicts

- **Scenario: Non-overlapping edits**
  - **Given:** The user edited a file locally while the same file was edited on the server
  - **When:** The edits touch different parts of the file
  - **Then:** Changes merge automatically. No user action needed.

- **Scenario: Overlapping edits**
  - **Given:** Both local and server changed the same region of the same file
  - **When:** Sync detects the conflict
  - **Then:** The app keeps both versions and asks the user to pick one (or manually merge). Neither version is lost silently.

- **Scenario: File deleted on server, edited locally**
  - **Given:** The server deleted a file that the user edited locally
  - **When:** Sync runs
  - **Then:** The local version is preserved. The user is told the file was deleted on the server and can choose to re-create it or discard their edits.

### 5. Sync across devices

- **Scenario: Edit on device A, read on device B**
  - **Given:** Two devices point to the same backend server
  - **When:** The user edits a file on device A and later opens device B
  - **Then:** Device B pulls the latest version during sync. The user sees the updated file.

- **Scenario: Both devices edit the same file**
  - **Given:** Device A and device B both edit the same file before syncing
  - **When:** Both devices sync with the server
  - **Then:** Conflict resolution applies (see scenario 4 above).

### 6. Control sync behavior

- **Scenario: Manual sync**
  - **When:** The user triggers sync manually (button or shortcut)
  - **Then:** Sync starts immediately regardless of any automatic schedule.

- **Scenario: Automatic sync**
  - **Given:** The backend is reachable
  - **When:** The user makes a change
  - **Then:** The change syncs to the server within a few seconds, without user action.

### 7. Sync only what changed

- **Scenario: One file added**
  - **Given:** The user created one new file since the last sync
  - **When:** Sync runs
  - **Then:** Only that one file is sent to the server. The rest of the vault is not re-uploaded.

- **Scenario: One file edited**
  - **Given:** The user edited one file since the last sync
  - **When:** Sync runs
  - **Then:** Only the changed file is pushed. Unchanged files are not touched.

- **Scenario: Server has new changes**
  - **Given:** Another device added or edited files on the server
  - **When:** This device syncs
  - **Then:** Only the files that changed on the server are pulled. The full vault is not re-downloaded.

- **Scenario: Nothing changed**
  - **Given:** No changes on either side since the last sync
  - **When:** Sync runs (automatic or manual)
  - **Then:** Sync completes almost instantly. No file content is transferred.

## Requirements

- [ ] The app loads and is fully usable from the local cache when the backend is unreachable
- [ ] File opens are served from the local cache first (no network round-trip for cached content)
- [ ] The file tree renders from the local cache without waiting for the server
- [ ] The local cache stores the full vault: file tree structure (`fs_nodes`) and file content (`fs_content`)
- [ ] Local edits are persisted to the local cache immediately (survive app restart)
- [ ] A visible sync indicator shows: synced, pending changes (with count), syncing, or error
- [ ] Non-overlapping edits to the same file merge automatically
- [ ] Overlapping edits surface a conflict for the user to resolve — no silent data loss
- [ ] Deleted-on-server vs. edited-locally conflicts preserve the local version and prompt the user
- [ ] Sync happens automatically within seconds of a local change when the server is reachable
- [ ] Manual sync is available via a button or shortcut
- [ ] Multiple devices pointing to the same server converge to the same state
- [ ] File version history continues to work (snapshots still created on save)
- [ ] Sync transfers only changed files — not the entire vault
- [ ] A sync with no changes on either side transfers no file content
- [ ] Search runs against the local cache (works offline, no server round-trip)
- [ ] Sync runs in the background from app start — no "waiting for server" state
- [ ] Conflicts use a simple modal: show both versions, user picks or edits
- [ ] File version history is stored on the server only, not in the local cache

## Decisions

- **Search**: Runs against the local cache only. Works offline, no server round-trip.
- **Server connectivity**: No timeout or "waiting for server" state. Sync runs in the background from app start. The app is always usable from the local cache.
- **Conflict UI**: Simple modal showing both versions. User picks one or edits. No inline merge markers.
- **Version history**: Server-only. Local cache stores `fs_nodes` + `fs_content`, not `fs_versions`.
- **Metadata**: Not synced. Tags, links, backlinks, frontmatter are derived in-memory from content. Each device rebuilds its own `MetadataIndex`.
- **First sync**: Full download of the vault. Subsequent syncs are incremental.
- **Deleted file tracking**: Soft delete (`deleted_at` column on `fs_nodes`). Queries filter with `WHERE deleted_at IS NULL`. Avoids the "forgot to write a tombstone" class of bugs.
- **Sync frequency**: Debounce push (few seconds after last edit) + poll for pull (every 30 seconds). No WebSocket.
- **Sync granularity**: Per-row. Tree changes (`fs_nodes`) and content changes (`fs_content`) sync independently. A rename transfers no content. A content edit transfers no tree metadata.
- **Conflict resolution**: Last-write-wins using `updated_at` timestamps. Content hash can be added later for true conflict detection.
- **Sync order**: Pull before push. Device gets latest server state before deciding what to push.

## Out of Scope

- Real-time collaborative editing (two users editing the same file simultaneously)
- Partial sync (syncing only some folders or files)
- End-to-end encryption of synced data
- Peer-to-peer sync without a central server
- WebSocket push notifications (polling is sufficient for now)
