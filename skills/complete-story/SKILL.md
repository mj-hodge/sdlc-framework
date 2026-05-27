---
name: complete-story
description: Mark a story as complete — update Asana, backlog.md, .project, and merge worktree.
---

# Complete Story

Mark a story as complete — update Asana (section + completed flag), update backlog.md, update .project.

## Usage

```
/complete-story [STORY-ID or story title]
```

## Prerequisites

- `ASANA_TOKEN` environment variable set

> **Note:** Asana MCP tools (`asana_*`) are Claude Code specific. All CLIs must use the wrapper form: `cai asana-api.sh ...`.

## Steps

1. **Find story** — Search in `backlog.md` In Progress section

2. **Get task GID** from Asana using `asana_search_tasks` or from `backlog.md`

3. **Verify completion:**
   - All acceptance criteria met?
   - All tasks in development-tasks.md complete?
   - Tests passing?
   - For Medium+: Phase 8b code review complete with all findings dispositioned?
   - For Large/New: Both Phase 9 AND Phase 10 complete? (check Parallel Group Status if `[9, 10]` was active)
   - For epic stories: All [OPS] stories from Phase 10 completed? Epic cannot close with open ops tickets.
   - If `.project` shows `parallel_active` status: all phases in the group must be `complete`

4. **Merge worktree (multi-worker mode)**
   When `multi_worker: true` in `config.yaml` and story has a worktree:
   1. Run full test suite in worktree — verify all tests pass before merge
   2. Switch to main branch
   3. Merge worktree branch: `git merge --no-ff phase-N/story-slug`
      - If merge conflicts: resolve using smallest-changeset-first strategy
      - If multiple stories completing simultaneously: merge smallest changeset first
   4. Run full test suite on main after merge — if failures, investigate before proceeding
   5. Remove worktree: `git worktree remove .worktrees/STORY-ID`
   6. Delete branch: `git branch -d phase-N/story-slug`

5. **Move to Done section in Asana:**
   ```bash
   cai asana-api.sh move "<task_gid>" "<done_section_gid>"
   ```

6. **Mark task as completed in Asana** (REQUIRED — moving to Done section alone is NOT sufficient):
   ```bash
   cai asana-api.sh complete "<task_gid>"
   ```

7. **Update phase progress to show all phases complete:**
   1. Read current notes: `cai asana-api.sh get "<task_gid>"` → extract `.notes`
   2. Rebuild the SDLC Progress block with all phases marked `[x]` (no `← current`)
   3. Replace existing progress block in notes, or prepend if none exists
   4. Write text to temp file, then pass: `cat > /tmp/asana-notes.txt << 'NOTES' ... NOTES` then `cai asana-api.sh update-notes "<task_gid>" "$(cat /tmp/asana-notes.txt)"`
   See `/next` skill § Phase Progress Format for the exact block format.

8. **Update backlog.md:**
   - Move from In Progress to Done section
   - Add `Completed` date field
   - Mark all acceptance criteria as `[x]`
   - Remove any stale notes (e.g., "8b review pending")

9. **Update .project:**
   - Set Current Phase Status to `complete`
   - Add version history entry and phase history
   - **Worktree rule:** If running in a worktree, do NOT update the version field or Version History table — they are stale snapshots. Version bumps happen exclusively at merge time in the main branch. Only update phase status.

10. **Update Story Status table (multi-worker mode)**
    When `multi_worker: true` in `config.yaml`:
    - Remove the story's row from `.project` Story Status table (or mark as `complete`)
    - Clear Asana task assignee

11. **Clean up:**
   - Archive completed tasks from development-tasks.md
   - Archive feature-spec.md if applicable (move to `archive/`)

12. **Epic-end retro hook (STORY-1003):**
    If this is the LAST story of an epic, dispatch `/retro <epic-name>` as a follow-up job so the team captures lessons before the epic closes.

    **Epic-completion check:**
    - Look up the epic this story belongs to (Asana parent task, or `epic:` field in `backlog.md` / `.project`).
    - The epic is considered complete when **every** story in it is in the Done section AND marked `completed=true` in Asana.
    - **TODO (canon-backport followup):** if the project does not yet expose an `active-projects.md` ledger, fall back to checking `state/morris/active-projects.md` for a matching epic with status `closing` or `complete`. If that file does not exist, skip the auto-dispatch and emit a warning so the user can run `/retro` manually.

    **Dispatch:**
    ```bash
    # Pseudo: enqueue via the v2 dispatch queue (mirrors phase-9 → canon-backport).
    # The retro skill itself runs as a follow-up dispatch and writes
    # features/<epic-folder>/retro-proposal.yaml (+ optional gc-data-v2 companion).
    POST {ops_console}/api/dispatch/v2/enqueue
      story_id: "<epic-name>-retro"
      prompt:   "/retro <epic-name>"
      scope:    "small"
      enqueued_by: "complete-story-hook"
    ```

    **Skip conditions:** if the epic is not complete, OR if a retro-proposal.yaml already exists for this epic (idempotency), skip the dispatch and log the reason.

## Verification Checklist

Before marking complete:
- [ ] All acceptance criteria checked off
- [ ] Tests written and passing
- [ ] Code reviewed (Phase 8b for Medium+)
- [ ] No open tasks remaining
- [ ] Ops requirements from Phase 6 design verified as implemented (epic stories)
- [ ] No open [OPS] stories blocking epic close (epic stories)
- [ ] Asana task in Done section AND marked `completed=true`
- [ ] backlog.md reflects Done status with completion date
- [ ] .project version history updated
- [ ] Worktree merged to main (multi-worker)
- [ ] All tests passing on main after merge (multi-worker)
- [ ] Worktree removed and branch deleted (multi-worker)
- [ ] Story Status table updated (multi-worker)

## Output

- Asana story moved to Done AND marked completed
- backlog.md updated (story in Done section, criteria checked)
- .project updated (version, phase history)
- Summary of completed work

**Completion message (REQUIRED):**
Always end with guidance on what the user can do next:
```
Story STORY-016 complete. Worktree merged and cleaned up.
Remaining active stories: STORY-017 (Phase 6), STORY-018 (Phase 4)
Suggested next: `/next STORY-017` or `/next --claim`
```
If no remaining stories:
```
Story STORY-016 complete. No active stories remaining.
Suggested next: `/next --claim` to pick up the next Ready story
```

**STOP AFTER COMPLETION (CRITICAL):**
After outputting the completion message, **STOP immediately. END your response.** The "Suggested next:" lines are for the **user to read and decide** — do NOT execute them yourself. Do NOT auto-claim the next story. Do NOT start any new work. Wait for the user's explicit instruction.
