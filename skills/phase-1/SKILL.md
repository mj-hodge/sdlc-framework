---
name: phase-1
description: Run Phase 1 (Concept & Seed) to capture the initial idea, classify scope, and gather codebase context.
---

# Phase 1: Concept & Seed

Run the Concept & Seed phase to capture the initial idea, classify scope, and gather codebase context.

## Identity
- **Role:** Business Analyst
- **Goal:** Deeply understand business needs and define clear requirements
- **Persona:** `.sdlc/agents/phase-1-seed.md`

## Turn Budget & Efficiency (STORY-511)

**Completion is the contract. Conciseness is the tactic.** Your job is to produce this phase's deliverable — not to bail out at the budget. The target below is a pace-setter, not a quit signal.

**Target pace:** ~10 turns. If you're working efficiently (see tactics below) you should land here. The harness cap is higher as a safety ceiling — going over the target is a smell, not a failure.

**Tactics to hit the pace:**

- **Reuse session context.** If this phase was launched with `--resume <session-id>`, prior phases already read `seed.md`, `feature-spec.md`, `test-design.md`, etc. in this same session. Do not re-read them — trust the session cache. Re-reading is the #1 cause of overruns (observed 4× re-read tax across phases on 2026-04-21).
- **Read once, narrowly.** Each file at most once per phase. Use `offset`/`limit` to grab only the part you need. Don't re-open a file to "double-check" — your prior read is authoritative.
- **Stay in scope.** Produce this phase's deliverable first. "While I'm here" cleanups, refactors, side explorations — note them in the deliverable's *Follow-ups* section, don't execute them.
- **Concise output.** Deliverables are file content, not narration. No "I'll now..." framing, no post-hoc recap paragraphs. Ship the file, update tracking docs, stop.
- **Commit as you go.** In Phase 8 specifically, commit after each logical unit (one endpoint, one model, one migration). Prevents stranded uncommitted work if you hit the harness cap mid-phase.

**If the phase is genuinely over-scope (rare):**

Only when the work truly cannot fit in the harness cap — e.g., a Large Phase 8 with 5 independent endpoints. In that case:

1. Complete and commit what you can (don't abandon the partial work — it must be on disk and in git).
2. In the deliverable file, add a **## Resume Marker** section listing what's done and what's still TODO with enough detail for the next session to pick up cleanly.
3. Update `.project` → Phase Routing to note "partial — resume needed."
4. Exit. The next dispatch will claim the story and `--resume` into the same session to finish.

This is iteration, not abandonment. Partial-but-committed is always better than complete-but-uncommitted.

## Steps

1. **Check .project** — Read if exists, note current state
2. **Gather context:**
   - What problem are we solving?
   - Who is the target user?
   - What does success look like?
3. **Classify scope:**
   - Trivial: No logic changes (typos, config)
   - Small: Isolated change, single component
   - Medium: Crosses components, API/DB changes
   - Large: Architectural impact, major refactor
4. **For feature updates:** Use Explore agent to understand affected codebase areas
5. **Create seed.md** using template from software-development-guidance.md
6. **Update .project** with phase status and version history
7. **Create Asana story (REQUIRED):**
   - At the end of Phase 1, you MUST create a new task in the project's Asana board.
   - Use the `cai asana-api.sh` script to create the task.
   - Project name follows the pattern `sdlc-<project-name>`.
   - Task name should be clear and concise.
   - Task notes should contain the expanded story description and initial acceptance criteria from `seed.md`.
   ```bash
   # Get project GID
   PROJECT_GID=$(cai asana-api.sh find-project "sdlc-<project-name>")

   # Create task and get its GID
   TASK_GID=$(cai asana-api.sh create "$PROJECT_GID" "STORY-XXX: <name>" "Notes...")

   # Move to "Backlog" section (default)
   SECTION_GID=$(cai asana-api.sh find-section "$PROJECT_GID" "Backlog")
   cai asana-api.sh move "$TASK_GID" "$SECTION_GID"
   ```
   **For Epic scope — create parent + story subtasks:**
   ```bash
   # Create epic parent task
   EPIC_GID=$(cai asana-api.sh create "$PROJECT_GID" "EPIC: <name>" "Epic description...")
   SECTION_GID=$(cai asana-api.sh find-section "$PROJECT_GID" "Backlog")
   cai asana-api.sh move "$EPIC_GID" "$SECTION_GID"

   # Create story subtasks under the epic (one per decomposed story)
   STORY_GID=$(cai asana-api.sh create-subtask "$EPIC_GID" "[P1] STORY-XXX: <name>" "Notes...")
   cai asana-api.sh move "$STORY_GID" "$SECTION_GID"

   # Create E2E gate subtasks between delivery phases
   E2E_GID=$(cai asana-api.sh create-subtask "$EPIC_GID" "[E2E] STORY-XXX: Phase N Integration" "E2E notes...")
   cai asana-api.sh move "$E2E_GID" "$SECTION_GID"
   ```
8. **Recommend next phase** based on scope

## Outputs

- `features/story-XXX-slug/seed.md` — Problem statement, scope, success criteria
- `.project` — Updated with Phase 1 complete

**Create the story directory** `features/story-XXX-slug/` before writing `seed.md`.

## seed.md — REQUIRED sections (STORY-511 + STORY-528 2026-04-22)

### ## Acceptance Diff — MANDATORY for every seed

Every seed MUST contain a `## Acceptance Diff` section that names the
**specific source files and optional symbols/anchors the PR MUST touch**.
Phase 8 refuses to report Complete unless every named file appears in the
PR's diff. This is the #1 fix for the 2026-04-22 "dashboard work never
landed" class of bug — STORY-515 shipped a reconciler and passing tests
but zero changes to the dashboard components Mark actually wanted updated.

Format (markdown):

```
## Acceptance Diff

The PR for this story MUST include changes to these files. Phase 8 will
fail if any are missing from `git diff origin/main --name-only`:

- `frontend/src/components/DispatchQueue.tsx` must-contain `case 'in_review':` must-contain `in_review` — badge for in_review
- `frontend/src/components/AgentCard.tsx` must-contain `rate_limited` — WorkDetail handles rate-limited case
- `tests/frontend/DispatchQueue.test.tsx` — (file presence only — no content check)
```

Bullet format: `` `<path>` [must-contain `<token>`]... — <human description>``.

- The verifier always checks path presence in the diff.
- For every `must-contain <token>` clause, the file's diff must CONTAIN that literal
  string. This catches the 2026-04-22 STORY-515 class of bug where the agent
  touched the right file but didn't add the specific symbol/line the spec
  demanded. Multiple `must-contain` clauses per bullet are allowed — all
  must appear. No token? File-presence check only.
- The "human description" after the em-dash is for readers; the verifier
  ignores it.

Files that are purely tracking (`.project`, `backlog.md`) are automatic;
don't list them. Phase-1 seed itself IS being written, so don't list
`features/story-XXX-*/seed.md` either.

**If you genuinely have no file-level criterion** (rare — mostly pure-doc
stories), write `## Acceptance Diff` followed by `_None — spec-only story_`
as the body. The verifier treats that as opt-out.

### ## Target Branch — OPTIONAL, for stories patching an existing PR

When this story is a rework / follow-up to an EXISTING PR (e.g. "fix
the review findings on PR #135"), include a ``## Target Branch`` section
in seed.md naming the existing branch. Without it, ``_ensure_branch``
creates a fresh ``story-{N}/story-{N}`` from main and opens a second PR
— the rework never lands on the original PR's review thread.

Format:

```
## Target Branch

story-517/story-517
```

(One line, backticks optional.) When present, ``_ensure_branch`` checks
out that branch from origin, the phase runner commits to it, and
``_save_partial_work``'s branch-isolation guard accepts pushes to it.
Omit the section for greenfield stories — the default story-id-derived
branch is correct for those.

### Other required sections (STORY-511)

Every seed.md MUST contain these four sections with these literal headings.
The compliance test `test_every_seed_has_test_criteria_and_validation` fails
the CI build if any seed.md in `features/` is missing them. Agents will
rightfully refuse a dispatch whose prompt is silent on them — "be
concise" does not mean "skip the contract."

1. `## Problem Statement` — what is broken or missing, in one paragraph.
2. `## Scope` — Trivial / Small / Medium / Large plus a one-line
   justification. Drives the phase path.
3. `## Test Criteria` — a numbered list of pytest-level (or integration-level)
   checks that must pass before the story is "done." Phase 7 picks these up
   verbatim. Not negotiable; a seed without concrete tests is a wish, not a story.
4. `## Validation` — how we'll confirm the fix works end-to-end after it
   ships. Example: "re-run STORY-495 dispatch, observe Phase 6 rc=0"
   or "run agent-doctor.sh on all VMs, every check OK". Phase 8 agents
   check this section before reporting COMPLETE.

Retro-compat: existing seeds without these sections are grandfathered in
(the compliance test only enforces for seeds written after 2026-04-22 via
an mtime check). New seeds don't get the pass.

## Next Phase

| Scope | Next |
|-------|------|
| Trivial | Phase 8 (Implementation) |
| Small | Phase 7 (Test Design) |
| Medium | Phase 4 (Analysis) |
| Large / New | Phase 2 (Research) |

**Full scope paths:**

| Scope | Path |
|-------|------|
| Trivial | → 8 → Done |
| Small | 1 → 7 → 8 → Done |
| Medium | 1 → 4 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → Done |
| Large/New | 1 → 2 → 3 → 4 → 5 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → [9, 10] → Done |

Use `/next` to advance automatically.
