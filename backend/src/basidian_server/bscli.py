"""bscli - Basidian CLI tool for file operations and search."""

import asyncio
from datetime import datetime, timezone
from typing import Optional

import click

from . import database


DEFAULT_DB_PATH = "./pb_data/data.db"


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


async def _init_db(db_path: str):
    """Initialize database connection."""
    await database.init(db_path)


async def _close_db():
    """Close database connection."""
    await database.close()


async def _list_files(parent_path: str) -> list[dict]:
    """List files at a given path."""
    assert database.db is not None
    cursor = await database.db.execute(
        "SELECT * FROM fs_nodes WHERE parent_path = ? ORDER BY type DESC, name ASC",
        (parent_path,)
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def _get_tree(parent_path: str = "", depth: int = 0) -> list[dict]:
    """Get tree structure recursively."""
    assert database.db is not None
    cursor = await database.db.execute(
        "SELECT * FROM fs_nodes WHERE parent_path = ? ORDER BY type DESC, name ASC",
        (parent_path,)
    )
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        node = dict(row)
        node["_depth"] = depth
        result.append(node)
        if node["type"] == "folder":
            children = await _get_tree(node["path"], depth + 1)
            result.extend(children)
    return result


async def _get_node_by_path(path: str) -> Optional[dict]:
    """Get a node by its path."""
    assert database.db is not None
    cursor = await database.db.execute(
        "SELECT * FROM fs_nodes WHERE path = ?", (path,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def _create_node(path: str, node_type: str, content: str = "") -> dict:
    """Create a new file or folder."""
    assert database.db is not None

    # Parse path to get name and parent
    path = path.rstrip("/")
    if "/" in path:
        parts = path.rsplit("/", 1)
        parent_path = parts[0] if parts[0] else ""
        name = parts[1]
    else:
        parent_path = ""
        name = path.lstrip("/")

    now = datetime.now(timezone.utc).isoformat()
    node_id = database.generate_id()

    await database.db.execute(
        """INSERT INTO fs_nodes (id, type, name, path, parent_path, content, sort_order, created, updated)
           VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)""",
        (node_id, node_type, name, path, parent_path, content, now, now)
    )
    await database.db.commit()

    return {
        "id": node_id,
        "type": node_type,
        "name": name,
        "path": path,
        "parent_path": parent_path,
        "content": content,
    }


async def _delete_node(path: str) -> bool:
    """Delete a node and its children."""
    assert database.db is not None

    node = await _get_node_by_path(path)
    if not node:
        return False

    # Delete children if folder
    if node["type"] == "folder":
        await database.db.execute(
            "DELETE FROM fs_nodes WHERE path LIKE ?", (path + "/%",)
        )

    await database.db.execute("DELETE FROM fs_nodes WHERE path = ?", (path,))
    await database.db.commit()
    return True


async def _move_node(old_path: str, new_path: str) -> Optional[dict]:
    """Move or rename a node."""
    assert database.db is not None

    node = await _get_node_by_path(old_path)
    if not node:
        return None

    # Parse new path
    new_path = new_path.rstrip("/")
    if "/" in new_path:
        parts = new_path.rsplit("/", 1)
        new_parent = parts[0] if parts[0] else ""
        new_name = parts[1]
    else:
        new_parent = ""
        new_name = new_path.lstrip("/")

    now = datetime.now(timezone.utc).isoformat()

    # Update the node
    await database.db.execute(
        "UPDATE fs_nodes SET name = ?, path = ?, parent_path = ?, updated = ? WHERE path = ?",
        (new_name, new_path, new_parent, now, old_path)
    )

    # Update children paths if folder
    if node["type"] == "folder":
        cursor = await database.db.execute(
            "SELECT * FROM fs_nodes WHERE path LIKE ?", (old_path + "/%",)
        )
        children = await cursor.fetchall()
        for child in children:
            child_new_path = new_path + child["path"][len(old_path):]
            child_new_parent = new_path + child["parent_path"][len(old_path):] if child["parent_path"].startswith(old_path) else child["parent_path"]
            await database.db.execute(
                "UPDATE fs_nodes SET path = ?, parent_path = ?, updated = ? WHERE id = ?",
                (child_new_path, child_new_parent, now, child["id"])
            )

    await database.db.commit()
    return await _get_node_by_path(new_path)


async def _search(query: str) -> list[dict]:
    """Search files by name or content."""
    assert database.db is not None
    cursor = await database.db.execute(
        "SELECT * FROM fs_nodes WHERE name LIKE ? OR content LIKE ? ORDER BY updated DESC",
        (f"%{query}%", f"%{query}%")
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def _recent(limit: int) -> list[dict]:
    """Get recently modified files."""
    assert database.db is not None
    cursor = await database.db.execute(
        "SELECT * FROM fs_nodes WHERE type = 'file' ORDER BY updated DESC LIMIT ?",
        (limit,)
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# CLI commands

@click.group()
@click.option("--db", "db_path", default=DEFAULT_DB_PATH, help="Database path")
@click.pass_context
def cli(ctx, db_path: str):
    """bscli - Basidian CLI tool."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db_path


@cli.group()
def files():
    """File and folder operations."""
    pass


@files.command("list")
@click.option("--path", default="", help="Parent path to list")
@click.pass_context
def files_list(ctx, path: str):
    """List files and folders at a path."""
    async def _run():
        await _init_db(ctx.obj["db_path"])
        try:
            nodes = await _list_files(path)
            if not nodes:
                click.echo("No files found.")
                return
            for node in nodes:
                icon = "📁" if node["type"] == "folder" else "📄"
                click.echo(f"{icon} {node['name']}")
        finally:
            await _close_db()

    run_async(_run())


@files.command("tree")
@click.pass_context
def files_tree(ctx):
    """Show full tree structure."""
    async def _run():
        await _init_db(ctx.obj["db_path"])
        try:
            nodes = await _get_tree()
            if not nodes:
                click.echo("No files found.")
                return
            for node in nodes:
                indent = "  " * node["_depth"]
                icon = "📁" if node["type"] == "folder" else "📄"
                click.echo(f"{indent}{icon} {node['name']}")
        finally:
            await _close_db()

    run_async(_run())


@files.command("create")
@click.argument("path")
@click.option("--type", "node_type", type=click.Choice(["file", "folder"]), default="file", help="Node type")
@click.option("--content", default="", help="File content")
@click.pass_context
def files_create(ctx, path: str, node_type: str, content: str):
    """Create a new file or folder."""
    async def _run():
        await _init_db(ctx.obj["db_path"])
        try:
            # Check if exists
            existing = await _get_node_by_path(path)
            if existing:
                click.echo(f"Error: {path} already exists", err=True)
                return

            node = await _create_node(path, node_type, content)
            click.echo(f"Created {node_type}: {node['path']}")
        finally:
            await _close_db()

    run_async(_run())


@files.command("read")
@click.argument("path")
@click.pass_context
def files_read(ctx, path: str):
    """Read file content."""
    async def _run():
        await _init_db(ctx.obj["db_path"])
        try:
            node = await _get_node_by_path(path)
            if not node:
                click.echo(f"Error: {path} not found", err=True)
                return
            if node["type"] == "folder":
                click.echo(f"Error: {path} is a folder", err=True)
                return
            click.echo(node["content"])
        finally:
            await _close_db()

    run_async(_run())


@files.command("delete")
@click.argument("path")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def files_delete(ctx, path: str, force: bool):
    """Delete a file or folder."""
    async def _run():
        await _init_db(ctx.obj["db_path"])
        try:
            node = await _get_node_by_path(path)
            if not node:
                click.echo(f"Error: {path} not found", err=True)
                return

            if not force:
                click.confirm(f"Delete {node['type']} '{path}'?", abort=True)

            await _delete_node(path)
            click.echo(f"Deleted: {path}")
        finally:
            await _close_db()

    run_async(_run())


@files.command("move")
@click.argument("source")
@click.argument("dest")
@click.pass_context
def files_move(ctx, source: str, dest: str):
    """Move or rename a file/folder."""
    async def _run():
        await _init_db(ctx.obj["db_path"])
        try:
            node = await _move_node(source, dest)
            if not node:
                click.echo(f"Error: {source} not found", err=True)
                return
            click.echo(f"Moved: {source} -> {dest}")
        finally:
            await _close_db()

    run_async(_run())


@cli.command()
@click.argument("query")
@click.pass_context
def search(ctx, query: str):
    """Search files by name or content."""
    async def _run():
        await _init_db(ctx.obj["db_path"])
        try:
            results = await _search(query)
            if not results:
                click.echo("No results found.")
                return
            click.echo(f"Found {len(results)} result(s):\n")
            for node in results:
                icon = "📁" if node["type"] == "folder" else "📄"
                click.echo(f"{icon} {node['path']}")
        finally:
            await _close_db()

    run_async(_run())


@cli.command()
@click.option("--limit", "-n", default=10, help="Number of results")
@click.pass_context
def recent(ctx, limit: int):
    """List recently modified files."""
    async def _run():
        await _init_db(ctx.obj["db_path"])
        try:
            results = await _recent(limit)
            if not results:
                click.echo("No files found.")
                return
            for node in results:
                updated = node["updated"][:16] if node["updated"] else "unknown"
                click.echo(f"{updated}  {node['path']}")
        finally:
            await _close_db()

    run_async(_run())


if __name__ == "__main__":
    cli()
