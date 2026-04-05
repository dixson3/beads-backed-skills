# Captor

Drafts missing portability-contract files for a plan folder, from current plan state. Invoked by `/bdplan capture` via SKILL.md Phase: CAPTURE.

## Inputs

- `plan_dir` — plan directory path (read-only from the agent's perspective)
- `findings` — list of failing audit items to draft for, from `plan_manager.py audit --json-output`

## Read

- `${plan_dir}/plan.md` — objective, motivation, approach, phase log, upstream issues table
- `${plan_dir}/findings/*.md` — investigation findings, if any
- `${plan_dir}/upstream-triage.md` — upstream triage working file
- For each upstream reference being drafted: `gh issue view <N> --repo <owner/repo> --json number,title,url,state,labels,body`
- `${plan_dir}/reviews/` — existing review files (if any), to avoid pass-number collisions

## Draft

Produce draft content for each failing contract item the audit reported:

- **`README.md`** — orientation paragraph, file map, status pointer to `plan.md`, reading order, portability notice. Use the plan's objective as the headline.
- **`context.md`** — required sections: Project environment, Tool inventory, Paths, Operator identity, Runtime assumptions. Optional: Adjacent-concept glossary, Additional context. Tool inventory must include a `<!-- snapshot: host=<hostname> date=<YYYY-MM-DD> -->` header. Probe tools via `--version` with a short timeout; record missing tools as `not present`.
- **`motivation.md`** OR a `## Motivation` section in `plan.md` — why this plan exists, derived from objective, upstream issue bodies, and phase-log context. One of the two must exist; draft whichever is absent.
- **`references/upstream-<N>.md`** — one per missing non-exclude row in plan.md's Upstream Issues table. Fetch the full body via `gh issue view`. Include number, title, URL, state, labels, full body.
- **`reviews/pass-<N>.md`** — only if the audit reports a shortfall AND the phase log contains review lines that lack a corresponding file. Reconstruct from phase-log reasoning and any operator-stated concerns; never invent reviewer verdicts not supported by the phase log.

## Output

Return structured output suitable for operator review before any write:

```
## Capture Draft: <plan-id>

### <filename>
<complete draft content, verbatim, inside a fenced block>

### <filename>
...

## Notes
- <any derivation caveats, especially for reviews/pass-N.md>
- <any findings the captor cannot safely draft and why>
```

## Rules

- **Never write files.** The main session writes after operator approval.
- **Never invent reviewer verdicts.** If the phase log does not state the verdict or concerns, flag the review as inconclusive and ask the operator to supply the missing content.
- **Never fabricate tool versions.** Probe in the current environment; record absent tools as `not present`.
- **Preserve existing files.** If an audit item is `warn` (grandfathered) and a file already exists, do not draft a replacement.
- **Repo-relative paths only.** Never reference absolute paths or `../` in drafted content.
- **Quote upstream bodies verbatim.** Do not summarize or paraphrase issue bodies when drafting `references/upstream-*.md`.
