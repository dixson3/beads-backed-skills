#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Convert Obsidian wiki-links to GFM markdown links across a vault.

One-time migration tool that backs the `markdown-lint` skill's de-Obsidian-ify
flow. Resolves `[[target]]`, `[[target|alias]]`, `[[target#heading]]`,
`[[#heading]]`, and `![[embed]]` to standard markdown links/images with
relative paths and GFM-slugified anchors.

Code-aware: never rewrites wiki-link syntax inside YAML frontmatter, fenced
code blocks, or inline code spans (so docs that *describe* wiki-link syntax are
left intact).

Resolution follows Obsidian semantics: bare basenames resolve vault-wide
(same-dir > shortest-path tie-break); slash-bearing targets resolve as
vault-relative paths. Unresolved/ambiguous links are best-effort converted and
listed in the report.

Usage:
    uv run convert_wikilinks.py <dir> [<dir>...] [--vault-root DIR]
                                [--dry-run] [--report FILE]

Exit code 0 always (report-driven, not gate-driven).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".pdf"}
# Only strip a trailing ".ext" when it is a real, known file extension — many
# note names contain dots (e.g. "2.1-pl-by-stage"), which splitext would
# otherwise mistake for an extension.
KNOWN_EXTS = IMAGE_EXTS | {
    ".md", ".csv", ".txt", ".json", ".yaml", ".yml", ".toml", ".html", ".d2",
}


def strip_known_ext(s: str) -> str:
    base, ext = os.path.splitext(s)
    return base if ext.lower() in KNOWN_EXTS else s

# A wiki-link: optional leading ! (embed), [[ ... ]] with no nested ]].
WIKILINK_RE = re.compile(r"(!?)\[\[([^\]]+?)\]\]")
# Inline code spans: runs of backticks ... matching run. Group 0 spans the code.
INLINE_CODE_RE = re.compile(r"(`+)(?:.*?)\1")


def gfm_slug(text: str) -> str:
    """GitHub-flavored anchor slug for a heading's text."""
    s = text.strip().lower()
    # drop punctuation except word chars, whitespace, hyphen (\w keeps underscore)
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = s.replace(" ", "-")
    return s


def heading_slugs(md_path: Path) -> set[str]:
    """All GFM anchor slugs a renderer would emit for this file's headings."""
    slugs: set[str] = set()
    seen: Counter[str] = Counter()
    in_fence = False
    fence = ""
    try:
        lines = md_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return slugs
    for line in lines:
        stripped = line.lstrip()
        m = re.match(r"^(```+|~~~+)", stripped)
        if m:
            tok = m.group(1)[0]
            if not in_fence:
                in_fence, fence = True, tok
            elif fence == tok:
                in_fence = False
            continue
        if in_fence:
            continue
        hm = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if not hm:
            continue
        base = gfm_slug(hm.group(1))
        n = seen[base]
        seen[base] += 1
        slugs.add(base if n == 0 else f"{base}-{n}")
    return slugs


class VaultIndex:
    def __init__(self, vault_root: Path):
        self.root = vault_root.resolve()
        # relpath without extension (lowercased) -> paths (any file type)
        self.exact_noext: dict[str, list[Path]] = defaultdict(list)
        # basename stem (lowercased) -> paths (any file type)
        self.basename_noext: dict[str, list[Path]] = defaultdict(list)
        # (noext_lower, Path) for suffix matching
        self.noext_items: list[tuple[str, Path]] = []
        self._slug_cache: dict[Path, set[str]] = {}
        self._build()

    def _build(self) -> None:
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in filenames:
                p = Path(dirpath) / fn
                rel = p.relative_to(self.root).as_posix()
                noext = strip_known_ext(rel).lower()
                self.exact_noext[noext].append(p)
                self.basename_noext[Path(noext).name].append(p)
                self.noext_items.append((noext, p))

    def slugs(self, p: Path) -> set[str]:
        if p not in self._slug_cache:
            self._slug_cache[p] = heading_slugs(p)
        return self._slug_cache[p]

    @staticmethod
    def _prefer_md(cands: list[Path]) -> list[Path]:
        md = [c for c in cands if c.suffix.lower() == ".md"]
        return md if md else cands

    def resolve(self, target: str, source: Path) -> tuple[Path | None, bool]:
        """Return (resolved_path, ambiguous). None path => unresolved.

        Obsidian-style priority: exact vault-relative path -> unique suffix
        path match -> basename (markdown notes preferred, else any file).
        """
        target = target.strip().strip("[]").strip()
        if target.startswith("./"):
            target = target[2:]
        target = target.rstrip("/")
        if not target:
            return None, False
        # Resolve explicit relative paths (../, used in some table cells) against
        # the source file's directory, then fall into the normal pipeline.
        if target.startswith("../"):
            cand = (source.resolve().parent / target).resolve()
            try:
                target = cand.relative_to(self.root).as_posix()
            except ValueError:
                pass
        key = strip_known_ext(target).lower()
        has_slash = "/" in target

        # 1. exact vault-relative path (no extension)
        hits = self.exact_noext.get(key, [])
        if len(hits) == 1:
            return hits[0], False
        if len(hits) > 1:
            return self._pick(self._prefer_md(hits), source)

        # 2. unique suffix path match (Obsidian resolves partial paths)
        if has_slash:
            suf = "/" + key
            hits = [p for k, p in self.noext_items if k.endswith(suf)]
            if len(hits) == 1:
                return hits[0], False
            if len(hits) > 1:
                return self._pick(self._prefer_md(hits), source)

        # 3. basename match
        cands = self.basename_noext.get(Path(key).name, [])
        return self._pick(self._prefer_md(cands), source)

    @staticmethod
    def _pick(cands: list[Path], source: Path) -> tuple[Path | None, bool]:
        if not cands:
            return None, False
        if len(cands) == 1:
            return cands[0], False
        sparts = source.resolve().parent.parts
        same = [c for c in cands if c.resolve().parent == source.resolve().parent]
        if len(same) == 1:
            # Obsidian's deterministic same-folder rule -> confident, not ambiguous
            return same[0], False

        def common_prefix(c: Path) -> int:
            n = 0
            for a, b in zip(sparts, c.resolve().parent.parts):
                if a != b:
                    break
                n += 1
            return n

        # Prefer nearest in the tree (longest shared path), then shallowest, then lexical
        scored = sorted(cands, key=lambda c: (-common_prefix(c), len(c.resolve().parts), str(c)))
        best = scored[0]
        # Confident if it has a strictly closer ancestor than every other candidate
        confident = len(scored) == 1 or common_prefix(best) > common_prefix(scored[1])
        return best, not confident


def encode_dest(rel: str) -> str:
    return rel.replace("%", "%25").replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def reldest(target_path: Path, source: Path) -> str:
    rel = os.path.relpath(target_path.resolve(), source.resolve().parent)
    return Path(rel).as_posix()


class Stats:
    def __init__(self) -> None:
        self.converted = 0
        self.unresolved: list[tuple[str, str]] = []   # (source_rel, raw)
        self.ambiguous: list[tuple[str, str, str]] = []  # (source_rel, raw, picked)
        self.bad_anchor: list[tuple[str, str, str]] = []  # (source_rel, raw, anchor)
        self.block_ref: list[tuple[str, str]] = []
        self.embed_downgrade: list[tuple[str, str]] = []


def split_target(inner: str) -> tuple[str, str | None, str | None]:
    """inner of [[...]] -> (target, anchor_or_None, alias_or_None)."""
    # In table cells Obsidian escapes the alias pipe as ``\|``; normalize it.
    inner = inner.replace("\\|", "|")
    alias = None
    if "|" in inner:
        inner, alias = inner.split("|", 1)
        alias = alias.strip()
    anchor = None
    if "#" in inner:
        target, anchor = inner.split("#", 1)
        anchor = anchor.strip()
    else:
        target = inner
    return target.strip(), anchor, alias


def convert_link(m: re.Match, source: Path, src_rel: str, index: VaultIndex, st: Stats) -> str:
    raw = m.group(0)
    is_embed = m.group(1) == "!"
    target, anchor, alias = split_target(m.group(2))

    # Same-file anchor: [[#heading]]
    if not target and anchor is not None:
        slug = gfm_slug(anchor.lstrip("^"))
        if anchor.startswith("^"):
            st.block_ref.append((src_rel, raw))
            display = alias or anchor
            return display  # no anchor target available; leave as plain text
        if slug not in index.slugs(source):
            st.bad_anchor.append((src_rel, raw, anchor))
        display = alias or anchor
        st.converted += 1
        return f"[{display}](#{slug})"

    resolved, ambiguous = index.resolve(target, source)
    block = anchor is not None and anchor.startswith("^")

    # Build anchor fragment
    frag = ""
    if anchor and not block:
        # Obsidian allows nested #h1#h2; GFM anchors the deepest heading
        last = anchor.split("#")[-1]
        slug = gfm_slug(last)
        frag = f"#{slug}"
    if block:
        st.block_ref.append((src_rel, raw))

    display = alias or (m.group(2).split("|", 1)[0]).strip()

    if resolved is None:
        st.unresolved.append((src_rel, raw))
        # best-effort: keep the target text as a relative-ish dest
        guess = target if target.lower().endswith((".md",) + tuple(IMAGE_EXTS)) else target + ".md"
        dest = encode_dest(guess) + frag
        st.converted += 1
        # Unresolved targets become a plain link whether or not they were an
        # embed (no file to embed); the image-embed form only applies to a
        # resolved image, handled below.
        return f"[{display}]({dest})"

    if ambiguous:
        st.ambiguous.append((src_rel, raw, os.path.relpath(resolved, index.root)))

    # anchor existence check against resolved md file
    if frag and resolved.suffix.lower() == ".md":
        if frag[1:] not in index.slugs(resolved):
            st.bad_anchor.append((src_rel, raw, anchor or ""))

    dest = encode_dest(reldest(resolved, source)) + frag
    st.converted += 1

    if is_embed:
        if resolved.suffix.lower() in IMAGE_EXTS:
            return f"![{display}]({dest})"
        # note transclusion: GFM has no equivalent -> link + report
        st.embed_downgrade.append((src_rel, raw))
        return f"[{display}]({dest})"
    return f"[{display}]({dest})"


def process_text(text: str, source: Path, src_rel: str, index: VaultIndex, st: Stats) -> str:
    """Rewrite wiki-links in non-code text, leaving inline code spans intact."""
    out = []
    pos = 0
    for cm in INLINE_CODE_RE.finditer(text):
        seg = text[pos:cm.start()]
        out.append(WIKILINK_RE.sub(lambda m: convert_link(m, source, src_rel, index, st), seg))
        out.append(cm.group(0))  # code span verbatim
        pos = cm.end()
    tail = text[pos:]
    out.append(WIKILINK_RE.sub(lambda m: convert_link(m, source, src_rel, index, st), tail))
    return "".join(out)


def convert_file(p: Path, index: VaultIndex, st: Stats, dry: bool) -> bool:
    try:
        raw = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    lines = raw.split("\n")
    src_rel = p.resolve().relative_to(index.root).as_posix()

    out: list[str] = []
    i = 0
    n = len(lines)
    # preserve YAML frontmatter verbatim
    if n and lines[0].strip() == "---":
        out.append(lines[0])
        i = 1
        while i < n and lines[i].strip() != "---":
            out.append(lines[i])
            i += 1
        if i < n:
            out.append(lines[i])  # closing ---
            i += 1

    in_fence = False
    fence_tok = ""
    while i < n:
        line = lines[i]
        stripped = line.lstrip()
        fm = re.match(r"^(```+|~~~+)", stripped)
        if fm:
            tok = fm.group(1)[0]
            if not in_fence:
                in_fence, fence_tok = True, tok
            elif fence_tok == tok:
                in_fence = False
            out.append(line)
            i += 1
            continue
        if in_fence:
            out.append(line)
            i += 1
            continue
        if "[[" in line:
            line = process_text(line, p, src_rel, index, st)
        out.append(line)
        i += 1

    new = "\n".join(out)
    if new != raw:
        if not dry:
            p.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--vault-root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    index = VaultIndex(Path(args.vault_root))
    st = Stats()
    changed_files = 0
    scanned = 0
    for d in args.dirs:
        base = Path(d)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if not x.startswith(".")]
            for fn in filenames:
                if not fn.endswith(".md"):
                    continue
                p = Path(dirpath) / fn
                scanned += 1
                if convert_file(p, index, st, args.dry_run):
                    changed_files += 1

    lines = []
    lines.append(f"# Wiki-link conversion report{' (dry-run)' if args.dry_run else ''}")
    lines.append("")
    lines.append(f"- Files scanned: {scanned}")
    lines.append(f"- Files changed: {changed_files}")
    lines.append(f"- Links converted: {st.converted}")
    lines.append(f"- Unresolved (best-effort guessed): {len(st.unresolved)}")
    lines.append(f"- Ambiguous (multiple targets): {len(st.ambiguous)}")
    lines.append(f"- Bad/missing anchors: {len(st.bad_anchor)}")
    lines.append(f"- Block refs (^id, no GFM equiv): {len(st.block_ref)}")
    lines.append(f"- Note embeds downgraded to links: {len(st.embed_downgrade)}")

    def section(title, rows, fmt):
        lines.append("")
        lines.append(f"## {title} ({len(rows)})")
        for r in rows:
            lines.append("- " + fmt(r))

    def grouped(title, rows, keyidx=0):
        by = Counter(r[keyidx] for r in rows)
        lines.append("")
        lines.append(f"## {title} ({len(rows)} across {len(by)} files)")
        for f, c in sorted(by.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"- `{f}`: {c}")

    # Unresolved links are the actionable ones -> list each
    if st.unresolved:
        section("Unresolved links", st.unresolved, lambda r: f"`{r[1]}` in `{r[0]}`")
    if st.ambiguous:
        grouped("Ambiguous links (per file)", st.ambiguous)
    if st.bad_anchor:
        grouped("Non-resolving anchors — pre-existing citation IDs etc. (per file)", st.bad_anchor)
    if st.block_ref:
        section("Block references", st.block_ref, lambda r: f"`{r[1]}` in `{r[0]}`")
    if st.embed_downgrade:
        section("Downgraded embeds", st.embed_downgrade, lambda r: f"`{r[1]}` in `{r[0]}`")

    report = "\n".join(lines) + "\n"
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"Report written to {args.report}")
    print("\n".join(lines[:9]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
