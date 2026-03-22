from typing import Optional

from pydantic import BaseModel


# Filesystem models
class FsNode(BaseModel):
    id: str
    parent_id: Optional[str] = None
    parent_path: str = "/"
    type: str
    name: str
    path: str
    content: Optional[str] = None
    sort_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FsNodeRequest(BaseModel):
    type: str
    name: str
    parent_path: str = "/"
    content: str = ""
    sort_order: int = 0


class FsNodeUpdateRequest(BaseModel):
    name: str | None = None
    content: str | None = None
    sort_order: int | None = None


class MoveRequest(BaseModel):
    new_parent_path: str = ""
    new_name: str = ""


# File version models
class FileVersion(BaseModel):
    id: str
    node_id: str
    body: str
    created_at: str


class FileVersionSummary(BaseModel):
    id: str
    node_id: str
    created_at: str
    lines_added: int
    lines_removed: int
