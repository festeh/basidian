# Plan: Daily Notes Plugin for BasidianClient

**Spec**: No formal spec — requirements derived from frontend daily-notes plugin.

## Tech Stack

- Language: Python 3.12+
- Library: basidian (shared package at `backend/src/basidian/`)
- Testing: pytest (existing test setup)
- Downstream consumer: bro (`agent/notes/basidian_agent.py`)

## Structure

```
basidian/backend/src/basidian/
├── client.py                 # Unchanged — stays lean
├── models.py                 # Unchanged
└── plugins/
    ├── __init__.py
    └── daily_notes.py        # Daily notes logic, composes on BasidianClient

bro/agent/notes/
└── basidian_agent.py         # Add today_note operation using the plugin
```

`BasidianClient` stays generic. Plugin code lives in `basidian.plugins.daily_notes`.

## Approach

### 1. Create `basidian/plugins/daily_notes.py`

A standalone module that takes a `BasidianClient` instance and provides daily note operations:

```python
from basidian.client import BasidianClient
from basidian.models import FsNode

class DailyNotes:
    def __init__(
        self,
        client: BasidianClient,
        folder: str = "/daily",
        date_format: str = "%Y-%m-%d",
    ):
        self._client = client
        self.folder = folder
        self.date_format = date_format

    async def get_or_create_today(self, template: str | None = None) -> FsNode:
        """Get today's note, creating it if it doesn't exist."""

    async def get(self, date: str) -> FsNode | None:
        """Get a daily note by date string (e.g. "2026-01-15")."""

    async def list(self) -> list[FsNode]:
        """List all daily notes."""

    async def append_today(self, content: str) -> FsNode:
        """Append content to today's note, creating it if needed."""
```

This mirrors the frontend plugin's `openOrCreateDaily`, `getDailyPath`, and `getDailyNotesForMonth` — without UI concerns.

**Usage pattern:**
```python
async with BasidianClient(base_url) as client:
    daily = DailyNotes(client)
    today = await daily.get_or_create_today()
    await daily.append_today("Meeting notes: ...")
```

### 2. Export from `basidian.plugins`

`plugins/__init__.py` re-exports `DailyNotes` for convenience:

```python
from .daily_notes import DailyNotes
```

### 3. Add `today_note` operation to bro's `BasidianAgent`

In `bro/agent/notes/basidian_agent.py`:

- Add `TODAY_NOTE = "today_note"` to the `Operation` enum
- In `_run_operation`, instantiate `DailyNotes(client)` and call `get_or_create_today()`
- Update `SYSTEM_PROMPT_TEMPLATE` to document the new operation:
  ```
  - today_note: Open or create today's daily note. Args: {} (no args needed)
  ```

### 4. No backend server changes needed

The existing filesystem API endpoints already support everything. The daily note logic is pure client-side composition — same approach as the frontend plugin.

## Risks

- **Folder convention mismatch**: Frontend defaults to `/daily`. We use the same default so they stay in sync.
- **Date format mismatch**: Frontend uses `YYYY-MM-DD`, Python uses `%Y-%m-%d`. Same output (e.g., `2026-02-01`).
- **Concurrent creation race**: Two callers could both see "not found" and try to create. Low risk for personal daily notes.

## Decisions

- **No `template_path` support for now.** Can add later if needed. Default template is `# {date}\n\n`.
