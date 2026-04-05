# Portability Specification

<!-- activation: 2026-04-05 -->

Plans are portable artifacts. A cold reader on a different machine, in a different repo, with no access to the drafting conversation, must be able to understand why a plan exists, what environment it assumes, what reviewers flagged, and what upstream issues it resolves — from the plan folder alone.

## Activation

REQ-PORT-ACT: The portability contract activated on **2026-04-05**. Plans whose first `scoping:` phase-log entry is on or after this date are subject to hard audit enforcement at intake. Plans whose first scoping entry is earlier are grandfathered: missing scaffolding yields `warn` findings instead of `fail`.
Rationale: Pre-existing plans in other projects must not be blocked from intake on their next use. The activation date lets new plans get full enforcement while giving existing plans a graceful migration path via `/bdplan capture`.
Verification: `plan_manager.py::PORTABILITY_ACTIVATION_DATE` matches the date in this file's activation header.

## Contract

REQ-PORT-001: Every plan folder under `docs/plans/<plan-id>/` must contain `README.md` at the plan root with file-map and reading-order sections.
Rationale: The README is the entry point for a cold reader. Without it, the reader has no orientation to the folder's contents.
Verification: `plan_manager.py audit` checks file presence and required section headers `File map` and `Reading order`.

REQ-PORT-002: Every plan folder must contain `context.md` at the plan root with non-empty required sections: Project environment, Tool inventory, Paths, Operator identity, Runtime assumptions.
Rationale: Runtime assumptions and tool versions are load-bearing but never derivable from `plan.md` alone. A cold reader on a different machine needs to know whether the plan is safe to execute as-is.
Verification: `plan_manager.py audit` enforces per-section non-emptiness. Optional sections (Adjacent-concept glossary, Additional context) may be empty.

REQ-PORT-003: `context.md` Tool inventory section must include a snapshot header of the form `<!-- snapshot: host=<hostname> date=<YYYY-MM-DD> -->`. Tool versions are recorded as best-effort; missing tools are `not present`.
Rationale: Tool snapshots are inherently machine-specific. The header tells the cold reader where and when the snapshot was taken so they can judge staleness.
Verification: `_detect_tools` in `plan_manager.py` produces the snapshot header via `_portability_snapshot_header`.

REQ-PORT-004: Every plan must capture its motivation — the "why this exists" — either as a `## Motivation` section in `plan.md` or as a `motivation.md` file at the plan root. Neither may be empty nor contain only the seed placeholder text.
Rationale: The motivating use case is the most-likely-to-be-lost class of context during scope reframings. A cold reader cannot judge a plan's value without it.
Verification: `plan_manager.py audit` checks both locations and rejects placeholder text.

REQ-PORT-005: Every non-exclude row in plan.md's Upstream Issues table must have a corresponding `references/upstream-<N>.md` file containing the full issue body, URL, state, and labels.
Rationale: Upstream issue bodies must travel with the plan folder. `gh issue view` does not resolve across repositories and does not work offline.
Verification: `plan_manager.py audit` counts non-exclude rows and `references/upstream-*.md` files; counts must match.

REQ-PORT-006: The number of `reviews/pass-*.md` files must equal the number of `^- \d{4}-\d{2}-\d{2} review:` lines in plan.md's phase log. Pass numbering is strict and deterministic — `pass-N.md` where `N` is the review-line count immediately after the phase-log entry is written.
Rationale: Reviewer verdicts degrade to one-line phase-log entries unless captured. Strict correspondence prevents silent loss on REVISE loops.
Verification: `plan_manager.py audit` compares `len(glob('reviews/pass-*.md'))` to review-line count.

REQ-PORT-007: Plan files may not contain dangling external references. Dangling is defined as: absolute paths matching `/Users/`, `/home/`, `/opt/`, `/var/`, `/tmp/`, `/etc/`, or `C:\`; or parent-traversal `../`. Repo-relative paths (`skills/bdplan/SKILL.md`) are explicitly allowed. Content inside fenced code blocks and inline code spans is exempt — pattern documentation and command examples legitimately mention such paths.
Rationale: Absolute paths and parent-traversal break the moment a plan folder moves. Repo-relative paths are portable under any repo clone.
Verification: `plan_manager.py audit` greps all plan files after stripping code spans.

## Audit Invariants

REQ-PORT-010: The portability audit is **mechanical only** — file existence, grep, placeholder detection, regex. No semantic evaluation. No LLM calls.
Rationale: Semantic audits are non-deterministic and cannot be version-controlled. Mechanical checks produce the same verdict on the same input forever.
Verification: `_audit_plan` in `plan_manager.py` uses only stdlib (`pathlib`, `re`, `subprocess`) — no external deps beyond click.

REQ-PORT-011: The audit overall status is `pass` iff no finding has status `fail`. Warn findings do not degrade overall status. A `fail` finding halts intake.
Rationale: Two-level severity lets the grandfather clause downgrade without removing the audit entirely.
Verification: `_audit_plan` sets `status = "fail" if any_fail else "pass"`.

REQ-PORT-012: The audit is inserted into SKILL.md Phase 4 between `update-status approved` (§4.1) and `bd mol pour` (§4.2). It is a script exit-code check, NOT a bd gate. The term "gate" is reserved for bd gates.
Rationale: A bd gate would require its own beads and dependencies; the audit is a pre-molecule precondition and has no ongoing execution state.
Verification: SKILL.md §4.1a contains the audit dispatch snippet; no `bd create -t gate` call in the audit path.

## Override

REQ-PORT-020: `/bdplan execute --force-intake` (alias `/bdplan intake --force`) bypasses the portability audit. The override must append a phase-log entry of the form `- YYYY-MM-DD approved: intake forced past audit — reasoning: <operator reason>`. Unlogged overrides are forbidden.
Rationale: A hard audit with no escape hatch produces operator frustration in legitimate edge cases; an unlogged escape hatch hides quality regressions. Mandatory reasoning gives the audit teeth without blocking operator judgment.
Verification: SKILL.md §4.1a documents the override and the phase-log line format.

## /bdplan capture

REQ-PORT-030: `/bdplan capture [<plan-id>]` is re-entrant, status-agnostic (runs in any phase before intake), and **does not advance plan status**. It does not mutate beads or pour molecules.
Rationale: Capture is a maintenance operation on the plan folder, not a phase transition. Advancing status would conflict with the scoping/investigating/drafting workflow.
Verification: SKILL.md "Phase: CAPTURE (manual)" section explicitly states "does NOT advance plan status"; `/bdplan capture` path in SKILL.md has no `update-status` call.

REQ-PORT-031: `/bdplan capture` drafts missing contract files via the captor agent (`agents/captor.md`). The captor is read-only — drafts are returned for operator review and written by the main session only on approval.
Rationale: Mirrors the reviewer pattern (REQ-AGENT-043) and keeps agent scope clean (per REQ-AGENT-050).
Verification: `agents/captor.md` Rules section: "Never write files. The main session writes after operator approval."
