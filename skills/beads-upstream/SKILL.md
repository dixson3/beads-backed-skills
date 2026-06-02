---
name: beads-upstream
description: >
  Configurable, GitHub-first upstream-tracking skill for beads. Pushes open/deferred
  beads to an issue tracker (GitHub/GitLab/Jira) as a land-the-plane step, and enumerates
  upstream issues as the authoritative worklist on status/pull.
  TRIGGER when: /beads-upstream invoked; "set up upstream tracking" / "configure upstream"
  (init); "push beads upstream" / "push open work to GitHub"; asking for project status,
  available work, or the worklist when upstream tracking is configured (status/pull).
  SKIP for: routine local `bd ready` / `bd show` / `bd close` (use `beads`); direct-CLI
  `bd` scripting gotchas (use `beads-extra`); authoring beads-backed skills
  (use `beads-authoring`). The close-time / land-the-plane push trigger is NOT carried in
  this description — it lives in the always-loaded companion rule (protocols/UPSTREAM_TRACKING.md).
user-invocable: true
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - AskUserQuestion
---

# beads-upstream

A **utility skill** (no formula / `bd mol pour` / coordinator) that binds a beads workspace
to an upstream issue tracker. It owns three operations: `init` (configure a backend), the
**push step** (land-the-plane: push open/deferred beads upstream), and **status/pull**
(treat upstream issues as the worklist). GitHub is fully implemented; GitLab/Jira ship as
config-only stubs sharing the same verb shape.

Built on bd 1.0.5's first-class `bd github` / `bd gitlab` / `bd jira` upstream sync. For the
`bd` CLI gotchas these steps rely on (defensive `--json` parsing, issue-type semantics) see
`beads-extra`.

## SKILL_DIR

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name beads-upstream -type d 2>/dev/null | head -1)
[ -z "$SKILL_DIR" ] && { echo "ERROR: beads-upstream skill directory not found"; exit 1; }
```

All skill-internal paths use `${SKILL_DIR}/` prefix.

## Trigger split (the load-bearing design)

Two distinct trigger classes, deliberately routed to two different surfaces:

- **Intent triggers → this SKILL's `description`.** `init`, `status`/pull, "set up upstream
  tracking", "push beads upstream". Description-matching catches these reliably because the
  user states the intent.
- **Procedural trigger → the always-loaded companion rule** (`protocols/UPSTREAM_TRACKING.md`,
  installed to the rules surface). The push-at-session-close / land-the-plane step is *not*
  reliably caught by a description — nobody says "trigger the upstream skill" when wrapping
  up — so the rule binds it and is in context every turn. The rule is minimal: the close-time
  trigger + the one safety invariant + a pointer here. All procedure lives in this SKILL.

## Backends

| Backend  | Config namespace                         | Status      |
|----------|------------------------------------------|-------------|
| `github` | `github.owner` / `github.repo` / token   | implemented, dry-run-tested |
| `gitlab` | `gitlab.*`                               | config-only stub (unverified) |
| `jira`   | `jira.*`                                 | config-only stub (unverified; field model differs) |
| `none`   | `custom.upstream.enabled=false`          | first-class: upstream tracking fully disabled |

Auth is always passed **inline, never persisted**: `TOKEN=$(...) bd <backend> sync …`.

## `/beads-upstream init`

Configure the backend only. `init` does **not** write any rule file into the project — the
trigger contract ships as this skill's companion rule (installed by `install.sh`).

### 1 — Detect the remote and propose a backend

```bash
REMOTE_URL=$(git config --get remote.origin.url 2>/dev/null)
```

- `github.com` → propose `github`; `gitlab.*` → propose `gitlab`; otherwise propose `none`.
- Parse `owner`/`repo` from the URL (`…/<owner>/<repo>(.git)`).

### 2 — Confirm with the operator

Use `AskUserQuestion`: backend = `github` | `gitlab` | `jira` | `none` (detected default first).
`none` is a first-class choice — upstream tracking fully disabled.

### 3 — Write config

**GitHub** (analogous keys for `gitlab.*` / `jira.*`):

```bash
bd config set github.owner "<owner>"
bd config set github.repo  "<repo>"
bd config set custom.upstream.enabled true
bd config set custom.upstream.backend github
```

Never write a token to config. Auth is inline at call time: `GITHUB_TOKEN=$(gh auth token) bd github …`.

**`none`** — write an explicit *opted-out* marker (not merely unconfigured), so push/status
no-op and the close-time rule trigger stays silent; re-running `init` can re-enable:

```bash
bd config set custom.upstream.enabled false
bd config set custom.upstream.backend none
```

### 4 — `dolt.local-only` guard

Upstream tracking assumes the dolt DB is local-only (issues live upstream, not in a dolt remote).
Before flipping it, detect an existing remote — the operator may run one intentionally:

```bash
bd config get dolt.local-only          # current value
bd dolt remote list                    # any configured remote?
```

If a dolt remote **is** configured, confirm with the operator before `bd config set dolt.local-only true`.
If none, set it. Skip the flip entirely for backend `none`.

## Push step (land-the-plane)

Push **open + deferred** beads (blocked, descoped, discovered-but-not-done, follow-ups) upstream
as the session/plan closes. Closed beads are never pushed.

### 0 — Disabled short-circuit (first, always)

```bash
bd config get custom.upstream.enabled
```

If `false` / backend `none`: report "upstream tracking disabled" and **exit 0**. No enumeration,
no prompt, no upstream call.

### 1 — Auth pre-flight

Verify the token resolves **before** any push; fail fast on empty/expired:

```bash
GITHUB_TOKEN=$(gh auth token 2>/dev/null)
[ -z "$GITHUB_TOKEN" ] && { echo "ERROR: no GitHub token (run: gh auth login)"; exit 1; }
```

### 2 — Enumerate candidates

```bash
uv run ${SKILL_DIR}/scripts/upstream.py enumerate --json   # open+blocked+deferred, not-yet-mapped
```

The helper (see `scripts/upstream.py`) lists candidate bead IDs and flags those already carrying
an `External:` mapping (parsed defensively per `beads-extra`). Present the set; the operator
confirms the scoped IDs.

### 3 — Dry-run, then scoped push

Use the dedicated `bd github push` (≡ `bd github sync --push-only --issues <ids>`); **never a bare
`bd github sync`**:

```bash
GITHUB_TOKEN=$(gh auth token) bd github push <id1> <id2> … --dry-run   # confirm only intended beads
GITHUB_TOKEN=$(gh auth token) bd github push <id1> <id2> …             # real push
```

(For a whole subtree: `bd github sync --push-only --parent <id> --dry-run`.) After a successful
push, bd records the new issue URL on each bead as a single `External:` line in `bd show <id>`:

```
External: https://github.com/<owner>/<repo>/issues/<N>
```

This mapping is what suppresses duplicate creation on re-push (verified live on 1.0.5 — see step 5).

### 4 — Partial-push / failure handling

On non-zero `bd github push` exit: re-enumerate `External:` mappings, report **pushed-vs-remaining**
beads, and surface (never swallow) the error:

```bash
uv run ${SKILL_DIR}/scripts/upstream.py mappings --issues <id1>,<id2>,… --json
```

Do not blind-retry — a re-run on already-mapped beads is safe (step 5) but must be a *deliberate*
re-push of the remaining set, not a bare sync.

### 5 — Idempotency checkpoint (gates this step)

A re-push of an already-mapped bead must **not** create a duplicate upstream issue. This rests on
bd recording the `External:` mapping and suppressing re-push for mapped beads. **Verify on the live
binary against a throwaway repo before relying on it** (see `spec/` / the build-time check): dry-run
+ real scoped push of a fresh bead, then re-push the same bead and confirm no second issue. If
`bd github push` does not record the mapping the way bare `sync` does, redesign the recovery story
before trusting re-push.

> **Verified (bd 1.0.5, throwaway repo, 2026-06-01):** `bd github push <id>` records
> `External: …/issues/N` on the bead; a second `bd github push <id>` left the upstream issue count
> at 1 (no duplicate — it updates the mapped issue). The dedicated `push` subcommand records the
> mapping identically to bare `sync`, so scoped re-push is safe for partial-failure recovery.

## Status / pull

First read the config (`bd config get custom.upstream.enabled`).

**Disabled (`none` / `enabled=false`):** report "upstream tracking disabled" and fall back to
the local worklist — `bd ready` (unblocked) then `bd list --status open` (full inventory). No
upstream calls.

**Enabled:** the upstream tracker is the authoritative worklist (the local bead set may be
stale). Enumerate open upstream issues, ordered by labels/priority:

```bash
gh issue list --repo "<owner>/<repo>" --state open \
  --json number,title,labels,url --jq 'sort_by(.labels)'
```

Order the execution sequence by the issues' labels (severity/priority, `bug` before
`enhancement`, blocked-by relationships). Local beads are a convenience view over this list.
`bd github status` shows sync state (config + last-sync) but is not the worklist.

(GitLab/Jira: substitute `glab issue list` / Jira JQL — see Backend generalization.)

## Backend generalization

GitHub is the implemented, dry-run-and-live-tested path (see Push step step 5). GitLab and
Jira are **config-only stubs** — the config keys and verb shape are wired, but no push has
been exercised against a live GitLab/Jira instance. Do not present them as tested.

All three backends expose `push` / `pull` / `status` / `sync` subcommands. Scoped-push
translation (verified against `bd <backend> sync --help` on 1.0.5):

| Step          | GitHub                              | GitLab                              | Jira (unverified)                          |
|---------------|-------------------------------------|-------------------------------------|--------------------------------------------|
| Config        | `github.owner` / `github.repo`      | `gitlab.*` (+ `--project` group id) | `jira.*`                                    |
| Scoped push   | `bd github push <ids>`              | `bd gitlab push <ids>`              | `bd jira push <ids>`                        |
| ≡ sync form   | `sync --push-only --issues <ids>`   | `sync --push-only --issues <ids>`   | `sync --push --issues <ids>` ⚠             |
| Subtree push  | `sync --push-only --parent <id>`    | `sync --push-only --parent <id>`    | `sync --push --parent <id>` ⚠              |
| Dry-run       | `--dry-run`                         | `--dry-run`                         | `--dry-run`                                 |

⚠ **Jira divergence:** `bd jira sync` uses `--push` / `--pull` (not `--push-only` /
`--pull-only`) and adds `--create-only` for new-issues-only. Jira's field model (projects,
issue types, required fields) differs from GitHub/GitLab labels — the stub is unverified and
will likely need field mapping before a real push. Prefer the dedicated `bd jira push <ids>`
subcommand, which mirrors the others' positional-IDs shape.

The `--issues` / `--parent` / `--dry-run` flags are confirmed present on backend-generic
`bd <backend> sync` for all three (plan-003 Investigation Finding; re-verified here via
`bd <backend> sync --help`). The never-bare-`sync` invariant applies to every backend.

## Safety invariants

- **Never run a bare `bd <backend> sync`.** A bare sync re-imports every upstream issue as a
  duplicate bead and pushes the entire local DB (closed epics, gates, dupes) upstream. Always
  `--push-only` + scoped `--issues <ids>` (or `--parent <id>`), `--dry-run` first.
- **Auth is inline-only.** `TOKEN=$(...) bd <backend> sync …` — never write a token to config.
- **Disabled (`none`) is honored everywhere.** Push and status no-op cleanly; the close-time
  rule trigger is a silent no-op.

## See also

- **`beads`** — the canonical routine `bd` loop.
- **`beads-extra`** — defensive `--json` parsing, issue-type/gate semantics this skill relies on.
- **companion rule** `protocols/UPSTREAM_TRACKING.md` — the always-loaded close-time trigger.
  After editing it, restamp the hash: `uv run ${SKILL_DIR}/scripts/manifest_update.py ${SKILL_DIR}/protocols`.
