---
name: sync-source
description: Pull incremental updates from a Claude desktop app project sync folder into the project's reference/, classify each change, and propose SDLC follow-up actions.
---

# Sync Source

Pull updates from a synced source-of-truth folder (typically the Claude desktop app's project sync directory) into the project's committed `reference/` folder, classify each change, and propose the right SDLC re-entry point if any.

## Use case

A claude.ai project shared with you contains source-of-truth briefs maintained by another author. The Claude desktop app syncs that project to your local filesystem at a stable path (typically `~/Desktop/<project-uuid>/` on macOS, `Desktop\<project-uuid>\` on Windows). This skill compares the synced state against the last-ingested baseline, identifies new / modified / deleted files, classifies the change impact, and proposes SDLC follow-up actions.

## Configuration

Add to your project's `config.yaml`:

```yaml
source_sync:
  enabled: true
  source_path: "C:/Users/Lawrence Paul/Desktop/<project-uuid>"  # absolute path to the synced source folder
  reference_path: "reference"                                    # destination directory inside the project
  baseline_file: ".claude/sync/source-baseline.json"             # tracked state for diff detection
```

If `source_sync.enabled` is `false` or the section is missing, the skill exits with a configuration error.

## Workflow

1. **Read config** — load `source_sync` from `config.yaml`. Verify `source_path` exists. If `enabled: false`, exit.
2. **Run the helper script** — `python .sdlc/scripts/sync_source.py --source <source_path> --baseline <baseline_file>` (DO NOT pass `--update-baseline` yet). Capture the JSON output.
3. **First-run mode** (no baseline yet) — if `mode: "initial"`, confirm with the user that the current state of the source folder is the correct baseline. Re-run with `--update-baseline` to write the baseline. No SDLC follow-up; commit with `sync(source): initial baseline of N files`.
4. **Diff mode** — show the summary (NEW / MODIFIED / DELETED / UNCHANGED counts) to the user.
5. **Gather diffs** — for each MODIFIED text file, `Read` both old (`reference_path/<rel>`) and new (`source_path/<rel>`) versions and compute a unified diff. For NEW files, `Read` the new file. For binary files, capture only size delta.
6. **Dispatch the validator sub-agent** (`agents/sync-source-validator.md`):
   - Tier-2 (Sonnet), low effort
   - Inputs: all diffs, plus `seed.md`, `research.md`, `.project`, contents of `reference/briefs/`
   - Output: a structured markdown report (validator table + summary + contradictions)
7. **If validator returns 1+ `new-requirement` classifications, dispatch the story-spawner sub-agent** (`agents/sync-source-story-spawner.md`):
   - Tier-1 (Opus), high effort
   - Inputs: each new-requirement diff + validator reasoning + current `features/` listing + `backlog.md` + `.project` Key Decisions + STORY-001 seed
   - Output: drafted `seed.md` files at `features/_proposed/STORY-NNN-slug/seed.md` + summary blocks
8. **If validator returns 1+ `contradiction` classifications**, do NOT auto-resolve. Surface the contradiction analysis verbatim to the user and ask which phase deliverable to revisit (Phase 4 / 5 / 6 most commonly).
9. **Present consolidated report to user**:
   - Validator table + summary + contradictions
   - Story-spawner drafts (read each `_proposed/STORY-NNN/seed.md` and show the user)
   - Recommended SDLC follow-ups
10. **User approves** → apply changes:
    - Copy each updated/new file from `source_path` to `reference_path`
    - For each approved drafted story: move `features/_proposed/STORY-NNN-slug/` → `features/STORY-NNN-slug/`; append to `backlog.md` "Backlog" section; create monday task (or queue for `/sync-backlog`)
    - Re-run helper script with `--update-baseline` to write the new baseline
    - Append rows to `.project` § Key Decisions for material changes (severity ≥ medium)
    - Append rows to `.project` § Phase History if a contradiction triggers a phase revisit
11. **Commit** — `sync(source): N modified, M added, K deleted (Y new stories drafted, Z contradictions flagged)`. Body lists each file + classification + severity, plus drafted story numbers.
12. **Push** to `origin/main`.
13. **Print "Suggested SDLC follow-up"** — list any new stories to seed (now in `features/`), phases to revisit (per contradictions), or Phase 1 gates to re-run for proposed stories.

> **User-in-the-loop is mandatory.** Even with validator + spawner automation, drafted stories live in `features/_proposed/` until the user approves. Contradictions are NEVER auto-resolved.

## Outputs

- Updated files in `reference_path` (or whatever was configured)
- Updated `.claude/sync/source-baseline.json`
- Commit pushed to `origin/main`
- (Optional) new entries in `.project` § Key Decisions
- (Optional) new story folders in `features/` (if user accepts new-requirement proposal)
- Console output: list of recommended SDLC follow-ups

## Tools

- `Read`, `Bash`, `Edit`, `Write` — standard tools
- `.sdlc/scripts/sync_source.py` — file-hash + diff helper (cross-platform Python)

## Edge cases

- **Source path doesn't exist** → error and exit; tell user to check claude.ai desktop app sync.
- **Binary files** (xlsx, pdf, images) → no inline diff; show size delta only; user decides if material.
- **Renames** → v1 reports as DELETED + NEW; user confirms intent. (Future: detect by content hash match.)
- **Concurrent edits during sync** → if hashes change between read and copy, retry once; abort if still inconsistent.
- **Path with spaces / non-ASCII** — script handles via `pathlib`; always quote in shell.

## See also

- `/sync-backlog` — sibling skill for syncing task tracker → `backlog.md`
- AGENTS.md § Skills table
