from datetime import datetime, timezone
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from loguru import logger

from basidian.models import FsNode, FsNodeRequest, FsNodeUpdateRequest, MoveRequest
from basidian.server.metadata import MetadataIndex

from ..db import generate_id, get_db, utcnow_iso
from .history import create_version_if_changed

INACTIVITY_THRESHOLD_MINUTES = 10

router = APIRouter()

# Column lists for different query types
_TREE_COLS = "id, parent_id, type, name, path, sort_order, created_at, updated_at"
_FULL_COLS = (
    "n.id, n.parent_id, n.type, n.name, n.path, n.sort_order, n.created_at, n.updated_at, "
    "c.body AS content"
)


def _build_path(parent_path: str, name: str) -> str:
    """Build full path from parent path and name."""
    if parent_path == "/":
        return f"/{name}"
    return f"{parent_path}/{name}"


async def _get_parent_path(db: aiosqlite.Connection, parent_id: str | None) -> str:
    """Get the path of a parent node, or '/' for root."""
    if parent_id is None:
        return "/"
    async with db.execute(
        "SELECT path FROM fs_nodes WHERE id = ?", (parent_id,)
    ) as cursor:
        row = await cursor.fetchone()
    return row["path"] if row else "/"


def _row_to_node(row, include_content: bool = False) -> FsNode:
    """Convert a database row to an FsNode model."""
    parent_id = row["parent_id"]
    return FsNode(
        id=row["id"],
        parent_id=parent_id,
        parent_path="",  # computed below if needed
        type=row["type"],
        name=row["name"],
        path=row["path"],
        content=row["content"] if include_content and "content" in row.keys() else None,
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _compute_parent_path(path: str) -> str:
    """Derive parent_path from the node's path."""
    if "/" not in path.lstrip("/"):
        return "/"
    return path.rsplit("/", 1)[0]


def _enrich_parent_paths(nodes: list[FsNode]) -> list[FsNode]:
    """Fill in parent_path for a list of nodes using their paths."""
    for node in nodes:
        node.parent_path = _compute_parent_path(node.path)
    return nodes


@router.get("/api/fs/tree")
async def get_tree(
    parent_path: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FsNode]:
    """Get filesystem tree structure. Returns nodes without content."""
    logger.info("GetTree: Fetching filesystem tree")

    if parent_path:
        # Find the parent node to get its ID
        async with db.execute(
            "SELECT id FROM fs_nodes WHERE path = ? AND deleted_at IS NULL",
            (parent_path,),
        ) as cursor:
            parent_row = await cursor.fetchone()

        if parent_row:
            async with db.execute(
                f"""
                SELECT {_TREE_COLS}
                FROM fs_nodes
                WHERE parent_id = ? AND deleted_at IS NULL
                ORDER BY type DESC, sort_order ASC, name ASC
                """,
                (parent_row["id"],),
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            rows = []
    else:
        async with db.execute(f"""
            SELECT {_TREE_COLS}
            FROM fs_nodes
            WHERE deleted_at IS NULL
            ORDER BY type DESC, sort_order ASC, name ASC
        """) as cursor:
            rows = await cursor.fetchall()

    nodes = [_row_to_node(row) for row in rows]
    _enrich_parent_paths(nodes)
    logger.info(f"GetTree: Found {len(nodes)} nodes")
    return nodes


@router.get("/api/fs/node")
async def get_node(
    path: str = Query(...),
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Get a single node by path, including content for files."""
    async with db.execute(
        f"""
        SELECT {_FULL_COLS}
        FROM fs_nodes n
        LEFT JOIN fs_content c ON c.node_id = n.id
        WHERE n.path = ? AND n.deleted_at IS NULL
        """,
        (path,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    node = _row_to_node(row, include_content=True)
    node.parent_path = _compute_parent_path(node.path)
    return node


@router.get("/api/fs/node/{node_id}")
async def get_node_by_id(
    node_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Get a single node by ID, including content for files."""
    async with db.execute(
        f"""
        SELECT {_FULL_COLS}
        FROM fs_nodes n
        LEFT JOIN fs_content c ON c.node_id = n.id
        WHERE n.id = ? AND n.deleted_at IS NULL
        """,
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    node = _row_to_node(row, include_content=True)
    node.parent_path = _compute_parent_path(node.path)
    return node


def _get_index(request: Request) -> MetadataIndex:
    return request.app.state.metadata_index


@router.post("/api/fs/node", status_code=201)
async def create_node(
    req: FsNodeRequest,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Create a new file or folder."""
    if req.type not in ("folder", "file"):
        raise HTTPException(status_code=400, detail="Type must be 'folder' or 'file'")

    name = req.name.strip() if req.name else ""
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    parent_path = req.parent_path if req.parent_path else "/"

    # Resolve parent_id from parent_path
    parent_id = None
    if parent_path != "/":
        async with db.execute(
            "SELECT id FROM fs_nodes WHERE path = ? AND type = 'folder' AND deleted_at IS NULL",
            (parent_path,),
        ) as cursor:
            parent_row = await cursor.fetchone()
            if parent_row is None:
                raise HTTPException(status_code=400, detail="Parent folder not found")
            parent_id = parent_row["id"]

    # Build the full path
    node_path = _build_path(parent_path, name)

    # Check if path already exists
    async with db.execute(
        "SELECT 1 FROM fs_nodes WHERE path = ? AND deleted_at IS NULL", (node_path,)
    ) as cursor:
        if await cursor.fetchone() is not None:
            raise HTTPException(status_code=409, detail="Path already exists")

    node_id = generate_id()
    now = utcnow_iso()

    # Insert tree node
    await db.execute(
        """
        INSERT INTO fs_nodes (id, parent_id, type, name, path, sort_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (node_id, parent_id, req.type, name, node_path, req.sort_order, now, now),
    )

    # Insert content row for files
    content = ""
    if req.type == "file":
        content = req.content
        await db.execute(
            "INSERT INTO fs_content (node_id, body, updated_at) VALUES (?, ?, ?)",
            (node_id, content, now),
        )

    await db.commit()

    # Update metadata index for new files
    if req.type == "file":
        _get_index(request).update_node(node_id, name, node_path, content)

    logger.info(f"CreateNode: Created {req.type} at {node_path}")
    return FsNode(
        id=node_id,
        parent_id=parent_id,
        parent_path=parent_path,
        type=req.type,
        name=name,
        path=node_path,
        content=content if req.type == "file" else None,
        sort_order=req.sort_order,
        created_at=now,
        updated_at=now,
    )


@router.put("/api/fs/node/{node_id}")
async def update_node(
    node_id: str,
    req: FsNodeUpdateRequest,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Update an existing node."""
    # Get current node metadata
    async with db.execute(
        "SELECT type, name, sort_order, updated_at FROM fs_nodes WHERE id = ?",
        (node_id,),
    ) as cursor:
        node_row = await cursor.fetchone()

    if node_row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    new_name = req.name if req.name is not None else node_row["name"]
    new_sort_order = (
        req.sort_order if req.sort_order is not None else node_row["sort_order"]
    )

    now_dt = datetime.now(timezone.utc)
    now_iso = utcnow_iso()

    # Handle content update (files only)
    content_changing = False
    if req.content is not None and node_row["type"] == "file":
        # Get current content from fs_content
        async with db.execute(
            "SELECT body, updated_at FROM fs_content WHERE node_id = ?", (node_id,)
        ) as cursor:
            content_row = await cursor.fetchone()

        old_body = content_row["body"] if content_row else ""
        content_changing = req.content != old_body

        if content_changing and content_row and content_row["updated_at"]:
            # Auto-snapshot on inactivity gap
            try:
                last_updated = datetime.fromisoformat(
                    content_row["updated_at"]
                ).replace(tzinfo=timezone.utc)
                gap = now_dt - last_updated
                if gap.total_seconds() >= INACTIVITY_THRESHOLD_MINUTES * 60:
                    await create_version_if_changed(
                        db, node_id, old_body, content_row["updated_at"]
                    )
            except (ValueError, TypeError):
                pass

        if content_row:
            await db.execute(
                "UPDATE fs_content SET body = ?, updated_at = ? WHERE node_id = ?",
                (req.content, now_iso, node_id),
            )
        else:
            # Content row missing (shouldn't happen, but handle gracefully)
            await db.execute(
                "INSERT INTO fs_content (node_id, body, updated_at) VALUES (?, ?, ?)",
                (node_id, req.content, now_iso),
            )

    # Update tree node metadata (always update updated_at to keep recent files in sync)
    await db.execute(
        """
        UPDATE fs_nodes
        SET name = ?, sort_order = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_name, new_sort_order, now_iso, node_id),
    )
    await db.commit()

    # Update metadata index if content changed
    if content_changing and req.content is not None:
        async with db.execute(
            "SELECT name, path FROM fs_nodes WHERE id = ?", (node_id,)
        ) as cursor:
            node_info = await cursor.fetchone()
        if node_info:
            _get_index(request).update_node(
                node_id, node_info["name"], node_info["path"], req.content
            )

    # Fetch and return updated node
    async with db.execute(
        f"""
        SELECT {_FULL_COLS}
        FROM fs_nodes n
        LEFT JOIN fs_content c ON c.node_id = n.id
        WHERE n.id = ?
        """,
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    node = _row_to_node(row, include_content=True)
    node.parent_path = _compute_parent_path(node.path)
    return node


@router.delete("/api/fs/node/{node_id}", status_code=204)
async def delete_node(
    node_id: str,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> None:
    """Soft-delete a node. Sets deleted_at on the node and all descendants."""
    async with db.execute(
        "SELECT path, type FROM fs_nodes WHERE id = ? AND deleted_at IS NULL",
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    node_path = row["path"]
    now = utcnow_iso()
    index = _get_index(request)

    # Soft-delete the node and all descendants
    await db.execute(
        """
        WITH RECURSIVE descendants AS (
            SELECT id FROM fs_nodes WHERE id = ?
            UNION ALL
            SELECT n.id FROM fs_nodes n JOIN descendants d ON n.parent_id = d.id
        )
        UPDATE fs_nodes SET deleted_at = ?, updated_at = ?
        WHERE id IN (SELECT id FROM descendants) AND deleted_at IS NULL
        """,
        (node_id, now, now),
    )
    await db.commit()

    # Collect all affected IDs for index cleanup
    async with db.execute(
        """
        WITH RECURSIVE descendants AS (
            SELECT id FROM fs_nodes WHERE id = ?
            UNION ALL
            SELECT n.id FROM fs_nodes n JOIN descendants d ON n.parent_id = d.id
        )
        SELECT id FROM descendants
        """,
        (node_id,),
    ) as cursor:
        all_ids = [r["id"] for r in await cursor.fetchall()]

    for nid in all_ids:
        index.remove_node(nid)

    logger.info(f"DeleteNode: Soft-deleted {node_path}")


@router.post("/api/fs/move/{node_id}")
async def move_node(
    node_id: str,
    req: MoveRequest,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> FsNode:
    """Move or rename a node."""
    # Get current node info
    async with db.execute(
        "SELECT id, parent_id, path, name, type FROM fs_nodes WHERE id = ? AND deleted_at IS NULL",
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Node not found")

    old_path = row["path"]
    old_name = row["name"]
    old_parent_id = row["parent_id"]
    node_type = row["type"]

    # Resolve new parent
    new_name = req.new_name.strip() if req.new_name else old_name
    new_parent_id = old_parent_id
    new_parent_path = await _get_parent_path(db, old_parent_id)

    if req.new_parent_path:
        new_parent_path = req.new_parent_path
        if new_parent_path == "/":
            new_parent_id = None
        else:
            async with db.execute(
                "SELECT id FROM fs_nodes WHERE path = ? AND type = 'folder' AND deleted_at IS NULL",
                (new_parent_path,),
            ) as cursor:
                parent_row = await cursor.fetchone()
                if parent_row is None:
                    raise HTTPException(
                        status_code=400, detail="Target folder not found"
                    )
                new_parent_id = parent_row["id"]

    new_path = _build_path(new_parent_path, new_name)

    # Check if new path already exists
    if new_path != old_path:
        async with db.execute(
            "SELECT 1 FROM fs_nodes WHERE path = ? AND deleted_at IS NULL", (new_path,)
        ) as cursor:
            if await cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409, detail="Destination path already exists"
                )

    now = utcnow_iso()

    # Update the node itself (O(1) for parent_id change)
    await db.execute(
        """
        UPDATE fs_nodes
        SET parent_id = ?, name = ?, path = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_parent_id, new_name, new_path, now, node_id),
    )

    # If it's a folder and path changed, update all descendant paths
    if node_type == "folder" and new_path != old_path:
        # Use recursive CTE to find all descendants and update paths
        async with db.execute(
            """
            WITH RECURSIVE descendants AS (
                SELECT id, path, parent_id FROM fs_nodes WHERE parent_id = ?
                UNION ALL
                SELECT n.id, n.path, n.parent_id
                FROM fs_nodes n
                JOIN descendants d ON n.parent_id = d.id
            )
            SELECT id, path FROM descendants
            """,
            (node_id,),
        ) as cursor:
            children = await cursor.fetchall()

        for child in children:
            child_new_path = new_path + child["path"][len(old_path) :]
            await db.execute(
                "UPDATE fs_nodes SET path = ?, updated_at = ? WHERE id = ?",
                (child_new_path, now, child["id"]),
            )

    await db.commit()

    # Update metadata index for path changes
    index = _get_index(request)
    index.on_move(node_id, old_path, new_path, new_name)

    # Fetch updated node
    async with db.execute(
        f"""
        SELECT {_FULL_COLS}
        FROM fs_nodes n
        LEFT JOIN fs_content c ON c.node_id = n.id
        WHERE n.id = ?
        """,
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()

    node = _row_to_node(row, include_content=True)
    node.parent_path = new_parent_path
    logger.info(f"MoveNode: Moved {old_path} to {new_path}")
    return node


@router.get("/api/fs/recent")
async def get_recent_files(
    limit: int = Query(default=10, ge=1, le=50),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FsNode]:
    """Get recently updated files (without content)."""
    async with db.execute(
        f"""
        SELECT {_TREE_COLS}
        FROM fs_nodes
        WHERE type = 'file' AND updated_at IS NOT NULL AND deleted_at IS NULL
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ) as cursor:
        rows = await cursor.fetchall()

    nodes = [_row_to_node(row) for row in rows]
    return _enrich_parent_paths(nodes)


@router.get("/api/fs/search")
async def search_files(
    q: str = Query(..., min_length=1),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FsNode]:
    """Search for files containing the query."""
    search_pattern = f"%{q}%"

    async with db.execute(
        f"""
        SELECT {_FULL_COLS}
        FROM fs_nodes n
        LEFT JOIN fs_content c ON c.node_id = n.id
        WHERE n.type = 'file' AND n.deleted_at IS NULL AND (n.name LIKE ? OR c.body LIKE ?)
        ORDER BY n.updated_at DESC
        """,
        (search_pattern, search_pattern),
    ) as cursor:
        rows = await cursor.fetchall()

    nodes = [_row_to_node(row, include_content=True) for row in rows]
    return _enrich_parent_paths(nodes)
