# Drift-Check Trigger Protocol

Always-loaded firing surface for the `drift-check` skill. The engine is `user-invocable: false`,
so a `description` alone cannot reliably fire it — this rule binds the on-edit trigger that a
description cannot. Procedure (manifest schema, the four checks, bootstrap, dispatch) lives in
the skill's `SKILL.md` and `spec/`; this rule binds only when the engine runs.

## On-edit trigger

After any create or modify of a file, if the repo has an **approved** `DRIFT-CHECK.md` manifest
and the changed path matches one of that manifest's **Trigger Scope** (§6) globs, invoke
`drift-check`: dispatch the report-only `drift-verifier` over the edges that glob scopes to, and
act on the findings (FAIL → resolve in the same pass; INCONCLUSIVE → surface to the operator;
fixed-authority conflict → halt per the manifest's §7 policy).

Per-repo scoping is the manifest's job — this rule carries the *when-to-fire* trigger; the
manifest's §6 globs carry *which paths* and *which edges*.

## Silent no-op

**Unless the repo has an approved `DRIFT-CHECK.md`** (REQ-ENGINE-001 / REQ-ENGINE-002), this
trigger is a **silent no-op** — do not check, prompt, nag, or offer to bootstrap. Bootstrap is
offered only on explicit invocation or first install (REQ-ENGINE-003), never on every edit.

## Scope boundary

drift-check verifies that already-written artifacts **agree** across declared edges. It never
authors, optimizes, or restructures, and never auto-fixes. Authoring/optimizing skill-dir
instruction files routes to `skill-authoring`; project-root `CLAUDE.md` / `AGENTS.md` routes to
`optimal-instructions`. drift-check never lists those project-root files as nodes, so it is
structurally silent on the project-root axis. On skill-dir files it may fire alongside
`skill-authoring` on an orthogonal axis (content agreement vs. authoring conventions); the
per-repo suppression lever is to omit the glob from the manifest's §6.

For the manifest schema, check semantics, and dispatch flow, see the `drift-check` `SKILL.md`
and `spec/`.
