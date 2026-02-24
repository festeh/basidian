"""HTTP client for the Basidian API."""

from typing import Optional

import httpx

from .models import FsNode, MoveRequest, Note


def _parse_node(item: dict) -> FsNode:
    return FsNode(
        id=item["id"],
        type=item["type"],
        name=item["name"],
        path=item["path"],
        parent_path=item["parent_path"],
        content=item.get("content", ""),
        sort_order=item.get("sort_order", 0),
        created_at=item.get("created_at"),
        updated_at=item.get("updated_at"),
    )


def _parse_note(item: dict) -> Note:
    return Note(
        id=item["id"],
        title=item["title"],
        content=item["content"],
        date=item["date"],
        created_at=item.get("created_at"),
        updated_at=item.get("updated_at"),
    )


class BasidianClient:
    """Async HTTP client for the Basidian API."""

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

    # ---- Filesystem ----

    async def get_tree(self, parent_path: Optional[str] = None) -> list[FsNode]:
        params = {}
        if parent_path is not None:
            params["parent_path"] = parent_path
        response = await self.client.get("/api/fs/tree", params=params)
        response.raise_for_status()
        return [_parse_node(item) for item in response.json()]

    async def get_node(self, path: str) -> Optional[FsNode]:
        response = await self.client.get("/api/fs/node", params={"path": path})
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return _parse_node(response.json())

    async def get_node_by_id(self, node_id: str) -> Optional[FsNode]:
        response = await self.client.get(f"/api/fs/node/{node_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return _parse_node(response.json())

    async def create_node(
        self, path: str, node_type: str, content: str = ""
    ) -> FsNode:
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
        return _parse_node(response.json())

    async def update_node(self, node_id: str, content: str) -> FsNode:
        response = await self.client.put(
            f"/api/fs/node/{node_id}", json={"content": content}
        )
        response.raise_for_status()
        return _parse_node(response.json())

    async def delete_node(self, node_id: str) -> bool:
        response = await self.client.delete(f"/api/fs/node/{node_id}")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    async def move_node(
        self, node_id: str, new_parent_path: str = "", new_name: str = ""
    ) -> Optional[FsNode]:
        payload = MoveRequest(
            new_parent_path=new_parent_path, new_name=new_name
        ).model_dump()
        response = await self.client.post(f"/api/fs/move/{node_id}", json=payload)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return _parse_node(response.json())

    async def search_files(self, query: str) -> list[FsNode]:
        response = await self.client.get("/api/fs/search", params={"q": query})
        response.raise_for_status()
        return [_parse_node(item) for item in response.json()]

    # ---- Notes ----

    async def get_notes(self) -> list[Note]:
        response = await self.client.get("/api/notes")
        response.raise_for_status()
        return [_parse_note(item) for item in response.json()]

    async def search_notes(self, query: str) -> list[Note]:
        response = await self.client.get("/api/search", params={"q": query})
        response.raise_for_status()
        return [_parse_note(item) for item in response.json()]
