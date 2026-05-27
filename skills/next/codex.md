# /next — Codex Execution

Platform-specific execution details for the `next` skill in Codex sessions.

## Model Tier Mapping

| Tier | Codex Model |
|------|-------------|
| tier-1 (reasoning) | gpt-5 |
| tier-2 (execution) | gpt-5-mini |

## Sub-agent Dispatch

Codex may not provide Claude-style Task subagents. If parallel dispatch is unavailable:

1. Execute orchestrated personas sequentially in the same session.
2. Preserve model-tier enforcement from `AGENTS.md` and `config.yaml`.
3. Keep outputs phase-scoped and update tracking docs atomically.

## Parallel Group Execution

### [6b, 6c, 6d] — Security + UX + Ops Review
- Run Phase 6b persona to produce `security-review.md`
- Run Phase 6c persona to produce `ux-review.md`
- Run Phase 6d persona to produce `ops-review.md`
- Run sequentially unless explicit parallel workers are available

### Phase 8 — Parallel Stories
- Prefer git worktrees for isolation: `git worktree add`
- Use one Codex session per worktree when parallelizing
- Branch naming: `phase-8/{story-slug}`

### Phase 11 — Pre-Deploy Gate
- Run Phase 11 persona (read `agents/phase-11-predeploy-gate.md`)
- Run all 8 automated checks, produce `predeploy-gate.md`
- **GATE STOP:** Present report, wait for explicit "Approved to deploy" user sign-off
- Do NOT proceed until user approves

### [9, 10] — Refinement + Operations
- Run Phase 10 persona for `site-reliability.md`
- Run Phase 9 persona for code refinement

## Context Management

- Clear or compact context between context groups.
- After reset, re-read `AGENTS.md`, `.project`, and current phase persona.
- Do not reset context during active Phase 8 merge orchestration.

## Asana Integration

Use bash scripts directly. For Codex approval matching, always call Asana helpers in direct form (`cai asana-api.sh ...`) and do not shell-wrap with `/bin/zsh -lc`.
- Do not use pipes, redirects, command substitution (`$(...)`), or chained operators in the same Asana command.

```bash
cai asana-api.sh get "<task_gid>"
cai asana-api.sh update-notes "<task_gid>" "<notes>"
cai asana-api.sh comment "<task_gid>" "<text>"
cai asana-api.sh move "<task_gid>" "<section_gid>"
cai asana-api.sh complete "<task_gid>"
```
