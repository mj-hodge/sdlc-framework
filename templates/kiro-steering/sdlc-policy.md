---
inclusion: always
---

# SDLC Policy (Kiro)

This project uses the SDLC framework. The authoritative policy document is
[AGENTS.md](../../AGENTS.md) in the workspace root — read it for phase paths,
advance categories, deliverable locations, model policy, data mutation rules,
and git conventions.

Kiro reads `AGENTS.md` as a workspace-level rule automatically. This file
exists so Kiro also surfaces the SDLC workflow via its native steering system.

## Quick reference

- **Starting new work:** Any prompt beginning with "spec" initiates Phase 1 (Seed).
- **Advancing phases:** Say "next" or "next STORY-ID" — the agent checks `.project` and advances.
- **Skills location:** `.kiro/skills/` (symlinked from `~/.sdlc/skills/`). Every phase and workflow is a skill.
- **Deliverables:** All phase outputs go in `features/story-XXX-slug/`, never the project root.

## Phase paths

| Scope | Path |
|-------|------|
| Trivial | → 8 → Done |
| Small | 1 → 7 → 8 → Done |
| Medium | 1 → 4 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → Done |
| Large/New | 1 → 2 → 3 → 4 → 5 → 6 → [6b, 6c, 6d] → 7 → 8 → 8b → 11 → [9, 10] → Done |

## Hard stops

- Never auto-advance a gate phase (1, 8, 11) without explicit user approval.
- Never auto-switch to a new story when the current one completes — wait for user direction.
- Never write directly to the database — use application APIs.
- Never make real HTTP calls to external production APIs from tests or dev runs.

## References

- `AGENTS.md` — canonical SDLC policy (always-included workspace rule)
- `.kiro/skills/` — all phase and workflow skills
- `agents/phase-*.md` — agent personas per phase
- `software-development-guidance.md` — full phase details and lessons learned
