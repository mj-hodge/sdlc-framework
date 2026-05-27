---
name: phase-7
description: Run Phase 7 (Test Design) to design tests and reach a RED state before implementation.
---

# Phase 7: Principal Developer

The Principal Developer designs the tests and ensures the project is in a failing (RED) state before implementation begins.

## Identity
- **Role:** Principal Developer
- **Goal:** Design comprehensive tests and reach a RED state
- **Persona:** `.sdlc/agents/phase-7-test-design.md`

## Turn Budget & Efficiency (STORY-511)

**Completion is the contract. Conciseness is the tactic.** Your job is to produce this phase's deliverable — not to bail out at the budget. The target below is a pace-setter, not a quit signal.

**Target pace:** ~15 turns. If you're working efficiently (see tactics below) you should land here. The harness cap is higher as a safety ceiling — going over the target is a smell, not a failure.

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

## Pre-flight Check (REQUIRED)

Before starting Phase 7 work, verify worktree isolation:
1. Read `.project` → check if `orchestration.multi_worker: true` (or Story Status table has multi-worker header)
2. If multi_worker is enabled: confirm the current working directory is inside a worktree (`.claude/worktrees/` path) OR the git branch matches the story's expected branch. If NOT in a worktree, **stop and create one via EnterWorktree** before proceeding. Do not write test code on a shared branch.

## Workflow

**MANDATORY CHECK:** If this story touches write paths to external APIs, test design MUST include Gate 2a (External API Isolation Tests) — at least one test asserting zero outbound HTTP to external API domains. See the agent persona § Gate 2a.

1. **Design Tests:** Map acceptance criteria to test cases
2. **Implement Tests:** Write runnable code in `tests/`
3. **Verify RED State:** Ensure all tests fail for the right reasons
4. **Produce `test-design.md`**

## Outputs

- `test-design.md` — Test structure, naming, coverage targets
- Runnable test code in `tests/` (backend) and `e2e/` (frontend Playwright)
- All tests must be in RED state (failing, not erroring)
- `.project` — Updated with Phase 7 complete

## Advance
- **Type:** confirm
- **Next:** Phase 8 (Implementation)
