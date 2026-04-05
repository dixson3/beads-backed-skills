# plan-001-james-dixson-c88e7a

> Make bdplan plan folders self-contained and portable before intake (upstream #3)

This plan folder is **portable**. A reader should be able to understand the
plan's purpose, environment, reviewer history, and upstream context from the
files here alone — without access to the drafting conversation.

## File map

- `plan.md` — the plan. Authoritative status, phase log, objective, motivation,
  approach, epics, gates, risks, success criteria.
- `context.md` — project environment snapshot (tool versions, paths, operator,
  runtime assumptions) at the time the plan was authored.
- `references/` — inlined upstream issue bodies (`upstream-<N>.md`), one file
  per non-excluded row in plan.md's Upstream Issues table. Snapshots, not live.
- `reviews/` — reviewer verdicts (`pass-<N>.md`), one file per review cycle,
  in strict correspondence with the phase log's review lines.
- `findings/` — investigation experiment results (if any).
- `scope-answers.md` — scoping questionnaire answers (if complex scoping ran).
- `upstream-triage.md` — upstream disposition working file (source of truth is
  plan.md's Upstream Issues table; this file stays for context).
- `assets/` — diagrams, attachments, generated artifacts.

## Reading order

1. `plan.md` Objective + Motivation → why this plan exists
2. `context.md` → what environment it assumes
3. `references/` → upstream issues it addresses
4. `plan.md` Approach + Epics → how it will be executed
5. `reviews/` → what reviewers flagged and how it was resolved
6. `plan.md` Phase log → full history

**Read only from this folder.** If documentation outside this folder is
required to understand the plan, the portability contract has been violated.
