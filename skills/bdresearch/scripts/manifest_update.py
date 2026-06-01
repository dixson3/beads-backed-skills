#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Recompute hashes + bump versions in a skill's protocols/manifest.json.

Reads `<protocols-dir>/manifest.json`, recomputes sha256 for each declared
file, and on change appends the prior entry to `previous_versions[]` and
bumps the semver. Writes back atomically.

Per the Skill Surface Convention
(skill-authoring/reference/SURFACE_CONVENTION.md § 2 "Hash manifest").
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Tuple

SCHEMA_VERSION = 1


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def bump(version: str, level: str) -> str:
    parts = version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise SystemExit(f"manifest_update: version {version!r} is not MAJOR.MINOR.PATCH")
    major, minor, patch = (int(p) for p in parts)
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def atomic_write(path: Path, data: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def update_manifest(protocols_dir: Path, level: str, dry_run: bool) -> Tuple[int, list[str]]:
    manifest_path = protocols_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"manifest_update: {manifest_path} does not exist")

    manifest = json.loads(manifest_path.read_text())
    schema = manifest.get("schema_version")
    if schema != SCHEMA_VERSION:
        raise SystemExit(
            f"manifest_update: schema_version {schema!r} unsupported (this helper speaks v{SCHEMA_VERSION})"
        )

    files = manifest.setdefault("files", {})
    changes: list[str] = []

    for fname, entry in files.items():
        target = protocols_dir / fname
        if not target.exists():
            raise SystemExit(f"manifest_update: declared file {fname!r} is missing from {protocols_dir}")
        new_hash = sha256_file(target)
        old_hash = entry.get("sha256")
        old_version = entry.get("version", "0.0.0")
        if old_hash == new_hash:
            continue
        prev = entry.setdefault("previous_versions", [])
        if old_hash:
            prev.append({"sha256": old_hash, "version": old_version})
        entry["sha256"] = new_hash
        entry["version"] = bump(old_version, level)
        entry.setdefault("deprecated", False)
        changes.append(f"{fname}: {old_version} -> {entry['version']} ({old_hash[:8] if old_hash else 'new'} -> {new_hash[:8]})")

    if changes and not dry_run:
        atomic_write(manifest_path, json.dumps(manifest, indent=2) + "\n")

    return len(changes), changes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recompute hashes + bump versions in a skill's protocols/manifest.json."
    )
    parser.add_argument(
        "protocols_dir",
        type=Path,
        help="path to the skill's protocols/ directory (must contain manifest.json)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--minor", action="store_true", help="bump minor instead of patch")
    group.add_argument("--major", action="store_true", help="bump major instead of patch")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    args = parser.parse_args()

    level = "major" if args.major else "minor" if args.minor else "patch"
    count, changes = update_manifest(args.protocols_dir.resolve(), level, args.dry_run)

    if count == 0:
        print("manifest_update: no changes (all hashes match)")
        return 0
    verb = "would update" if args.dry_run else "updated"
    print(f"manifest_update: {verb} {count} entry/entries:")
    for c in changes:
        print(f"  - {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
