"""File version history endpoints."""

import difflib
from datetime import datetime, timedelta, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from basidian.models import FileVersion, FileVersionSummary

from ..db import generate_id, get_db, utcnow_iso

router = APIRouter()


async def _get_node_content(db: aiosqlite.Connection, node_id: str) -> str | None:
    """Get current content of a node from fs_content, or None if not found."""
    async with db.execute(
        "SELECT body FROM fs_content WHERE node_id = ?", (node_id,)
    ) as cursor:
        row = await cursor.fetchone()
    return row["body"] if row else None


async def _get_latest_version_body(
    db: aiosqlite.Connection, node_id: str
) -> str | None:
    """Get body of the most recent version, or None if no versions exist."""
    async with db.execute(
        "SELECT body FROM fs_versions WHERE node_id = ? ORDER BY created_at DESC LIMIT 1",
        (node_id,),
    ) as cursor:
        row = await cursor.fetchone()
    return row["body"] if row else None


async def create_version_if_changed(
    db: aiosqlite.Connection, node_id: str, body: str, timestamp: str | None = None
) -> bool:
    """Create a version snapshot if body differs from the latest version.

    Returns True if a version was created.
    """
    latest = await _get_latest_version_body(db, node_id)
    if latest == body:
        return False

    version_id = generate_id()
    now = timestamp or utcnow_iso()
    await db.execute(
        "INSERT INTO fs_versions (id, node_id, body, created_at) VALUES (?, ?, ?, ?)",
        (version_id, node_id, body, now),
    )
    return True


def _compute_diff_summary(old_body: str, new_body: str) -> tuple[int, int]:
    """Compute lines added/removed between two bodies."""
    old_lines = old_body.splitlines(keepends=True)
    new_lines = new_body.splitlines(keepends=True)
    added = 0
    removed = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, old_lines, new_lines
    ).get_opcodes():
        if tag == "replace":
            removed += i2 - i1
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "insert":
            added += j2 - j1
    return added, removed


@router.get("/api/fs/node/{node_id}/versions")
async def list_versions(
    node_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FileVersionSummary]:
    """List all versions for a file, most recent first."""
    async with db.execute(
        "SELECT id, node_id, body, created_at FROM fs_versions WHERE node_id = ? ORDER BY created_at DESC",
        (node_id,),
    ) as cursor:
        rows = await cursor.fetchall()

    if not rows:
        return []

    # Get current content to diff against the most recent version
    current_body = await _get_node_content(db, node_id)

    summaries: list[FileVersionSummary] = []
    for i, row in enumerate(rows):
        # Compare each version against the one before it (newer content)
        if i == 0:
            # Most recent version: diff against current file content
            newer = current_body or ""
        else:
            newer = rows[i - 1]["body"]

        added, removed = _compute_diff_summary(row["body"], newer)
        summaries.append(
            FileVersionSummary(
                id=row["id"],
                node_id=row["node_id"],
                created_at=row["created_at"],
                lines_added=added,
                lines_removed=removed,
            )
        )

    return summaries


@router.get("/api/fs/node/{node_id}/versions/{version_id}")
async def get_version(
    node_id: str,
    version_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> FileVersion:
    """Get a specific version's full content."""
    async with db.execute(
        "SELECT id, node_id, body, created_at FROM fs_versions WHERE id = ? AND node_id = ?",
        (version_id, node_id),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Version not found")

    return FileVersion(
        id=row["id"],
        node_id=row["node_id"],
        body=row["body"],
        created_at=row["created_at"],
    )


@router.post("/api/fs/node/{node_id}/snapshot", status_code=201)
async def snapshot(
    node_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """Create a version snapshot of the current file content.

    Called by the frontend on file switch and app close.
    Only creates a version if content has changed since the last version.
    """
    body = await _get_node_content(db, node_id)
    if body is None:
        raise HTTPException(status_code=404, detail="Node not found")

    created = await create_version_if_changed(db, node_id, body)
    if created:
        await db.commit()
        logger.info(f"Snapshot: Created version for node {node_id}")

    return {"created": created}


@router.post("/api/fs/node/{node_id}/restore/{version_id}")
async def restore_version(
    node_id: str,
    version_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> FileVersion:
    """Restore a file to a previous version.

    1. Snapshots the current content (so the restore is undoable)
    2. Replaces file content with the version's body
    3. Returns the restored version
    """
    # Get the version to restore
    async with db.execute(
        "SELECT body FROM fs_versions WHERE id = ? AND node_id = ?",
        (version_id, node_id),
    ) as cursor:
        version_row = await cursor.fetchone()

    if version_row is None:
        raise HTTPException(status_code=404, detail="Version not found")

    # Snapshot current content before restoring
    current_body = await _get_node_content(db, node_id)
    if current_body is None:
        raise HTTPException(status_code=404, detail="Node not found")

    await create_version_if_changed(db, node_id, current_body)

    # Update the file content
    now = utcnow_iso()
    await db.execute(
        "UPDATE fs_content SET body = ?, updated_at = ? WHERE node_id = ?",
        (version_row["body"], now, node_id),
    )

    # Also update fs_nodes.updated_at to keep recent files in sync
    await db.execute(
        "UPDATE fs_nodes SET updated_at = ? WHERE id = ?",
        (now, node_id),
    )

    # Create a version of the restored content too
    restore_version_id = generate_id()
    await db.execute(
        "INSERT INTO fs_versions (id, node_id, body, created_at) VALUES (?, ?, ?, ?)",
        (restore_version_id, node_id, version_row["body"], now),
    )

    await db.commit()
    logger.info(f"Restore: Restored node {node_id} to version {version_id}")

    return FileVersion(
        id=restore_version_id,
        node_id=node_id,
        body=version_row["body"],
        created_at=now,
    )


async def cleanup_versions(db: aiosqlite.Connection) -> int:
    """Clean up old versions per retention policy.

    - Keep all versions from the last 7 days
    - Keep one per day for 7-30 days
    - Keep one per week for older than 30 days
    - Delete the rest

    Returns the number of deleted versions.
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=7)).replace(tzinfo=None).isoformat()
    thirty_days_ago = (now - timedelta(days=30)).replace(tzinfo=None).isoformat()

    # Get all versions older than 7 days, grouped by node
    async with db.execute(
        "SELECT id, node_id, created_at FROM fs_versions WHERE created_at < ? ORDER BY node_id, created_at DESC",
        (seven_days_ago,),
    ) as cursor:
        old_versions = await cursor.fetchall()

    if not old_versions:
        return 0

    ids_to_delete: list[str] = []

    # Group by node_id
    by_node: dict[str, list] = {}
    for row in old_versions:
        by_node.setdefault(row["node_id"], []).append(row)

    for versions in by_node.values():
        # Split into 7-30 day range and 30+ day range
        mid_range = []  # 7-30 days
        old_range = []  # 30+ days

        for v in versions:
            if v["created_at"] >= thirty_days_ago:
                mid_range.append(v)
            else:
                old_range.append(v)

        # Mid range: keep one per day
        seen_days: set[str] = set()
        for v in mid_range:
            day = v["created_at"][:10]  # YYYY-MM-DD
            if day in seen_days:
                ids_to_delete.append(v["id"])
            else:
                seen_days.add(day)

        # Old range: keep one per week (ISO week)
        seen_weeks: set[str] = set()
        for v in old_range:
            dt = datetime.fromisoformat(v["created_at"])
            week = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
            if week in seen_weeks:
                ids_to_delete.append(v["id"])
            else:
                seen_weeks.add(week)

    if ids_to_delete:
        placeholders = ",".join("?" * len(ids_to_delete))
        await db.execute(
            f"DELETE FROM fs_versions WHERE id IN ({placeholders})",
            ids_to_delete,
        )
        await db.commit()

    logger.info(f"Cleanup: Deleted {len(ids_to_delete)} old versions")
    return len(ids_to_delete)
