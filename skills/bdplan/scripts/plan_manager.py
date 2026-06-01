# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1",
# ]
# ///
"""Plan manager utility for the /bdplan skill.

Handles plan directory creation, index management, status queries,
and plan.md generation/updates.
"""

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click

PLANS_DIR = Path("docs/plans")
INCUBATOR_PARENT = Path("Incubator")

# Skill Surface Convention (see skill-authoring/reference/SURFACE_CONVENTION.md):
# operator config vs runtime state vs the hash-checked installed rule.
SKILL_NAME = "bdplan"
RULE_NAME = "PLANS.md"
CONFIG_FILE = Path(f".{SKILL_NAME}.local.json")          # operator decisions (gitignored)
STATE_DIR = Path(".state") / SKILL_NAME                  # runtime cache (gitignored)
STATE_FILE = STATE_DIR / "preflight.json"

# Idempotent project scaffold (Surface Convention §6/§7). Bump SCAFFOLD_VERSION
# when the anchor set changes — preflight re-ensures once per version.
SCAFFOLD_VERSION = 1
GITIGNORE_FILE = Path(".gitignore")
GITIGNORE_ANCHORS = (f"/{CONFIG_FILE}", "/.state/")      # enumerated, anchored, no globs


def _skill_surface() -> str | None:
    # Which surface this skill is installed under, from the script's own path.
    # Honor the invocation path first (a .claude/skills symlink keeps .claude),
    # then the resolved path (canonical tree when .claude/skills -> .agents).
    for p in (Path(__file__), Path(__file__).resolve()):
        parts = p.parts
        if ".claude" in parts:
            return ".claude"
        if ".agents" in parts:
            return ".agents"
    return None


def _skill_scope() -> str | None:
    # user-scope when the skill is installed under $HOME/.<surface> (e.g.
    # ~/.claude/skills); project-scope when installed inside a project tree.
    # Inferred from the dir that holds the surface element in the script's own
    # path. None when the skill resolves under no recognized surface.
    home = Path.home()
    for p in (Path(__file__), Path(__file__).resolve()):
        parts = p.parts
        for surface in (".claude", ".agents"):
            if surface in parts:
                idx = parts.index(surface)
                root = Path(*parts[:idx]) if idx > 0 else None
                return "user" if root == home else "project"
    return None


def _git_root() -> Path:
    # Project anchor for project-scope rule installs. Falls back to cwd outside a
    # git repo (matches the SKILL_DIR resolver's `|| echo .`).
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=2)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path(".")


def _rules_dir() -> Path:
    # Install target for the companion rule, anchored by scope and surface:
    #   user-scope    -> ~/.<surface>/rules
    #   project-scope -> <git-root>/.<surface>/rules
    # Both axes come from the skill's own install path. A dev checkout that
    # resolves under neither surface falls back to an existing project surface
    # (else .claude), project-anchored.
    surface = _skill_surface()
    scope = _skill_scope()
    if surface is None:
        surface = ".agents" if Path(".agents").is_dir() else ".claude"
        scope = "project"
    anchor = Path.home() if scope == "user" else _git_root()
    return anchor / surface / "rules"


def _rule_candidates() -> list[Path]:
    # Precedence order for an already-installed rule (installed by install.sh).
    # The user/global home dir (~/.<surface>/rules) is checked before the project
    # copy: a correct global copy satisfies any project, so no per-project install
    # is required. Trailing project-relative dirs catch a copy left by an earlier
    # surface/scope.
    seen: list[Path] = []

    def add(d: Path) -> None:
        if d not in seen:
            seen.append(d)

    surface = _skill_surface() or ".claude"
    other = ".agents" if surface == ".claude" else ".claude"
    add(Path.home() / surface / "rules")
    add(Path.home() / other / "rules")
    add(_rules_dir())
    add(Path(".agents/rules"))
    add(Path(".claude/rules"))
    return seen


MANIFEST_FILE = Path(__file__).resolve().parent.parent / "protocols" / "manifest.json"
MANIFEST_SCHEMA = 1

MIN_BD_VERSION = (1, 0, 5)

# Tools probed by _detect_tools (Epic 1.4). Each is best-effort; missing tools
# are recorded as "not present" and never fail init.
DETECT_TOOLS = ("bd", "git", "uv", "python", "gh", "glab", "claude")
DETECT_TIMEOUT_SEC = 2

# Portability contract activation date (spec/portability.md REQ-PORT-ACT).
# Plans whose first scoping phase-log entry is on/after this date get hard
# audit failures for missing scaffolding. Older plans get warns (grandfather).
PORTABILITY_ACTIVATION_DATE = "2026-04-05"


def get_git_user() -> str:
    """Get normalized git username for plan IDs."""
    try:
        name = subprocess.check_output(
            ["git", "config", "user.name"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        name = os.environ.get("USER", "unknown")
    # Normalize: lowercase, spaces to hyphens, filename-safe
    return "".join(
        c if c.isalnum() or c == "-" else "-" for c in name.lower().replace(" ", "-")
    ).strip("-")


RESEARCH_DIR = Path("docs/research")


def list_plan_roots() -> list[Path]:
    """Return every directory that may hold `plan-*` dirs.

    Globally numbered plans live across `docs/plans/` and per-incubator
    `Incubator/<slug>/plans/` roots; this function returns all that exist on
    disk so callers can enumerate or count across the whole vault.
    """
    return _list_kind_roots("plans", PLANS_DIR)


def list_research_roots() -> list[Path]:
    """Return every directory that may hold research item dirs.

    Research lives across `docs/research/` (deep-research vault-default) and
    per-incubator `Incubator/<slug>/research/` roots. Items are either
    deep-research topics (`NNN-topic-slug/` with `plan.yaml`) or rehoused
    bdplan plans (`plan-NNN-…/` with `plan.md`).
    """
    return _list_kind_roots("research", RESEARCH_DIR)


def _list_kind_roots(kind_dir: str, default_root: Path) -> list[Path]:
    roots: list[Path] = []
    if default_root.exists():
        roots.append(default_root)
    if INCUBATOR_PARENT.exists():
        for inc in INCUBATOR_PARENT.iterdir():
            if not inc.is_dir():
                continue
            p = inc / kind_dir
            if p.exists():
                roots.append(p)
    return roots


def _scope_for_root(root: Path, default_root: Path) -> str | None:
    """Return the incubator slug for a root, or None for the vault-default."""
    if root == default_root:
        return None
    try:
        return root.relative_to(INCUBATOR_PARENT).parts[0]
    except (ValueError, IndexError):
        return None


def _research_item_info(d: Path) -> dict | None:
    """Inspect a research-root child and classify it.

    Returns a dict for tracked items (deep-research topics or rehoused
    bdplan plans); returns None for flat `.md` notes or other unstructured
    siblings that just happen to live alongside research items.
    """
    if not d.is_dir():
        return None
    plan_yaml = d / "plan.yaml"
    plan_md = d / "plan.md"

    if plan_yaml.exists():
        topic = d.name
        try:
            for line in plan_yaml.read_text().splitlines():
                stripped = line.strip()
                if stripped.startswith("topic:"):
                    topic = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    break
        except OSError:
            pass
        return {"id": d.name, "topic": topic, "kind": "research", "path": str(d)}

    if plan_md.exists() and d.name.startswith("plan-"):
        topic = d.name
        try:
            for line in plan_md.read_text().splitlines():
                if line.startswith("# Plan: "):
                    topic = line[8:].strip()
                    break
        except OSError:
            pass
        return {"id": d.name, "topic": topic, "kind": "rehoused-plan", "path": str(d)}

    return None


def detect_incubator_from_cwd() -> str | None:
    """Return the incubator slug if CWD is inside `Incubator/<slug>/...`."""
    try:
        cwd = Path.cwd().resolve()
    except OSError:
        return None
    try:
        parent_abs = INCUBATOR_PARENT.resolve()
    except (OSError, FileNotFoundError):
        return None
    try:
        rel = cwd.relative_to(parent_abs)
    except ValueError:
        return None
    parts = rel.parts
    return parts[0] if parts else None


def resolve_plans_dir(incubator: str | None = None) -> Path:
    """Choose the plans root for a new plan.

    - explicit `incubator` → `Incubator/<slug>/plans`
    - else falls back to `docs/plans`
    """
    if incubator:
        return INCUBATOR_PARENT / incubator / "plans"
    return PLANS_DIR


def get_next_index() -> int:
    """Get next plan index by counting every plan-* dir vault-wide.

    Counts plan-* directories under both plan roots and research roots so
    rehoused plans (e.g. an old bdplan moved into `Incubator/<slug>/research/`)
    still consume a number and IDs stay globally unique.
    """
    total = 0
    for root in (*list_plan_roots(), *list_research_roots()):
        total += sum(
            1 for d in root.iterdir()
            if d.is_dir() and d.name.startswith("plan-")
        )
    return total + 1


def make_plan_id(objective: str) -> str:
    """Generate plan ID: plan-NNN-user-hash."""
    idx = f"{get_next_index():03d}"
    user = get_git_user()
    raw = f"{objective}{datetime.now().isoformat()}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:6]
    return f"plan-{idx}-{user}-{h}"


def make_plan_dir(plan_id: str, plans_dir: Path | None = None) -> Path:
    """Create plan directory structure under the given root.

    `plans_dir` defaults to `docs/plans` for back-compat; callers that
    target an incubator should pass `resolve_plans_dir(incubator)`.
    """
    root = plans_dir if plans_dir is not None else PLANS_DIR
    plan_dir = root / plan_id
    (plan_dir / "findings").mkdir(parents=True, exist_ok=True)
    (plan_dir / "assets").mkdir(parents=True, exist_ok=True)
    return plan_dir


def seed_plan_md(plan_dir: Path, plan_id: str, objective: str, author: str) -> Path:
    """Create initial plan.md with scoping status."""
    today = datetime.now().strftime("%Y-%m-%d")
    content = f"""# Plan: {objective}

**ID:** {plan_id}
**Author:** {author}
**Created:** {today}
**Status:** scoping
**Phase log:**
- {today} scoping: initial scope captured

## Objective
{objective}

## Motivation
_Why this plan exists: the problem, who is affected, what triggered the work.
Replace this placeholder before intake (portability contract)._

## Upstream Issues
| Issue | Title | Disposition | Notes | Resolved By |
|-------|-------|-------------|-------|-------------|

## Investigation Findings
_No investigations yet._

## Approach
_To be determined after scoping and investigation._

## Epics
_To be determined._

## Gates
### Start Gate (mandatory)
- Type: human
- Approvers: operator

## Risks & Mitigations
_To be determined._

## Success Criteria
_To be determined._
"""
    plan_md = plan_dir / "plan.md"
    plan_md.write_text(content)
    return plan_md


def _detect_tools() -> dict[str, str]:
    """Probe portability-relevant tools for their version strings.

    Epic 1.4: best-effort, 2s timeout per tool, missing/failing tools recorded
    as 'not present'. Never raises — init must proceed even if every probe
    fails.
    """
    # Each tuple: (binary, version-arg). --version works for all currently
    # probed tools; keeping the per-tool arg explicit in case that changes.
    probes = {
        "bd": ["bd", "--version"],
        "git": ["git", "--version"],
        "uv": ["uv", "--version"],
        "python": ["python", "--version"],
        "gh": ["gh", "--version"],
        "glab": ["glab", "--version"],
        "claude": ["claude", "--version"],
    }
    results: dict[str, str] = {}
    for name in DETECT_TOOLS:
        cmd = probes.get(name)
        if not cmd or not shutil.which(cmd[0]):
            results[name] = "not present"
            continue
        try:
            out = subprocess.check_output(
                cmd,
                text=True,
                stderr=subprocess.STDOUT,
                timeout=DETECT_TIMEOUT_SEC,
            )
            # Collapse multi-line output (gh prints multiple lines) to first
            # non-empty line — the version stamp.
            first = next((ln.strip() for ln in out.splitlines() if ln.strip()),
                         "unknown")
            results[name] = first
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                FileNotFoundError, OSError):
            results[name] = "not present"
    return results


def _portability_snapshot_header() -> str:
    """Tool-inventory snapshot header: hostname + detection date."""
    host = socket.gethostname() or "unknown-host"
    date = datetime.now().strftime("%Y-%m-%d")
    return f"<!-- snapshot: host={host} date={date} -->"


def seed_readme(plan_dir: Path, plan_id: str, objective: str) -> Path:
    """Write README.md orientation file (Epic 1.2)."""
    content = f"""# {plan_id}

> {objective}

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
"""
    path = plan_dir / "README.md"
    path.write_text(content)
    return path


def seed_context_md(plan_dir: Path, author: str,
                    tools: dict[str, str] | None = None) -> Path:
    """Write context.md with required/optional sections (Epic 1.3 + 1.4).

    Required sections audit-enforces non-empty: Project environment, Tool
    inventory, Paths, Operator identity, Runtime assumptions. Optional sections
    may be empty: Adjacent-concept glossary, Additional context.
    """
    if tools is None:
        tools = _detect_tools()
    header = _portability_snapshot_header()
    tool_lines = "\n".join(f"- `{name}`: {tools[name]}" for name in DETECT_TOOLS)
    try:
        cwd = str(Path.cwd().resolve())
    except OSError:
        cwd = "unknown"
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL, timeout=DETECT_TIMEOUT_SEC,
        ).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError, OSError):
        repo_root = cwd

    content = f"""# Project Environment Context

_Snapshot taken at plan-authoring time. Cold readers: verify these values
against the current environment before acting. The snapshot header below
records the machine and date of capture._

## Project environment

Describe the project this plan belongs to: what it does, what stack it uses,
any non-obvious setup. A cold reader should not need to infer this from code.

## Tool inventory

{header}

{tool_lines}

## Paths

- Repo root: `{repo_root}`
- Working directory at plan creation: `{cwd}`
- Plan directory: `{plan_dir}`

## Operator identity

- Git user: `{author}`
- Attribution: fill in role, contact, and authority scope before intake.

## Runtime assumptions

List the assumptions this plan makes about the environment it will execute in
(OS, shell, network access, credentials, side-effect permissions). A cold
reader on a different machine should be able to decide whether the plan is
safe to run as-is.

## Adjacent-concept glossary

_Optional._ Terms, acronyms, or project-specific jargon the plan uses.

## Additional context

_Optional._ Anything else a cold reader needs that does not fit above.
"""
    path = plan_dir / "context.md"
    path.write_text(content)
    return path


def seed_portability_scaffolding(plan_dir: Path, plan_id: str, objective: str,
                                 author: str) -> dict[str, str]:
    """Epic 1.1/1.5: seed README.md, context.md, references/, reviews/.

    Returns a dict of created paths suitable for merging into init JSON
    output. Best-effort tool detection runs inline — any probe failure is
    non-fatal (see _detect_tools).
    """
    readme = seed_readme(plan_dir, plan_id, objective)
    context = seed_context_md(plan_dir, author)
    references = plan_dir / "references"
    reviews = plan_dir / "reviews"
    references.mkdir(parents=True, exist_ok=True)
    reviews.mkdir(parents=True, exist_ok=True)
    return {
        "readme_md": str(readme),
        "context_md": str(context),
        "references_dir": str(references),
        "reviews_dir": str(reviews),
    }


def _write_upstream_reference(plan_dir: Path, issue: dict) -> Path:
    """Epic 2.1/2.2: write one references/upstream-<N>.md file per issue.

    Full (untruncated) body. Clobbers existing file on re-triage — operator
    hand-edits will be lost (see SKILL.md Phase 1.3 and Epic 2.3).
    """
    number = issue.get("number", "unknown")
    refs_dir = plan_dir / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    path = refs_dir / f"upstream-{number}.md"
    labels_raw = issue.get("labels") or []
    if labels_raw and isinstance(labels_raw[0], dict):
        labels = ", ".join(lbl.get("name", "") for lbl in labels_raw)
    else:
        labels = ", ".join(str(lbl) for lbl in labels_raw)
    content = f"""# Upstream #{number}: {issue.get("title", "")}

- **Number:** {number}
- **Title:** {issue.get("title", "")}
- **URL:** {issue.get("url", "")}
- **State:** {issue.get("state", "")}
- **Labels:** {labels}

## Body

{issue.get("body", "") or "_(empty)_"}
"""
    path.write_text(content)
    return path


def seed_scope_answers(plan_dir: Path, objective: str) -> Path:
    """Create scope-answers.md questionnaire."""
    content = f"""# Scope Questionnaire: {objective}

Instructions: Fill in your answers below each question.
Delete or leave blank any that aren't applicable.
When done, tell the agent: "answers ready" (or similar).

## Objective
> {objective}
Is this correct? Adjustments?

**Answer:**

## Constraints
Platform requirements? Dependencies? Timeline? Budget?

**Answer:**

## Investigation Needs
What unknowns require experimentation before committing?
(API behavior, library evaluation, performance, etc.)

**Answer:**

## Scope Boundaries
What is explicitly out of scope?

**Answer:**

## Success Criteria
How do we know the plan is done?

**Answer:**

## Additional Context
Anything else relevant?

**Answer:**
"""
    path = plan_dir / "scope-answers.md"
    path.write_text(content)
    return path


def seed_upstream_triage(plan_dir: Path, objective: str,
                         issues: list[dict]) -> tuple[Path, list[Path]]:
    """Create upstream-triage.md for operator editing.

    Also writes one `references/upstream-<N>.md` file per issue containing the
    full (untruncated) body — portability contract (Epic 2.1/2.2). The 200-char
    truncation is kept at the triage-display line for readability.

    Returns (triage_path, [reference_paths]).
    """
    lines = [
        f"# Upstream Issue Triage: {objective}",
        "",
        "Instructions: For each issue, set disposition to: include, exclude, partial, supersede.",
        "Add notes as needed. When done, say \"triage ready\".",
        "",
        "_Full issue bodies are inlined under `references/upstream-<N>.md` (regenerated on re-triage)._",
        "",
    ]
    reference_paths: list[Path] = []
    for issue in issues:
        number = issue.get("number", "?")
        title = issue.get("title", "Untitled")
        labels_raw = issue.get("labels", []) or []
        if labels_raw and isinstance(labels_raw[0], dict):
            labels = ", ".join(lbl.get("name", "") for lbl in labels_raw)
        else:
            labels = ", ".join(str(lbl) for lbl in labels_raw)
        body = (issue.get("body", "") or "")[:200]
        lines.extend([
            f"## #{number} — {title}",
            f"Labels: {labels}" if labels else "",
            f"> {body}..." if body else "",
            "",
            "**Disposition:**",
            "**Notes:**",
            "",
        ])
        if number != "?":
            reference_paths.append(_write_upstream_reference(plan_dir, issue))
    path = plan_dir / "upstream-triage.md"
    path.write_text("\n".join(lines))
    return path, reference_paths


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _read_config() -> dict:
    """Operator config (.bdplan.local.json) — operator decisions only (e.g. ignore-skill)."""
    return _read_json(CONFIG_FILE) if CONFIG_FILE.exists() else {}


def _read_state() -> dict:
    """Runtime state (.state/bdplan/preflight.json) — cache, never operator config."""
    return _read_json(STATE_FILE) if STATE_FILE.exists() else {}


def _write_state(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2) + "\n")


def _update_state(**kv) -> None:
    """Merge keys into runtime state (never clobber sibling keys)."""
    state = _read_state()
    state.update(kv)
    _write_state(state)


def _ensure_scaffold() -> list[str]:
    """Idempotent, additive project scaffold (Surface Convention §6/§7).

    Dirs are ensured every call (infrastructure, safe to recreate). The gitignore
    anchors are ensured once per SCAFFOLD_VERSION (gated by state) — additive only,
    never removing or reordering existing lines, so it will not fight an operator
    who later drops an anchor. Returns a human-readable list of what it created.
    """
    added: list[str] = []

    # Required dirs — ensured every call.
    if not PLANS_DIR.exists():
        PLANS_DIR.mkdir(parents=True, exist_ok=True)
        added.append(f"created {PLANS_DIR}/")

    # Gitignore anchors — ensured once per scaffold version.
    if _read_state().get("scaffold-ensured") != SCAFFOLD_VERSION:
        lines = GITIGNORE_FILE.read_text().splitlines() if GITIGNORE_FILE.exists() else []
        present = {ln.strip() for ln in lines}
        missing = [a for a in GITIGNORE_ANCHORS if a not in present]
        if missing:
            if lines and lines[-1].strip():
                lines.append("")
            lines.append(f"# Skill runtime state + local config ({SKILL_NAME}; Surface Convention §6)")
            lines.extend(missing)
            GITIGNORE_FILE.write_text("\n".join(lines) + "\n")
            added += [f"gitignore {m}" for m in missing]
        _update_state(**{"scaffold-ensured": SCAFFOLD_VERSION})

    return added


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_rule() -> dict:
    """Compare the installed companion rule against protocols/manifest.json.

    Evaluates candidate locations in precedence order (the user/global home copy
    before the project copy); a correct global copy short-circuits so no
    per-project copy is required. The rule is installed by install.sh, not init.
    Outcomes: ok | update_available | drift | deprecated | missing |
    manifest_schema_unknown | manifest_missing (Surface Convention § Hash manifest).
    """
    manifest = _read_json(MANIFEST_FILE)
    if not manifest:
        return {"outcome": "manifest_missing", "rule": RULE_NAME}
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        return {"outcome": "manifest_schema_unknown", "rule": RULE_NAME,
                "schema_version": manifest.get("schema_version")}
    entry = manifest.get("files", {}).get(RULE_NAME, {})

    def outcome_for(path: Path) -> str:
        if entry.get("deprecated"):
            return "deprecated"
        installed = _sha256(path)
        if installed == entry.get("sha256"):
            return "ok"
        if any(installed == p.get("sha256") for p in entry.get("previous_versions", [])):
            return "update_available"
        return "drift"

    rank = {"ok": 0, "update_available": 1, "deprecated": 2, "drift": 3}
    best, best_path = None, None
    for cand in _rule_candidates():
        path = cand / RULE_NAME
        if not path.exists():
            continue
        oc = outcome_for(path)
        if best is None or rank[oc] < rank[best]:
            best, best_path = oc, path
            if oc == "ok":
                break
    if best is None:
        return {"outcome": "missing", "rule": RULE_NAME}
    result = {"outcome": best, "rule": RULE_NAME, "path": str(best_path)}
    if best in ("ok", "update_available"):
        result["version"] = entry.get("version")
    return result


def _parse_bd_version() -> tuple[int, ...] | None:
    """Parse bd version into a tuple, or None if unavailable."""
    try:
        output = subprocess.check_output(
            ["bd", "--version"], text=True, stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", output)
    if not match:
        return None
    parts = [int(g) for g in match.groups() if g is not None]
    return tuple(parts)


_RULE_INSTRUCTIONS = {
    "missing": f"{RULE_NAME} is not installed — run the repo installer (install.sh) to install it to the scope+surface rules dir (user-scope ~/.<surface>/rules, project-scope <git-root>/.<surface>/rules); add --force to overwrite an existing copy",
    "drift": f"Installed {RULE_NAME} diverges from the manifest — re-run the repo installer with --force (install.sh --force) to restore the shipped version, or resolve manually",
    "deprecated": f"{RULE_NAME} is deprecated — remove it from the rules dir (the skill no longer ships it)",
    "manifest_schema_unknown": f"Upgrade {SKILL_NAME}: manifest schema_version not understood",
    "manifest_missing": f"{SKILL_NAME} packaging error: protocols/manifest.json is missing",
}


def _check_prerequisites() -> dict:
    """Preflight per the Surface Convention: deps (cached in state) + installed-rule hash.

    Returns {status, missing, instructions, rule}. ignore-skill is an operator decision
    (config); prereqs-present is a cache (state). update_available is non-blocking.
    """
    if _read_config().get("ignore-skill"):
        return {"status": "ignored", "missing": [], "instructions": [], "rule": None}

    # System deps — checked once, then cached in state.
    if not _read_state().get("prereqs-present"):
        missing, instructions = [], []
        if not shutil.which("git"):
            missing.append("git")
            instructions.append("Install git via your system package manager")
        if not shutil.which("uv"):
            missing.append("uv")
            instructions.append("Install uv: https://docs.astral.sh/uv/")
        bd_version = _parse_bd_version()
        if bd_version is None:
            missing.append("bd")
            instructions.append("Install beads: https://github.com/gastownhall/beads")
        elif bd_version < MIN_BD_VERSION:
            v_str = ".".join(str(p) for p in bd_version)
            min_str = ".".join(str(p) for p in MIN_BD_VERSION)
            missing.append(f"bd>={min_str}")
            instructions.append(
                f"Upgrade beads: bd upgrade (current: {v_str}, required: >= {min_str})"
            )
        if missing:
            return {"status": "system_deps_missing", "missing": missing,
                    "instructions": instructions, "rule": None}
        try:
            subprocess.check_output(["bd", "status", "--json"], stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"status": "bd_not_initialized", "missing": [],
                    "instructions": ["Run: bd init"], "rule": None}
        _update_state(**{"prereqs-present": True})

    # Installed companion-rule hash — checked every run (cheap).
    rule = _check_rule()
    outcome = rule["outcome"]
    if outcome in ("ok", "update_available"):
        # Ensure the idempotent scaffold only when the project is otherwise ready.
        scaffold_added = _ensure_scaffold()
        return {"status": "ok", "missing": [], "rule": rule,
                "scaffold_added": scaffold_added,
                "instructions": ([] if outcome == "ok"
                                  else [f"A newer {RULE_NAME} is available — re-run the repo installer (install.sh --force) to update"])}
    return {"status": f"rule_{outcome}" if outcome in ("missing", "drift", "deprecated") else outcome,
            "missing": [], "instructions": [_RULE_INSTRUCTIONS.get(outcome, "")], "rule": rule}


@click.group()
def cli():
    """Plan manager for the /bdplan skill."""
    pass


@cli.command()
@click.option("--json-output", "as_json", is_flag=True,
              help="Emit JSON (for skill bootstrap). Default is human-readable.")
def check(as_json: bool):
    """Check system prerequisites for bdplan."""
    result = _check_prerequisites()

    if as_json:
        click.echo(json.dumps(result, indent=2))
        sys.exit(0)

    # Human-readable output
    if result["status"] == "ignored":
        click.echo("bdplan is ignored in this project.")
        sys.exit(0)

    if result["status"] != "ok":
        for msg in result["instructions"]:
            click.echo(f"ERROR: {msg}", err=True)
        sys.exit(1)

    # status == "ok" — rule hash verified and scaffold ensured in _check_prerequisites.
    for entry in result.get("scaffold_added", []):
        click.echo(f"NOTE: scaffold — {entry}", err=True)
    if result.get("instructions"):
        for msg in result["instructions"]:
            click.echo(f"NOTE: {msg}", err=True)
    click.echo("All prerequisites satisfied.")


@cli.command("json-get")
@click.argument("keys", nargs=-1, required=True)
def json_get(keys: tuple[str, ...]):
    """Extract a value from JSON on stdin by key path.

    Each argument is one level of nesting:
      echo '{"a":{"b.c":1}}' | plan_manager.py json-get a "b.c"
    """
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        click.echo(f"ERROR: invalid JSON on stdin: {e}", err=True)
        sys.exit(1)
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError, IndexError):
            click.echo(
                f"ERROR: key {key!r} not found in path {' -> '.join(keys)}",
                err=True,
            )
            sys.exit(1)
    if isinstance(data, (dict, list)):
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(data)


@cli.command()
@click.argument("objective")
@click.option(
    "--incubator", default=None,
    help="Incubator slug to scope plan to (e.g. 'bookpipe'). "
         "If omitted, CWD is checked for an Incubator/<slug>/ prefix; "
         "otherwise plan lands in docs/plans/.",
)
def init(objective: str, incubator: str | None):
    """Initialize a new plan directory with seed documents."""
    if incubator is None:
        incubator = detect_incubator_from_cwd()
    plans_dir = resolve_plans_dir(incubator)
    plans_dir.mkdir(parents=True, exist_ok=True)
    user = get_git_user()
    plan_id = make_plan_id(objective)
    plan_dir = make_plan_dir(plan_id, plans_dir)
    plan_md = seed_plan_md(plan_dir, plan_id, objective, user)
    scaffolding = seed_portability_scaffolding(plan_dir, plan_id, objective, user)

    result = {
        "plan_id": plan_id,
        "plan_dir": str(plan_dir),
        "plans_root": str(plans_dir),
        "incubator": incubator,
        "plan_md": str(plan_md),
        **scaffolding,
    }
    click.echo(json.dumps(result, indent=2))


@cli.command()
@click.argument("plan_dir", type=click.Path(exists=True))
@click.argument("objective")
def scope(plan_dir: str, objective: str):
    """Generate scope-answers.md questionnaire for a plan."""
    path = seed_scope_answers(Path(plan_dir), objective)
    click.echo(json.dumps({"scope_answers": str(path)}, indent=2))


@cli.command()
@click.argument("plan_dir", type=click.Path(exists=True))
@click.argument("objective")
@click.option("--issues-json", type=click.Path(exists=True),
              help="JSON file with upstream issues to triage")
def triage(plan_dir: str, objective: str, issues_json: str):
    """Generate upstream triage document from issues JSON."""
    with open(issues_json) as f:
        issues = json.load(f)
    path, refs = seed_upstream_triage(Path(plan_dir), objective, issues)
    click.echo(json.dumps({
        "upstream_triage": str(path),
        "references": [str(p) for p in refs],
    }, indent=2))


@cli.command("list")
@click.option("--json-output", "as_json", is_flag=True)
def list_plans(as_json: bool):
    """List all plans and research items, across vault-default + Incubator roots."""
    plans = []
    for root in list_plan_roots():
        incubator = _scope_for_root(root, PLANS_DIR)
        for d in sorted(root.iterdir()):
            if not d.is_dir() or not d.name.startswith("plan-"):
                continue
            plan_md = d / "plan.md"
            if not plan_md.exists():
                continue

            text = plan_md.read_text()
            status = "unknown"
            objective = d.name
            for line in text.splitlines():
                if line.startswith("# Plan: "):
                    objective = line[8:].strip()
                if line.startswith("**Status:**"):
                    status = line.split("**Status:**")[1].strip()

            plans.append({
                "id": d.name,
                "objective": objective,
                "status": status,
                "incubator": incubator,
                "path": str(d),
            })
    plans.sort(key=lambda p: p["id"])

    research = []
    for root in list_research_roots():
        incubator = _scope_for_root(root, RESEARCH_DIR)
        for d in sorted(root.iterdir()):
            info = _research_item_info(d)
            if info is None:
                continue
            research.append({
                **info,
                "incubator": incubator,
            })
    research.sort(key=lambda r: (r["incubator"] or "", r["id"]))

    if as_json:
        click.echo(json.dumps({"plans": plans, "research": research}, indent=2))
        return

    if not plans:
        click.echo("No plans found.")
    else:
        click.echo("Plans:")
        for p in plans:
            scope = p["incubator"] or "docs"
            click.echo(
                f"  {p['id']:<35} [{scope:<18}] "
                f"{p['objective']:<40} status: {p['status']}"
            )

    if research:
        click.echo("")
        click.echo("Research:")
        for r in research:
            scope = r["incubator"] or "docs"
            kind_tag = "rehoused-plan" if r["kind"] == "rehoused-plan" else "research"
            click.echo(
                f"  {r['id']:<35} [{scope:<18}] "
                f"{r['topic']:<40} kind: {kind_tag}"
            )


@cli.command()
@click.argument("plan_dir", type=click.Path(exists=True))
@click.argument("status")
@click.option("--message", "-m", default=None, help="Phase log message")
def update_status(plan_dir: str, status: str, message: str):
    """Update plan.md status and append to phase log."""
    plan_md = Path(plan_dir) / "plan.md"
    if not plan_md.exists():
        click.echo("ERROR: plan.md not found", err=True)
        sys.exit(1)

    today = datetime.now().strftime("%Y-%m-%d")
    text = plan_md.read_text()
    lines = text.splitlines()
    new_lines = []
    log_entry = f"- {today} {status}: {message or status}"

    skip_until = -1
    for i, line in enumerate(lines):
        if i < skip_until:
            continue
        if line.startswith("**Status:**"):
            new_lines.append(f"**Status:** {status}")
        elif line.startswith("**Phase log:**"):
            new_lines.append(line)
            j = i + 1
            while j < len(lines) and lines[j].startswith("- "):
                new_lines.append(lines[j])
                j += 1
            new_lines.append(log_entry)
            skip_until = j
        else:
            new_lines.append(line)

    plan_md.write_text("\n".join(new_lines) + "\n")
    click.echo(json.dumps({"status": status, "log_entry": log_entry}))


# ---------------------------------------------------------------------------
# Portability audit (Epic 4)
# ---------------------------------------------------------------------------

# Dangling-reference detection: absolute paths and parent-traversal only.
# Repo-relative paths like `skills/bdplan/SKILL.md` are explicitly allowed.
_ABS_PATH_PATTERNS = (
    re.compile(r"(?<![\w/])/Users/"),
    re.compile(r"(?<![\w/])/home/"),
    re.compile(r"(?<![\w/])/opt/"),
    re.compile(r"(?<![\w/])/var/"),
    re.compile(r"(?<![\w/])/tmp/"),
    re.compile(r"(?<![\w/])/etc/"),
    re.compile(r"[A-Za-z]:\\"),
)
_PARENT_TRAVERSAL = re.compile(r"(?<![\w.])\.\./")

_CONTEXT_REQUIRED_SECTIONS = (
    "Project environment",
    "Tool inventory",
    "Paths",
    "Operator identity",
    "Runtime assumptions",
)

# Seeded instructional prose per section (from seed_context_md). A section whose body
# still contains its marker is unedited template text and fails the portability audit.
# Tool inventory / Paths are auto-filled with real data at seed time, so they have no marker.
_CONTEXT_PLACEHOLDERS = {
    "Project environment": "Describe the project this plan belongs to",
    "Operator identity": "fill in role, contact, and authority scope",
    "Runtime assumptions": "List the assumptions this plan makes about",
}

_README_REQUIRED_SECTIONS = ("File map", "Reading order")


def _plan_phase_log_lines(plan_md_text: str) -> list[str]:
    """Return the lines of the Phase log list (without the header)."""
    lines = plan_md_text.splitlines()
    out: list[str] = []
    in_log = False
    for line in lines:
        if line.startswith("**Phase log:**"):
            in_log = True
            continue
        if in_log:
            if line.startswith("- "):
                out.append(line)
            else:
                if out:
                    break
    return out


def _plan_first_scoping_date(plan_md_text: str) -> str | None:
    """Extract the date of the earliest `scoping:` phase-log entry, if any."""
    for line in _plan_phase_log_lines(plan_md_text):
        m = re.match(r"- (\d{4}-\d{2}-\d{2}) scoping:", line)
        if m:
            return m.group(1)
    return None


def _plan_review_line_count(plan_md_text: str) -> int:
    count = 0
    for line in _plan_phase_log_lines(plan_md_text):
        if re.match(r"- \d{4}-\d{2}-\d{2} review:", line):
            count += 1
    return count


def _plan_non_exclude_upstream_numbers(plan_md_text: str) -> list[str]:
    """Parse the Upstream Issues table and return issue numbers for any row
    whose disposition is not `exclude` and not a placeholder.
    """
    numbers: list[str] = []
    in_table = False
    for line in plan_md_text.splitlines():
        if line.startswith("## Upstream Issues"):
            in_table = True
            continue
        if in_table:
            if line.startswith("## "):
                break
            if "|" not in line:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            if cells[0].lower() in ("issue", "-----", ""):
                continue
            # Header separator line (---|---|---)
            if all(set(c) <= set("-: ") for c in cells):
                continue
            issue_cell = cells[0]
            disposition = cells[2].lower()
            if disposition in ("", "exclude"):
                continue
            # Extract trailing #N from "owner/repo#3" or "#3"
            m = re.search(r"#(\d+)", issue_cell)
            if m:
                numbers.append(m.group(1))
    return numbers


def _audit_finding(item: str, status: str, detail: str) -> dict:
    return {"item": item, "status": status, "detail": detail}


def _audit_plan(plan_dir: Path) -> dict:
    """Run the portability precondition audit. Returns structured result.

    status ∈ {"pass", "fail"} — a result is "pass" iff no findings have
    status="fail". Warn findings (grandfather clause) do not degrade overall
    status.
    """
    findings: list[dict] = []
    plan_md = plan_dir / "plan.md"

    if not plan_md.exists():
        return {
            "status": "fail",
            "findings": [_audit_finding("plan.md", "fail", "missing")],
            "report": f"{plan_dir}: plan.md missing; cannot audit.",
        }

    plan_text = plan_md.read_text()
    first_scoping = _plan_first_scoping_date(plan_text)
    grandfathered = (
        first_scoping is not None
        and first_scoping < PORTABILITY_ACTIVATION_DATE
    )
    missing_level = "warn" if grandfathered else "fail"

    # 1. README.md
    readme = plan_dir / "README.md"
    if not readme.exists() or not readme.read_text().strip():
        findings.append(_audit_finding(
            "README.md", missing_level,
            "missing or empty; expected portability orientation file",
        ))
    else:
        rtxt = readme.read_text()
        missing_sections = [s for s in _README_REQUIRED_SECTIONS
                            if s not in rtxt]
        if missing_sections:
            findings.append(_audit_finding(
                "README.md", "fail",
                f"missing required sections: {', '.join(missing_sections)}",
            ))

    # 2. context.md — required sections non-empty (no unfilled placeholder lines)
    context = plan_dir / "context.md"
    if not context.exists() or not context.read_text().strip():
        findings.append(_audit_finding(
            "context.md", missing_level,
            "missing or empty; expected project-environment snapshot",
        ))
    else:
        ctext = context.read_text()
        for section in _CONTEXT_REQUIRED_SECTIONS:
            # Extract the section's body (everything up to the next `## ` header)
            m = re.search(
                rf"^##\s+{re.escape(section)}\s*$(.*?)(?=^##\s+|\Z)",
                ctext, flags=re.MULTILINE | re.DOTALL,
            )
            if not m:
                findings.append(_audit_finding(
                    f"context.md §{section}", "fail",
                    "section header missing",
                ))
                continue
            body = m.group(1).strip()
            # Strip HTML comment (snapshot header) before evaluating emptiness.
            stripped = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
            if not stripped:
                findings.append(_audit_finding(
                    f"context.md §{section}", "fail",
                    "section is empty",
                ))
            elif (marker := _CONTEXT_PLACEHOLDERS.get(section)) and marker in stripped:
                findings.append(_audit_finding(
                    f"context.md §{section}", "fail",
                    "contains unedited template prose; fill in real values",
                ))

    # 3. Motivation: plan.md §Motivation or motivation.md, non-empty and not placeholder
    motivation_ok = False
    motivation_detail = ""
    mot_md = plan_dir / "motivation.md"
    if mot_md.exists() and mot_md.read_text().strip():
        motivation_ok = True
    else:
        m = re.search(
            r"^##\s+Motivation\s*$(.*?)(?=^##\s+|\Z)",
            plan_text, flags=re.MULTILINE | re.DOTALL,
        )
        if m:
            body = m.group(1).strip()
            if body and "Replace this placeholder" not in body \
                    and not re.fullmatch(r"_[^_]+_", body.strip()):
                motivation_ok = True
            else:
                motivation_detail = "§Motivation contains placeholder text"
        else:
            motivation_detail = "no plan.md §Motivation section or motivation.md file"
    if not motivation_ok:
        findings.append(_audit_finding(
            "motivation", "fail", motivation_detail or "missing",
        ))

    # 4. references/upstream-*.md — one file per non-exclude row
    expected_upstream = _plan_non_exclude_upstream_numbers(plan_text)
    refs_dir = plan_dir / "references"
    for n in expected_upstream:
        ref_file = refs_dir / f"upstream-{n}.md"
        if not ref_file.exists() or not ref_file.read_text().strip():
            findings.append(_audit_finding(
                f"references/upstream-{n}.md", "fail",
                "missing body for non-exclude upstream issue",
            ))

    # 5. reviews/pass-*.md — count == phase-log review line count
    expected_reviews = _plan_review_line_count(plan_text)
    reviews_dir = plan_dir / "reviews"
    actual_reviews = 0
    if reviews_dir.exists():
        actual_reviews = len(list(reviews_dir.glob("pass-*.md")))
    if actual_reviews != expected_reviews:
        findings.append(_audit_finding(
            "reviews/", missing_level if actual_reviews == 0 else "fail",
            f"expected {expected_reviews} pass-*.md (one per phase-log review line), "
            f"found {actual_reviews}",
        ))

    # 6. No dangling external refs across all plan files.
    # Strip fenced/inline code spans first — they contain pattern examples,
    # regex snippets, and command documentation that legitimately mention
    # absolute paths without being references.
    dangling: list[str] = []
    for path in plan_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in (".md", ".txt", ""):
            continue
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        stripped = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        stripped = re.sub(r"`[^`]*`", "", stripped)
        for pat in _ABS_PATH_PATTERNS:
            for m in pat.finditer(stripped):
                dangling.append(f"{path.relative_to(plan_dir)}: {m.group(0)}")
        for _ in _PARENT_TRAVERSAL.finditer(stripped):
            dangling.append(f"{path.relative_to(plan_dir)}: ../ parent traversal")
    if dangling:
        findings.append(_audit_finding(
            "dangling-refs", "fail",
            "; ".join(sorted(set(dangling))[:10]),
        ))

    any_fail = any(f["status"] == "fail" for f in findings)
    status = "fail" if any_fail else "pass"
    report_lines = [f"Portability audit: {plan_dir}", ""]
    if grandfathered:
        report_lines.append(
            f"[grandfather] first scoping {first_scoping} < activation "
            f"{PORTABILITY_ACTIVATION_DATE}; missing scaffolding downgraded to warn."
        )
        report_lines.append("")
    for f in findings:
        report_lines.append(f"  [{f['status']:<4}] {f['item']}: {f['detail']}")
    if not findings:
        report_lines.append("  All checks passed.")
    return {
        "status": status,
        "findings": findings,
        "report": "\n".join(report_lines),
        "grandfathered": grandfathered,
    }


@cli.command()
@click.argument("plan_dir", type=click.Path(exists=True))
@click.option("--json-output", "as_json", is_flag=True,
              help="Emit structured JSON. Default is human-readable report.")
def audit(plan_dir: str, as_json: bool):
    """Run portability precondition audit on a plan directory (Epic 4)."""
    result = _audit_plan(Path(plan_dir))
    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(result["report"])
    sys.exit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    cli()
