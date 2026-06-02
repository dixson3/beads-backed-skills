# Upstream Issue Triage: executor crash recovery resume orphan review report capture retro portability

Instructions: For each issue, set disposition to: include, exclude, partial, supersede.
Add notes as needed. When done, say "triage ready".

_Full issue bodies are inlined under `references/upstream-<N>.md` (regenerated on re-triage)._

## #2 — bdplan: cross-session crash recovery and orphan cleanup for executor

> ## Summary

When a `bdplan execute` session crashes mid-run (OOM, timeout, user abort), the next session has no structured way to detect the interrupted epic and resume it cleanly. The current flow cr...

**Disposition:**
**Notes:**

## #3 — bdplan: make plan folders self-contained / portable before intake

> ## Summary

bdplan plans accumulate substantial context during the scoping → investigating → drafting → review lifecycle. Much of that context lives **in the drafting conversation** rather than in the...

**Disposition:**
**Notes:**

## #4 — bdplan: capture review report to reviews/pass-N.md immediately when review is presented
Labels: enhancement
> ## Problem

When `/bdplan` runs the review phase, the reviewer's full output (verdict, concerns, recommendations) is presented in the conversation but is **not automatically written to `reviews/pass-N...

**Disposition:**
**Notes:**
