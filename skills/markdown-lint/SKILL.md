---
name: markdown-lint
skill-group: markdown
depends-on-tool: [uv]
depends-on-skill: []
description: >
  Conventional GitHub-Flavored-Markdown linter. Checks that documents are valid
  GFM with well-formed, resolvable links — no Obsidian wiki-links (`[[...]]`) or
  embeds (`![[...]]`), valid relative links/anchors, and consistent tables.
  TRIGGER when: /markdown-lint invoked; checking markdown validity; verifying a
  generated/edited `.md` file is clean GFM; after a generator skill writes
  markdown. SKIP for: non-markdown files; Obsidian-specific wiki-link tooling
  (plain GFM is the convention this linter enforces).
---

# markdown-lint

Lint markdown against conventional GFM rules encoded in
`scripts/markdown_lint.py`. The target dialect is **plain GFM** — Obsidian
wiki-links and embeds are not used.

## Invocation

```
/markdown-lint [<path> ...] [--rules ML001,...] [--format text|json]
```

- No args: lint the current directory tree
- `<path>`: one or more files or directories
- `--rules`: comma-separated subset (default: all)
- `--format json`: machine-readable output

```bash
uv run .claude/skills/markdown-lint/scripts/markdown_lint.py ${ARGS:-.}
```

Exit 1 if any violation is found; report each and explain the rule.

## Rules

| ID | Description |
|----|-------------|
| ML001 | Obsidian wiki-link `[[...]]` (use a `[text](path)` link) |
| ML002 | Obsidian embed `![[...]]` (use `![alt](path)`) |
| ML003 | Broken relative link (destination file does not exist) |
| ML004 | Broken link anchor (no matching heading in target / this file) |
| ML005 | Malformed GFM table (row column count ≠ delimiter row) |
| ML006 | Empty link destination `[text]()` |
| ML007 | Malformed table delimiter / alignment marker (e.g. `:-:-`) |

Frontmatter, fenced code blocks, and inline code spans are exempt from the
link/wiki-link checks (so docs that *describe* wiki-link syntax aren't flagged).
Anchors are validated with GitHub heading-slug rules (lowercase, punctuation
stripped, spaces→hyphens, duplicate `-N` suffixes).

## Table authoring (GFM)

Use **pipe tables** only — pandoc grid/multiline tables render as literal text in
Obsidian and GitHub. For a wide table, split it into narrower ones rather than
switching format.

- **Alignment:** `:--` left, `:-:` center, `--:` right — supported by GFM,
  Obsidian, and pandoc. Right-align numerics, center short categorical/flag
  columns, left for text.
- **In-cell line breaks:** use `<br>` for intentional wrapping inside a cell
  (renders in GFM, Obsidian, and pandoc). A literal newline can't occur inside a
  pipe-table row, so `<br>` is the only portable break.
- **PDF column width** is tuned by the separator's dash counts when rendering
  via the [`markdown-pdf`](../markdown-pdf/SKILL.md) skill (invisible to Obsidian
  and GitHub). When adding `:` markers, keep each segment's length fixed so those
  tuned widths survive.

When ML007 fires on a malformed delimiter, that table fails to parse, so ML005
(cell-count) checks are suppressed for its remaining rows — fix the delimiter and
re-lint to surface any further table issues.

## Migration helper

`scripts/convert_wikilinks.py` is a one-time converter that rewrites Obsidian
wiki-links into GFM links (resolving relative paths and heading anchors). Run it
on any directory that still contains `[[...]]`:

```bash
uv run .claude/skills/markdown-lint/scripts/convert_wikilinks.py <dir> --vault-root . --report <out.md>
```

It is code-aware and idempotent; unresolved/ambiguous links are best-effort
converted and listed in the report.

## Optional FileChanged hook

To lint on every `.md` edit, hand-wire a `FileChanged` hook for `**/*.md` in
your `.claude/settings.json`. Run only the authoring-time rules (wiki-links,
embeds, tables, empty links) and skip link/anchor resolution (ML003/ML004) so
the hook stays fast and quiet:

```bash
uv run .claude/skills/markdown-lint/scripts/markdown_lint.py "$CLAUDE_FILE_PATHS" --rules ML001,ML002,ML005,ML006,ML007
```

Run the full rule set (including ML003/ML004) for a deliberate link audit. This
hook is not managed by the skill installer — edit `settings.json` to add, change,
or remove it; keep its `--rules` list in sync with this section.

---
MIT © 2026 James Dixson <dixson3@gmail.com>, Yoshiko Studios LLC
