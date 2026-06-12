---
name: beads-init
description: >
  Verify, initialize, and repair a functioning beads (`bd`) configuration in a repository,
  and the shared dependency-verification home that other beads skills' preflights route to.
  TRIGGER when: /beads-init invoked; a repository is being set up for beads and `bd` is
  present but the repo's beads configuration is **non-existent, incorrect, or appears
  corrupted** (e.g. `bd status` errors, `bd doctor` reports errors, a wedged schema
  migration, or `bd ready`/`bd list` work while `bd status` does not); or another beads
  skill's preflight reports `system_deps_missing` / `bd_not_initialized` / a corrupted DB.
  SKIP when: bd is healthy (`beads_init.py verify` returns `ok`) and you only need routine
  issue operations (use the `beads` skill); for direct-CLI gotchas use `beads-extra`.
user-invocable: true
skill-group: beads
depends-on-tool: [bd, uv, git]
depends-on-skill: [beads-extra]
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
---

# beads-init

The dependency-verification and repair home for a functioning beads configuration. Other
beads-backed skills (`bdplan`, `bdresearch`, `beads-upstream`, …) verify prerequisites in
their own preflight; when that preflight reports missing deps, an uninitialized repo, or a
corrupted DB, it routes here. This skill is also invoked directly when standing up beads in a
new repository.

## SKILL_DIR

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name beads-init -type d 2>/dev/null | head -1)
[ -z "$SKILL_DIR" ] && { echo "ERROR: beads-init skill directory not found"; exit 1; }
```

## The engine

```bash
uv run ${SKILL_DIR}/scripts/beads_init.py verify --json-output     # READ-ONLY health check
uv run ${SKILL_DIR}/scripts/beads_init.py repair                   # dry-run: print the fix plan
uv run ${SKILL_DIR}/scripts/beads_init.py repair --apply           # apply the standard repairs
uv run ${SKILL_DIR}/scripts/beads_init.py repair --apply --local-only   # also assert no Dolt remote
uv run ${SKILL_DIR}/scripts/beads_init.py status                   # one-line human status
```

`verify` is the canonical preflight check. It returns `status ∈ {ok, deps_missing,
not_initialized, corrupted}` with `diagnostics` and `remediations`.

## The one correction that matters most

`bd status --json` can return an **error JSON with exit code 0**. A preflight that trusts the
exit code — or that maps any `bd status` failure to "not initialized" — produces a **false
negative**: the repo *is* initialized, just wedged. The classic signature:

- `bd ready` / `bd list` / `bd create` all work, **but** `bd status` returns
  `{"error": "...pending schema migrations alter pre-existing dirty tables..."}`.
- `bd doctor` shows the DB version behind the CLI version.

`verify` inspects the parsed JSON for an `error` key instead of trusting the exit code, so it
classifies this as `corrupted` (repairable), never `not_initialized`.

## Procedure

1. **Verify.** Run `verify --json-output`. Branch on `status`:
   - `ok` — nothing to do.
   - `deps_missing` — install the listed tools (`bd` ≥ 1.0.5, `uv`, `git`); stop.
   - `not_initialized` — no usable `.beads/`. Confirm intent, then `bd init`, then go to step 3.
   - `corrupted` — initialized but wedged/broken; go to step 2.
2. **Diagnose & repair.** Run `repair` (dry-run) to see the plan, then `repair --apply`. The
   standard repairs, in order:
   - **Wedged schema migration** (the common case): `bd dolt stop` flushes and clears the
     in-memory Dolt working set; then `bd migrate schema` applies pending migrations; then
     bare `bd migrate` updates the DB metadata version. *Do not* try `bd vc commit` first —
     it cannot open the wedged DB (chicken-and-egg).
   - **Permissions:** `chmod 700 .beads` (bd warns at `0750`).
   - **Outdated git hooks:** `bd hooks install --force`.
   - **Gitignore drift:** `bd doctor --fix`, then top up any patterns it misses (the engine
     adds them): `.beads/.gitignore` ← `.env, export-state.json, embeddeddolt/, proxieddb/,
     dolt-server.activity, daemon.*, *.lock, *.corrupt.backup/, .beads-credential-key,
     proxied_server_client_info.json`; project `.gitignore` ← `.beads-credential-key,
     .beads/proxieddb/`.
   - **Portable record:** `bd export -o .beads/issues.jsonl` (ensure it is **not** gitignored).
3. **Re-verify.** Run `verify` again; expect `ok`. Then `bd doctor` — 0 errors. Classify
   remaining warnings: *accepted by design* vs *actionable*. `Remote Consistency: No remotes
   configured` is **accepted** when the repo is intentionally local-only (resolving it would
   add a Dolt remote); `Dolt Status` / `Git Working Tree` warnings are transient (clear on
   commit).

## Local-only repositories

When beads is intentionally local-only (issues live upstream, e.g. GitHub, not in a Dolt
remote): `bd config set dolt.local-only true`, keep `bd dolt remote list` empty, and never
`bd dolt push`. `repair --apply --local-only` sets the flag. Upstream issue tracking is the
`beads-upstream` skill's job.

## As a preflight dependency for other beads skills

This skill is the home for "is bd usable here?". A beads skill's preflight should:

1. Run its own system-deps + rule checks.
2. On a beads-config failure (`bd_not_initialized`, a corrupted DB, or a `bd status` error
   JSON), route the operator to `/beads-init` (or run `beads_init.py verify` / `repair`)
   rather than re-deriving the repair steps. The always-loaded companion rule
   `protocols/BEADS_INIT.md` carries this trigger so it fires regardless of which skill is
   active.

## Reference skills

- **`beads`** — routine `bd` loop once the config is healthy.
- **`beads-extra`** — direct-CLI gotchas (issue types, dep edges, `--json` parsing).
- **`beads-upstream`** — push open/deferred beads to a GitHub/GitLab/Jira tracker (local-only DB).
