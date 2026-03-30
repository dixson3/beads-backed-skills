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
import shutil
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


def seed_upstream_triage(plan_dir: Path, objective: str, issues: list[dict]) -> Path:
    """Create upstream-triage.md for operator editing."""
    lines = [
        f"# Upstream Issue Triage: {objective}",
        "",
        "Instructions: For each issue, set disposition to: include, exclude, partial, supersede.",
        "Add notes as needed. When done, say \"triage ready\".",
        "",
    ]
    for issue in issues:
        number = issue.get("number", "?")
        title = issue.get("title", "Untitled")
        labels = ", ".join(issue.get("labels", []))
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
    path = plan_dir / "upstream-triage.md"
    path.write_text("\n".join(lines))
    return path


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


@cli.command()
@click.argument("objective")
def init(objective: str):
    """Initialize a new plan directory with seed documents."""
    user = get_git_user()
    plan_id = make_plan_id(objective)
    plan_dir = make_plan_dir(plan_id)
    plan_md = seed_plan_md(plan_dir, plan_id, objective, user)

    result = {"plan_id": plan_id, "plan_dir": str(plan_dir), "plan_md": str(plan_md)}
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
    path = seed_upstream_triage(Path(plan_dir), objective, issues)
    click.echo(json.dumps({"upstream_triage": str(path)}, indent=2))


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


if __name__ == "__main__":
    cli()
