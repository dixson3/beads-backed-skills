# Formula: Toolsmith

## Purpose

Create and validate scripts from `plan.yaml` `tooling_needed` entries.

## Context

- `plan.yaml` — read `tooling_needed` entries
- Excluded: artifacts, sources.json, Summary.md

## Tools

Bash, Write, Edit

## Resolve the skill directory

Subagents do not inherit `${SKILL_DIR}`. Resolve it before placing shared scripts:

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name bdresearch -type d 2>/dev/null | head -1)
```

## Instructions

1. Read `plan.yaml` `tooling_needed` section
2. For each entry, create a Python script with PEP 723 inline dependencies
3. Scripts must use `click` for CLI when >200 lines
4. Test each script with `uv run <script> --help`
5. Place topic-specific scripts in `${research_dir}/scripts/`
6. Place shared scripts (reusable across topics) in the skill's own `scripts/` directory (resolve via `${SKILL_DIR}/scripts/`)

## Constraints: Rate Limiting

When building scripts that call external APIs, enforce these limits:

| Service | Requests/Minute | Requests/Day | Burst | Notes |
|---------|----------------|-------------|-------|-------|
| Tavily Search | 10 | 1000 | 3 | Free tier: 1000/month |
| Perplexity API | 5 | 50 | 2 | Conservative; actual limit may be higher |
| Generic HTTP (WebFetch) | 2 | 20 | 1 | Per-domain limit |
| GitHub API (`gh`) | 10 | 500 | 5 | Authenticated via gh CLI |

**Backoff strategy:** On HTTP 429, stop all requests to that service, wait 60 seconds, halve the rate for the remainder of the session. Never retry immediately.

Scripts must fail gracefully with a clear error if API keys are missing — never hang or retry indefinitely.

Required environment variables:

```
TAVILY_API_KEY           # Tavily Search API key
PERPLEXITY_API_KEY       # Perplexity API key
```
