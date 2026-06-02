# Upstream Tracking Protocol

Always-loaded trigger contract for the `beads-upstream` skill. Procedure (init, backends,
auth, failure handling) lives in the skill's `SKILL.md`; this rule binds only what a
description cannot reliably catch.

## Close-time push trigger

On push-like operations, session or plan close, or "land the plane": invoke `/beads-upstream`
to push **open + deferred** beads (blocked, descoped, discovered-but-not-done, follow-ups)
upstream before the session ends.

**Unless upstream tracking is disabled** (`custom.upstream.enabled=false` / backend `none`),
in which case this trigger is a **silent no-op** — do not enumerate, prompt, or nag.

## Safety invariant

Never run a bare `bd <backend> sync` — it re-imports every upstream issue as a duplicate bead
and pushes the whole local DB upstream. Always `--push-only` (Jira: `--push`) + scoped
`--issues <ids>` / `--parent <id>`, and `--dry-run` first. Auth is inline-only
(`TOKEN=$(...) bd <backend> …`), never written to config.

For config, backends, and failure handling, see the `beads-upstream` SKILL.
