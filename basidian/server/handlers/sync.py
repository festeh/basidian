"""Sync API endpoints for client-server data synchronization."""

from datetime import datetime
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, Request
from loguru import logger
from pydantic import BaseModel

from basidian.server.metadata import MetadataIndex

from ..db import get_db

router = APIRouter()


class SyncNodeRow(BaseModel):
    id: str
    parent_id: Optional[str] = None
    type: str
    name: str
    path: str
    sort_order: int = 0
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None


class SyncContentRow(BaseModel):
    node_id: str
    body: str
    updated_at: str


class SyncChangesResponse(BaseModel):
    nodes: list[SyncNodeRow]
    content: list[SyncContentRow]
    server_time: str


class SyncPushRequest(BaseModel):
    nodes: list[SyncNodeRow] = []
    content: list[SyncContentRow] = []


class SyncPushResult(BaseModel):
    id: str
    accepted: bool
    reason: Optional[str] = None
    server_updated_at: Optional[str] = None


class SyncPushResponse(BaseModel):
    results: list[SyncPushResult]
    server_time: str


@router.get("/api/sync/changes")
async def get_changes(
    since: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db),
) -> SyncChangesResponse:
    """Return all rows changed since the given timestamp.

    If `since` is omitted, returns everything (full sync).
    Includes soft-deleted nodes so clients can apply deletions.
    """
    server_time = datetime.now().isoformat()

    if since:
        logger.info(f"Sync pull: changes since {since}")
        async with db.execute(
            """
            SELECT id, parent_id, type, name, path, sort_order,
                   created_at, updated_at, deleted_at
            FROM fs_nodes
            WHERE updated_at > ? OR (deleted_at IS NOT NULL AND deleted_at > ?)
            """,
            (since, since),
        ) as cursor:
            node_rows = await cursor.fetchall()

        async with db.execute(
            "SELECT node_id, body, updated_at FROM fs_content WHERE updated_at > ?",
            (since,),
        ) as cursor:
            content_rows = await cursor.fetchall()
    else:
        logger.info("Sync pull: full sync (no since parameter)")
        async with db.execute(
            """
            SELECT id, parent_id, type, name, path, sort_order,
                   created_at, updated_at, deleted_at
            FROM fs_nodes
            """
        ) as cursor:
            node_rows = await cursor.fetchall()

        async with db.execute(
            "SELECT node_id, body, updated_at FROM fs_content"
        ) as cursor:
            content_rows = await cursor.fetchall()

    nodes = [
        SyncNodeRow(
            id=r["id"],
            parent_id=r["parent_id"],
            type=r["type"],
            name=r["name"],
            path=r["path"],
            sort_order=r["sort_order"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            deleted_at=r["deleted_at"],
        )
        for r in node_rows
    ]

    content = [
        SyncContentRow(
            node_id=r["node_id"],
            body=r["body"],
            updated_at=r["updated_at"],
        )
        for r in content_rows
    ]

    logger.info(f"Sync pull: {len(nodes)} nodes, {len(content)} content rows")
    return SyncChangesResponse(
        nodes=nodes, content=content, server_time=server_time
    )


def _get_index(request: Request) -> MetadataIndex:
    return request.app.state.metadata_index


@router.post("/api/sync/push")
async def push_changes(
    req: SyncPushRequest,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> SyncPushResponse:
    """Accept changed rows from a client. Last-write-wins by updated_at."""
    server_time = datetime.now().isoformat()
    results: list[SyncPushResult] = []
    index = _get_index(request)

    for node in req.nodes:
        # Check if this node exists on the server
        async with db.execute(
            "SELECT updated_at, deleted_at FROM fs_nodes WHERE id = ?", (node.id,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing is None:
            # New node — insert
            await db.execute(
                """
                INSERT INTO fs_nodes
                    (id, parent_id, type, name, path, sort_order, created_at, updated_at, deleted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node.id, node.parent_id, node.type, node.name, node.path,
                    node.sort_order, node.created_at, node.updated_at, node.deleted_at,
                ),
            )
            results.append(SyncPushResult(id=node.id, accepted=True))
        elif node.updated_at > existing["updated_at"]:
            # Client is newer — update
            await db.execute(
                """
                UPDATE fs_nodes
                SET parent_id = ?, type = ?, name = ?, path = ?, sort_order = ?,
                    created_at = ?, updated_at = ?, deleted_at = ?
                WHERE id = ?
                """,
                (
                    node.parent_id, node.type, node.name, node.path, node.sort_order,
                    node.created_at, node.updated_at, node.deleted_at, node.id,
                ),
            )
            results.append(SyncPushResult(id=node.id, accepted=True))

            # Update metadata index
            if node.deleted_at:
                index.remove_node(node.id)
        else:
            # Server is newer — reject
            results.append(SyncPushResult(
                id=node.id,
                accepted=False,
                reason="newer_on_server",
                server_updated_at=existing["updated_at"],
            ))

    for content in req.content:
        async with db.execute(
            "SELECT updated_at FROM fs_content WHERE node_id = ?", (content.node_id,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing is None:
            # New content row — insert
            await db.execute(
                "INSERT INTO fs_content (node_id, body, updated_at) VALUES (?, ?, ?)",
                (content.node_id, content.body, content.updated_at),
            )
            results.append(SyncPushResult(id=content.node_id, accepted=True))
        elif content.updated_at > existing["updated_at"]:
            # Client is newer — update
            await db.execute(
                "UPDATE fs_content SET body = ?, updated_at = ? WHERE node_id = ?",
                (content.body, content.updated_at, content.node_id),
            )
            results.append(SyncPushResult(id=content.node_id, accepted=True))

            # Update metadata index
            async with db.execute(
                "SELECT name, path FROM fs_nodes WHERE id = ?", (content.node_id,)
            ) as cursor:
                node_info = await cursor.fetchone()
            if node_info:
                index.update_node(content.node_id, node_info["name"], node_info["path"], content.body)
        else:
            results.append(SyncPushResult(
                id=content.node_id,
                accepted=False,
                reason="newer_on_server",
                server_updated_at=existing["updated_at"],
            ))

    await db.commit()

    accepted = sum(1 for r in results if r.accepted)
    rejected = sum(1 for r in results if not r.accepted)
    logger.info(f"Sync push: {accepted} accepted, {rejected} rejected")

    return SyncPushResponse(results=results, server_time=server_time)
