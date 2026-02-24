"""basync - Sync files between local filesystem and Basidian."""

import asyncio
import fnmatch
from pathlib import Path
from typing import Optional

import click

from core.client import BasidianClient
from core.models import FsNode

from .config import BasyncConfig, load_config


def should_include(path: str, include: list[str], exclude: list[str]) -> bool:
    """Check if a path should be included based on patterns."""
    name = Path(path).name

    # Skip hidden files by default
    if name.startswith("."):
        # Unless explicitly included
        for pattern in include:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    # Check excludes
    for pattern in exclude:
        if fnmatch.fnmatch(name, pattern):
            return False
        # Also check full path
        if fnmatch.fnmatch(path, pattern):
            return False

    # Check includes (if specified, only include matching)
    if include:
        for pattern in include:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    return True


def is_text_file(path: Path) -> bool:
    """Check if a file is likely a text file."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
            if b"\x00" in chunk:
                return False
        return True
    except Exception:
        return False


def collect_local_files(
    local_path: Path, include: list[str], exclude: list[str]
) -> dict[str, Path]:
    """Collect local files recursively, returning remote_path -> local_path mapping."""
    files: dict[str, Path] = {}

    if not local_path.exists():
        return files

    for item in local_path.rglob("*"):
        if item.is_dir():
            continue

        rel_path = item.relative_to(local_path)
        remote_path = "/" + str(rel_path)

        # Check each path component for exclusions
        skip = False
        for part in rel_path.parts:
            if not should_include(part, include, exclude):
                skip = True
                break

        if skip:
            continue

        if not should_include(str(rel_path), include, exclude):
            continue

        files[remote_path] = item

    return files


async def do_push(
    client: BasidianClient,
    local_path: Path,
    remote_path: str,
    include: list[str],
    exclude: list[str],
    dry_run: bool,
) -> tuple[int, int, int]:
    """Push local files to Basidian. Returns (created, updated, skipped)."""
    created = 0
    updated = 0
    skipped = 0

    # Collect local files
    local_files = collect_local_files(local_path, include, exclude)
    total = len(local_files)

    if total == 0:
        click.echo("No files to push.")
        return created, updated, skipped

    # Get existing remote nodes
    remote_nodes = await client.get_tree()
    remote_by_path: dict[str, FsNode] = {n.path: n for n in remote_nodes}

    # Track folders we need to create
    folders_to_create: set[str] = set()

    for i, (file_remote_path, file_local_path) in enumerate(sorted(local_files.items()), 1):
        # Adjust remote path if not root
        if remote_path != "/":
            full_remote_path = remote_path.rstrip("/") + file_remote_path
        else:
            full_remote_path = file_remote_path

        # Check if text file
        if not is_text_file(file_local_path):
            click.echo(f"[!] skip (binary): {full_remote_path}")
            skipped += 1
            continue

        # Check file size
        file_size = file_local_path.stat().st_size
        if file_size > 1024 * 1024:  # 1MB
            click.echo(f"[!] skip (too large): {full_remote_path}")
            skipped += 1
            continue

        # Read content
        try:
            content = file_local_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            click.echo(f"[!] skip (encoding): {full_remote_path}")
            skipped += 1
            continue

        # Collect parent folders
        parts = full_remote_path.strip("/").split("/")
        for j in range(1, len(parts)):
            folder_path = "/" + "/".join(parts[:j])
            if folder_path not in remote_by_path:
                folders_to_create.add(folder_path)

        # Check if exists
        existing = remote_by_path.get(full_remote_path)

        if existing:
            if existing.content == content:
                click.echo(f"[=] unchanged ({i}/{total}): {full_remote_path}")
                continue

            click.echo(f"[~] update ({i}/{total}): {full_remote_path}")
            if not dry_run:
                await client.update_node(existing.id, content)
            updated += 1
        else:
            click.echo(f"[+] create ({i}/{total}): {full_remote_path}")
            if not dry_run:
                # Create folders first
                for folder_path in sorted(folders_to_create):
                    if folder_path not in remote_by_path:
                        node = await client.create_node(folder_path, "folder")
                        remote_by_path[folder_path] = node
                folders_to_create.clear()

                node = await client.create_node(full_remote_path, "file", content)
                remote_by_path[full_remote_path] = node
            created += 1

    return created, updated, skipped


async def do_pull(
    client: BasidianClient,
    local_path: Path,
    remote_path: str,
    include: list[str],
    exclude: list[str],
    dry_run: bool,
) -> tuple[int, int, int]:
    """Pull files from Basidian to local. Returns (created, updated, skipped)."""
    created = 0
    updated = 0
    skipped = 0

    # Get remote nodes
    remote_nodes = await client.get_tree()

    # Filter to requested path
    if remote_path != "/":
        prefix = remote_path.rstrip("/")
        remote_nodes = [
            n for n in remote_nodes
            if n.path == prefix or n.path.startswith(prefix + "/")
        ]

    # Filter to files only
    files = [n for n in remote_nodes if n.type == "file"]
    total = len(files)

    if total == 0:
        click.echo("No files to pull.")
        return created, updated, skipped

    for i, node in enumerate(sorted(files, key=lambda n: n.path), 1):
        # Calculate local path
        if remote_path != "/":
            rel_path = node.path[len(remote_path.rstrip("/")):]
        else:
            rel_path = node.path

        rel_path = rel_path.lstrip("/")

        # Check filters
        skip = False
        for part in Path(rel_path).parts:
            if not should_include(part, include, exclude):
                skip = True
                break

        if skip:
            click.echo(f"[!] skip (filtered): {node.path}")
            skipped += 1
            continue

        if not should_include(rel_path, include, exclude):
            click.echo(f"[!] skip (filtered): {node.path}")
            skipped += 1
            continue

        file_path = local_path / rel_path

        # Check if exists locally
        if file_path.exists():
            try:
                local_content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                local_content = None

            if local_content == node.content:
                click.echo(f"[=] unchanged ({i}/{total}): {rel_path}")
                continue

            click.echo(f"[~] update ({i}/{total}): {rel_path}")
            if not dry_run:
                file_path.write_text(node.content, encoding="utf-8")
            updated += 1
        else:
            click.echo(f"[+] create ({i}/{total}): {rel_path}")
            if not dry_run:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(node.content, encoding="utf-8")
            created += 1

    return created, updated, skipped


# CLI

@click.group()
@click.option("--config", "config_path", type=click.Path(exists=True), help="Config file path")
@click.pass_context
def cli(ctx, config_path: Optional[str]):
    """basync - Sync files between local filesystem and Basidian."""
    ctx.ensure_object(dict)
    config = load_config(Path(config_path) if config_path else None)
    ctx.obj["config"] = config


@cli.command()
@click.argument("path", default="", required=False)
@click.option("--local", "local_path", help="Local directory")
@click.option("--remote", "remote_path", help="Remote Basidian path")
@click.option("--include", "includes", multiple=True, help="Include pattern (repeatable)")
@click.option("--exclude", "excludes", multiple=True, help="Exclude pattern (repeatable)")
@click.option("--dry-run", is_flag=True, help="Show what would happen")
@click.option("--url", "backend_url", help="Backend URL")
@click.pass_context
def push(
    ctx,
    path: str,
    local_path: Optional[str],
    remote_path: Optional[str],
    includes: tuple[str, ...],
    excludes: tuple[str, ...],
    dry_run: bool,
    backend_url: Optional[str],
):
    """Push local files to Basidian."""
    config: BasyncConfig = ctx.obj["config"]

    # Merge CLI options with config
    local = Path(local_path or config.local_path)
    remote = remote_path or path or config.remote_path
    url = backend_url or config.backend_url
    include = list(includes) or config.include
    exclude = list(excludes) if excludes else config.exclude

    if not remote.startswith("/"):
        remote = "/" + remote

    if dry_run:
        click.echo("DRY RUN - no changes will be made\n")

    click.echo(f"Pushing: {local} -> {url}{remote}\n")

    async def _run():
        async with BasidianClient(url) as client:
            try:
                created, updated, skipped = await do_push(
                    client, local, remote, include, exclude, dry_run
                )
                click.echo(f"\nDone: {created} created, {updated} updated, {skipped} skipped")
                return 0 if skipped == 0 else 1
            except Exception as e:
                click.echo(f"\nError: {e}", err=True)
                return 1

    exit_code = asyncio.run(_run())
    ctx.exit(exit_code)


@cli.command()
@click.argument("path", default="", required=False)
@click.option("--local", "local_path", help="Local directory")
@click.option("--remote", "remote_path", help="Remote Basidian path")
@click.option("--include", "includes", multiple=True, help="Include pattern (repeatable)")
@click.option("--exclude", "excludes", multiple=True, help="Exclude pattern (repeatable)")
@click.option("--dry-run", is_flag=True, help="Show what would happen")
@click.option("--url", "backend_url", help="Backend URL")
@click.pass_context
def pull(
    ctx,
    path: str,
    local_path: Optional[str],
    remote_path: Optional[str],
    includes: tuple[str, ...],
    excludes: tuple[str, ...],
    dry_run: bool,
    backend_url: Optional[str],
):
    """Pull files from Basidian to local."""
    config: BasyncConfig = ctx.obj["config"]

    # Merge CLI options with config
    local = Path(local_path or config.local_path)
    remote = remote_path or path or config.remote_path
    url = backend_url or config.backend_url
    include = list(includes) or config.include
    exclude = list(excludes) if excludes else config.exclude

    if not remote.startswith("/"):
        remote = "/" + remote

    if dry_run:
        click.echo("DRY RUN - no changes will be made\n")

    click.echo(f"Pulling: {url}{remote} -> {local}\n")

    async def _run():
        async with BasidianClient(url) as client:
            try:
                created, updated, skipped = await do_pull(
                    client, local, remote, include, exclude, dry_run
                )
                click.echo(f"\nDone: {created} created, {updated} updated, {skipped} skipped")
                return 0 if skipped == 0 else 1
            except Exception as e:
                click.echo(f"\nError: {e}", err=True)
                return 1

    exit_code = asyncio.run(_run())
    ctx.exit(exit_code)


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    cfg: BasyncConfig = ctx.obj["config"]
    click.echo(f"backend_url = {cfg.backend_url!r}")
    click.echo(f"local_path = {cfg.local_path!r}")
    click.echo(f"remote_path = {cfg.remote_path!r}")
    click.echo(f"exclude = {cfg.exclude!r}")
    click.echo(f"include = {cfg.include!r}")


if __name__ == "__main__":
    cli()
