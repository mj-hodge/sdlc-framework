# /next — Gemini CLI Execution

Platform-specific execution details for the `next` skill in Gemini CLI.

## Model Tier Mapping

| Tier | Gemini Model |
|------|-------------|
| tier-1 (reasoning) | Pro (always latest) |
| tier-2 (execution) | Flash (always latest) |

## Sub-agent Dispatch

Gemini CLI does not have a native parallel sub-agent dispatch mechanism. For orchestrated phases:

1. **Use `codebase_investigator`** for research-oriented sub-agents (Phase 2, 3, 4)
2. **Adopt persona explicitly** by reading the agent file from `.sdlc/agents/` and following its instructions
3. Execute sub-agent personas **sequentially** — complete one, then the next
4. Synthesize results after all sub-agent work is complete

### Model Enforcement

- Before each phase, verify your model matches the required tier
- **Gemini CLI Constraint:** If you are running as Gemini Pro (tier-1) and the phase requires tier-2 (e.g., Phase 8), **PROCEED sequentially** if you are the primary session and cannot delegate to a Flash sub-agent.
- **Cost Awareness:** Mention that tier-1 is more expensive, but prioritize finishing the current logical unit (story) over stopping for model switching if no automation is available.
- **For orchestrated phases:** Adopt each sub-agent persona sequentially.


## Parallel Group Execution

### [6b, 6c, 6d] — Security + UX + Ops Review
- Adopt Phase 6b persona → produce `security-review.md`
- Adopt Phase 6c persona → produce `ux-review.md`
- Adopt Phase 6d persona → produce `ops-review.md`
- Run sequentially (no true parallel dispatch available)

### Phase 8 — Parallel Stories
- Use git worktrees manually for isolation: `git worktree add`
- Run separate Gemini sessions per worktree if parallel execution is needed
- Or execute stories sequentially in the main session
- Branch naming: `phase-8/{story-slug}`

### Phase 11 — Pre-Deploy Gate
- Adopt Phase 11 persona (read `agents/phase-11-predeploy-gate.md`)
- Run all 8 automated checks sequentially, record results
- Produce `predeploy-gate.md`
- **GATE STOP:** Present report, wait for explicit "Approved to deploy" user sign-off
- Do NOT advance until user approves

### [9, 10] — Refinement + Operations
- Adopt Phase 10 persona first → produce `site-reliability.md` (no code changes)
- Then adopt Phase 9 persona → refine code in main session

## Context Management

- Clear context between context groups by starting a new session or clearing the conversation
- Tell user: "Please clear context, then continue to start Phase X."
- Do NOT clear context during Phase 8 parallel execution

## Asana Integration

Use bash scripts for all Asana operations:

```bash
cai asana-api.sh get "<task_gid>"              # Read task details (name, notes, assignee, status)
cai asana-api.sh update-name "<task_gid>" "<name>"    # Update task name
cai asana-api.sh update-notes "<task_gid>" "$(cat /tmp/asana-notes.txt)"  # Update notes (write to temp file first)
cai asana-api.sh comment "<task_gid>" "$(cat /tmp/asana-comment.txt)"    # Add comment (write to temp file first)
cai asana-api.sh move "<task_gid>" "<section_gid>"
cai asana-api.sh complete "<task_gid>"
cai asana-api.sh find-project "sdlc-<project-name>"
cai asana-api.sh sections "<project_gid>"
```

**Long text args:** Always write multi-line or special-char text to a temp file first (`cat > /tmp/asana-notes.txt << 'NOTES' ... NOTES`), then pass via `"$(cat /tmp/asana-notes.txt)"`. This avoids shell quoting issues.

**Phase progress update (every phase transition):**
After advancing a phase, update the task notes with the SDLC Progress block (see SKILL.md § Phase Progress Format). Use `get` to read current notes, rebuild the progress block, then `update-notes` to write back.

## Multi-Worker Story Dispatch

When `multi_worker: true` in `config.yaml`:

### Story-Scoped Phase Advancement
- Each `next STORY-ID` reads that story's row from `.project` Story Status table
- Adopt the persona for that story's current phase
- All phase work happens in the story's worktree branch
- Phase completion updates both the Story Status table and Asana

### --claim Mode
- Search Asana for Ready tasks with no assignee using `cai asana-api.sh`. **Exclude tasks in "Do Not Do" section.**
- **DO NOT AUTO-CLAIM.** List the available stories for the user and tell them to run `/start-story STORY-ID`.

### Completion UX (CRITICAL — ALWAYS STOP)

You must **STOP** and wait for explicit user confirmation after completing **every** phase.
- **gate** (1, 8, 11): **STOP.** Show deliverables. Wait for explicit user approval.
- **confirm** (all other phases): **STOP.** Ask "Proceed to Phase X for STORY-016?" Wait for yes/no.
- **auto**: **DISABLED.** Do NOT proceed to the next phase without confirmation.

**Story completion — HARD STOP (CRITICAL):**
When a story reaches Done (all phases complete, Asana updated, backlog updated):
1. Output the completion summary
2. **STOP. END YOUR RESPONSE IMMEDIATELY.**
3. Do NOT claim the next story. Do NOT run `/next`. Do NOT start new work.
4. Wait for the user to explicitly tell you what to do next.
5. This applies even with auto-accept enabled — auto-accept controls phase transitions, NEVER story transitions.
6. The user must manually run `/next` or `/start-story` for new work.
