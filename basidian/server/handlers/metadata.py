"""Metadata API endpoints — tags, links, backlinks, daily dates.

All data served from the in-memory MetadataIndex, not from SQLite.
"""

import aiosqlite
from fastapi import APIRouter, Depends, Query, Request

from basidian.models import FsNode
from basidian.server.metadata import MetadataIndex

from ..db import get_db

router = APIRouter()


def _get_index(request: Request) -> MetadataIndex:
    """Get the metadata index from app state."""
    return request.app.state.metadata_index


@router.get("/api/fs/tags")
async def list_tags(
    request: Request,
) -> list[dict]:
    """List all tags with usage counts."""
    index = _get_index(request)
    return index.get_tags_with_counts()


@router.get("/api/fs/tags/{tag}")
async def get_nodes_by_tag(
    tag: str,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FsNode]:
    """Get nodes with a given tag (without content)."""
    index = _get_index(request)
    node_ids = index.get_nodes_for_tag(tag)
    if not node_ids:
        return []

    placeholders = ",".join("?" * len(node_ids))
    async with db.execute(
        f"""
        SELECT id, parent_id, type, name, path, sort_order, created_at, updated_at
        FROM fs_nodes
        WHERE id IN ({placeholders})
        ORDER BY name ASC
        """,
        list(node_ids),
    ) as cursor:
        rows = await cursor.fetchall()

    return [
        FsNode(
            id=row["id"],
            parent_id=row["parent_id"],
            parent_path=_compute_parent_path(row["path"]),
            type=row["type"],
            name=row["name"],
            path=row["path"],
            sort_order=row["sort_order"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.get("/api/fs/backlinks")
async def get_backlinks(
    request: Request,
    path: str = Query(...),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    """Get nodes that link to a given path."""
    index = _get_index(request)
    source_ids = index.get_backlinks(path)
    if not source_ids:
        return []

    placeholders = ",".join("?" * len(source_ids))
    async with db.execute(
        f"SELECT id, name, path FROM fs_nodes WHERE id IN ({placeholders})",
        list(source_ids),
    ) as cursor:
        rows = await cursor.fetchall()

    return [
        {"source_id": row["id"], "source_name": row["name"], "source_path": row["path"]}
        for row in rows
    ]


@router.get("/api/fs/links/{node_id}")
async def get_links(
    node_id: str,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    """Get outgoing links from a node."""
    index = _get_index(request)
    target_paths = index.get_links(node_id)
    if not target_paths:
        return []

    results = []
    for target_path in target_paths:
        # Try to resolve the target path to a node
        # Check both with and without leading slash
        resolved = None
        for path_variant in [target_path, f"/{target_path}", target_path.lstrip("/")]:
            async with db.execute(
                "SELECT id, name FROM fs_nodes WHERE path = ?", (path_variant,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    resolved = {"target_id": row["id"], "target_name": row["name"]}
                    break

        results.append(
            {
                "target_path": target_path,
                **(resolved or {"target_id": None, "target_name": None}),
            }
        )

    return results


@router.get("/api/fs/daily-dates")
async def get_daily_dates(
    request: Request,
) -> dict[str, str]:
    """Get map of daily dates to node IDs (for calendar view)."""
    index = _get_index(request)
    return index.daily_dates


def _compute_parent_path(path: str) -> str:
    """Derive parent_path from the node's path."""
    if "/" not in path.lstrip("/"):
        return "/"
    return path.rsplit("/", 1)[0]
