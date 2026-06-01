# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.1"]
# ///
"""Research index manager.

Manages _index.md artifact manifests for research topics.
Provides init, add, and list operations.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import click

INDEX_FILENAME = "_index.md"
HEADER_TEMPLATE = """# Research Index: {topic}

| Timestamp | Phase | Artifact | Description |
|-----------|-------|----------|-------------|
"""


def _index_path(research_dir: str) -> Path:
    return Path(research_dir) / INDEX_FILENAME


def _parse_rows(content: str) -> list[dict]:
    """Parse markdown table rows from _index.md content."""
    rows = []
    in_table = False
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("| Timestamp"):
            in_table = True
            continue
        if line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 4:
                rows.append({
                    "timestamp": cells[0],
                    "phase": cells[1],
                    "artifact": cells[2],
                    "description": cells[3],
                })
    return rows


@click.group()
def cli():
    """Manage _index.md research artifact manifests."""
    pass


@cli.command()
@click.argument("research_dir")
@click.argument("topic")
def init(research_dir: str, topic: str):
    """Initialize a new _index.md for a research topic."""
    path = _index_path(research_dir)
    if path.exists():
        click.echo(f"_index.md already exists at {path}", err=True)
        return

    Path(research_dir).mkdir(parents=True, exist_ok=True)
    path.write_text(HEADER_TEMPLATE.format(topic=topic))
    click.echo(f"Created {path}")


@cli.command()
@click.argument("research_dir")
@click.argument("phase")
@click.argument("artifact")
@click.argument("description")
@click.option("--timestamp", "-t", default=None, help="Override timestamp (ISO format)")
def add(research_dir: str, phase: str, artifact: str, description: str, timestamp: str | None):
    """Add an artifact entry to _index.md."""
    path = _index_path(research_dir)
    if not path.exists():
        click.echo(f"ERROR: {path} does not exist. Run 'init' first.", err=True)
        raise SystemExit(1)

    ts = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    # Render .md artifacts as Obsidian wikilinks so the artifact column is clickable.
    # No alias — the bare wikilink avoids the `|` collision with markdown table columns.
    if artifact.endswith(".md"):
        artifact_cell = f"[[{artifact[:-3]}]]"
    else:
        artifact_cell = artifact
    row = f"| {ts} | {phase} | {artifact_cell} | {description} |\n"

    content = path.read_text()
    # Append row to end of file
    if not content.endswith("\n"):
        content += "\n"
    content += row
    path.write_text(content)
    click.echo(f"Added: {phase} / {artifact}")


@cli.command("list")
@click.argument("research_dir")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
@click.option("--phase", "-p", default=None, help="Filter by phase")
def list_entries(research_dir: str, json_output: bool, phase: str | None):
    """List artifacts in _index.md."""
    path = _index_path(research_dir)
    if not path.exists():
        click.echo(f"ERROR: {path} does not exist.", err=True)
        raise SystemExit(1)

    rows = _parse_rows(path.read_text())

    if phase:
        rows = [r for r in rows if r["phase"].upper() == phase.upper()]

    if json_output:
        click.echo(json.dumps(rows, indent=2))
    else:
        for r in rows:
            click.echo(f"  {r['timestamp']}  [{r['phase']}]  {r['artifact']}  — {r['description']}")


if __name__ == "__main__":
    cli()
