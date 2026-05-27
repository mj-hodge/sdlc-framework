# GEMINI.md

> **DIRECTIVE:** This file contains critical guidance that MUST be followed for all work.
> After context compaction, re-read this file and `.project` to restore phase context.
> Read and follow [AGENTS.md](./AGENTS.md) for complete development guidance.

---


## SDLC Process (REQUIRED)

See [AGENTS.md](./AGENTS.md) for: phase paths, advance categories, data mutation policy, skills, tech stack, writing rules, and git conventions.

**"spec" trigger:** Any prompt starting with "spec" MUST immediately initiate Phase 1 by activating the `phase-1` skill. Treat "spec" as a Directive to enter Phase 1.

**Story switching (CRITICAL — NEVER auto-switch stories, even with auto-accept):**
`auto` advance means auto-advance to the next **phase within the same story**. It NEVER means switch to a different story/ticket. When a story is complete:
1. Output the completion summary
2. **STOP. END YOUR RESPONSE. Do NOT claim, start, or begin the next story.**
3. Wait for the user to explicitly tell you which story to work on next
4. This rule applies even if auto-accept is enabled — auto-accept controls phase transitions, NEVER story transitions

**Full phase details:** See [software-development-guidance.md](.sdlc/software-development-guidance.md)

---

## Deliverable Location (REQUIRED)

**All phase deliverables MUST be written to:** `features/<story-folder>/`

**Folder naming:** `features/story-XXX-kebab-case-slug/` where XXX is the story number and slug is derived from the Asana task name.

Example: `features/story-014-str-automations/seed.md`

**NEVER write deliverables to the project root or a `docs/` directory.** The `features/` directory is the single source of truth for all SDLC artifacts.

**Multi-worker mode:** When using worktrees, deliverables still go in `features/<story-folder>/` within the worktree.

---

## Phase Deliverables (REQUIRED — every phase MUST produce its file)

All files below are written to `features/<story-folder>/`:

| Phase | Output File(s) | Scope |
|-------|---------------|-------|
| 1 | `seed.md` | All |
| 2 | `research.md` | Large/New |
| 3 | `expansion.md` | Large/New |
| 4 | `analysis.md` | Medium+ |
| 5 | `selection.md` | Large/New |
| 6 | `feature-spec.md` (Medium) OR `specification.md`, `architecture.md`, `api-design.md`, `database-schema.md`, `implementation-plan.md` (Large/New) | Medium+ |
| 6b | `security-review.md` | Medium+ |
| 6c | `ux-review.md` | Medium+ |
| 7 | `test-design.md` + runnable test code in `tests/`/`e2e/` (RED state) | All |
| 8 | Implementation code (all tests GREEN) | All |
| 8b | `code-review.md` | Medium+ |
| 11 | `predeploy-gate.md` | Medium+ |
| 9 | `refinement-report.md` | Large/New |
| 10 | `site-reliability.md` | Large/New |

**Every phase MUST also update:** `.project`, `backlog.md`, `development-tasks.md`, Asana task (add comment summarizing work)

**A phase is NOT complete until its output file exists in `features/<story-folder>/` and tracking docs are updated.**

---

## Context Management (CRITICAL)

- Clear context between context groups, not every phase (default: grouped strategy)
- Use separate searches for research (Phases 2-3) — don't pollute main context
- After 2 failed corrections, start a new session with a better prompt
- Commit after each logical unit in Phase 8
- Never implement more than one function/endpoint per prompt

**Context groups:** Seed | Research (2,3) | Evaluation (4,5) | Design (6,[6b,6c,6d]) | Test (7) | Implementation (8,8b) | Deploy (11) | Polish ([9,10])

**After clearing context — "continue" or "next step":**
1. Read `.project` → Phase Routing section to find current phase and status
2. Read the agent persona for that phase
3. Begin or resume the phase — no re-explanation needed

---

## Model Policy (Gemini-specific)

| Phase | Model | Effort |
|-------|-------|--------|
| 1 (Seed) | Pro (always) | high |
| 2-5 | Flash (default), Pro for large/complex | medium |
| 6 (Design) | Pro (default), Flash ok for small | high |
| 7 (Test Design) | Flash (default) | medium |
| 8 (Implementation) | Flash (default) | medium |
| 8b (Code Review) | Flash (default) | medium |
| 11 (Pre-Deploy Gate) | Flash (default) | medium |
| 9 (Refinement) | Pro (always) | high |
| 10 (Operations) | Pro (always) | high |

**Model Enforcement (HARD GATE — no exceptions):**
- Before starting ANY phase, check: does your current model match the phase's required model?
- **Pro doing Flash work (e.g., Phase 8):** Delegate ALL work to Flash. Pro orchestrates only.
- **Flash doing Pro work (e.g., Phase 1, 9, 10):** Delegate ALL work to a Pro sub-agent. Never ask the user to switch models.

---

---

## Reference

- [AGENTS.md](./AGENTS.md) — Canonical SDLC policy (phase paths, skills, tech stack, Asana, git)
- [software-development-guidance.md](.sdlc/software-development-guidance.md) — Phase details, gates, hooks, lessons learned
- [templates/](.sdlc/templates/) — File and config templates
