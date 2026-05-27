#!/usr/bin/env python3
"""
sync_source.py — file-hash + diff helper for the /sync-source skill.

Computes SHA-256 hashes for every file under --source. Compares against the
JSON baseline at --baseline. Emits a JSON report to stdout describing NEW,
MODIFIED, DELETED, and UNCHANGED files.

Pass --update-baseline to write the current source state as the new baseline.

JSON output (diff mode):
{
  "mode": "diff",
  "source": "<absolute path>",
  "summary": {"new": N, "modified": M, "deleted": K, "unchanged": U},
  "new":      [{"path": "...", "size": N, "is_binary": bool}, ...],
  "modified": [{"path": "...", "old_hash": "...", "new_hash": "...",
                "old_size": N, "new_size": M, "is_binary": bool}, ...],
  "deleted":  [{"path": "...", "old_hash": "..."}, ...],
  "unchanged":[{"path": "..."}, ...]
}

JSON output (first run, no baseline):
{
  "mode": "initial",
  "source": "<absolute path>",
  "files": ["rel/path1", "rel/path2", ...],
  "count": N
}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

BINARY_EXTENSIONS = {
    ".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".zip", ".gz", ".tar", ".7z", ".docx", ".pptx", ".bin", ".exe", ".dll",
    ".so", ".dylib", ".woff", ".woff2", ".ttf", ".eot", ".ico", ".mp3",
    ".mp4", ".mov", ".avi",
}


def hash_file(path: Path) -> tuple[str, int]:
    """Return (sha256_hex, size_bytes) for a single file."""
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def hash_folder(source: Path) -> dict[str, dict]:
    """Walk source recursively. Return {posix_relative_path: {hash, size}}."""
    out: dict[str, dict] = {}
    for p in source.rglob("*"):
        if p.is_file():
            rel = p.relative_to(source).as_posix()
            digest, size = hash_file(p)
            out[rel] = {"hash": digest, "size": size}
    return out


def is_binary(rel_path: str) -> bool:
    return Path(rel_path).suffix.lower() in BINARY_EXTENSIONS


def diff(current: dict[str, dict], baseline: dict[str, dict]) -> dict:
    new, modified, deleted, unchanged = [], [], [], []
    for path, info in current.items():
        if path not in baseline:
            new.append({"path": path, "size": info["size"], "is_binary": is_binary(path)})
        elif baseline[path]["hash"] != info["hash"]:
            modified.append({
                "path": path,
                "old_hash": baseline[path]["hash"],
                "new_hash": info["hash"],
                "old_size": baseline[path]["size"],
                "new_size": info["size"],
                "is_binary": is_binary(path),
            })
        else:
            unchanged.append({"path": path})
    for path, info in baseline.items():
        if path not in current:
            deleted.append({"path": path, "old_hash": info["hash"]})
    return {
        "summary": {
            "new": len(new),
            "modified": len(modified),
            "deleted": len(deleted),
            "unchanged": len(unchanged),
        },
        "new": new,
        "modified": modified,
        "deleted": deleted,
        "unchanged": unchanged,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Absolute path to source folder")
    parser.add_argument("--baseline", required=True, help="Path to baseline JSON file")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="After computing, write current state as the new baseline file",
    )
    args = parser.parse_args()

    source = Path(args.source).resolve()
    baseline_path = Path(args.baseline)

    if not source.exists():
        print(json.dumps({"error": f"source path does not exist: {source}"}), file=sys.stderr)
        return 1
    if not source.is_dir():
        print(json.dumps({"error": f"source path is not a directory: {source}"}), file=sys.stderr)
        return 1

    current = hash_folder(source)

    if not baseline_path.exists():
        result = {
            "mode": "initial",
            "source": str(source),
            "files": sorted(current.keys()),
            "count": len(current),
        }
        print(json.dumps(result, indent=2))
        if args.update_baseline:
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            baseline_path.write_text(
                json.dumps({"source": str(source), "files": current}, indent=2)
            )
        return 0

    baseline_data = json.loads(baseline_path.read_text())
    baseline_files = baseline_data.get("files", {})

    result = diff(current, baseline_files)
    result["mode"] = "diff"
    result["source"] = str(source)
    print(json.dumps(result, indent=2))

    if args.update_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(
            json.dumps({"source": str(source), "files": current}, indent=2)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
