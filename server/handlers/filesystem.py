from datetime import datetime
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from basidian.models import FsNode, FsNodeRequest, FsNodeUpdateRequest, MoveRequest

from ..db import generate_id, get_db

router = APIRouter()


def _build_path(parent_path: str, name: str) -> str:
    """Build full path from parent path and name."""
    if parent_path == "/":
        return f"/{name}"
    return f"{parent_path}/{name}"


def _row_to_node(row) -> FsNode:
    """Convert a database row to an FsNode model."""
    created = row["created"] if row["created"] else None
    updated = row["updated"] if row["updated"] else None
    return FsNode(
        id=row["id"],
        type=row["type"],
        name=row["name"],
        path=row["path"],
        parent_path=row["parent_path"],
        content=row["content"],
        sort_order=row["sort_order"],
        created_at=created,
        updated_at=updated,
    )


@router.get("/api/fs/tree")
async def get_tree(
    parent_path: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FsNode]:
    """Get filesystem tree structure."""
    logger.info("GetTree: Fetching filesystem tree")

    if parent_path:
        async with db.execute(
            """
            SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
            FROM fs_nodes
            WHERE parent_path = ?
            ORDER BY type DESC, sort_order ASC, name ASC
            """,
            (parent_path,),
        ) as cursor:
            rows = await cursor.fetchall()
    else:
        async with db.execute("""
            SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
            FROM fs_nodes
            ORDER BY type DESC, sort_order ASC, name ASC
        """) as cursor:
            rows = await cursor.fetchall()

    nodes = [_row_to_node(row) for row in rows]
    logger.info(f"GetTree: Found {len(nodes)} nodes")
    return nodes


@router.get("/api/fs/node")
async def get_node(
    path: str = Query(...),
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Get a single node by path."""
    async with db.execute(
        """
        SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
        FROM fs_nodes
        WHERE path = ?
        """,
        (path,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    return _row_to_node(row)


@router.get("/api/fs/node/{node_id}")
async def get_node_by_id(
    node_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Get a single node by ID."""
    async with db.execute(
        """
        SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
        FROM fs_nodes
        WHERE id = ?
        """,
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    return _row_to_node(row)


@router.post("/api/fs/node", status_code=201)
async def create_node(
    req: FsNodeRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Create a new file or folder."""
    if req.type not in ("folder", "file"):
        raise HTTPException(status_code=400, detail="Type must be 'folder' or 'file'")

    name = req.name.strip() if req.name else ""
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    parent_path = req.parent_path if req.parent_path else "/"

    # Check if parent exists (unless parent is root)
    if parent_path != "/":
        async with db.execute(
            "SELECT 1 FROM fs_nodes WHERE path = ? AND type = 'folder'",
            (parent_path,),
        ) as cursor:
            if await cursor.fetchone() is None:
                raise HTTPException(status_code=400, detail="Parent folder not found")

    # Build the full path
    node_path = _build_path(parent_path, name)

    # Check if path already exists
    async with db.execute(
        "SELECT 1 FROM fs_nodes WHERE path = ?", (node_path,)
    ) as cursor:
        if await cursor.fetchone() is not None:
            raise HTTPException(status_code=409, detail="Path already exists")

    node_id = generate_id()
    now = datetime.now().isoformat()

    await db.execute(
        """
        INSERT INTO fs_nodes (id, type, name, path, parent_path, content, is_daily, sort_order, created, updated)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        """,
        (
            node_id,
            req.type,
            name,
            node_path,
            parent_path,
            req.content,
            req.sort_order,
            now,
            now,
        ),
    )
    await db.commit()

    logger.info(f"CreateNode: Created {req.type} at {node_path}")
    return FsNode(
        id=node_id,
        type=req.type,
        name=name,
        path=node_path,
        parent_path=parent_path,
        content=req.content,
        sort_order=req.sort_order,
        created_at=now,
        updated_at=now,
    )


@router.put("/api/fs/node/{node_id}")
async def update_node(
    node_id: str,
    req: FsNodeUpdateRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Update an existing node."""
    # Check if node exists and get current values
    async with db.execute(
        "SELECT type, name, content, sort_order FROM fs_nodes WHERE id = ?",
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    new_name = req.name if req.name is not None else row["name"]
    new_content = req.content if req.content is not None else row["content"]
    new_sort_order = req.sort_order if req.sort_order is not None else row["sort_order"]

    now = datetime.now().isoformat()

    await db.execute(
        """
        UPDATE fs_nodes
        SET name = ?, content = ?, sort_order = ?, updated = ?
        WHERE id = ?
        """,
        (new_name, new_content, new_sort_order, now, node_id),
    )
    await db.commit()

    # Fetch updated node
    async with db.execute(
        """
        SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
        FROM fs_nodes WHERE id = ?
        """,
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    return _row_to_node(row)


@router.delete("/api/fs/node/{node_id}", status_code=204)
async def delete_node(
    node_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> None:
    """Delete a node (and children if folder)."""
    # Get node info
    async with db.execute(
        "SELECT path, type FROM fs_nodes WHERE id = ?",
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    node_path = row["path"]
    node_type = row["type"]

    # If it's a folder, delete all children first
    if node_type == "folder":
        await db.execute(
            "DELETE FROM fs_nodes WHERE path LIKE ?",
            (f"{node_path}/%",),
        )

    # Delete the node itself
    await db.execute("DELETE FROM fs_nodes WHERE id = ?", (node_id,))
    await db.commit()

    logger.info(f"DeleteNode: Deleted {node_path}")


@router.post("/api/fs/move/{node_id}")
async def move_node(
    node_id: str,
    req: MoveRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Move or rename a node."""
    # Get current node info
    async with db.execute(
        "SELECT path, name, parent_path, type FROM fs_nodes WHERE id = ?",
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    old_path = row["path"]
    old_name = row["name"]
    old_parent_path = row["parent_path"]
    node_type = row["type"]

    new_name = req.new_name.strip() if req.new_name else old_name
    new_parent_path = req.new_parent_path if req.new_parent_path else old_parent_path
    new_path = _build_path(new_parent_path, new_name)

    # Check if new path already exists
    if new_path != old_path:
        async with db.execute(
            "SELECT 1 FROM fs_nodes WHERE path = ?", (new_path,)
        ) as cursor:
            if await cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409, detail="Destination path already exists"
                )

    now = datetime.now().isoformat()

    # Update the node
    await db.execute(
        """
        UPDATE fs_nodes
        SET name = ?, path = ?, parent_path = ?, updated = ?
        WHERE id = ?
        """,
        (new_name, new_path, new_parent_path, now, node_id),
    )

    # If it's a folder, update all children paths
    if node_type == "folder":
        async with db.execute(
            "SELECT id, path, parent_path FROM fs_nodes WHERE path LIKE ?",
            (f"{old_path}/%",),
        ) as cursor:
            children = await cursor.fetchall()

        for child in children:
            child_old_path = child["path"]
            child_old_parent = child["parent_path"]

            child_new_path = child_old_path.replace(old_path, new_path, 1)
            child_new_parent = child_old_parent.replace(old_path, new_path, 1)
            if child_old_parent == old_path:
                child_new_parent = new_path

            await db.execute(
                """
                UPDATE fs_nodes SET path = ?, parent_path = ?, updated = ? WHERE id = ?
                """,
                (child_new_path, child_new_parent, now, child["id"]),
            )

    await db.commit()

    # Fetch updated node
    async with db.execute(
        """
        SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
        FROM fs_nodes WHERE id = ?
        """,
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    logger.info(f"MoveNode: Moved {old_path} to {new_path}")
    return _row_to_node(row)


@router.get("/api/fs/search")
async def search_files(
    q: str = Query(..., min_length=1),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FsNode]:
    """Search for files containing the query."""
    search_pattern = f"%{q}%"

    async with db.execute(
        """
        SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
        FROM fs_nodes
        WHERE type = 'file' AND (name LIKE ? OR content LIKE ?)
        ORDER BY updated DESC
        """,
        (search_pattern, search_pattern),
    ) as cursor:
        rows = await cursor.fetchall()

    return [_row_to_node(row) for row in rows]
