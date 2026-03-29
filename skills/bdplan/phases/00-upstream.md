# Phase 0: UPSTREAM DISCOVERY

Runs once per project (persisted to CLAUDE.md), re-validated at start of each new plan.

## 1 — Auto-detect

```bash
REMOTE_URL=$(git config --get remote.origin.url 2>/dev/null)
if echo "$REMOTE_URL" | grep -qE 'github\.com'; then
  gh auth status 2>/dev/null && UPSTREAM="github"
elif echo "$REMOTE_URL" | grep -qE 'gitlab\.com|gitlab\.' ; then
  glab auth status 2>/dev/null && UPSTREAM="gitlab"
fi
grep -q "## Upstream Tracking" CLAUDE.md 2>/dev/null && UPSTREAM="configured"
```

## 2 — Probe for issues (if no config)

```bash
gh issue list --limit 5 --json number,title,state 2>/dev/null
glab issue list --per-page 5 2>/dev/null
```

## 3 — Confirm with operator

Ask: use GitHub Issues, GitLab Issues, Jira, Linear, or none?

## 4 — Persist to CLAUDE.md

```markdown
## Upstream Tracking

- **Source:** github
- **Repo:** <owner>/<repo>
- **Tool:** `gh issue`
- **Notes:** <operator instructions>
```

On subsequent plans, read existing config. Re-validate if remote URL changed.
