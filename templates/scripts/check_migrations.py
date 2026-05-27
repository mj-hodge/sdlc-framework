#!/usr/bin/env python3
"""check_migrations.py — Detect Alembic head conflicts without a DB.

Scans alembic/versions/*.py for two failure modes that `alembic upgrade
head` only reports at runtime — when it has already been deployed to a
real environment:

  1. **Duplicate revision IDs** — two files claiming `revision = "030"`.
     Alembic cannot distinguish them; the upgrade fails on whichever it
     tries to apply second. Most common when parallel worktrees / agents
     each pick the next free number from main without rebasing.

  2. **Divergent down_revisions** — two migrations both chaining from the
     same parent (`down_revision = "029"`). This produces multiple heads;
     `alembic upgrade head` requires exactly one head.

Exit codes:
  0 — chain is linear, no conflicts
  1 — one or more conflicts found (deploy should be blocked)

Usage:
  python3 scripts/check_migrations.py
  python3 scripts/check_migrations.py --versions-dir path/to/alembic/versions

Wire this in CI as a hard gate (NOT warn-only) on every PR. UAT outages
caused by alembic-upgrade-fail typically fall back to restrictive default
policies (e.g., admin-only access) and lock real users out within seconds.

Why this script and not `alembic heads`?
  `alembic heads` only catches divergent down_revisions (case 2). Two
  files with the SAME `revision = "X"` (case 1) are silently picked-one;
  the failure surfaces only when the upgrade actually runs in production.
  This script catches both cases statically, with no DB connection and
  no Alembic install required.

Adopt this script per the Phase 8 implementation agent's "Migration
Revision-ID Collision Check" section in agents/phase-8-implementation.md.
"""

import argparse
import os
import re
import sys


def parse_revisions(versions_dir: str) -> list[dict]:
    entries = []
    for fname in sorted(os.listdir(versions_dir)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        path = os.path.join(versions_dir, fname)
        content = open(path).read()

        rev_match = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', content, re.M)
        down_match = re.search(r'^down_revision\s*=\s*["\']([^"\']+)["\']\s*(?:#.*)?\s*$', content, re.M)

        if not rev_match:
            continue

        entries.append({
            "file": fname,
            "revision": rev_match.group(1).strip(),
            "down_revision": down_match.group(1).strip() if down_match else None,
        })
    return entries


def check(versions_dir: str) -> list[str]:
    entries = parse_revisions(versions_dir)
    errors = []

    # 1. Duplicate revision IDs — two files claiming to be the same revision.
    rev_seen: dict[str, str] = {}
    for e in entries:
        rev = e["revision"]
        if rev in rev_seen:
            errors.append(
                f"DUPLICATE REVISION '{rev}': {rev_seen[rev]} and {e['file']} "
                f"both declare revision='{rev}'. Alembic cannot distinguish them."
            )
        else:
            rev_seen[rev] = e["file"]

    # 2. Duplicate down_revision — two migrations both chaining from the same parent
    #    (divergent heads / fork in the chain).
    down_seen: dict[str, str] = {}
    for e in entries:
        dr = e["down_revision"]
        if dr is None:
            continue
        if dr in down_seen:
            errors.append(
                f"DIVERGENT HEAD at '{dr}': {down_seen[dr]} and {e['file']} "
                f"both have down_revision='{dr}'. "
                f"Run `alembic heads` to confirm — there should be exactly one head."
            )
        else:
            down_seen[dr] = e["file"]

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--versions-dir",
        default=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "alembic", "versions",
        ),
        help="Path to alembic/versions directory",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.versions_dir):
        print(f"ERROR: versions dir not found: {args.versions_dir}", file=sys.stderr)
        return 1

    errors = check(args.versions_dir)

    if not errors:
        files = [f for f in os.listdir(args.versions_dir) if f.endswith(".py") and not f.startswith("_")]
        print(f"OK — {len(files)} migration(s), linear chain, no conflicts.")
        return 0

    print(f"MIGRATION CONFLICT — {len(errors)} issue(s) found:\n", file=sys.stderr)
    for err in errors:
        print(f"  ✗ {err}\n", file=sys.stderr)
    print(
        "Fix: renumber the conflicting migration(s) so each revision ID is unique\n"
        "and each down_revision points to exactly one parent.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
