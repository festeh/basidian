import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from .. import database as db
from ..models import DailyContentRequest, DailyListResponse, DailyNote, DailyYear

router = APIRouter()
logger = logging.getLogger(__name__)


def _date_to_path(date_str: str) -> str:
    """Convert YYYY-MM-DD to /daily/YYYY-MM-DD.md path."""
    return f"/daily/{date_str}.md"


async def _ensure_daily_folder() -> None:
    """Create the /daily folder if it doesn't exist."""
    assert db.db is not None

    async with db.db.execute(
        "SELECT 1 FROM fs_nodes WHERE path = '/daily'"
    ) as cursor:
        if await cursor.fetchone() is None:
            folder_id = db.generate_id()
            now = datetime.now().isoformat()
            await db.db.execute(
                """
                INSERT INTO fs_nodes (id, type, name, path, parent_path, content, is_daily, sort_order, created, updated)
                VALUES (?, 'folder', 'daily', '/daily', '/', '', 0, 0, ?, ?)
                """,
                (folder_id, now, now),
            )
            await db.db.commit()
            logger.info("Created /daily folder")


@router.get("/api/daily/{date}")
async def get_daily_file(date: str) -> JSONResponse:
    """Get a daily note for a specific date, creates if not exists."""
    # Validate date format
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    assert db.db is not None

    path = _date_to_path(date)
    name = f"{date}.md"

    # Check if note exists
    async with db.db.execute(
        """
        SELECT id, path, name, content, created, updated
        FROM fs_nodes
        WHERE path = ? AND is_daily = 1
        """,
        (path,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        # Create new daily note
        await _ensure_daily_folder()

        note_id = db.generate_id()
        now = datetime.now().isoformat()
        content = f"# {parsed_date.strftime('%B %d, %Y')}\n\n"

        await db.db.execute(
            """
            INSERT INTO fs_nodes (id, type, name, path, parent_path, content, is_daily, sort_order, created, updated)
            VALUES (?, 'file', ?, ?, '/daily', ?, 1, 0, ?, ?)
            """,
            (note_id, name, path, content, now, now),
        )
        await db.db.commit()

        logger.info(f"Created daily note: {path}")
        return JSONResponse(
            status_code=201,
            content=DailyNote(
                id=note_id,
                date=date,
                name=name,
                path=path,
                content=content,
                created_at=now,
                updated_at=now,
            ).model_dump(),
        )

    # Return existing note
    created = row["created"] if row["created"] else None
    updated = row["updated"] if row["updated"] else None

    return JSONResponse(
        status_code=200,
        content=DailyNote(
            id=row["id"],
            date=date,
            name=row["name"],
            path=row["path"],
            content=row["content"],
            created_at=created,
            updated_at=updated,
        ).model_dump(),
    )


@router.put("/api/daily/{date}")
async def update_daily_file(date: str, req: DailyContentRequest) -> JSONResponse:
    """Update a daily note's content."""
    # Validate date format
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    assert db.db is not None

    path = _date_to_path(date)
    name = f"{date}.md"
    now = datetime.now().isoformat()

    # Check if exists
    async with db.db.execute(
        "SELECT id FROM fs_nodes WHERE path = ? AND is_daily = 1", (path,)
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        # Create new
        await _ensure_daily_folder()

        note_id = db.generate_id()
        content = req.content if req.content else f"# {parsed_date.strftime('%B %d, %Y')}\n\n"

        await db.db.execute(
            """
            INSERT INTO fs_nodes (id, type, name, path, parent_path, content, is_daily, sort_order, created, updated)
            VALUES (?, 'file', ?, ?, '/daily', ?, 1, 0, ?, ?)
            """,
            (note_id, name, path, content, now, now),
        )
        await db.db.commit()

        logger.info(f"Created daily note: {path}")
        return JSONResponse(
            status_code=201,
            content=DailyNote(
                id=note_id,
                date=date,
                name=name,
                path=path,
                content=content,
                created_at=now,
                updated_at=now,
            ).model_dump(),
        )

    # Update existing
    note_id = row["id"]
    await db.db.execute(
        "UPDATE fs_nodes SET content = ?, updated = ? WHERE id = ?",
        (req.content, now, note_id),
    )
    await db.db.commit()

    # Fetch updated
    async with db.db.execute(
        """
        SELECT id, path, name, content, created, updated
        FROM fs_nodes WHERE id = ?
        """,
        (note_id,),
    ) as cursor:
        row = await cursor.fetchone()

    created = row["created"] if row["created"] else None
    updated = row["updated"] if row["updated"] else None

    logger.info(f"Updated daily note: {path}")
    return JSONResponse(
        status_code=200,
        content=DailyNote(
            id=row["id"],
            date=date,
            name=row["name"],
            path=row["path"],
            content=row["content"],
            created_at=created,
            updated_at=updated,
        ).model_dump(),
    )


@router.get("/api/daily")
async def list_daily_files() -> DailyListResponse:
    """List all daily notes organized by year."""
    assert db.db is not None

    async with db.db.execute("""
        SELECT id, path, name, created, updated
        FROM fs_nodes
        WHERE is_daily = 1 AND type = 'file'
        ORDER BY path DESC
    """) as cursor:
        rows = await cursor.fetchall()

    # Group by year
    year_map: dict[str, list[DailyNote]] = {}

    for row in rows:
        path = row["path"]
        # Extract date from path: /daily/YYYY-MM-DD.md (length >= 20)
        if len(path) >= 20:
            date = path[7:17]  # Extract YYYY-MM-DD
            year = date[:4]

            created = row["created"] if row["created"] else None
            updated = row["updated"] if row["updated"] else None

            note = DailyNote(
                id=row["id"],
                date=date,
                name=row["name"],
                path=path,
                created_at=created,
                updated_at=updated,
            )

            if year not in year_map:
                year_map[year] = []
            year_map[year].append(note)

    # Convert to response format
    years = []
    for year, notes in sorted(year_map.items(), reverse=True):
        # Sort notes by date descending
        notes.sort(key=lambda n: n.date, reverse=True)
        years.append(DailyYear(year=year, notes=notes))

    return DailyListResponse(years=years)


@router.delete("/api/daily/{date}", status_code=204)
async def delete_daily_file(date: str) -> None:
    """Delete a daily note."""
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    assert db.db is not None

    path = _date_to_path(date)

    cursor = await db.db.execute(
        "DELETE FROM fs_nodes WHERE path = ? AND is_daily = 1", (path,)
    )
    await db.db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Daily note not found")

    logger.info(f"Deleted daily note: {path}")


@router.get("/api/daily/config")
async def get_daily_config() -> dict:
    """Get the daily notes configuration."""
    assert db.db is not None

    async with db.db.execute(
        "SELECT COUNT(*) as count FROM fs_nodes WHERE is_daily = 1 AND type = 'file'"
    ) as cursor:
        row = await cursor.fetchone()

    return {"storage": "sqlite", "count": row["count"]}


@router.put("/api/daily/config")
async def set_daily_config() -> dict:
    """Set daily notes configuration (no-op for SQLite)."""
    return {"storage": "sqlite", "message": "Daily notes are stored in SQLite database"}
