"""HTTP client for Basidian API."""

from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class FsNode:
    """Filesystem node from Basidian."""

    id: str
    type: str
    name: str
    path: str
    parent_path: str
    content: str
    sort_order: int
    created: Optional[str] = None
    updated: Optional[str] = None


class BasidianClient:
    """Async HTTP client for Basidian API."""

    def __init__(self, base_url: str = "http://localhost:8090"):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        return self._client

    async def get_tree(self, parent_path: Optional[str] = None) -> list[FsNode]:
        """Get all nodes, optionally filtered by parent path."""
        params = {}
        if parent_path is not None:
            params["parent_path"] = parent_path

        response = await self.client.get("/api/fs/tree", params=params)
        response.raise_for_status()

        nodes = []
        for item in response.json():
            nodes.append(
                FsNode(
                    id=item["id"],
                    type=item["type"],
                    name=item["name"],
                    path=item["path"],
                    parent_path=item["parent_path"],
                    content=item.get("content", ""),
                    sort_order=item.get("sort_order", 0),
                    created=item.get("created"),
                    updated=item.get("updated"),
                )
            )
        return nodes

    async def get_node(self, path: str) -> Optional[FsNode]:
        """Get a single node by path."""
        response = await self.client.get("/api/fs/node", params={"path": path})
        if response.status_code == 404:
            return None
        response.raise_for_status()

        item = response.json()
        return FsNode(
            id=item["id"],
            type=item["type"],
            name=item["name"],
            path=item["path"],
            parent_path=item["parent_path"],
            content=item.get("content", ""),
            sort_order=item.get("sort_order", 0),
            created=item.get("created"),
            updated=item.get("updated"),
        )

    async def create_node(
        self, path: str, node_type: str, content: str = ""
    ) -> FsNode:
        """Create a new file or folder."""
        # Parse path to get name and parent
        path = path.strip("/")
        if "/" in path:
            parts = path.rsplit("/", 1)
            parent_path = "/" + parts[0]
            name = parts[1]
        else:
            parent_path = "/"
            name = path

        payload = {
            "type": node_type,
            "name": name,
            "path": "/" + path,
            "parent_path": parent_path if parent_path != "/" else "",
            "content": content if node_type == "file" else "",
        }

        response = await self.client.post("/api/fs/node", json=payload)
        response.raise_for_status()

        item = response.json()
        return FsNode(
            id=item["id"],
            type=item["type"],
            name=item["name"],
            path=item["path"],
            parent_path=item["parent_path"],
            content=item.get("content", ""),
            sort_order=item.get("sort_order", 0),
            created=item.get("created"),
            updated=item.get("updated"),
        )

    async def update_node(self, node_id: str, content: str) -> FsNode:
        """Update a file's content."""
        response = await self.client.put(
            f"/api/fs/node/{node_id}", json={"content": content}
        )
        response.raise_for_status()

        item = response.json()
        return FsNode(
            id=item["id"],
            type=item["type"],
            name=item["name"],
            path=item["path"],
            parent_path=item["parent_path"],
            content=item.get("content", ""),
            sort_order=item.get("sort_order", 0),
            created=item.get("created"),
            updated=item.get("updated"),
        )

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node."""
        response = await self.client.delete(f"/api/fs/node/{node_id}")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True
