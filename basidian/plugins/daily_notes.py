"""Daily notes plugin for BasidianClient.

Mirrors the frontend daily-notes plugin logic (folder convention,
date-based filenames) as a composable Python class.
"""

from __future__ import annotations

from datetime import date, datetime

from basidian.client import BasidianClient
from basidian.models import FsNode


class DailyNotes:
    """Daily note operations on top of BasidianClient."""

    def __init__(
        self,
        client: BasidianClient,
        folder: str = "/daily",
        date_format: str = "%d-%b-%y",
    ) -> None:
        self._client = client
        self.folder = folder
        self.date_format = date_format

    def _path_for(self, d: date) -> str:
        date_str = d.strftime(self.date_format)
        return f"{self.folder}/{date_str}.md"

    def _default_template(self, d: date) -> str:
        return f"# {d.strftime(self.date_format)}\n\n"

    async def _ensure_folder(self) -> None:
        existing = await self._client.get_node(self.folder)
        if not existing:
            await self._client.create_node(self.folder.lstrip("/"), "folder")

    async def get_or_create_today(self) -> FsNode:
        """Get today's daily note, creating it if it doesn't exist."""
        today = date.today()
        path = self._path_for(today)

        existing = await self._client.get_node(path)
        if existing:
            return existing

        await self._ensure_folder()
        return await self._client.create_node(
            path.lstrip("/"), "file", self._default_template(today)
        )

    async def get(self, date_str: str) -> FsNode | None:
        """Get a daily note by date string (e.g. '15-Jan-26')."""
        d = datetime.strptime(date_str, self.date_format).date()
        return await self._client.get_node(self._path_for(d))

    async def list(self) -> list[FsNode]:
        """List all daily notes in the folder."""
        return await self._client.get_tree(parent_path=self.folder)

    async def append_today(self, content: str) -> FsNode:
        """Append content to today's note, creating it if needed."""
        node = await self.get_or_create_today()
        new_content = node.content.rstrip("\n") + "\n\n" + content + "\n"
        return await self._client.update_node(node.id, new_content)
