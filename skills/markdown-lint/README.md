# markdown-lint

Lint markdown as conventional GitHub-Flavored Markdown — no Obsidian
wiki-links/embeds, resolvable relative links/anchors, well-formed tables. See
[SKILL.md](SKILL.md) for the rule list, table-authoring conventions, and the
optional `FileChanged` hook.

## Prerequisites

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| `uv` | any | Runs the linter scripts (PEP 723) | https://docs.astral.sh/uv/ |

Mirrors SKILL.md frontmatter `depends-on-tool: [uv]`. No `init` step, no config,
no companion rule.

## Install

Installed by the repo-level `install.sh` / `install.py`, which auto-discovers
every `skills/*/` directory (group `markdown`). See the project
[README](../../README.md) for flags. Or per-skill: copy `skills/markdown-lint` to
`~/.claude/skills/markdown-lint`.

## Usage

User-invocable. Lint files or directories, optionally scoping the rule set:

```
/markdown-lint [<path> ...] [--rules ML001,...] [--format text|json]
```

```bash
uv run .claude/skills/markdown-lint/scripts/markdown_lint.py ${ARGS:-.}
# one-time Obsidian wiki-link -> GFM migration for a tree
uv run .claude/skills/markdown-lint/scripts/convert_wikilinks.py <dir> --vault-root . --report <out.md>
```

Exit 1 on any violation. Rules ML001–ML007 are documented in
[SKILL.md](SKILL.md#rules); the optional lint-on-edit `FileChanged` hook is in
[SKILL.md](SKILL.md#optional-filechanged-hook).

## Phase model

None. This is a tool/reference skill with no phases or state transitions.

## File layout

```text
markdown-lint/
  SKILL.md            entry point — rules, table conventions, hook
  README.md           this file
  scripts/
    markdown_lint.py      the GFM linter (PEP 723, argparse)
    convert_wikilinks.py  one-time wiki-link → GFM migration tool
```

---
MIT © 2026 James Dixson <dixson3@gmail.com>, Yoshiko Studios LLC
