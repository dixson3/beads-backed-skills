---
name: markdown-pdf
skill-group: markdown
depends-on-tool: [uv, pandoc, xelatex]
depends-on-skill: []
description: >
  Render a Markdown file to PDF via the pandoc + xelatex pipeline — xelatex
  engine, a broad-coverage Unicode font (so →, ≤, ≈ and similar glyphs render),
  1in margins, blue links, and relative image paths (`![](diagrams/x.png)`)
  resolved against the source file's directory.
  TRIGGER when: /markdown-pdf invoked; the user wants a PDF created/generated
  from a `.md` file; "export this report to PDF", "make a PDF of this note".
  SKIP for: slide decks; HTML or non-PDF output; linting markdown
  (use `markdown-lint`).
---

# markdown-pdf

Convert Markdown to PDF with pandoc + xelatex. A pandoc + xelatex pipeline tuned
for Unicode-glyph coverage and relative image paths.

## Invocation

```bash
uv run .claude/skills/markdown-pdf/scripts/md2pdf.py <input.md>
```

Output defaults to `<input>.pdf` beside the source. Multiple inputs each render
to `<name>.pdf`. `-o OUT.pdf` overrides the path (single input only).

```bash
# explicit output
uv run .claude/skills/markdown-pdf/scripts/md2pdf.py report.md -o /tmp/report.pdf
# batch
uv run .claude/skills/markdown-pdf/scripts/md2pdf.py a.md b.md
# override the main font / margin; pass extra pandoc flags after `--`
uv run .claude/skills/markdown-pdf/scripts/md2pdf.py r.md --mainfont "STIX Two Text" -- --toc
# no table shrink; rotate any table with >8 columns to landscape
uv run .claude/skills/markdown-pdf/scripts/md2pdf.py r.md --table-font normalsize --landscape-cols 8
```

## Pipeline defaults

The script runs `pandoc --pdf-engine=xelatex` with: `geometry:margin=1in`,
`linkcolor=blue`, `mainfont=Arial Unicode MS`, `monofont=Menlo`, and
`--resource-path=<dir of the source .md>`.

- **Font choice matters.** The default LaTeX fonts lack common glyphs (→ ≤ ≈).
  `Arial Unicode MS` (macOS) covers them. On a host without it, pass
  `--mainfont` a Unicode-complete font or the render shows "Missing character"
  warnings (the script surfaces these — they do not fail the build).
- **Relative images resolve from the source dir** via `--resource-path`. Keep
  referenced images present, or pandoc errors.

## Tables

Wide / many-column tables are the main PDF rendering pain point. PDF-specific
levers:

- `--table-font SIZE` (default `footnotesize`) shrinks all table text so dense
  tables fit without cells bleeding into neighbors. `normalsize` = no shrink.
- **Dash-width tuning.** pandoc sets each column's PDF width from the length of
  its separator segment (`---`, dashes *and* colons), so more dashes on a
  text-heavy column widens it. Only engages once the separator row is wider than
  `--columns` (default 72); lower `--columns` to tune narrower tables. Obsidian
  and GitHub ignore dash counts, so this is invisible there.
- `--landscape-cols N` rotates any table with more than N columns onto a
  landscape page (`0` = off). A render-time Lua filter — no `\begin{landscape}`
  in the source (which would show as literal text in Obsidian/GitHub).

Portable pipe-table authoring — `:` alignment, `<br>` in-cell breaks, pipe-only
(don't switch to grid/multiline), split wide tables — lives in the
[`markdown-lint`](../markdown-lint/SKILL.md) skill; those render identically in
pandoc, Obsidian, and GitHub.

## Requirements

`pandoc` and `xelatex` (a LaTeX distribution) on PATH. The script checks both
and exits with a clear message if either is missing.
