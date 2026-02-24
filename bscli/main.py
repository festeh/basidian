"""bscli - Basidian CLI tool for file operations and search."""

import asyncio
from typing import Optional

import click

from core.client import BasidianClient


DEFAULT_URL = "http://localhost:8090"


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


# CLI commands

@click.group()
@click.option("--url", default=DEFAULT_URL, help="Backend URL")
@click.pass_context
def cli(ctx, url: str):
    """bscli - Basidian CLI tool."""
    ctx.ensure_object(dict)
    ctx.obj["url"] = url


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
        async with BasidianClient(ctx.obj["url"]) as client:
            nodes = await client.get_tree(path or None)
            if not nodes:
                click.echo("No files found.")
                return
            for node in nodes:
                icon = "\U0001f4c1" if node.type == "folder" else "\U0001f4c4"
                click.echo(f"{icon} {node.name}")

    run_async(_run())


@files.command("tree")
@click.pass_context
def files_tree(ctx):
    """Show full tree structure."""
    async def _run():
        async with BasidianClient(ctx.obj["url"]) as client:
            nodes = await client.get_tree()
            if not nodes:
                click.echo("No files found.")
                return

            # Build depth map from parent_path relationships
            path_depth: dict[str, int] = {}
            for node in nodes:
                parts = node.path.strip("/").split("/")
                path_depth[node.path] = len(parts) - 1

            for node in nodes:
                depth = path_depth.get(node.path, 0)
                indent = "  " * depth
                icon = "\U0001f4c1" if node.type == "folder" else "\U0001f4c4"
                click.echo(f"{indent}{icon} {node.name}")

    run_async(_run())


@files.command("create")
@click.argument("path")
@click.option("--type", "node_type", type=click.Choice(["file", "folder"]), default="file", help="Node type")
@click.option("--content", default="", help="File content")
@click.pass_context
def files_create(ctx, path: str, node_type: str, content: str):
    """Create a new file or folder."""
    async def _run():
        async with BasidianClient(ctx.obj["url"]) as client:
            # Check if exists
            existing = await client.get_node(path)
            if existing:
                click.echo(f"Error: {path} already exists", err=True)
                return
            node = await client.create_node(path, node_type, content)
            click.echo(f"Created {node_type}: {node.path}")

    run_async(_run())


@files.command("read")
@click.argument("path")
@click.pass_context
def files_read(ctx, path: str):
    """Read file content."""
    async def _run():
        async with BasidianClient(ctx.obj["url"]) as client:
            node = await client.get_node(path)
            if not node:
                click.echo(f"Error: {path} not found", err=True)
                return
            if node.type == "folder":
                click.echo(f"Error: {path} is a folder", err=True)
                return
            click.echo(node.content)

    run_async(_run())


@files.command("delete")
@click.argument("path")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def files_delete(ctx, path: str, force: bool):
    """Delete a file or folder."""
    async def _run():
        async with BasidianClient(ctx.obj["url"]) as client:
            node = await client.get_node(path)
            if not node:
                click.echo(f"Error: {path} not found", err=True)
                return

            if not force:
                click.confirm(f"Delete {node.type} '{path}'?", abort=True)

            await client.delete_node(node.id)
            click.echo(f"Deleted: {path}")

    run_async(_run())


@files.command("move")
@click.argument("source")
@click.argument("dest")
@click.pass_context
def files_move(ctx, source: str, dest: str):
    """Move or rename a file/folder."""
    async def _run():
        async with BasidianClient(ctx.obj["url"]) as client:
            node = await client.get_node(source)
            if not node:
                click.echo(f"Error: {source} not found", err=True)
                return

            # Parse dest into parent_path and name
            dest_stripped = dest.rstrip("/")
            if "/" in dest_stripped:
                parts = dest_stripped.rsplit("/", 1)
                new_parent = parts[0] if parts[0] else "/"
                new_name = parts[1]
            else:
                new_parent = "/"
                new_name = dest_stripped.lstrip("/")

            result = await client.move_node(node.id, new_parent, new_name)
            if not result:
                click.echo(f"Error: {source} not found", err=True)
                return
            click.echo(f"Moved: {source} -> {dest}")

    run_async(_run())


@cli.command()
@click.argument("query")
@click.pass_context
def search(ctx, query: str):
    """Search files by name or content."""
    async def _run():
        async with BasidianClient(ctx.obj["url"]) as client:
            results = await client.search_files(query)
            if not results:
                click.echo("No results found.")
                return
            click.echo(f"Found {len(results)} result(s):\n")
            for node in results:
                icon = "\U0001f4c1" if node.type == "folder" else "\U0001f4c4"
                click.echo(f"{icon} {node.path}")

    run_async(_run())


@cli.command()
@click.option("--limit", "-n", default=10, help="Number of results")
@click.pass_context
def recent(ctx, limit: int):
    """List recently modified files."""
    async def _run():
        async with BasidianClient(ctx.obj["url"]) as client:
            # Get all files and take the most recent ones
            # (the tree endpoint returns all nodes)
            nodes = await client.get_tree()
            files = [n for n in nodes if n.type == "file"]
            files.sort(key=lambda n: n.updated_at or "", reverse=True)
            files = files[:limit]

            if not files:
                click.echo("No files found.")
                return
            for node in files:
                updated = node.updated_at[:16] if node.updated_at else "unknown"
                click.echo(f"{updated}  {node.path}")

    run_async(_run())


if __name__ == "__main__":
    cli()
