# Plan: Adopt bd remember (M2 clone-local memory) and build a beads-upstream skill (GitHub-first), with plugin-bridge refactors to beads-extra/beads-authoring

**ID:** plan-003-james-dixson-adacc7
**Author:** james-dixson
**Created:** 2026-06-01
**Status:** complete
**Phase log:**
- 2026-06-01 scoping: initial scope captured
- 2026-06-01 scoping: operator decisions locked (M2 per-project memory; GitHub-first; D3 folded in)
- 2026-06-01 drafting: plan v1 presented
- 2026-06-01 review: plan v1 presented
- 2026-06-01 drafting: review pass-1 concerns resolved (revised in place); awaiting operator approval
- 2026-06-01 drafting: 2.2/2.7 revised: ship minimal companion rule (protocols/UPSTREAM_TRACKING.md + manifest), lean on description-triggering for intent entry points
- 2026-06-01 approved: operator approved; portability audit pass
- 2026-06-01 approved: amended: backend 'none' (fully-disabled) is a first-class config option
- 2026-06-01 executing: start gate resolved
- 2026-06-01 complete: plan complete: 3 epics closed, beads-upstream shipped, plugin-bridge corrected, memory M2 adopted

## Objective

Three coupled deliverables, all triggered by installing the user-scope `beads` plugin (bd 1.0.5):

1. **Memory (M2):** adopt `bd remember` as clone-local working memory and deprecate `AGENTS/MEMORY.md`.
2. **`beads-upstream` skill:** generalize pybridge's `UPSTREAM_TRACKING.md` into a configurable, GitHub-first skill that pushes open/deferred beads to an issue tracker as a land-the-plane step.
3. **Plugin-bridge refactors:** correct/realign `beads-extra` and `beads-authoring` against the now-installed (and partly stale) `beads` plugin resource docs.

## Motivation

Installing the `beads` plugin (1.0.5) created three frictions in this repo:

- The plugin's `bd prime` SessionStart hook instructs every agent to use `bd remember` and **not** `MEMORY.md` files, directly contradicting this repo's `CLAUDE.md` (`@AGENTS/MEMORY.md` include + "review AGENTS/MEMORY.md on session start"). Agents now receive conflicting memory instructions every session.
- bd 1.0.5 ships first-class `bd github`/`bd gitlab`/`bd jira` upstream sync. The pybridge repo already encodes a working "dolt local-only + push open/deferred beads to GitHub" discipline (`~/workspace/evri/pybridge/AGENTS/UPSTREAM_TRACKING.md`), but it is hand-written per-project and GitHub-only. Generalizing it into a skill makes the discipline reusable and backend-configurable.
- The plugin's `resources/` docs are pre-1.0.5 (0.60.0/ACF-era) and wrong in places (`bd gate approve`/`eval`/`close`, bare `bd pour`/`bd wisp`, `bd mol catalog`). `beads-extra`/`beads-authoring` are the 1.0.5-verified layer and must explicitly correct, not silently overlap, the plugin.

## Upstream Issues

No open issue on `dixson3/beads-backed-skills` (#2–#8) relates to this work; all are pre-existing bdplan enhancements. No upstream incorporation, no reconcile gate. New follow-ups discovered during execution are filed via `gh issue` per repo convention.

## Investigation Findings

No separate investigation phase — the bd 1.0.5 CLI surface was verified directly against the installed binary during scoping:

- **Upstream backends:** `bd github`, `bd gitlab`, `bd jira` exist (plus `linear.*` config). `bd <backend> sync` supports `--push-only`, `--pull-only`, `--issues <csv>`, `--parent <id>` (mutually exclusive with `--issues`), `--dry-run`, and conflict policy (`--prefer-newer|local|github`). `bd <backend> status` exists. Config namespaces: `github.owner/repo/token` (+ env `GITHUB_TOKEN`), `jira.*`, `gitlab.*`.
- **Memory:** `bd remember`/`bd recall`/`bd memories`/`bd forget`; stored in the project dolt DB, injected at `bd prime`. JSONL export does **not** carry memories and "is not cross-machine sync." Cross-machine memory requires a dolt remote on the holding DB.
- **`--global`/`beads_global`:** a single shared DB (`beads_global`), not per-project DBs in a shared server. Machine-global at most; still not cross-machine without a dolt remote. Operator chose strict per-project (M2), so `--global` is not used.
- **Stale plugin docs confirmed against binary:** gate verbs are `create|check|resolve` (no `approve`/`eval`/`close`); chemistry is `bd mol pour`/`bd mol wisp` (bare `bd pour`/`bd wisp` → `unknown command`).
- **`-t` enum (authoritative `bd create --help`):** `bug|feature|task|epic|chore|decision` (custom types need `types.custom` config). `event` is created via `--type=event` (gated by `--event-*` flags), `gate` via `bd gate create`/formula — **not** general `-t` issue types. `beads-extra/SKILL.md:29` currently reads `bug | feature | task | epic | chore | molecule | gate | event`: it **omits `decision`**, lists **`molecule`** (a chemistry artifact, not a `-t` type), and treats `gate|event` as plain `-t` types without noting their special creation paths. Epic 3.2 corrects this.

**Build-time verification (not plan blockers), to perform during Epic 2/3:**
- Run `bd github sync --push-only --issues <id> --dry-run` and capture exact output shape + the `External:` mapping format it records, in a throwaway repo — **never** a bare sync against this repo.
- In an isolated DB (`bd --db /tmp/probe.db …`), probe `bd create -t {decision,gate,event,molecule}` to settle exactly which are accepted before rewriting the `beads-extra` list (Epic 3.2).

## Approach

- **Epic 1 (memory)** is independent and small: documentation-only edits in `CLAUDE.md` + removal of `AGENTS/MEMORY.md`, plus a grep sweep for dangling references. Triggers `optimal-instructions` (project instruction-file change).
- **Epic 2 (beads-upstream)** is the substantial deliverable: a **utility skill** (not a formula/coordinator beads-orchestration skill — no `bd mol pour`). It owns an `init` flow, a land-the-plane push step, and a status/pull step, with GitHub fully implemented and GitLab/Jira as config-only stubs sharing the same verb shape. The push trigger is a **skill-invoked step** (cross-harness portable), explicitly **not** a `settings.json` hook. Reliability comes from a **minimal always-loaded companion rule** (shipped under `protocols/`, like `bdplan`/`bdresearch`) that binds the close-time push trigger + the never-bare-sync invariant; all procedure lives in the SKILL.md, which leans on description-triggering for intent-based entry points (`init`, `status`). Auto-discovered by `install.sh` (no edit); added to the project README.
- **Epic 3 (plugin-bridge)** is corrective documentation work on `beads-extra`/`beads-authoring`: a "corrects-the-plugin" callout, a `-t` type-list fix, and converting duplicated dependency-taxonomy into citations to the plugin's stable docs.

Each epic ends with the repo's mandated checks: `AGENTS/CONSISTENCY.md` (sub-agent per modified skill), `AGENTS/DOCUMENTATION.md` (README sync), `AGENTS/OPTIMIZED_SKILLS.md` (token-efficiency), and `skill-authoring`/`optimal-instructions` where their triggers fire.

## Epics

### Epic 1: Memory adoption (M2) — deprecate AGENTS/MEMORY.md
- Issue 1.1: Rewrite the **Memory** section of `CLAUDE.md` with the M2 split — ephemeral/clone-local working memory → `bd remember`/`bd memories`/`bd recall` (injected at `bd prime`, never synced upstream); durable/cross-clone/behavioral knowledge → `AGENTS/` rules or a filed-and-upstreamed bead. **State the rationale**: `bd remember` is project-DB-local and not carried in JSONL export, so per the operator's global portability rule it must NOT be promoted to durable/portable use — durable knowledge stays in `AGENTS/` rules or upstreamed beads. Remove the `@AGENTS/MEMORY.md` include and the "review AGENTS/MEMORY.md on session start / prune superseded entries" instruction.
- Issue 1.2: Delete `AGENTS/MEMORY.md`.
  - depends-on: 1.1
- Issue 1.3: Grep sweep — confirm no remaining references to `AGENTS/MEMORY.md` anywhere (README, other `AGENTS/` rules, skills, install.sh). Fix any found. Run `optimal-instructions` on the changed `CLAUDE.md`.
  - depends-on: 1.2

### Epic 2: beads-upstream skill (GitHub-first)
- Issue 2.1: Scaffold `skills/beads-upstream/` — `SKILL.md` (YAML frontmatter, `user-invocable: true`, `allowed-tools`), `README.md` per `DOCUMENTATION.md`. Establish it as a **utility skill** (no formula/coordinator). **Trigger split (the load-bearing design):** the SKILL.md `description` carries the *intent*-triggered entry points only — `init`, `status`/pull, "set up upstream tracking", "push beads upstream" — which description-matching catches reliably. The *procedural* trigger (push at session-close / land-the-plane) is NOT reliably caught by a description, so it lives in the always-loaded companion rule (2.7), not the description. Gate: entry leaf.
  - depends-on: start-gate
- Issue 2.2: Implement `/beads-upstream init` — detect git remote → propose backend (`github|gitlab|jira|none`) → confirm via `AskUserQuestion`; write `<backend>.*` config via `bd config set`; document the inline-token auth pattern (`TOKEN=$(...) bd <backend> sync …`, never persisted). **`none` is a first-class choice — upstream tracking fully disabled.** Selecting `none` writes an explicit disabled marker (e.g. `custom.upstream.enabled=false`, `custom.upstream.backend=none` via `bd config set`) so the state is *opted-out*, not *unconfigured*; init completes cleanly and re-running `init` can re-enable. **`dolt.local-only` guard:** detect current value; if a dolt remote is already configured, confirm with the operator before flipping `local-only=true` (they may run a remote intentionally). `init` configures the backend only — it does **not** write any rule file into the target project (the trigger contract ships as the skill's companion rule, 2.7).
  - depends-on: 2.1
- Issue 2.3: Implement the land-the-plane **push step** — **first read the upstream config; if `custom.upstream.enabled=false` / backend `none`, no-op cleanly** (report "upstream tracking disabled" and exit 0 — no enumeration, no prompt). Otherwise: enumerate open/deferred beads (helper script, defensive JSON per `beads-extra`); `--dry-run` scoped push (`--push-only --issues <ids>` or `--parent`); operator confirm; push; record `External:` mappings. Hard guard against bare `bd <backend> sync`. **Failure paths (required):** (a) pre-flight auth check — verify the token resolves before any push; fail fast with a clear message if empty/expired. (b) Partial-push handling — on non-zero `bd sync` exit, re-enumerate `External:` mappings, report pushed-vs-remaining beads, and surface (never swallow) the error. (c) **Idempotency checkpoint (gates this issue's completion):** verify via dry-run + a real scoped push in the throwaway test repo that a re-push of an already-mapped bead does **not** duplicate upstream. If `--push-only --issues` does not record the mapping the way bare `sync` does, redesign the recovery story before declaring 2.3 done — the skill's safety rests on this.
  - depends-on: 2.2
- Issue 2.4: Implement the **status/pull** step — when disabled (`none`), report "upstream tracking disabled" and fall back to local `bd ready`/`bd list` as the worklist. When enabled, enumerate upstream issues as the authoritative worklist (not just local beads), ordered by labels/priority.
  - depends-on: 2.2
- Issue 2.5: Generalize across backends — GitHub implemented and dry-run-tested; GitLab/Jira as config-only stubs with a verb/translation table and an explicit "unverified; Jira field model differs" note. The stubs may claim the **same** `--push-only --issues/--parent --dry-run` flag shape — cite the Investigation Finding that verified these flags on backend-generic `bd <backend> sync` rather than asserting it.
  - depends-on: 2.3, 2.4
- Issue 2.6: Extract any JSON-parsing/orchestration bash into a `scripts/` Python helper (`uv run`, PEP 723) per `OPTIMIZED_SKILLS.md`.
  - depends-on: 2.3
- Issue 2.7: **Author the companion rule** `skills/beads-upstream/protocols/UPSTREAM_TRACKING.md` + `manifest.json` (vendor `manifest_update.py`, run it to stamp the hash), mirroring `bdplan`/`bdresearch`. `install.sh` needs **no edit** — it auto-discovers `skills/*/` and `install_rules` surfaces `protocols/*.md` to the rules dir (verified). **Prune the rule to the minimal trigger contract** (model on PLANS.md, ~15-20 lines): (a) the close-time trigger — on push-like ops / session or plan close / "land the plane", invoke `/beads-upstream` to push **open + deferred** beads upstream, **unless upstream tracking is disabled (`none`), in which case the trigger is a silent no-op** (so opted-out projects are never nagged); (b) the one safety invariant — never bare `bd <backend> sync`; always `--push-only` + scoped `--issues`/`--parent` + `--dry-run` first; (c) a one-line pointer to the SKILL for config/backends/auth. Everything else (init flow, backend table, failure handling) stays in SKILL.md, loaded only on activation. Add to project `README.md` skills index + prerequisites table + per-skill summary (`DOCUMENTATION.md`). Reference the push step from the land-the-plane / bdplan handoff narrative.
  - depends-on: 2.5, 2.6
- Issue 2.8: Run `AGENTS/CONSISTENCY.md` consistency sub-agent on `skills/beads-upstream/`; fix FAIL items; draft `spec/` if none exists.
  - depends-on: 2.7

### Epic 3: Plugin-bridge refactors (beads-extra / beads-authoring)
- Issue 3.1: R1 — add a "corrects-the-plugin" callout to `beads-extra` naming the stale plugin resources (`ASYNC_GATES.md` `bd gate approve`/`eval`/`close`; `CHEMISTRY_PATTERNS.md` bare `bd pour`/`bd wisp`/`bd mol catalog`) and stating this skill wins for 1.0.5.
  - depends-on: start-gate
- Issue 3.2: R3 — fix the `beads-extra/SKILL.md:29` `bd create -t` list. Current text: `bug | feature | task | epic | chore | molecule | gate | event`. Probe an isolated DB (`bd --db /tmp/probe.db create -t {decision,gate,event,molecule}`) and correct against `bd create --help` (authoritative enum: `bug|feature|task|epic|chore|decision`): **add `decision`**, **remove `molecule`** (chemistry artifact, not a `-t` type), and either drop `gate`/`event` from the `-t` list or annotate their special creation paths (`gate` via `bd gate create`/formula; `event` via `--type=event` + `--event-*` flags). Update the surrounding prose (the "`gate` is first-class" note) to match.
  - depends-on: start-gate
- Issue 3.3: R2/R4 — convert duplicated dependency-type taxonomy in `beads-extra`/`beads-authoring` into citations to the plugin's stable `resources/DEPENDENCIES.md` and `resources/WORKFLOWS.md`, keeping only the mutation/gotcha mechanics the plugin lacks.
  - depends-on: 3.1, 3.2
- Issue 3.4: Run `AGENTS/CONSISTENCY.md` sub-agent on `skills/beads-extra/` and `skills/beads-authoring/`; sync both READMEs (`DOCUMENTATION.md`); fix FAIL items.
  - depends-on: 3.3

## Gates

### Start Gate (mandatory)
- Type: human
- Approvers: operator

No capability gates (no external preconditions; GitHub push is validated by `--dry-run` at build, not a human gate). No reconcile gate (no upstream issues incorporated).

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `beads-upstream` live push has irreversible side effects (creates real upstream issues) | Skill bakes in `--dry-run`-first + scoped `--issues`/`--parent` + operator confirm; **never** bare-sync. Build-time idempotency/live-push testing uses a **throwaway GitHub repo under the operator's account** (real repo needed so `External:` mapping formats), created for the test and torn down after — never this repo. |
| Re-push after partial failure duplicates upstream issues | Idempotency checkpoint in 2.3 verifies `External:`-mapping suppresses re-push before the step is declared done; auth pre-flight + partial-failure reporting prevent blind re-runs. |
| Removing `AGENTS/MEMORY.md` leaves dangling `@`-includes or instructions | Issue 1.3 grep sweep across repo before close. |
| `beads-extra` `-t` assertion wrong again | Issue 3.2 re-probes the live binary before asserting. |
| Jira/GitLab stubs imply tested support | Stubs explicitly labelled unverified; Jira field-model divergence called out. |
| Push step / bdplan land-the-plane integration drifts from `bd` reality | Reference, don't restate, `bd <backend> sync` flags; cite `beads-extra` for JSON parsing. |

## Success Criteria

1. `CLAUDE.md` contains no `@AGENTS/MEMORY.md` include; `AGENTS/MEMORY.md` is deleted; the Memory section states the M2 split; `grep -ri 'AGENTS/MEMORY.md'` over the repo is clean (excluding this plan + git history).
2. `skills/beads-upstream/` exists with a frontmatter-valid `SKILL.md` (description carrying intent-triggers + SKIP), `README.md`, `init` + push + status/pull procedures; backend `none` (fully-disabled) is a valid init choice that makes push/status no-op and the close-time trigger silent; GitHub path dry-run-verified; GitLab/Jira config stubs present and labelled. A pruned companion rule `protocols/UPSTREAM_TRACKING.md` (close-time push trigger honoring the disabled flag + never-bare-sync invariant + SKILL pointer) ships with a hash-stamped `manifest.json`; auto-discovered by `install.sh`; added to project `README.md`. `CONSISTENCY.md` sub-agent returns no unresolved FAIL.
3. `beads-extra` has the corrects-the-plugin callout, a 1.0.5-correct `-t` list, and taxonomy citations; `beads-authoring` taxonomy references are citations; both READMEs synced; `CONSISTENCY.md` clean.
4. All changes committed; relevant `gh issue`s filed/closed; `git push` succeeds and `git status` is clean.
