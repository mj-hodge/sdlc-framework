---
name: spec
description: Start the SDLC process for a new feature, bug fix, or change request. Use when the user says "spec" followed by a description.
---

# Spec — SDLC Entry Point

Start the SDLC process for a new feature, bug fix, or change request.

**Usage:** `/spec <description of what to build>` (Claude/Gemini) or `spec <description>` in Codex plain language

> **Platform execution:** For Codex-specific execution notes, read `codex.md` in this directory.

## What This Skill Does

This is the **mandatory entry point** for all new work. It initiates Phase 1 (Seed) and routes through the full SDLC based on scope classification.

**Do NOT:**
- Skip directly to implementation
- Create task lists or arbitrary subfolders without going through phases
- Write any code — Phase 1 produces only `seed.md` and tracking updates
- Write deliverables to the project root or a `docs/` directory

**Deliverable location:** `features/story-XXX-kebab-case-slug/` — create this directory in Phase 1 and write `seed.md` inside it.

## Steps

1. **Read project state:**
   - Read `.project` — note current stories, version, active work
   - Read `config.yaml` — check `multi_worker`, `scope`, model settings
   - Read `backlog.md` — check for existing stories (avoid duplicates)

2. **Activate Phase 1 (Seed):**
   - Read the Phase 1 agent persona from `.sdlc/agents/phase-1-seed.md` (or `agents/phase-1-seed.md` if in the config repo)
   - Adopt the **Business Analyst** role
   - Use the user's description as the feature input
   - Follow ALL Phase 1 steps: gather context, classify scope, create `seed.md`, update `.project`
   - **Ask about real data:** "Are there real data samples available (CSVs, API responses, database exports)?" — use real shapes over synthetic, anonymize before including in deliverables

3. **Allocate STORY-N (REQUIRED — single source of truth):**

   Before writing `seed.md`, the STORY-N number MUST be claimed from a single
   registry. **Never write `seed.md` with a STORY-N you "expect to be free"**
   — speculative numbering causes seed-vs-shipped collisions that require
   destructive cleanup (e.g. `features/_shipped/` relocations) once both the
   speculative seed and a production-numbered story share the same `story-NNN`
   directory prefix.

   **Single registry rule.** The project picks exactly ONE registry as the
   source of truth via `config.yaml`:
   - `story_registry: asana` (default) — next free number is `max(Asana
     STORY-N task name prefix in the project) + 1`
   - `story_registry: backlog` — next free number is `max(STORY-N row in
     backlog.md) + 1`

   **Collision check (REQUIRED before writing seed.md):**
   ```bash
   # Refuse to allocate N if it already exists as a directory or backlog row
   N=<proposed_number>
   ls features/story-${N}-*/ features/_shipped/story-${N}-*/ 2>/dev/null && {
       echo "STORY-${N} already exists — pick a different number" >&2
       exit 1
   }
   grep -E "^\| STORY-${N}\b" backlog.md && {
       echo "STORY-${N} already in backlog.md — pick a different number" >&2
       exit 1
   }
   ```

   **Batch (epic) reservations.** When seeding multiple stories at once
   (e.g. an epic spanning 5+ stories), reserve the entire range in
   `backlog.md` BEFORE writing any `seed.md`:
   ```markdown
   | STORY-640 | Reserved — BSR Feature Path | Backlog |
   | STORY-641 | Reserved — BSR Feature Path | Backlog |
   | STORY-642 | Reserved — BSR Feature Path | Backlog |
   ```
   Then write each `seed.md` against its claimed number. This prevents the
   "epic-batched provisional numbering meets Asana-driven allocator" collision
   that produced 5 duplicate STORY-N seeds in a peer project (resolved by
   moving to `features/_shipped/`).

4. **Create or adopt Asana task (REQUIRED):**
   - Project: `sdlc-<directory-name>`
   - Task name: `STORY-XXX: <title>` (story number prefix + user-story format or concise descriptive title)
   - If adopting an existing Asana task: prepend the story number with `cai asana-api.sh update-name "<task_gid>" "STORY-XXX: <existing name>"`
   - Notes: expanded description + acceptance criteria from `seed.md`
   - Place in Backlog section
   ```bash
   PROJECT_GID=$(cai asana-api.sh find-project "sdlc-<project-name>")
   TASK_GID=$(cai asana-api.sh create "$PROJECT_GID" "Task name" "Notes...")
   SECTION_GID=$(cai asana-api.sh find-section "$PROJECT_GID" "Backlog")
   cai asana-api.sh move "$TASK_GID" "$SECTION_GID"
   ```

5. **STOP (gate) — Phase 1 advance category is `gate`:**
   - Show the `seed.md` deliverable
   - Show scope classification and recommended phase path
   - Wait for explicit user approval before doing anything else
   - Do NOT start the next phase

6. **After user approval — multi-worker auto-start:**
   When `multi_worker: true` in `config.yaml`:
   - Automatically run the `/start-story` protocol (claim + worktree + Story Status row)
   - This creates the worktree and prepares for Phase 2+ work
   - Output the exact `/next STORY-ID` command for the user

## Outputs

- `features/story-XXX-slug/seed.md` — Problem statement, scope, success criteria, acceptance criteria
- `.project` — Updated with new story and Phase 1 complete
- `backlog.md` — New story added
- Asana task — Created in project board

## Phase Path (determined by scope)

| Scope | Path |
|-------|------|
| Trivial | → 8 → Done |
| Small | 1 → 7 → 8 → Done |
| Medium | 1 → 4 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → Done |
| Large/New | 1 → 2 → 3 → 4 → 5 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → [9, 10] → Done |

## Example Completion Output

```
## Phase 1 Complete — Seed

**Story:** STORY-028: As a user I want dark mode so that I can reduce eye strain
**Scope:** Medium
**Phase path:** 1 → 4 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → Done
**Asana:** Task created (GID: 12345)

### seed.md Summary
- Problem: Users report eye strain during extended sessions
- Success: Toggle dark/light mode, persists across sessions
- Acceptance Criteria: 5 items

**Awaiting approval to proceed.**
Next: `/next STORY-028` (after approval)
```
