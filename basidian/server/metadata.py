"""In-memory metadata index for tags, links, backlinks, daily dates, and frontmatter.

Built on startup by parsing all file content. Updated incrementally on save/delete/move.
This is the Obsidian approach: fast reads from memory, trivially rebuildable.
"""

import re
from dataclasses import dataclass, field

import yaml
from loguru import logger

# Match #tag but not inside code blocks
_TAG_PATTERN = re.compile(r"(?<!\w)#([\w-]+)")
# Match [[wikilink]] and [[wikilink|display]]
_LINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
# Match ```...``` code blocks (to exclude tags inside them)
_CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")
# Match inline code `...`
_INLINE_CODE_PATTERN = re.compile(r"`[^`]+`")
# Daily note filename pattern: DD-MMM-YYYY.md
_DAILY_PATTERN = re.compile(
    r"(\d{2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{4})\.md$"
)
_MONTH_ABBREVS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def _strip_code_blocks(content: str) -> str:
    """Remove code blocks and inline code from content for tag extraction."""
    result = _CODE_BLOCK_PATTERN.sub("", content)
    result = _INLINE_CODE_PATTERN.sub("", result)
    return result


def _extract_tags(content: str) -> set[str]:
    """Extract #tags from content (not inside code blocks). Normalized to lowercase."""
    stripped = _strip_code_blocks(content)
    return {tag.lower() for tag in _TAG_PATTERN.findall(stripped)}


def _extract_links(content: str) -> set[str]:
    """Extract [[wikilink]] targets from content."""
    return set(_LINK_PATTERN.findall(content))


def _extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from content."""
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return {}


def _parse_daily_date(filename: str, folder: str) -> str | None:
    """Parse daily date from filename if under the daily folder. Returns ISO date string."""
    match = _DAILY_PATTERN.search(filename)
    if not match:
        return None
    day, month_abbr, year = match.group(1), match.group(2), match.group(3)
    month_idx = _MONTH_ABBREVS.index(month_abbr) + 1
    return f"{year}-{month_idx:02d}-{int(day):02d}"


@dataclass
class MetadataIndex:
    """In-memory index of parsed metadata from all notes."""

    # tag (lowercase) → set of node IDs
    tags: dict[str, set[str]] = field(default_factory=dict)

    # source node ID → set of target paths (raw wikilink text)
    links: dict[str, set[str]] = field(default_factory=dict)

    # target path → set of source node IDs
    backlinks: dict[str, set[str]] = field(default_factory=dict)

    # ISO date string → node ID
    daily_dates: dict[str, str] = field(default_factory=dict)

    # node ID → parsed frontmatter dict
    frontmatter: dict[str, dict] = field(default_factory=dict)

    # Config
    daily_folder: str = "/daily"

    def build(self, nodes: list[dict]) -> None:
        """Build full index from a list of {id, name, path, body} dicts."""
        self.tags.clear()
        self.links.clear()
        self.backlinks.clear()
        self.daily_dates.clear()
        self.frontmatter.clear()

        for node in nodes:
            self._index_node(node["id"], node["name"], node["path"], node["body"])

        logger.info(
            f"MetadataIndex: Built index for {len(nodes)} files — "
            f"{len(self.tags)} tags, {sum(len(v) for v in self.links.values())} links, "
            f"{len(self.daily_dates)} daily dates"
        )

    def update_node(self, node_id: str, name: str, path: str, body: str) -> None:
        """Re-index a single node after save."""
        self._remove_node(node_id)
        self._index_node(node_id, name, path, body)

    def remove_node(self, node_id: str) -> None:
        """Remove a node from all indexes."""
        self._remove_node(node_id)

    def on_move(
        self, node_id: str, old_path: str, new_path: str, new_name: str
    ) -> None:
        """Update indexes after a node move/rename."""
        # Update daily dates if filename changed
        self.daily_dates = {
            date: nid for date, nid in self.daily_dates.items() if nid != node_id
        }
        if new_path.startswith(self.daily_folder + "/"):
            daily_date = _parse_daily_date(new_name, self.daily_folder)
            if daily_date:
                self.daily_dates[daily_date] = node_id

        # Update backlinks: any link targeting old_path should now target new_path
        if old_path in self.backlinks:
            sources = self.backlinks.pop(old_path)
            self.backlinks.setdefault(new_path, set()).update(sources)

    def get_tags_with_counts(self) -> list[dict]:
        """Return all tags with usage counts, sorted by count desc."""
        result = [{"tag": tag, "count": len(ids)} for tag, ids in self.tags.items()]
        result.sort(key=lambda x: (-x["count"], x["tag"]))
        return result

    def get_nodes_for_tag(self, tag: str) -> set[str]:
        """Return node IDs that have a given tag."""
        return self.tags.get(tag.lower(), set())

    def get_backlinks(self, path: str) -> set[str]:
        """Return source node IDs that link to a given path."""
        # Try exact path match, and also match without leading slash
        result = set()
        result.update(self.backlinks.get(path, set()))
        # Wikilinks may omit the leading slash
        stripped = path.lstrip("/")
        result.update(self.backlinks.get(stripped, set()))
        return result

    def get_links(self, node_id: str) -> set[str]:
        """Return target paths that a node links to."""
        return self.links.get(node_id, set())

    def _index_node(self, node_id: str, name: str, path: str, body: str) -> None:
        """Index a single node."""
        # Tags
        for tag in _extract_tags(body):
            self.tags.setdefault(tag, set()).add(node_id)

        # Links + backlinks
        link_targets = _extract_links(body)
        if link_targets:
            self.links[node_id] = link_targets
            for target in link_targets:
                self.backlinks.setdefault(target, set()).add(node_id)

        # Frontmatter
        fm = _extract_frontmatter(body)
        if fm:
            self.frontmatter[node_id] = fm

        # Daily dates
        if path.startswith(self.daily_folder + "/"):
            daily_date = _parse_daily_date(name, self.daily_folder)
            if daily_date:
                self.daily_dates[daily_date] = node_id

    def _remove_node(self, node_id: str) -> None:
        """Remove a node from all indexes."""
        # Tags
        empty_tags = []
        for tag, ids in self.tags.items():
            ids.discard(node_id)
            if not ids:
                empty_tags.append(tag)
        for tag in empty_tags:
            del self.tags[tag]

        # Links + backlinks
        old_targets = self.links.pop(node_id, set())
        for target in old_targets:
            if target in self.backlinks:
                self.backlinks[target].discard(node_id)
                if not self.backlinks[target]:
                    del self.backlinks[target]

        # Frontmatter
        self.frontmatter.pop(node_id, None)

        # Daily dates
        self.daily_dates = {
            date: nid for date, nid in self.daily_dates.items() if nid != node_id
        }
