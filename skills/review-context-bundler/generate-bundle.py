#!/usr/bin/env python3
"""
review-context-bundler: Generate ~/state/morris/review-context.md

Produces a knowledge bundle that Morris's review-prs skill loads via
--append-system-prompt-file. Contains KB digest, SDLC matrix, runbook
excerpts, recent incidents, and knowledge-gap roll-up.

Idempotent: identical inputs produce identical output bytes.
Budget: <=120K chars. Drops least-recently-modified wiki pages if over.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHAR_BUDGET = 120_000  # hard ceiling

WIKI_ROOT = Path("/home/hermes/dev/hpi-gorillacommerce/tech-gc-knowledgebase/wiki")
AGENTS_MD = Path("/home/hermes/workspace/tech-dev-agents/.sdlc/AGENTS.md")
REVIEW_PRS_SKILL = Path(
    "/home/hermes/workspace/tech-dev-agents/.sdlc/skills/review-prs/SKILL.md"
)

# Active repos that may contain runbooks
REPO_BASE = Path("/home/hermes/dev/hpi-gorillacommerce")
RUNBOOK_GLOBS = ["runbooks", "docs/runbooks", "monitoring/runbooks"]

# Morris state — prefer workspace (git-tracked) over VM-local
STATE_DIR_WORKSPACE = Path(os.path.expanduser("~/workspace/tech-dev-agents/state/morris"))
STATE_DIR_LOCAL = Path(os.path.expanduser("~/state/morris"))

OUTPUT_PATH_WORKSPACE = STATE_DIR_WORKSPACE / "review-context.md"
OUTPUT_PATH_LOCAL = STATE_DIR_LOCAL / "review-context.md"
DROPPED_LOG = Path("/tmp/bundle-dropped.txt")

KNOWLEDGE_GAPS_PATHS = [
    STATE_DIR_WORKSPACE / "knowledge-gaps.jsonl",
    STATE_DIR_LOCAL / "knowledge-gaps.jsonl",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_page_digest(filepath: Path) -> dict | None:
    """Extract title, summary, and section headers with one-line summaries."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if not text.strip():
        return None

    lines = text.split("\n")

    # Title: first H1
    title = filepath.stem
    for line in lines:
        if line.startswith("# "):
            title = line.lstrip("# ").strip()
            break

    # Top-level summary: first paragraph after first heading
    summary = ""
    in_summary = False
    for line in lines:
        if not in_summary:
            if line.startswith("# "):
                in_summary = True
                continue
        else:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                summary = stripped
                break
            if stripped.startswith("#"):
                break

    # Section headers with one-line summaries
    sections: list[dict[str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^(#{2,4})\s+(.+)", line)
        if match:
            level = len(match.group(1))
            header = match.group(2).strip()
            # Find first non-empty, non-heading line after this header
            section_summary = ""
            j = i + 1
            while j < len(lines):
                sline = lines[j].strip()
                if sline and not sline.startswith("#") and not sline.startswith("---"):
                    # Take first meaningful line, truncate if needed
                    section_summary = sline[:200]
                    break
                if sline.startswith("#"):
                    break
                j += 1
            sections.append({
                "level": level,
                "header": header,
                "summary": section_summary,
            })
        i += 1

    return {
        "title": title,
        "file": str(filepath.name),
        "summary": summary[:300],
        "sections": sections,
        "mtime": filepath.stat().st_mtime,
    }


def format_page_digest(digest: dict) -> str:
    """Format a single page digest as compact markdown."""
    parts = [f"### {digest['title']}"]
    parts.append(f"_File: `{digest['file']}`_")
    if digest["summary"]:
        parts.append(f"\n{digest['summary']}")
    if digest["sections"]:
        parts.append("")
        for sec in digest["sections"]:
            prefix = "  " * (sec["level"] - 2)
            line = f"{prefix}- **{sec['header']}**"
            if sec["summary"]:
                line += f" -- {sec['summary']}"
            parts.append(line)
    return "\n".join(parts)


def collect_wiki_digests() -> tuple[list[dict], list[dict]]:
    """Collect digests from wiki/systems/ and wiki/processes/."""
    systems: list[dict] = []
    processes: list[dict] = []

    for subdir, target_list in [("systems", systems), ("processes", processes)]:
        wiki_dir = WIKI_ROOT / subdir
        if not wiki_dir.is_dir():
            continue
        for md_file in sorted(wiki_dir.glob("*.md")):
            if md_file.name == "README.md":
                continue
            digest = extract_page_digest(md_file)
            if digest:
                target_list.append(digest)

    # Sort deterministically by filename for idempotency
    systems.sort(key=lambda d: d["file"])
    processes.sort(key=lambda d: d["file"])
    return systems, processes


def extract_sdlc_matrix() -> str:
    """Extract deliverable matrix table and scope paths from AGENTS.md and review-prs SKILL.md."""
    parts: list[str] = []

    # --- From AGENTS.md: scope paths and model tiers ---
    try:
        agents_text = AGENTS_MD.read_text(encoding="utf-8")
    except OSError:
        agents_text = ""

    if agents_text:
        agents_lines = agents_text.split("\n")

        # Extract scope paths block (between "Phase paths:" and closing ```)
        in_paths = False
        paths_block: list[str] = []
        for line in agents_lines:
            if "Phase paths:" in line:
                in_paths = True
                paths_block.append(line)
                continue
            if in_paths:
                paths_block.append(line)
                if line.startswith("```") and len(paths_block) > 2:
                    in_paths = False
                    break

        if paths_block:
            parts.append("#### Scope Paths (from AGENTS.md)\n")
            parts.append("\n".join(paths_block))

        # Extract model tiers section
        model_lines: list[str] = []
        in_model_section = False
        for line in agents_lines:
            if line.strip().startswith("## Models"):
                in_model_section = True
            if in_model_section:
                model_lines.append(line)
                if line.startswith("---") and len(model_lines) > 5:
                    break

        if model_lines:
            parts.append("\n#### Model Tiers & Phase Selection\n")
            parts.extend(model_lines)

    # --- From review-prs SKILL.md: deliverable matrix + scope paths ---
    try:
        rp_text = REVIEW_PRS_SKILL.read_text(encoding="utf-8")
    except OSError:
        rp_text = ""

    if rp_text:
        rp_lines = rp_text.split("\n")

        # Extract deliverable matrix table (Trivial/Small/Medium/Large header row + all | rows)
        table_lines: list[str] = []
        in_table = False
        for line in rp_lines:
            if "|" in line and "Trivial" in line and "Small" in line:
                in_table = True
            if in_table:
                if line.strip().startswith("|"):
                    table_lines.append(line)
                elif table_lines and not line.strip().startswith("|"):
                    break

        if table_lines:
            parts.append("\n#### Deliverable Matrix (from review-prs SKILL.md)\n")
            parts.extend(table_lines)

        # Extract scope paths with severity classification
        scope_lines: list[str] = []
        in_scope = False
        for i, line in enumerate(rp_lines):
            if "### Scope paths" in line:
                in_scope = True
            if in_scope:
                scope_lines.append(line)
                if line.startswith("###") and len(scope_lines) > 3:
                    # Hit next section header
                    scope_lines.pop()  # remove the next header
                    break

        if scope_lines:
            parts.append("\n" + "\n".join(scope_lines))

        # Extract severity classification for missing deliverables
        severity_lines: list[str] = []
        in_severity = False
        for line in rp_lines:
            if "### Severity classification" in line:
                in_severity = True
            if in_severity:
                severity_lines.append(line)
                # Stop at next ## or ### that isn't the opening header
                if (line.startswith("##") and not line.startswith("###")) and len(severity_lines) > 3:
                    severity_lines.pop()
                    break
                if line.startswith("### ") and len(severity_lines) > 3:
                    severity_lines.pop()
                    break

        if severity_lines:
            parts.append("\n" + "\n".join(severity_lines))

    return "\n".join(parts) if parts else "_No SDLC matrix data extracted._"


def collect_runbook_digests() -> list[dict]:
    """Collect runbook digests from active repos."""
    digests: list[dict] = []

    if not REPO_BASE.is_dir():
        return digests

    for repo_dir in sorted(REPO_BASE.iterdir()):
        if not repo_dir.is_dir():
            continue
        for glob_pattern in RUNBOOK_GLOBS:
            runbook_dir = repo_dir / glob_pattern
            if not runbook_dir.is_dir():
                continue
            for md_file in sorted(runbook_dir.glob("*.md")):
                digest = extract_page_digest(md_file)
                if digest:
                    digest["repo"] = repo_dir.name
                    digest["path"] = str(md_file.relative_to(REPO_BASE))
                    digests.append(digest)

    digests.sort(key=lambda d: d["path"])
    return digests


def format_runbook_digest(digest: dict) -> str:
    """Format a runbook digest as compact markdown."""
    parts = [f"- **{digest['title']}** (`{digest['repo']}`)"]
    if digest["summary"]:
        parts.append(f"  {digest['summary'][:200]}")
    # Just list section headers, no full summaries for runbooks
    if digest["sections"]:
        headers = [s["header"] for s in digest["sections"][:8]]
        parts.append(f"  Sections: {', '.join(headers)}")
    return "\n".join(parts)


def collect_recent_incidents(days: int = 7) -> list[dict]:
    """Summarize action-log files from last N days."""
    incidents: list[dict] = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Check both locations for action logs
    for state_dir in [STATE_DIR_WORKSPACE, STATE_DIR_LOCAL]:
        for log_file in sorted(state_dir.glob("action-log-*.md")):
            # Extract date from filename
            match = re.search(r"action-log-(\d{4}-\d{2}-\d{2})", log_file.name)
            if not match:
                continue
            try:
                log_date = datetime.strptime(match.group(1), "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue

            if log_date < cutoff:
                continue

            try:
                text = log_file.read_text(encoding="utf-8")
            except OSError:
                continue

            # Extract PR review entries as incidents
            current_pr = None
            for line in text.split("\n"):
                if line.startswith("### "):
                    current_pr = line.lstrip("# ").strip()
                elif line.startswith("- **Action:**") or line.startswith("- **Verdict:**"):
                    detail = line.lstrip("- ").strip()
                    if current_pr:
                        incidents.append({
                            "date": match.group(1),
                            "pr": current_pr,
                            "detail": detail,
                            "file": log_file.name,
                        })

    # Deduplicate by (date, pr) — prefer workspace version
    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []
    for inc in incidents:
        key = (inc["date"], inc["pr"])
        if key not in seen:
            seen.add(key)
            unique.append(inc)

    # Sort deterministically
    unique.sort(key=lambda i: (i["date"], i["pr"]))
    return unique


def format_incident(incident: dict) -> str:
    """Format a single incident as a bullet."""
    return f"- **{incident['date']}** | {incident['pr']} | {incident['detail']}"


def collect_knowledge_gaps() -> list[tuple[str, int]]:
    """Read knowledge-gaps.jsonl, group by gap field, return top 10."""
    gap_counts: dict[str, int] = {}

    for gaps_path in KNOWLEDGE_GAPS_PATHS:
        if not gaps_path.is_file():
            continue
        try:
            for line in gaps_path.read_text(encoding="utf-8").strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    gap = entry.get("gap", "").strip()
                    if gap:
                        gap_counts[gap] = gap_counts.get(gap, 0) + 1
                except json.JSONDecodeError:
                    continue
        except OSError:
            continue

    # Sort by count desc, then alphabetically for determinism
    sorted_gaps = sorted(gap_counts.items(), key=lambda x: (-x[1], x[0]))
    return sorted_gaps[:10]


def build_bundle() -> str:
    """Assemble the full review-context bundle."""
    # Collect all data
    wiki_systems, wiki_processes = collect_wiki_digests()
    sdlc_matrix = extract_sdlc_matrix()
    runbook_digests = collect_runbook_digests()
    incidents = collect_recent_incidents(days=7)
    knowledge_gaps = collect_knowledge_gaps()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    wiki_count = len(wiki_systems) + len(wiki_processes)
    runbook_count = len(runbook_digests)
    incident_count = len(incidents)
    gap_count = len(knowledge_gaps)

    # --- Build sections ---
    sections: list[tuple[str, str, bool]] = []  # (name, content, droppable)

    # Section 1: KB Digest — Wiki Systems
    sys_parts = ["## KB Digest: Systems\n"]
    for digest in wiki_systems:
        sys_parts.append(format_page_digest(digest))
        sys_parts.append("")
    sections.append(("wiki_systems", "\n".join(sys_parts), False))

    # Section 2: KB Digest — Wiki Processes
    proc_parts = ["## KB Digest: Processes\n"]
    for digest in wiki_processes:
        proc_parts.append(format_page_digest(digest))
        proc_parts.append("")
    sections.append(("wiki_processes", "\n".join(proc_parts), False))

    # Section 3: SDLC Matrix
    sdlc_section = f"## SDLC Standards Matrix\n\n{sdlc_matrix}"
    sections.append(("sdlc_matrix", sdlc_section, False))

    # Section 4: Runbook Excerpts
    rb_parts = ["## Reliability Runbook Excerpts\n"]
    if runbook_digests:
        for digest in runbook_digests:
            rb_parts.append(format_runbook_digest(digest))
    else:
        rb_parts.append("_No runbooks found in active repos._")
    sections.append(("runbooks", "\n".join(rb_parts), False))

    # Section 5: Recent Fleet Incidents
    inc_parts = ["## Recent Fleet Incidents (Last 7 Days)\n"]
    if incidents:
        for inc in incidents:
            inc_parts.append(format_incident(inc))
    else:
        inc_parts.append("_No action-log entries in the last 7 days._")
    sections.append(("incidents", "\n".join(inc_parts), False))

    # Section 6: Knowledge Gaps
    gap_parts = ["## Knowledge Gaps Roll-Up (Top 10)\n"]
    if knowledge_gaps:
        for gap_text, count in knowledge_gaps:
            gap_parts.append(f"- **{gap_text}** ({count} occurrences)")
    else:
        gap_parts.append("_No knowledge-gaps.jsonl found or file is empty._")
    sections.append(("gaps", "\n".join(gap_parts), False))

    # --- Assemble with budget enforcement ---
    header = (
        f"<!-- review-context bundle: built={now} / "
        f"wiki_pages={wiki_count} / runbooks={runbook_count} / "
        f"incidents={incident_count} / gaps={gap_count} -->"
    )

    body = "\n\n".join(content for _, content, _ in sections)
    full = f"{header}\n\n{body}\n"

    if len(full) <= CHAR_BUDGET:
        return full

    # Over budget: drop wiki pages by least-recently-modified
    # Collect all wiki digests with their formatted sizes
    all_wiki = []
    for digest in wiki_systems:
        all_wiki.append(("systems", digest))
    for digest in wiki_processes:
        all_wiki.append(("processes", digest))

    # Sort by mtime ascending (oldest first = drop first)
    all_wiki.sort(key=lambda x: x[1]["mtime"])

    dropped: list[str] = []
    dropped_set: set[str] = set()

    while len(full) > CHAR_BUDGET and all_wiki:
        category, digest = all_wiki.pop(0)
        dropped.append(f"{category}/{digest['file']} (mtime={digest['mtime']:.0f})")
        dropped_set.add(digest["file"])

        # Rebuild sections without dropped pages
        wiki_systems_filtered = [
            d for d in wiki_systems if d["file"] not in dropped_set
        ]
        wiki_processes_filtered = [
            d for d in wiki_processes if d["file"] not in dropped_set
        ]

        new_wiki_count = len(wiki_systems_filtered) + len(wiki_processes_filtered)

        sys_parts = ["## KB Digest: Systems\n"]
        for d in wiki_systems_filtered:
            sys_parts.append(format_page_digest(d))
            sys_parts.append("")

        proc_parts = ["## KB Digest: Processes\n"]
        for d in wiki_processes_filtered:
            proc_parts.append(format_page_digest(d))
            proc_parts.append("")

        sections[0] = ("wiki_systems", "\n".join(sys_parts), False)
        sections[1] = ("wiki_processes", "\n".join(proc_parts), False)

        header = (
            f"<!-- review-context bundle: built={now} / "
            f"wiki_pages={new_wiki_count} / runbooks={runbook_count} / "
            f"incidents={incident_count} / gaps={gap_count} -->"
        )

        body = "\n\n".join(content for _, content, _ in sections)
        full = f"{header}\n\n{body}\n"

    # Log dropped pages
    if dropped:
        DROPPED_LOG.write_text(
            f"# Bundle pages dropped at {now}\n"
            + "\n".join(f"- {d}" for d in dropped)
            + "\n",
            encoding="utf-8",
        )

    return full


def main() -> None:
    bundle = build_bundle()

    # Write to workspace (git-tracked)
    OUTPUT_PATH_WORKSPACE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH_WORKSPACE.write_text(bundle, encoding="utf-8")

    # Write to local state (symlinked path) if different from workspace
    if OUTPUT_PATH_LOCAL.resolve() != OUTPUT_PATH_WORKSPACE.resolve():
        OUTPUT_PATH_LOCAL.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH_LOCAL.write_text(bundle, encoding="utf-8")

    char_count = len(bundle)
    print(f"Bundle written: {OUTPUT_PATH_WORKSPACE}")
    print(f"  Size: {char_count:,} chars ({char_count / 4:.0f} est. tokens)")
    print(f"  Budget: {'OK' if char_count <= CHAR_BUDGET else 'OVER'} ({char_count:,}/{CHAR_BUDGET:,})")

    if DROPPED_LOG.exists():
        print(f"  Dropped pages log: {DROPPED_LOG}")

    # Exit non-zero if over budget (should not happen after trimming)
    if char_count > CHAR_BUDGET:
        print("ERROR: Bundle exceeds character budget even after trimming!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
