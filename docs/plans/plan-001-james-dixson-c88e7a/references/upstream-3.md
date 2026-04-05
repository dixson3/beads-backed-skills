# Upstream #3: bdplan: make plan folders self-contained / portable before intake

- **Number:** 3
- **Title:** bdplan: make plan folders self-contained / portable before intake
- **URL:** https://github.com/dixson3/beads-backed-skills/issues/3
- **State:** OPEN
- **Labels:** 

## Body

## Summary

bdplan plans accumulate substantial context during the scoping → investigating → drafting → review lifecycle. Much of that context lives **in the drafting conversation** rather than in the plan folder itself. If a plan is moved to another project, or context is cleared before intake, or a new operator picks up the plan later, load-bearing information is lost.

This issue requests an enhancement to the bdplan skill: **treat plan folders as portable artifacts from day one**, and add a `/bdplan capture` (or equivalent) step that runs regularly during planning — particularly before intake — to ensure every plan folder is self-contained.

## Motivating example

During a recent plan (`plan-002` in `dixson3/obsidian-primary`: "Cross-project communication substrate"), the operator asked mid-way through drafting: *"if I moved this plan to another project, or cleared context before intake, what important context would I lose?"*

Audit found **seven distinct classes of information** that existed only in the drafting conversation, not in the plan folder:

1. **The motivating use case / workflow** that explained why the plan existed. The plan's `plan.md` had been rewritten during a scope reframing, and the concrete workflow the user originally described was dropped in favor of an abstract framing. Cold readers saw "cross-project communication substrate" without the 11-step flow that motivated it.
2. **Project environment context** — tool versions (in this case: `bd 0.62.0`, which was load-bearing because the plan's transport decision depended on bd NOT having scoped replication yet), control and work project paths, attribution conventions, Python/uv conventions.
3. **Relationships to adjacent concepts** — in this case, `smgr` (a downstream consumer of the plan's output) was referenced throughout but never explained. A cold reader had no grounding.
4. **Reviewer verdicts and their resolutions** — two red-team review passes had produced 12 concerns + 5 follow-up clarifications. Only one-line phase-log entries survived.
5. **Upstream issue bodies** — the plan referenced `obsidian-primary#3` as prior art, but the issue body only survived as `gh issue view 3` output. Moving the plan to another repo would break the reference.
6. **Scope-reframing history** — the original plan was rescoped mid-drafting after the operator clarified intent. The reasoning was in conversation; only a one-liner survived in the phase log.
7. **Assumptions about the operating environment** — same-machine topology, git remotes exist, bd databases are local, Python + uv available, Claude Code CLI available. None stated anywhere in the plan folder.

The operator and I addressed the gap by writing six new files into the plan folder (`README.md`, `context.md`, `orchestration-flow.md`, `reviews/pass-1-verdict.md`, `reviews/pass-2-verdict.md`, `references/obsidian-primary-issue-3.md`) and adding a \"Read first\" pointer to the top of `plan.md`. This was manual and ad-hoc.

**It should be a bdplan skill feature.**

## Proposal

Add a context-capture / reconcile step to the bdplan lifecycle that regularly ensures plan folders are self-contained. Concretely:

### 1. Portability contract

Every bdplan plan folder must satisfy, before intake:

- **`README.md`** at the plan root: orientation, file map, status, reading order.
- **`context.md`** at the plan root: project environment, tool inventory (with versions of load-bearing tools), control/work project paths, operator identity + attribution, assumed runtime environment, adjacent-concept glossary (e.g., \"what is smgr\").
- **Motivating use case** captured somewhere. Either inline in `plan.md` or as a dedicated file (`motivation.md` / `orchestration-flow.md` / similar). A cold reader must be able to answer \"why does this plan exist?\" without consulting the drafting conversation.
- **Inlined upstream issue bodies** for any issue referenced in the plan. A `references/` directory with one file per issue. Never rely on `gh issue view` resolving from a different repo context.
- **Reviewer verdicts preserved.** A `reviews/` directory capturing each review pass (verdict + concerns + resolutions). One-line phase-log entries are insufficient for post-hoc understanding.
- **Scope-change history** if the plan was rescoped mid-drafting. Either as dedicated phase-log entries with reasoning, or as a short memo under `context.md`.
- **No dangling references** to files outside the plan folder that a cold reader would need. Either inline, or explicitly marked as \"vault-local, will not travel\".

### 2. Automation

Two possible implementation shapes:

**Option A — `/bdplan capture` subcommand.** Operator-invoked. Scans the current plan folder against the portability contract, reports gaps, optionally drafts the missing files (README/context/orchestration-flow) by reading `plan.md`, findings, phase log, and any referenced external files. Operator reviews and commits.

**Option B — Automatic step in existing phases.**
- **Scoping phase:** auto-create `README.md` + `context.md` stubs as soon as the plan directory is minted. Populate the tool inventory via a detection script (`bd --version`, `git --version`, etc).
- **After each review:** append that review's verdict to `reviews/`.
- **At intake (before the start gate is wired):** run the portability audit and REFUSE to proceed if the contract is not satisfied. This is the \"regularly\" step — intake is the natural forcing function because the plan is about to be handed off to a new execution session.

Recommend **Option B** for default behavior (runs automatically, no extra operator command) with **Option A** as an explicit manual trigger for mid-plan checkpoints.

### 3. Intake becomes a hard gate on portability

Currently, `/bdplan execute` is the session handoff. Planning-phase agents must not execute code changes; intake is where beads are created and the start gate is wired. **Add a portability check as a precondition for intake completing.** If `README.md` is missing, if `context.md` has unfilled placeholders, if a `reviews/` entry is missing for the most recent review, intake fails with a clear message and a list of missing items.

### 4. Retrospective capture command

For plans drafted before this feature exists: `/bdplan capture --retro` reads the plan folder and the conversation history (if available), drafts the missing portability files, presents them for operator review, commits.

## Why \"before intake\" specifically

Intake is the point where the plan transitions from \"living in a drafting conversation\" to \"living in beads, ready to be executed by a potentially-different session/operator.\" After intake, the drafting conversation is no longer the source of truth. Any information that didn't make it into the plan folder by intake time is effectively lost to all future readers.

The portability contract should therefore be enforced **at intake**, not earlier (when it would be premature) and not later (when the information may already be gone).

## Success criteria

- Every plan folder under `docs/plans/` can be moved to a different repository and remain readable/executable by an operator who was not party to the drafting conversation.
- A new operator picking up an approved plan can answer \"why does this exist, what environment does it assume, and what did the reviewers flag?\" from the plan folder alone.
- Intake cannot complete for a plan that fails the portability audit.
- Retrospective capture works on the existing `plan-002` plan folder as a real-world test case.

## References

- The plan that surfaced this requirement: `dixson3/obsidian-primary` → `docs/plans/plan-002-james-dixson-f54627/` (the post-capture state of this plan folder is a reference implementation of what the contract should produce).
- bdplan skill source: `dixson3/beads-backed-skills` (this repo) → `skills/bdplan/`.
- Related: bdplan's existing `AGENTS/PLANS.md` protocol — this proposal extends rather than replaces the existing phase model.

---

Filed by James Dixson based on a concrete portability gap encountered mid-drafting on plan-002. The ad-hoc fix applied to that plan is a working example of what the automated feature should produce.
