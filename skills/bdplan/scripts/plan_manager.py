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
CONFIG_DIR = Path(".claude/.skill-bdplan")
CONFIG_FILE = CONFIG_DIR / "config.local.json"
GITIGNORE_FILE = CONFIG_DIR / ".gitignore"

MIN_BD_VERSION = (0, 60)

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


def get_next_index() -> int:
    """Get next plan index by counting existing plan dirs."""
    if not PLANS_DIR.exists():
        return 1
    existing = [d for d in PLANS_DIR.iterdir() if d.is_dir() and d.name.startswith("plan-")]
    return len(existing) + 1


def make_plan_id(objective: str) -> str:
    """Generate plan ID: plan-NNN-user-hash."""
    idx = f"{get_next_index():03d}"
    user = get_git_user()
    raw = f"{objective}{datetime.now().isoformat()}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:6]
    return f"plan-{idx}-{user}-{h}"


def make_plan_dir(plan_id: str) -> Path:
    """Create plan directory structure."""
    plan_dir = PLANS_DIR / plan_id
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


def _read_config() -> dict:
    """Read config.local.json, returning empty dict if missing/invalid."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write_config(data: dict) -> None:
    """Write config.local.json and ensure .gitignore covers it."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n")
    if not GITIGNORE_FILE.exists():
        GITIGNORE_FILE.write_text("config.local.json\n")


def _parse_bd_version() -> tuple[int, ...] | None:
    """Parse bd version into a tuple, or None if unavailable."""
    try:
        output = subprocess.check_output(
            ["bd", "--version"], text=True, stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    import re
    match = re.search(r"(\d+)\.(\d+)", output)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)))


def _check_prerequisites() -> dict:
    """Check all system prerequisites. Returns structured result."""
    config = _read_config()

    if config.get("ignore-skill"):
        return {"status": "ignored"}

    if config.get("prereqs-present"):
        return {"status": "ok", "missing": [], "instructions": []}

    missing = []
    instructions = []

    if not shutil.which("git"):
        missing.append("git")
        instructions.append("Install git via your system package manager")

    if not shutil.which("uv"):
        missing.append("uv")
        instructions.append("Install uv: https://docs.astral.sh/uv/")

    bd_version = _parse_bd_version()
    if bd_version is None:
        missing.append("bd")
        instructions.append(
            "Install beads: https://github.com/steveyegge/beads"
        )
    elif bd_version < MIN_BD_VERSION:
        v_str = f"{bd_version[0]}.{bd_version[1]}"
        missing.append(f"bd>={MIN_BD_VERSION[0]}.{MIN_BD_VERSION[1]}")
        instructions.append(
            f"Upgrade beads: bd upgrade (current: {v_str}, "
            f"required: >= {MIN_BD_VERSION[0]}.{MIN_BD_VERSION[1]})"
        )

    if missing:
        return {
            "status": "system_deps_missing",
            "missing": missing,
            "instructions": instructions,
        }

    # Check bd init
    try:
        subprocess.check_output(
            ["bd", "status", "--json"], stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            "status": "bd_not_initialized",
            "missing": [],
            "instructions": ["Run: bd init"],
        }

    # All passed — cache result
    _write_config({"prereqs-present": True})
    return {"status": "ok", "missing": [], "instructions": []}


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

    if result["status"] in ("system_deps_missing", "bd_not_initialized"):
        for msg in result["instructions"]:
            click.echo(f"ERROR: {msg}", err=True)
        sys.exit(1)

    # status == "ok" — run additional project-level checks
    errors = False
    if not Path("AGENTS/PLANS.md").exists():
        click.echo(
            "ERROR: AGENTS/PLANS.md not found. "
            "The planning protocol file is required.",
            err=True,
        )
        errors = True

    PLANS_DIR.mkdir(parents=True, exist_ok=True)

    if errors:
        sys.exit(1)
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
def init(objective: str):
    """Initialize a new plan directory with seed documents."""
    user = get_git_user()
    plan_id = make_plan_id(objective)
    plan_dir = make_plan_dir(plan_id)
    plan_md = seed_plan_md(plan_dir, plan_id, objective, user)
    scaffolding = seed_portability_scaffolding(plan_dir, plan_id, objective, user)

    result = {
        "plan_id": plan_id,
        "plan_dir": str(plan_dir),
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
    """List all plans with status."""
    if not PLANS_DIR.exists():
        if as_json:
            click.echo("[]")
        else:
            click.echo("No plans directory found.")
        return

    plans = []
    for d in sorted(PLANS_DIR.iterdir()):
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
            "path": str(d),
        })

    if as_json:
        click.echo(json.dumps(plans, indent=2))
    else:
        if not plans:
            click.echo("No plans found.")
            return
        for p in plans:
            click.echo(f"  {p['id']:<35} {p['objective']:<40} status: {p['status']}")


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
            elif "_Snapshot taken at plan-authoring time" in stripped and section == "Project environment":
                # Template preamble doesn't count as real content.
                pass

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
