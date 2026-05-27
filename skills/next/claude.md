# /next — Claude Code Execution

Platform-specific execution details for the `/next` skill in Claude Code.

## Model Tier Mapping

| Tier | Claude Model |
|------|-------------|
| tier-1 (reasoning) | Opus (always latest) |
| tier-2 (execution) | Sonnet (always latest) |

## Sub-agent Dispatch

Use Claude Code's **Task tool** to launch sub-agents:

```
Task(model: "sonnet", subagent_type: "general-purpose", prompt: "...")
```

### Model Enforcement

- **Opus doing tier-2 work (e.g., Phase 8):** Delegate ALL work to Task subagents with `model: "sonnet"`. Opus orchestrates only — dispatches, verifies, commits. Prevents ~15x cost overrun.
- **Sonnet doing tier-1 work (e.g., Phase 1, 9, 10):** Delegate ALL work to a Task subagent with `model: "opus"`. Sonnet orchestrates only — dispatches, verifies, commits. Never ask the user to switch models.
- **Orchestrated phases (2, 3, 4, 8b):** MUST specify `model: "sonnet"` (or `model: "opus"` for 8b-architect) on every Task subagent launch. Never inherit the orchestrator's model.
- **Override:** `config.yaml` → `models.opus_allowed: true` lets Opus do Sonnet-default phases directly.

## Parallel Group Execution

### [6b, 6c, 6d] — Security + UX + Ops Review
- Launch Phase 6b as Task subagent (model: "sonnet")
- Launch Phase 6c as Task subagent (model: "sonnet")
- Launch Phase 6d as Task subagent (model: "sonnet")
- All three run concurrently, orchestrator waits for results

### Phase 8 — Parallel Stories (Worktree Isolation)
- Launch one Task subagent per story with `isolation: "worktree"`
- Set `max_turns: 200` per story agent to prevent runaway token burn
- Install pre-commit hook in each worktree to enforce file boundary
- Branch naming: `phase-8/{story-slug}`
- Do NOT `/clear` during parallel execution — context needed for merge orchestration

### Phase 11 — Pre-Deploy Gate
- Phase 11 is a sequential gate — run in main session (not parallel-safe)
- Read `agents/phase-11-predeploy-gate.md`, adopt Release Engineer persona
- Run all 8 checks and produce `predeploy-gate.md`
- **GATE STOP:** Present report, wait for explicit "Approved to deploy" user sign-off
- Model: tier-2 (Sonnet) — delegate to Task subagent with `model: "sonnet"` if currently Opus

### [9, 10] — Refinement + Operations
- Phase 9 runs in main session (modifies code — not parallel-safe)
- Launch Phase 10 as Task subagent (model: "opus")

## Context Management

- Use `/clear` to clear context between context groups
- Tell user: "Please `/clear`, then use `/next` to start Phase X."
- **Exception:** No `/clear` during Phase 8 parallel execution

## Asana Integration

Both MCP tools and bash scripts are available:

**MCP tools:** `asana_search_tasks`, `asana_get_tasks`, `asana_update_task`, `asana_create_task`

**Bash scripts:**
```bash
cai asana-api.sh get "<task_gid>"              # Read task details (name, notes, assignee, status)
cai asana-api.sh update-name "<task_gid>" "<name>"    # Update task name
cai asana-api.sh update-notes "<task_gid>" "$(cat /tmp/asana-notes.txt)"  # Update notes (write to temp file first)
cai asana-api.sh comment "<task_gid>" "$(cat /tmp/asana-comment.txt)"    # Add comment (write to temp file first)
cai asana-api.sh move "<task_gid>" "<section_gid>"
cai asana-api.sh complete "<task_gid>"
```

**Long text args:** Always write multi-line or special-char text to a temp file first (`cat > /tmp/asana-notes.txt << 'NOTES' ... NOTES`), then pass via `"$(cat /tmp/asana-notes.txt)"`. This avoids shell quoting issues.

**Phase progress update (every phase transition):**
After advancing a phase, update the task notes with the SDLC Progress block (see SKILL.md § Phase Progress Format). Use `get` to read current notes, rebuild the progress block, write to `/tmp/asana-notes.txt`, then `update-notes` to write back.

## Multi-Worker Story Dispatch

When `multi_worker: true` in `config.yaml`:

### Story-Scoped Phase Advancement
- Each `/next STORY-ID` reads that story's row from `.project` Story Status table
- The agent adopts the persona for that story's current phase
- All phase work happens in the story's worktree branch
- Phase completion updates both the Story Status table and Asana

### --claim Mode
- Search Asana for Ready tasks with no assignee: `asana_search_tasks` in Ready section. **Exclude tasks in "Do Not Do" section.**
- Assign to current worker via `asana_update_task`
- Create worktree: use Task tool with `isolation: "worktree"` or `git worktree add`
- Add row to `.project` Story Status table
- Begin Phase 1 in the worktree

### Completion UX
After every phase completion, output the exact next command:
```
Phase 6 complete for STORY-016.
Next: `/next STORY-016`
```
Or if context clear needed:
```
Phase 7 complete for STORY-016. Context group change: test → implementation
Please `/clear`, then: `/next STORY-016`
```
