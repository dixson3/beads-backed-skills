#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Conventional GFM markdown linter for this vault.

Replaces the Obsidian-specific `obsidian-lint`. Checks that documents are valid
GitHub-Flavored Markdown with well-formed, resolvable links — no Obsidian
wiki-links or embeds.

Code-aware: YAML frontmatter, fenced code blocks, and inline code spans are
exempt from link/wikilink checks.

Rules:
  ML001  Obsidian wiki-link ``[[...]]`` (should be a ``[text](path)`` link)
  ML002  Obsidian embed ``![[...]]`` (should be ``![alt](path)``)
  ML003  Broken relative link (destination file does not exist)
  ML004  Broken link anchor (no matching heading in the target / this file)
  ML005  Malformed GFM table (row column count != delimiter row)
  ML006  Empty link destination ``[text]()``
  ML007  Malformed table delimiter / alignment marker (e.g. ``:-:-``)

Usage:
    uv run markdown_lint.py [<path> ...] [--rules ML001,...] [--format text|json]

Exit code 1 if any violation is found, else 0.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

WIKILINK_RE = re.compile(r"!?\[\[[^\]]+?\]\]")
INLINE_CODE_RE = re.compile(r"`+(?:.*?)`+")
# [text](dest) — dest captured up to first unescaped ) ; text allows nested brackets minimally
MDLINK_RE = re.compile(r"!?\[(?P<text>[^\]]*)\]\((?P<dest>[^)]*)\)")
URL_SCHEME_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#|mailto:)", re.I)
ALL_RULES = ["ML001", "ML002", "ML003", "ML004", "ML005", "ML006", "ML007"]


def gfm_slug(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    return s.replace(" ", "-")


def heading_slugs(path: Path) -> set[str]:
    slugs: set[str] = set()
    seen: Counter[str] = Counter()
    in_fence = False
    fence = ""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return slugs
    for line in lines:
        m = re.match(r"^(```+|~~~+)", line.lstrip())
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


def strip_inline_code(text: str) -> str:
    """Blank out inline code spans so their contents are not linted."""
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)


def table_cell_count(row: str) -> int:
    s = row.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return len(re.split(r"(?<!\\)\|", s))


def is_delim_row(row: str) -> bool:
    s = row.strip().strip("|")
    cells = re.split(r"(?<!\\)\|", s)
    if not cells:
        return False
    return all(re.fullmatch(r"\s*:?-{1,}:?\s*", c) for c in cells)


class Linter:
    def __init__(self, rules: set[str]):
        self.rules = rules
        self._slug_cache: dict[Path, set[str]] = {}

    def slugs(self, p: Path) -> set[str]:
        if p not in self._slug_cache:
            self._slug_cache[p] = heading_slugs(p)
        return self._slug_cache[p]

    def check_anchor(self, source: Path, dest_path: Path | None, frag: str) -> bool:
        """True if anchor exists. dest_path None => same-file anchor."""
        target = dest_path if dest_path is not None else source
        if target.suffix.lower() != ".md":
            return True  # only validate anchors into markdown
        return gfm_slug(urllib.parse.unquote(frag)) in self.slugs(target)

    def lint_file(self, path: Path) -> list[tuple[int, str, str]]:
        out: list[tuple[int, str, str]] = []
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return out
        lines = raw.split("\n")
        n = len(lines)
        i = 0
        # skip frontmatter
        if n and lines[0].strip() == "---":
            i = 1
            while i < n and lines[i].strip() != "---":
                i += 1
            i += 1

        in_fence = False
        fence_tok = ""
        # table tracking
        table_cols = None  # delimiter column count of current table
        prev_line = ""
        prev_code = ""     # prev_line with inline code blanked (pipe-gate test)
        prev_lineno = 0

        while i < n:
            line = lines[i]
            lineno = i + 1
            fm = re.match(r"^(```+|~~~+)", line.lstrip())
            if fm:
                tok = fm.group(1)[0]
                if not in_fence:
                    in_fence, fence_tok = True, tok
                elif fence_tok == tok:
                    in_fence = False
                table_cols = None
                prev_line = ""
                prev_code = ""
                i += 1
                continue
            if in_fence:
                i += 1
                continue

            code = strip_inline_code(line)

            # ML001 / ML002 wiki-links & embeds
            for m in WIKILINK_RE.finditer(code):
                tok = m.group(0)
                if tok.startswith("!"):
                    if "ML002" in self.rules:
                        out.append((lineno, "ML002", f"Obsidian embed: {tok}"))
                elif "ML001" in self.rules:
                    out.append((lineno, "ML001", f"Obsidian wiki-link: {tok}"))

            # ML003 / ML004 / ML006 markdown links
            for m in MDLINK_RE.finditer(code):
                dest = m.group("dest").strip()
                if not dest:
                    if "ML006" in self.rules:
                        out.append((lineno, "ML006", f"empty link destination: {m.group(0)}"))
                    continue
                # angle-bracket wrapped
                if dest.startswith("<") and dest.endswith(">"):
                    dest = dest[1:-1]
                if URL_SCHEME_RE.match(dest):
                    if dest.startswith("#"):
                        frag = dest[1:]
                        if "ML004" in self.rules and frag and not self.check_anchor(path, None, frag):
                            out.append((lineno, "ML004", f"broken same-file anchor: {dest}"))
                    continue  # external URL / scheme — not validated
                pathpart, _, frag = dest.partition("#")
                pathpart = urllib.parse.unquote(pathpart)
                if not pathpart:
                    continue
                target = (path.parent / pathpart).resolve()
                if "ML003" in self.rules and not target.exists():
                    out.append((lineno, "ML003", f"broken link target: {dest}"))
                    continue
                if "ML004" in self.rules and frag and target.exists() and not self.check_anchor(path, target, frag):
                    out.append((lineno, "ML004", f"broken anchor: {dest}"))

            # ML005 tables
            if "ML005" in self.rules:
                if table_cols is not None:
                    if "|" in line and line.strip():
                        if table_cell_count(line) != table_cols:
                            out.append((lineno, "ML005",
                                        f"table row has {table_cell_count(line)} cells, expected {table_cols}"))
                    else:
                        table_cols = None
                if table_cols is None and is_delim_row(line) and "|" in prev_code:
                    dc = table_cell_count(line)
                    if table_cell_count(prev_line) != dc:
                        out.append((prev_lineno, "ML005",
                                    f"table header has {table_cell_count(prev_line)} cells, delimiter has {dc}"))
                    table_cols = dc

            # ML007 malformed delimiter / alignment marker — a row that looks
            # like a botched delimiter (only -, :, |, spaces; has a dash; pipes
            # on it and the header) but isn't a valid GFM delimiter, so the table
            # silently fails to parse. Requiring pipes avoids thematic breaks; the
            # header test uses the inline-code-stripped form so a `cmd | x` span
            # isn't mistaken for a table header.
            if ("ML007" in self.rules and table_cols is None and "|" in line
                    and "|" in prev_code and prev_line.strip()):
                s = line.strip()
                if "-" in s and re.fullmatch(r"[\s:|-]+", s) and not is_delim_row(line):
                    out.append((lineno, "ML007",
                                f"malformed table delimiter / alignment marker: {s}"))

            prev_line = line
            prev_code = code
            prev_lineno = lineno
            i += 1
        return out


def _split_arg(arg: str) -> list[str]:
    # The FileChanged hook passes "$CLAUDE_FILE_PATHS" as one quoted arg, which
    # may hold several space-separated paths on a multi-file edit. Resolve the
    # whole token first (so paths that legitimately contain spaces survive); only
    # fall back to whitespace-splitting when the token isn't a real path.
    p = Path(arg)
    if p.is_file() or p.is_dir() or " " not in arg:
        return [arg]
    return arg.split()


def iter_md(paths: list[str]):
    for pth in (tok for arg in paths for tok in _split_arg(arg)):
        p = Path(pth)
        if p.is_file() and p.suffix == ".md":
            yield p
        elif p.is_dir():
            for dp, dn, fn in os.walk(p):
                dn[:] = [d for d in dn if not d.startswith(".")]
                for f in fn:
                    if f.endswith(".md"):
                        yield Path(dp) / f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--rules", default=None, help="comma-separated subset, e.g. ML001,ML003")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args()
    paths = args.paths or ["."]
    rules = set(args.rules.split(",")) if args.rules else set(ALL_RULES)

    linter = Linter(rules)
    findings = []
    for f in iter_md(paths):
        for lineno, rule, msg in linter.lint_file(f):
            findings.append({"file": str(f), "line": lineno, "rule": rule, "message": msg})

    if args.format == "json":
        print(json.dumps(findings, indent=2))
    else:
        if not findings:
            print("markdown-lint: clean")
        else:
            by_rule = Counter(x["rule"] for x in findings)
            for x in findings:
                print(f"{x['file']}:{x['line']}: {x['rule']} {x['message']}")
            print(f"\n{len(findings)} violation(s): " +
                  ", ".join(f"{r}={by_rule[r]}" for r in sorted(by_rule)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
