from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from .. import database as db
from ..models import Note, NoteRequest

router = APIRouter()


def _row_to_note(row) -> Note:
    """Convert a database row to a Note model."""
    created = row["created"] if row["created"] else None
    updated = row["updated"] if row["updated"] else None
    return Note(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        date=row["date"],
        created_at=created,
        updated_at=updated,
    )


@router.get("/api/notes")
async def get_notes() -> list[Note]:
    """Fetch all notes ordered by date descending."""
    logger.info("GetNotes: Fetching all notes")

    assert db.db is not None
    async with db.db.execute("""
        SELECT id, title, content, date, created, updated
        FROM notes
        ORDER BY date DESC
    """) as cursor:
        rows = await cursor.fetchall()

    notes = [_row_to_note(row) for row in rows]
    logger.info(f"GetNotes: Found {len(notes)} notes")
    return notes


@router.post("/api/notes", status_code=201)
async def create_note(req: NoteRequest) -> Note:
    """Create a new note."""
    assert db.db is not None

    note_id = db.generate_id()
    now = datetime.now().isoformat()

    date = req.date if req.date else datetime.now().strftime("%Y-%m-%d")

    await db.db.execute(
        """
        INSERT INTO notes (id, title, content, date, created, updated)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (note_id, req.title, req.content, date, now, now),
    )
    await db.db.commit()

    logger.info(f"CreateNote: Created note {note_id}")
    return Note(
        id=note_id,
        title=req.title,
        content=req.content,
        date=date,
        created_at=now,
        updated_at=now,
    )


@router.get("/api/notes/{note_id}")
async def get_note(note_id: str) -> Note:
    """Get a single note by ID."""
    assert db.db is not None

    async with db.db.execute(
        """
        SELECT id, title, content, date, created, updated
        FROM notes
        WHERE id = ?
        """,
        (note_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Note not found")

    return _row_to_note(row)


@router.put("/api/notes/{note_id}")
async def update_note(note_id: str, req: NoteRequest) -> Note:
    """Update an existing note."""
    assert db.db is not None

    # Check if note exists
    async with db.db.execute(
        "SELECT 1 FROM notes WHERE id = ?", (note_id,)
    ) as cursor:
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Note not found")

    now = datetime.now().isoformat()

    await db.db.execute(
        """
        UPDATE notes
        SET title = ?, content = ?, date = ?, updated = ?
        WHERE id = ?
        """,
        (req.title, req.content, req.date, now, note_id),
    )
    await db.db.commit()

    # Fetch updated record
    async with db.db.execute(
        """
        SELECT id, title, content, date, created, updated
        FROM notes WHERE id = ?
        """,
        (note_id,),
    ) as cursor:
        row = await cursor.fetchone()

    logger.info(f"UpdateNote: Updated note {note_id}")
    return _row_to_note(row)


@router.delete("/api/notes/{note_id}", status_code=204)
async def delete_note(note_id: str) -> None:
    """Delete a note."""
    assert db.db is not None

    # Check if note exists
    async with db.db.execute(
        "SELECT 1 FROM notes WHERE id = ?", (note_id,)
    ) as cursor:
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Note not found")

    await db.db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    await db.db.commit()

    logger.info(f"DeleteNote: Deleted note {note_id}")


@router.get("/api/notes/date/{date}")
async def get_notes_by_date(date: str) -> list[Note]:
    """Get notes for a specific date."""
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    assert db.db is not None
    async with db.db.execute(
        """
        SELECT id, title, content, date, created, updated
        FROM notes
        WHERE date LIKE ?
        ORDER BY created DESC
        """,
        (f"{date}%",),
    ) as cursor:
        rows = await cursor.fetchall()

    return [_row_to_note(row) for row in rows]


@router.get("/api/search")
async def search_notes(q: str = Query(..., min_length=1)) -> list[Note]:
    """Search notes by title or content."""
    assert db.db is not None

    search_pattern = f"%{q}%"

    async with db.db.execute(
        """
        SELECT id, title, content, date, created, updated
        FROM notes
        WHERE title LIKE ? OR content LIKE ?
        ORDER BY date DESC
        """,
        (search_pattern, search_pattern),
    ) as cursor:
        rows = await cursor.fetchall()

    return [_row_to_note(row) for row in rows]
