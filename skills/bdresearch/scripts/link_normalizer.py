# /// script
# requires-python = ">=3.11"
# dependencies = ["click"]
# ///
"""Normalize links in research topics for Obsidian rendering.

Operations:
  - build-sources: generate sources.md per topic from sources.json (or cluster
    sources-*.json files), one "## <ID>" heading per source.
  - link-citations: rewrite [ID] / [ID1, ID2] citation patterns in Summary.md
    and artifacts/*.md to [[sources#ID|ID]] wikilinks. Only rewrites IDs that
    exist in the topic's source set; annotations like [uncertain], [gap ...]
    are left untouched.
  - link-index: rewrite the Artifact column of _index.md to wikilinks.
  - all: run all three in order.

Intended to be idempotent; safe to re-run.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

import click

ID_RE = re.compile(r"^[A-Za-z]{1,3}\d+$")
# Brackets that contain at least one comma-separated token matching ID_RE.
# Mixed brackets like "[ABA-internal data, ME7]" are in scope — valid IDs get
# linked, annotation text stays as prose.
CITATION_RE = re.compile(r"\[([^\[\]\n]+)\]")
ANNOTATION_SKIP_RE = re.compile(
    r"^(uncertain|conflicted-source|gap|background|uncited|single-source|analytical\s+synthesis.*)$",
    re.IGNORECASE,
)


def load_sources(topic_dir: Path) -> tuple[list[dict], dict]:
    """Return (sources, meta). Meta includes clusters if available."""
    agg = topic_dir / "sources.json"
    if agg.exists():
        data = json.loads(agg.read_text())
        if isinstance(data, list):
            return data, {}
        return data.get("sources", []), {
            "clusters": data.get("clusters", []),
            "plan": data.get("plan"),
            "scoring": data.get("scoring"),
        }
    sources: list[dict] = []
    for p in sorted(topic_dir.glob("sources-*.json")):
        d = json.loads(p.read_text())
        if isinstance(d, list):
            sources.extend(d)
        elif isinstance(d, dict):
            sources.extend(d.get("sources", []))
    for p in sorted((topic_dir / "artifacts").glob("sources-*.json")):
        d = json.loads(p.read_text())
        if isinstance(d, list):
            sources.extend(d)
        elif isinstance(d, dict):
            sources.extend(d.get("sources", []))
    return sources, {}


def render_sources_md(topic_dir: Path, sources: list[dict], meta: dict) -> str:
    topic = topic_dir.name
    cluster_lookup = {c["name"]: c for c in meta.get("clusters", [])}
    lines = [
        "---",
        f'title: "Sources — {topic}"',
        "created: 2026-04-23",
        f"tags: [research, {topic}, sources]",
        "---",
        "",
        f"# Sources — {topic}",
        "",
        "Citation format: `[[sources#ID|ID]]` from Summary.md and artifacts.",
        "",
    ]
    by_cluster: dict[str, list[dict]] = {}
    for s in sources:
        by_cluster.setdefault(s.get("cluster", "uncategorized"), []).append(s)
    for cname in sorted(by_cluster.keys()):
        cmeta = cluster_lookup.get(cname, {})
        prefix = cmeta.get("prefix", "")
        header = f"## {cname}" + (f" ({prefix})" if prefix else "")
        lines += [header, ""]
        for s in by_cluster[cname]:
            sid = s.get("id") or s.get("original_id")
            if not sid:
                continue
            lines.append(f"### {sid}")
            if s.get("title"):
                lines.append(f"- **Title:** {s['title']}")
            if s.get("url"):
                lines.append(f"- **URL:** {s['url']}")
            if s.get("author"):
                lines.append(f"- **Author:** {s['author']}")
            if s.get("published"):
                lines.append(f"- **Published:** {s['published']}")
            score = s.get("credibility_score")
            cat = s.get("credibility_category")
            if score is not None:
                lines.append(f"- **Credibility:** {score} ({cat})" if cat else f"- **Credibility:** {score}")
            if s.get("credibility_rationale"):
                lines.append(f"- **Rationale:** {s['credibility_rationale']}")
            if s.get("snippet"):
                lines.append(f"- **Snippet:** {s['snippet']}")
            if s.get("quote"):
                q = s["quote"].replace("\n", " ").strip()
                lines.append(f"- **Quote:** > {q}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def rewrite_citations(text: str, known_ids: set[str]) -> tuple[str, int]:
    count = 0

    def sub(m: re.Match) -> str:
        nonlocal count
        raw = m.group(1)
        parts = [p.strip() for p in raw.split(",")]
        valid_idx = [i for i, p in enumerate(parts) if ID_RE.match(p) and p in known_ids]
        if not valid_idx:
            return m.group(0)
        # Skip brackets that are pure single-token annotations already (like [uncertain]).
        if len(parts) == 1 and ANNOTATION_SKIP_RE.match(parts[0]):
            return m.group(0)
        rendered: list[str] = []
        for i, p in enumerate(parts):
            if i in valid_idx:
                rendered.append(f"[[sources#{p}|{p}]]")
                count += 1
            else:
                rendered.append(p)
        # If all tokens are valid, drop outer brackets (cleaner in Obsidian).
        # If mixed, preserve the bracket grouping so annotations read naturally.
        if len(valid_idx) == len(parts):
            return ", ".join(rendered)
        # Mixed: use parens to avoid [[ ambiguity with Obsidian's wikilink parser.
        return "(" + ", ".join(rendered) + ")"

    new = CITATION_RE.sub(sub, text)
    # Cleanup pass: outer [...] wrappers that already contain a wikilink mixed
    # with prose should render as parens to avoid [[ parser ambiguity.
    mixed_re = re.compile(r"\[([^\[\]]*(?:\[\[sources#[^\]]+\]\][^\[\]]*)+)\]")
    new = mixed_re.sub(lambda m: "(" + m.group(1) + ")", new)
    return new, count


INDEX_ROW_RE = re.compile(
    r"^\|\s*(?P<ts>[^|]+?)\s*\|\s*(?P<phase>[^|]+?)\s*\|\s*(?P<artifact>[^|]+?)\s*\|\s*(?P<desc>[^|]*?)\s*\|\s*$"
)


def rewrite_index(text: str) -> tuple[str, int]:
    """Turn plain artifact cell into a wikilink when it resolves to a .md file."""
    count = 0
    out_lines = []
    for line in text.splitlines():
        m = INDEX_ROW_RE.match(line)
        if not m:
            out_lines.append(line)
            continue
        artifact = m.group("artifact")
        if "[[" in artifact or artifact in ("Artifact", "(none)", "-"):
            out_lines.append(line)
            continue
        if artifact.endswith(".md"):
            note = artifact[:-3]
            # No alias — `|` inside `[[ ]]` collides with markdown table column separator.
            link = f"[[{note}]]"
            new = f"| {m.group('ts')} | {m.group('phase')} | {link} | {m.group('desc')} |"
            out_lines.append(new)
            count += 1
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else ""), count


@click.group()
def cli():
    """Normalize research topic links for Obsidian."""


@cli.command("build-sources")
@click.argument("topic_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
def build_sources(topic_dir: Path):
    """Write sources.md for the topic."""
    sources, meta = load_sources(topic_dir)
    if not sources:
        click.echo(f"{topic_dir.name}: no sources found — skipped")
        return
    out = topic_dir / "sources.md"
    out.write_text(render_sources_md(topic_dir, sources, meta))
    click.echo(f"{topic_dir.name}: wrote {out.relative_to(topic_dir.parent)} ({len(sources)} sources)")


@cli.command("link-citations")
@click.argument("topic_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
def link_citations(topic_dir: Path):
    """Rewrite [ID] citations to wikilinks across Summary.md and artifacts/*.md."""
    sources, _ = load_sources(topic_dir)
    known: set[str] = {s["id"] for s in sources if s.get("id")}
    if not known:
        click.echo(f"{topic_dir.name}: no known IDs — skipped")
        return
    targets: list[Path] = []
    for p in [topic_dir / "Summary.md"]:
        if p.exists():
            targets.append(p)
    for p in sorted((topic_dir / "artifacts").glob("*.md")):
        targets.append(p)
    total = 0
    for p in targets:
        txt = p.read_text()
        new, n = rewrite_citations(txt, known)
        if new != txt:
            p.write_text(new)
            total += n
            click.echo(f"  {p.relative_to(topic_dir)}: {n} citations linked")
    click.echo(f"{topic_dir.name}: {total} citations linked across {len(targets)} files")


@cli.command("link-index")
@click.argument("topic_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
def link_index(topic_dir: Path):
    """Rewrite _index.md Artifact column to wikilinks."""
    idx = topic_dir / "_index.md"
    if not idx.exists():
        click.echo(f"{topic_dir.name}: no _index.md — skipped")
        return
    new, n = rewrite_index(idx.read_text())
    if n:
        idx.write_text(new)
    click.echo(f"{topic_dir.name}: {n} artifact cells wikilinked")


@cli.command("all")
@click.argument("topic_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.pass_context
def all_cmd(ctx, topic_dir: Path):
    ctx.invoke(build_sources, topic_dir=topic_dir)
    ctx.invoke(link_citations, topic_dir=topic_dir)
    ctx.invoke(link_index, topic_dir=topic_dir)


if __name__ == "__main__":
    cli()
