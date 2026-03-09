# File History

## What Users Can Do

1. **Browse a file's version history**

   - **Scenario: File has history**
     - **Given:** User is viewing a note that has been edited before
     - **When:** User opens the history panel
     - **Then:** They see a list of past versions, each showing a timestamp and a short summary of what changed (e.g., "3 lines added, 1 removed")

   - **Scenario: File has no history**
     - **Given:** User is viewing a newly created note
     - **When:** User opens the history panel
     - **Then:** They see a message like "No previous versions yet"

2. **View a past version**

   - **Scenario: Reading an old version**
     - **Given:** User is browsing a file's history
     - **When:** User selects a version from the list
     - **Then:** They see a diff view comparing that version to the current content

3. **Restore a past version**

   - **Scenario: Successful restore**
     - **Given:** User is viewing a past version
     - **When:** User clicks "Restore this version"
     - **Then:** The file content is replaced with the old version's content, and a new version is recorded (so the restore itself is undoable)

4. **Versions are saved automatically without flooding history**

   - **Scenario: Active editing session**
     - **Given:** User is actively typing in a note
     - **When:** Autosave fires repeatedly (every 2.5 seconds of idle)
     - **Then:** Only one version is captured per editing session, not one per autosave. An "editing session" ends after a period of inactivity (e.g., 5 minutes with no edits).

   - **Scenario: Returning to a file later**
     - **Given:** User edited a note, left for 30 minutes, then came back and edited again
     - **When:** The second round of edits is autosaved
     - **Then:** A new version is created, separate from the earlier session

   - **Scenario: Switching files**
     - **Given:** User is editing file A and switches to file B
     - **When:** The switch triggers a flush save on file A
     - **Then:** If file A's content changed since the last version, a version snapshot is captured

5. **Old versions are cleaned up over time**

   - **Scenario: Version retention**
     - **Given:** A file accumulates many versions over weeks/months
     - **When:** Cleanup runs
     - **Then:** Recent versions (last 7 days) are all kept. Older versions are thinned out — keep roughly one per day for the last month, one per week beyond that.

## Requirements

- [ ] Each version stores the full content of the file at that point in time
- [ ] Versions are tied to a file's identity, not its path (renaming/moving a file preserves its history)
- [ ] A version is captured when an editing session ends (inactivity timeout or file switch), not on every autosave
- [ ] Restoring a version creates a new version (never destroys history)
- [ ] The history panel shows timestamps in a human-friendly format ("2 hours ago", "yesterday")
- [ ] Diff view highlights added and removed lines
- [ ] Version cleanup runs automatically and respects the retention policy
- [ ] History adds no noticeable delay to normal editing or saving

## Out of Scope

- Manual named snapshots ("save points") — may revisit later
- Configurable retention policy — one fixed policy for now

## Decisions

- **Inactivity timeout:** 10 minutes. VS Code uses a 10s merge window for its local history; third-party history plugins default to ~10 min intervals. Given our 2.5s autosave, 10 minutes strikes a good balance.
- **Duplicated files:** Start with a fresh history (no inherited versions).
