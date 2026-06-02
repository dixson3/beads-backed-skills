# Spec: Backends & trigger split

## Requirements

- **REQ-BE-001:** GitHub is the implemented, dry-run-and-live-tested backend. GitLab and Jira are
  config-only stubs and must not be presented as tested. — *Rationale:* honesty about coverage.
  — *Verify:* SKILL.md "Backend generalization" §.

- **REQ-BE-002:** Backend-generic scoped-push flags `--issues` / `--parent` / `--dry-run` are present
  on `bd github|gitlab|jira sync`; Jira diverges by using `--push`/`--pull` (not `--push-only`) and
  `--create-only`. — *Rationale:* the translation table must reflect the real CLI, not assume uniformity.
  — *Verify:* `bd github|gitlab|jira sync --help`; SKILL.md backend table.

- **REQ-BE-003:** All four backend states are first-class, including `none` (fully disabled,
  re-enableable). — *Rationale:* disabling is a supported configuration, not an error state.
  — *Verify:* SKILL.md Backends table; REQ-OP-003.

- **REQ-BE-004 (trigger split):** Intent triggers (`init`, `status`/pull, "set up upstream tracking",
  "push beads upstream") live in the SKILL `description`; the procedural close-time/land-the-plane
  push trigger lives only in the always-loaded companion rule, never in the description. — *Rationale:*
  a description cannot reliably catch "wrapping up"; an always-loaded rule can. — *Verify:* SKILL.md
  frontmatter description + "Trigger split" §; protocols/UPSTREAM_TRACKING.md.

- **REQ-BE-005:** This is a utility skill — no formula, `bd mol pour`, or coordinator loop. — *Rationale:*
  the work is config + scoped CLI calls, not a multi-bead DAG. — *Verify:* absence of `formulas/`,
  `bd mol pour` in SKILL.md.
