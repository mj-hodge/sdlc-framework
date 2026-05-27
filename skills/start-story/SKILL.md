---
name: start-story
description: Begin work on a story — claim in Asana, create worktree, move to In Progress, break into tasks.
---

# Start Story

Begin work on a story — move to In Progress, create spec, break into tasks.

## Usage

```
/start-story [STORY-ID or story title]
```

## Prerequisites

- `ASANA_TOKEN` environment variable set

> **Note:** Asana MCP tools (`asana_*`) are Claude Code specific. All CLIs must use the wrapper form: `cai asana-api.sh ...`.

## Steps

1. **Find story** — Search in `backlog.md` or use `asana_search_tasks`

2. **Get task GID** from Asana

3. **Normalize Asana task (REQUIRED)**
   Backlog items may be rough ideas. Before starting work, ensure the Asana task follows convention:
   1. **Task name:** Must start with `STORY-XXX:` prefix. If missing, prepend it: `cai asana-api.sh update-name "<task_gid>" "STORY-XXX: <existing or cleaned name>"`. After the prefix, use the story format header: `As a [user] I want [capability] so that [benefit]`, or a short descriptive title if the user-story format doesn't fit
   2. **Description:** Must contain:
      - Full story description (expand rough notes into clear requirements)
      - `Acceptance Criteria:` section with checkboxes (`- [ ] ...`)
      - Scope classification (if already determined)
   3. If the task is just a rough idea (e.g., "add dark mode"), expand it:
      - Infer the user type, capability, and benefit from context
      - Draft 3-5 acceptance criteria based on the idea
      - Update the Asana task with the normalized content via `asana_update_task` (use `notes` field, NOT `html_notes`)
   4. If the task already follows convention, skip this step

4. **Check claim status (multi-worker mode)**
   When `multi_worker: true` in `config.yaml`:
   1. Check Asana task assignee — if already assigned, warn: "This story is claimed by [assignee name]. Continue anyway? (y/n)"
   2. On continue: set Asana task assignee to current worker identity
   3. Worker identity resolution (in order):
      - `config.yaml` → `orchestration.worker_id` (if set)
      - `git config user.name`
      - Auto-generate: `{model}-{YYYYMMDD}-{N}` (e.g., `claude-20260227-1`)

5. **Validate ready** — Confirm story has acceptance criteria (should now exist from step 3)

6. **Classify scope** — Determine if Small, Medium, or Large

7. **Move to In Progress in Asana:**
   ```bash
   # Get project and section GIDs
   PROJECT_GID=$(cai asana-api.sh find-project "sdlc-<project-name>")
   SECTION_GID=$(cai asana-api.sh find-section "$PROJECT_GID" "In Progress")

   # Move task
   cai asana-api.sh move "<task_gid>" "$SECTION_GID"
   ```

   **Set initial phase progress on Asana task (REQUIRED):**
   1. Read current notes: `cai asana-api.sh get "<task_gid>"` → extract `.notes`
   2. Build the SDLC Progress block based on the scope path with Phase 1 as `← current`
   3. Prepend the progress block before existing notes (preserve acceptance criteria etc.)
   4. Write text to temp file, then pass: `cat > /tmp/asana-notes.txt << 'NOTES' ... NOTES` then `cai asana-api.sh update-notes "<task_gid>" "$(cat /tmp/asana-notes.txt)"`
   See `/next` skill § Phase Progress Format for the exact block format.

   **Add comment to Asana task (REQUIRED):**
   ```bash
   cat > /tmp/asana-comment.txt << 'COMMENT'
   Started work on story. Scope: [Scope]. Path: [Phase Path].
   COMMENT
   cai asana-api.sh comment "<task_gid>" "$(cat /tmp/asana-comment.txt)"
   ```

8. **Create story worktree (multi-worker mode)**
   When `multi_worker: true` in `config.yaml`:
   1. Create worktree: `git worktree add .worktrees/STORY-ID -b phase-1/story-slug`
   2. **Switch to the worktree directory** — all subsequent phase work (deliverables, test files, code) MUST be written inside the worktree, never the main project root
   3. Shared files (`.project`, `backlog.md`, `development-tasks.md`) are read-only in worktrees — updated only by the orchestrator or at merge time
   4. **IMPORTANT:** The `.project` version field in the worktree is a stale snapshot. Do NOT read, compare, or reason about the version number. Version bumps happen exclusively at merge time in the main branch.

9. **Update backlog.md** — Move story to In Progress section

10. **Create spec (Medium+ scope):**
    - Create `feature-spec.md` using template
    - Include acceptance criteria
    - Add API/DB changes if applicable

11. **Gather codebase context:**
    - Use Explore agent to find affected files
    - Document in feature-spec.md or .project

12. **Create tasks** — Break story into tasks in `development-tasks.md`

13. **Update .project** — Set current phase based on scope

14. **Update Story Status table (multi-worker mode)**
    When `multi_worker: true` in `config.yaml`:
    Add a row to the `.project` Story Status table:
    ```markdown
    | STORY-016 | @worker-name | Medium | 1 | in_progress | phase-1/story-slug |
    ```

---

**Completion message (REQUIRED):**
Always end with the exact next command:
```
Story STORY-016 started (scope: Medium, phase path: 1 → 4 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → Done)
Worktree: .worktrees/STORY-016 (branch: phase-1/story-016)
Next: `/next STORY-016`
```

## Outputs

| Scope | Outputs |
|-------|---------|
| Small | Updated backlog.md, tasks in development-tasks.md |
| Medium | Above + feature-spec.md |
| Large | Above + full Phase 6 design docs |
| All (multi-worker) | Worktree created, Asana assignee set, Story Status row added |
