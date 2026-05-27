---
name: next
description: Advance to the next SDLC phase automatically. Resolves current story, checks advance category, and routes to the correct phase.
---

# Next Phase

Advance to the next SDLC phase automatically.

**Usage:** `/next [STORY-ID | --claim]` (Claude/Gemini) or `next [STORY-ID | --claim]` in Codex plain language

| Invocation | Behavior |
|-----------|----------|
| `/next` (no args) | **One story active** → advance it. **Multiple active** → list them with phases, ask which to advance. **Zero active** → auto-claim next Ready story from Asana and begin it. |
| `/next STORY-016` | Advance that specific story. Look up its current phase from `.project` Story Status table. |
| `/next --claim` | Explicitly claim next unclaimed Ready story in Asana, assign to current worker, move to In Progress, begin its first phase. |

> **Platform execution:** Read `claude.md` (Claude Code), `gemini.md` (Gemini CLI), or `codex.md` (Codex CLI) in this directory for platform-specific execution details.

## Steps

1. **Resolve target story**

   When `multi_worker: true` in `config.yaml`:
   1. If story ID provided → look up that story in `.project` → get current phase
   2. If no story ID → find all active stories:
      - **Check Asana first (live state):** query In Progress tasks in the project's Asana board — this is the source of truth for what's being worked on
      - **Cross-reference `.project`:** look for Story Status (Multi-Worker) table, or legacy Story Parallel Status table, or single-value Phase Routing
      - Include ALL stories with non-complete status (don't filter by assignee — the human user owns everything)
      - If `.project` and Asana disagree, trust Asana
   3. If exactly one → use it (zero friction — no confirmation needed)
   4. If multiple → list them with their current phases and assignees, ask user which to advance
   5. If zero → **list available stories**: query Asana for Ready tasks with **no assignee** — verify live state, don't rely on stale `.project`. **Exclude tasks in "Do Not Do" section.** List them and tell the user they can claim one via `/start-story STORY-ID`. **DO NOT AUTO-CLAIM.**
   6. If `--claim` → same as zero-story behavior above (explicit trigger) — list stories for user selection. **DO NOT AUTO-CLAIM.**

   **"Do Not Do" exclusion:** Tasks in the "Do Not Do" section are invisible to all agent operations — never claim, suggest, or include them in any listing.

   **CRITICAL:** `.project` may be stale in worktrees. Always verify against Asana before claiming or suggesting stories. A story showing as "Ready" in `.project` may already be claimed by another worker in Asana.

   When `multi_worker: false` (or missing) → proceed directly to Step 2 using single Phase Routing values from `.project`.

2. **Read `.project`** — Phase Routing section
   - Get `Current Phase`, `Current Status`, `Scope Path`, `Context Strategy`
   - If no `.project` exists, tell the user to start Phase 1 first

3. **Verify Asana is current (REQUIRED before advancing):**
   - Look up the project's Asana board (`sdlc-<directory-name>`)
   - Find the current story's Asana task
   - Check that its section matches the phase status in `.project`
   - If Asana is stale (wrong section, not updated): update it NOW before advancing
   - Use Asana MCP tools or `cai asana-api.sh` to verify/update
   - This step prevents drift — never skip it

4. **Check current phase status:**
   - If `in_progress` or `parallel_active`: resume (don't advance)
   - If `complete` or all parallel phases complete: advance to next step
   - If `pending`: begin the phase

5. **Determine next step from Scope Path:**
   - Parse the scope path to find what follows the current phase
   - Handle bracket notation: `[6b, 6c, 6d]` is a parallel group, not two separate steps

6. **Model enforcement gate (REQUIRED — check before ANY phase work):**
   - Read the next phase's `model` field from its agent persona YAML frontmatter
   - Determine your current model tier (tier-1 = reasoning, tier-2 = execution)
   - Map tiers to concrete models via `config.yaml` → `model_tiers` section
   - **If the phase requires tier-2 and you are tier-1:**
     - Do NOT begin the phase directly
     - Delegate ALL phase work to tier-2 sub-agents
     - Your role is orchestrator only: dispatch, monitor, verify results, commit code
     - Exception: `config.yaml` has `models.opus_allowed: true`
   - **If the phase requires tier-1 and you are tier-2:**
     - Delegate ALL phase work to a tier-1 sub-agent (e.g., `Task(model: "opus")`)
     - Your role is orchestrator only: dispatch, verify results, commit
     - The user should NEVER be asked to manually switch models
   - **For orchestrated phases (2, 3, 4, 8b):**
     - Always dispatch sub-agents at the correct tier (see platform-specific file)
     - Never let sub-agents inherit the orchestrator's model
   - Log the model check: "Model gate: current=tier-1, required=tier-2 → delegating to sub-agents"

7. **Apply advance category** (read from agent persona's `advance` field):

   **auto** (6b, 6c, 6d, 8b):
   - Start the next phase immediately
   - No user confirmation needed
   - Update `.project` and proceed

   **confirm** (2, 3, 4, 5, 6, 7, 9, 10):
   - Show a summary of what the completed phase produced
   - Show what the next phase will do
   - Ask: "Proceed to Phase X? (y/n)"
   - On "y": advance. On "n": stop and wait for user direction

   **gate** (1, 8, 11):
   - Show the phase deliverables for review
   - List any gate requirements that must be verified
   - Wait for explicit user approval before advancing

8. **Handle parallel groups:**

   **Starting `[6b, 6c, 6d]`:**
   - Set `.project` Current Phase to `[6b, 6c, 6d]`, status to `parallel_active`
   - Launch Phase 6b sub-agent:
     - Read `agents/phase-6b-security.md`
     - Read Phase 6 design docs (architecture.md, api-design.md, database-schema.md, feature-spec.md)
     - Produce `security-review.md`
   - Launch Phase 6c sub-agent:
     - Read `agents/phase-6c-ux-review.md`
     - Read Phase 6 design docs
     - Produce `ux-review.md`
   - Launch Phase 6d sub-agent:
     - Read `agents/phase-6d-ops-review.md`
     - Read Phase 6 design docs
     - Produce `ops-review.md`
   - Update Parallel Group Status table in `.project`
   - If any finds critical/high issues: set status to `blocked`, report findings
   - If all clean: advance past the group to next phase

   **Starting Phase 8 (parallel stories enabled):**
   1. Read `config.yaml` — check `orchestration.parallel_stories` and `parallel_stories_min`
   2. If `parallel_stories` is `false` or missing → use sequential Phase 8
   3. Read `implementation-plan.md` → locate File Ownership Matrix
   4. Count ready stories; if fewer than `parallel_stories_min` (default 3) → sequential
   5. Validate ownership matrix: no overlap in "Modifies" column across stories
      - If overlap found → STOP, report conflict, fall back to sequential
   6. Set `.project`:
      - Current Phase: `8`
      - Current Status: `parallel_active`
      - Populate Story Parallel Status table with one row per story (status: `pending`)
   7. Launch one sub-agent per story in an isolated environment:
      - Each agent reads: `agents/phase-8-implementation.md`, its story section of `implementation-plan.md`, its test files, design docs, its File Ownership Matrix row
      - Branch naming: `phase-8/{story-slug}`
      - Agent prompt must include: ownership boundary, test DB name (`test_db_{story_slug}`), forbidden actions list, interface contracts
      - See platform-specific file for isolation and dispatch details
   8. As agents complete: update Story Parallel Status table
   9. When ALL agents complete → follow Merge Gate steps in `agents/phase-8-implementation.md`
      - If tests pass → set Phase 8 status to `complete`, advance to 8b
      - If tests fail → set status to `merge_blocked`, report failures
   10. Do NOT clear context during parallel execution — context is needed for merge orchestration

   **Starting Phase 11 (Pre-Deploy Gate):**
   - Phase 11 is a sequential gate phase — not parallel
   - Set `.project` Current Phase to `11`, status to `in_progress`
   - Run all 8 automated checks (see `agents/phase-11-predeploy-gate.md`)
   - Produce `predeploy-gate.md` with results
   - **GATE STOP:** Present report, wait for explicit user "Approved to deploy"
   - Only after explicit approval: advance to next phase (Done for Medium, `[9, 10]` for Large/New)

   **Starting `[9, 10]`:**

   - Set `.project` Current Phase to `[9, 10]`, status to `parallel_active`
   - Phase 9 runs in main session (modifies code — not parallel-safe for sub-agent)
   - Launch Phase 10 sub-agent:
     - Read `agents/phase-10-operations.md`
     - Read implementation docs, architecture docs
     - Produce `site-reliability.md`
   - Begin Phase 9 in main session
   - When both complete: mark group as done

9. **Check context group boundary:**
   - Read current phase's `context_group` from agent persona
   - Read next phase's `context_group` from agent persona
   - If **same group** AND `context_strategy` is `grouped` or `minimal`: proceed directly (no context clear)
   - If **different group**: signal context boundary, update `.project` so next invocation picks up correctly
   - If `context_strategy` is `strict`: always signal context boundary
   - **Exception:** No context clear during Phase 8 parallel execution — context is needed for merge orchestration

10. **Update all tracking docs and output next command (atomic — all four, no exceptions):**
    - Follow Phase Completion Protocol
    - `.project` — phase routing (include story ID in Story Status table when `multi_worker: true`)
    - **Version rule:** When in a worktree, do NOT update the `.project` version field or Version History table — these are stale snapshots. Version bumps happen exclusively at merge time in the main branch. Only update phase routing and Story Status.
    - `backlog.md` — story status
    - `development-tasks.md` — task status
    - **Asana — move task to correct section, update status**
      ```bash
      cai asana-api.sh move "<task_gid>" "<section_gid>"
      ```
    - **Asana — add comment summarizing work (REQUIRED)**
      ```bash
      cat > /tmp/asana-comment.txt << 'COMMENT'
      Phase X completed. Summary of work...
      COMMENT
      cai asana-api.sh comment "<task_gid>" "$(cat /tmp/asana-comment.txt)"
      ```
    - If story is reaching its final phase, also mark Asana task complete:
      ```bash
      cai asana-api.sh complete "<task_gid>"
      ```
    - **Asana — update phase progress in task notes (REQUIRED at every phase transition):**
      1. Read current task notes: `cai asana-api.sh get "<task_gid>"` → extract `.notes`
      2. Build the progress block (see Phase Progress Format below)
      3. Replace existing progress block in notes (between `--- SDLC Progress ---` markers), or prepend if none exists
      4. Write text to temp file, then pass: `cat > /tmp/asana-notes.txt << 'NOTES' ... NOTES` then `cai asana-api.sh update-notes "<task_gid>" "$(cat /tmp/asana-notes.txt)"`
    - **Guide the user to the next step with minimal effort:**
      - **Same context group (no /clear needed):** Apply the advance category directly —
        - **auto:** proceed immediately, no user input
        - **confirm:** ask `"Continue to Phase 6 for STORY-016?"` — user confirms yes/no
        - **gate:** show deliverables, wait for approval, then continue
      - **Different context group (/clear needed):** tell the user `"Please /clear, then /next"` (the agent will auto-resolve the story after clear)
      - **Story done:** `"Story STORY-016 complete. Run /next to auto-claim the next story."`
      - The user should NEVER need to type a story ID — `/next` auto-resolves

## Phase Progress Format

The following block is prepended to (or replaces the existing block in) the Asana task notes at every phase transition. It gives visibility into SDLC progress directly on the Asana ticket.

**Format:**
```
--- SDLC Progress ---
Scope: Medium | Path: 1 → 4 → 6 → [6b,6c,6d] → 7 → 8 → 8b → 11

[x] Phase 1: Seed
[x] Phase 4: Analysis
[x] Phase 6: Design
[x] Phase 6b: Security Review
[x] Phase 6c: UX Review
[x] Phase 6d: Ops Review
[ ] Phase 7: Test Design  ← current
[ ] Phase 8: Implementation
[ ] Phase 8b: Code Review
[ ] Phase 11: Pre-Deploy Gate
--- End SDLC Progress ---
```

**Rules:**
- `[x]` = completed phase, `[ ]` = pending/future, `← current` marks the active phase
- Only include phases in the story's scope path (don't show phases not on the path)
- Parallel phases (e.g., 6b, 6c) are listed individually
- The block is delimited by `--- SDLC Progress ---` / `--- End SDLC Progress ---` markers for easy find-and-replace
- Everything after `--- End SDLC Progress ---` is the original task description (acceptance criteria, notes, etc.) — preserve it exactly

**Building the notes:**
1. `get` the task → extract `notes` field
2. If notes contain `--- SDLC Progress ---`, strip everything between (and including) the start/end markers
3. Prepend the new progress block + a blank line before the remaining notes
4. `update-notes` with the combined result

## Context Strategy Behavior

| Strategy | Context Clear Timing |
|----------|---------------------|
| `strict` | Between every phase (legacy) |
| `grouped` | Between context groups only (default) |
| `minimal` | Only before and after Phase 8 |

If `config.yaml` has no `orchestration` section, default to `strict` (backwards compatible).

## Examples

**Same context group — auto-continue (Phase 6 → [6b, 6c, 6d]):**
```
Phase 6 complete for STORY-016.
Same context group (design) — launching [6b, 6c, 6d] parallel reviews now...
```

**Same context group — confirm (Phase 4 → 6):**
```
Phase 4 complete for STORY-016.
Continue to Phase 6 (Design) for STORY-016? (y/n)
```

**Context group change (Phase 7 → 8):**
```
Phase 7 complete for STORY-016. Context group change: test → implementation
Please /clear, then /next
```

**Story complete:**
```
Story STORY-016 complete. All phases done.
Run /next to auto-claim the next Ready story.
```

**No story in progress — auto-claim (multi-worker):**
```
No active stories. Claiming next Ready story from Asana...
Starting STORY-019 (scope: Medium, phase path: 1 → 4 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → Done)
Worktree: .worktrees/STORY-019 (branch: phase-1/story-019)
Beginning Phase 1...
```

**Multiple stories in progress (multi-worker, /next with no args):**
```
Multiple stories in progress. Which would you like to advance?
- STORY-016 (currently at Phase 6 — Design)
- STORY-019 (currently at Phase 7 — Test Design)
Run /next STORY-016 or /next STORY-019.
```

## Backwards Compatibility

- When `multi_worker` is `false` or absent in `config.yaml`, `/next` behaves identically to the single-story design. The Story Status table has one row.
- "Clear context" + "continue" still works — the Continue Protocol in `.project` is unchanged
- Missing `orchestration` config defaults to `strict` (every phase clears)
- Scope paths without brackets work (fully sequential)
- All existing phase skills still work for manual invocation
