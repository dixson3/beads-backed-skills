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
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click

PLANS_DIR = Path("docs/plans")


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
            f"## #{number} -- {title}",
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


@click.group()
def cli():
    """Plan manager for the /bdplan skill."""
    pass


@cli.command()
@click.argument("objective")
@click.option("--complex-scope", is_flag=True, help="Generate scope questionnaire")
def init(objective: str, complex_scope: bool):
    """Initialize a new plan directory with seed documents."""
    user = get_git_user()
    plan_id = make_plan_id(objective)
    plan_dir = make_plan_dir(plan_id)
    plan_md = seed_plan_md(plan_dir, plan_id, objective, user)

    result = {"plan_id": plan_id, "plan_dir": str(plan_dir), "plan_md": str(plan_md)}

    if complex_scope:
        scope_path = seed_scope_answers(plan_dir, objective)
        result["scope_answers"] = str(scope_path)

    click.echo(json.dumps(result, indent=2))


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

    for i, line in enumerate(lines):
        if line.startswith("**Status:**"):
            new_lines.append(f"**Status:** {status}")
        elif line.startswith("**Phase log:**"):
            new_lines.append(line)
            # Find the last log entry and insert after it
            j = i + 1
            while j < len(lines) and lines[j].startswith("- "):
                new_lines.append(lines[j])
                j += 1
            new_lines.append(log_entry)
            # Skip the lines we already consumed
            for k in range(i + 1, j):
                lines[k] = None  # type: ignore
        elif line is not None:
            new_lines.append(line)

    plan_md.write_text("\n".join(new_lines) + "\n")
    click.echo(json.dumps({"status": status, "log_entry": log_entry}))


if __name__ == "__main__":
    cli()
