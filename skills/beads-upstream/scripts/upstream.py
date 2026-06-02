#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""beads-upstream helper: enumerate push candidates and read External: mappings.

Two subcommands the SKILL.md push step calls:

  enumerate [--json]            List open+blocked+deferred beads (push candidates),
                                flagging those that already carry an upstream
                                `External:` mapping.
  mappings --issues <csv> [--json]
                                For each bead ID, report its `External:` upstream
                                URL (or null if unmapped).

`bd list --json` may be a multi-document array and may carry warning prefixes on
stdout; we parse defensively (see the `beads-extra` skill → defensive JSON). The
upstream mapping is read from `bd show <id>` text — a single line anchored as
`External: <url>` — verified stable on bd 1.0.5.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

CANDIDATE_STATUSES = "open,blocked,deferred"
# Anchored: real mapping line starts the line and is a URL — avoids matching the
# word "External:" inside a description body.
EXTERNAL_RE = re.compile(r"^\s*External:\s*(https?://\S+)", re.MULTILINE)


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"command failed ({proc.returncode}): {' '.join(cmd)}")
    return proc.stdout


def parse_json_array(text: str) -> list[dict]:
    """Defensive parse of `bd ... --json`. Returns a list of issue dicts.

    Tolerates a warning prefix before the JSON and both shapes (top-level array,
    or {"issues":[...]}/single object). Falls back to extracting the first
    balanced [...] / {...} block if a direct load fails.
    """
    for candidate in (text, _first_balanced(text)):
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("issues", [data])
    return []


def _first_balanced(text: str) -> str | None:
    open_ch = None
    for opener, closer in (("[", "]"), ("{", "}")):
        i = text.find(opener)
        if i != -1 and (open_ch is None or i < open_ch[1]):
            open_ch = (opener, i, closer)
    if open_ch is None:
        return None
    opener, start, closer = open_ch
    depth = 0
    for j in range(start, len(text)):
        if text[j] == opener:
            depth += 1
        elif text[j] == closer:
            depth -= 1
            if depth == 0:
                return text[start : j + 1]
    return None


def external_for(bead_id: str) -> str | None:
    out = run(["bd", "show", bead_id])
    m = EXTERNAL_RE.search(out)
    return m.group(1) if m else None


def cmd_enumerate(as_json: bool) -> int:
    rows = parse_json_array(run(["bd", "list", "--status", CANDIDATE_STATUSES, "--json"]))
    # Skip container types — only push real work items.
    rows = [r for r in rows if r.get("issue_type") not in ("epic", "molecule", "gate")]
    out = []
    for r in rows:
        bid = r.get("id")
        if not bid:
            continue
        ext = external_for(bid)
        out.append(
            {
                "id": bid,
                "title": r.get("title", ""),
                "status": r.get("status", ""),
                "type": r.get("issue_type", ""),
                "mapped": ext is not None,
                "external": ext,
            }
        )
    if as_json:
        print(json.dumps(out, indent=2))
    else:
        unmapped = [r for r in out if not r["mapped"]]
        print(f"{len(out)} candidate(s) (open/blocked/deferred); {len(unmapped)} not yet mapped:")
        for r in out:
            flag = r["external"] if r["mapped"] else "—"
            print(f"  {r['id']:<16} [{r['status']}/{r['type']}] {r['title']}  ({flag})")
    return 0


def cmd_mappings(issues_csv: str, as_json: bool) -> int:
    ids = [s.strip() for s in issues_csv.split(",") if s.strip()]
    out = [{"id": bid, "external": external_for(bid)} for bid in ids]
    if as_json:
        print(json.dumps(out, indent=2))
    else:
        for r in out:
            print(f"  {r['id']:<16} {r['external'] or '(unmapped)'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="beads-upstream push helpers.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enum = sub.add_parser("enumerate", help="list open/blocked/deferred push candidates")
    p_enum.add_argument("--json", action="store_true", dest="as_json")

    p_map = sub.add_parser("mappings", help="report External: mappings for given bead IDs")
    p_map.add_argument("--issues", required=True, help="comma-separated bead IDs")
    p_map.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args()
    if args.cmd == "enumerate":
        return cmd_enumerate(args.as_json)
    if args.cmd == "mappings":
        return cmd_mappings(args.issues, args.as_json)
    return 1


if __name__ == "__main__":
    sys.exit(main())
