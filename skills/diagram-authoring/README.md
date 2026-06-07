# diagram-authoring

Generate light-mode, white-background diagram PNGs from **d2** source, keeping the `.d2` source
beside every `.png` render. d2 is the single, local, offline diagram engine for this toolchain
(replacing the ad-hoc mermaid+naba workflow). The skill is location-agnostic — callers
(bdplan, bdresearch, skill-authoring, top-level docs) supply the output directory.

## Prerequisites

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| `d2` | >= 0.7 | Diagram compiler/renderer (`.d2` → `.png`, theme 0, elk) | `brew install d2` |

Mirrors SKILL.md frontmatter `depends-on-tool: [d2]`. The first PNG render fetches a one-time
~140MB playwright Chromium; that warm-up is owned outside this skill (e.g. a dotfiles bootstrap
hook). Preflight only checks that `d2` is on PATH — it never probes the Chromium cache.

## Install

Installed by the repo-level `install.sh` / `install.py`, which auto-discovers every `skills/*/`
directory. No hook, no companion rule. See the project [README](../../README.md) for flags.

## Usage

User-invocable. Drive d2 through `scripts/render.py` (run via `uv run`):

```bash
uv run scripts/render.py preflight                 # OS-independent `command -v d2` check
uv run scripts/render.py render <slug>.d2          # one .d2 -> sibling .png (theme 0, elk)
uv run scripts/render.py render-dir <dir>          # (re)render every .d2 under <dir>
uv run scripts/render.py check-dir <dir>           # every .d2 has a .png (+ advisory staleness)
```

Write `.d2` source into the caller's diagrams location, render, then `Read` the PNG to verify
(white background, legible labels). Reference a render from docs with relative markdown image
syntax — `![alt](spec/<slug>.png)` from a skill README, `![alt](docs/diagrams/<slug>.png)` from
the project README. See SKILL.md for the full workflow, location conventions, and d2 authoring
notes.

## Layout

```
skills/diagram-authoring/
├── SKILL.md             # the d2 workflow, location conventions, when-to-diagram, d2 authoring notes
├── README.md            # this file
└── scripts/
    └── render.py        # PEP 723 helper: preflight / render / render-dir / check-dir
```
