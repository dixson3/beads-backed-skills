# markdown-pdf

Render a `.md` file to PDF via pandoc + xelatex, tuned for Unicode glyphs and
relative image paths. See [SKILL.md](SKILL.md) for the full contract.

## Prerequisites

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| `uv` | any | Runs the wrapper script (PEP 723) | https://docs.astral.sh/uv/ |
| `pandoc` | any | Markdown → PDF converter | https://pandoc.org/installing.html |
| `xelatex` | any | PDF engine (from a LaTeX distribution) | TeX Live / MacTeX |

Mirrors SKILL.md frontmatter `depends-on-tool: [uv, pandoc, xelatex]`. The script
checks for `pandoc` and `xelatex` and exits with a clear message if either is
missing. No `init` step, no config, no companion rule.

## Install

Installed by the repo-level `install.sh` / `install.py`, which auto-discovers
every `skills/*/` directory (group `markdown`). See the project
[README](../../README.md) for flags. Or per-skill: copy `skills/markdown-pdf` to
`~/.claude/skills/markdown-pdf`.

## Usage

User-invocable. Render one or more Markdown files to PDF:

```bash
uv run .claude/skills/markdown-pdf/scripts/md2pdf.py <input.md> [-o OUT.pdf]
# batch; override font; rotate wide tables to landscape
uv run .claude/skills/markdown-pdf/scripts/md2pdf.py a.md b.md
uv run .claude/skills/markdown-pdf/scripts/md2pdf.py r.md --mainfont "STIX Two Text" --table-font normalsize --landscape-cols 8
```

Output defaults to `<input>.pdf` beside the source. Pipeline defaults, font
notes, and the PDF table levers (`--table-font`, dash-width tuning,
`--landscape-cols`, `--columns`) are documented in [SKILL.md](SKILL.md).

## Phase model

None. This is a tool/reference skill with no phases or state transitions.

## File layout

```text
markdown-pdf/
  SKILL.md            entry point — trigger, invocation, pipeline defaults
  README.md           this file
  scripts/
    md2pdf.py                  pandoc/xelatex wrapper (PEP 723, argparse)
    landscape_wide_tables.lua  render-time filter: rotate wide tables to landscape
```

Requirements (`pandoc` + `xelatex`, and the macOS-only default font) are
documented in [SKILL.md](SKILL.md#requirements).

---
MIT © 2026 James Dixson <dixson3@gmail.com>, Yoshiko Studios LLC
