from typing import Optional

from pydantic import BaseModel


# Note models
class Note(BaseModel):
    id: str
    title: str
    content: str
    date: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class NoteRequest(BaseModel):
    title: str = ""
    content: str = ""
    date: str = ""


# Filesystem models
class FsNode(BaseModel):
    id: str
    type: str
    name: str
    path: str
    parent_path: str
    content: str
    is_daily: bool
    sort_order: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FsNodeRequest(BaseModel):
    type: str
    name: str
    parent_path: str = "/"
    content: str = ""
    is_daily: bool = False
    sort_order: int = 0


class MoveRequest(BaseModel):
    new_parent_path: str = ""
    new_name: str = ""


# Daily notes models
class DailyNote(BaseModel):
    id: str
    date: str
    name: str
    path: str
    content: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DailyYear(BaseModel):
    year: str
    notes: list[DailyNote]


class DailyListResponse(BaseModel):
    years: list[DailyYear]


class DailyContentRequest(BaseModel):
    content: str = ""
