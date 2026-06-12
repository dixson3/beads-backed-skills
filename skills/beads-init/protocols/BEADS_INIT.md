# Beads Initialization & Health Protocol

Always-loaded trigger contract for the `beads-init` skill. The procedure (verify/repair
engine, the wedged-migration fix, gitignore/hooks/permissions hardening, local-only config)
lives in the skill's `SKILL.md`; this rule binds only the triggers a description cannot
reliably catch. It is the shared **dependency-verification home** for every beads-backed
skill.

## Preflight trigger (all beads skills)

Before relying on `bd` in a repository — and as the first step of any beads skill's preflight
(`bdplan`, `bdresearch`, `beads-upstream`, the `beads` loop) — the beads configuration must be
**verified functional**, not merely present. If verification fails, invoke `beads-init`
(`beads_init.py verify`, then `repair`) before proceeding.

A beads config counts as needing `beads-init` when, with `bd` on PATH, the repo config is:

- **non-existent** — no usable `.beads/` (`bd init` needed); or
- **incorrect** — outdated hooks, gitignore drift, stale DB metadata, wrong permissions; or
- **corrupted / wedged** — `bd status` fails while `bd ready`/`bd list` work.

## The false-negative invariant

**Never infer "bd not initialized" from `bd status`'s exit code alone.** `bd status --json`
can return an **error JSON with exit 0** (e.g. a pending schema migration blocked by a dirty
Dolt working set). Inspect the parsed JSON for an `error` key. An initialized-but-wedged repo
must be classified **corrupted** (repairable via `beads-init`), never **not_initialized** —
the latter would wrongly send the operator to `bd init` and risk clobbering real data.

## Repair safety invariants

- The wedged-migration fix is `bd dolt stop` → `bd migrate schema` → `bd migrate`. Do **not**
  attempt `bd vc commit` first — it cannot open the wedged DB.
- Hardening (hooks, gitignore, metadata, perms, JSONL export) is idempotent and safe to re-run.
- For local-only repos, never add a Dolt remote or `bd dolt push`; assert
  `bd config set dolt.local-only true`. Upstream issue tracking routes to `beads-upstream`.

## Silent no-op

When `beads_init.py verify` returns `ok`, this trigger is a **silent no-op** — do not prompt,
nag, or re-run repairs. Bootstrap/repair is offered only on an actual failure or explicit
`/beads-init` invocation.

For the verify/repair engine, the full repair sequence, and local-only setup, see the
`beads-init` `SKILL.md`.
