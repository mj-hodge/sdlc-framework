---
name: phase-8b
description: Run Phase 8b (Code Review) to review implemented code via parallel specialized sub-agents.
---

# Phase 8b: Code Review Orchestrator

The Code Review Orchestrator manages the parallel review of implemented code by specialized sub-agents.

## Identity
- **Role:** Code Review Orchestrator
- **Goal:** Ensure quality, security, and spec compliance
- **Persona:** `.sdlc/agents/phase-8b-code-review.md`

## Turn Budget & Efficiency (STORY-511)

**Completion is the contract. Conciseness is the tactic.** Your job is to produce this phase's deliverable — not to bail out at the budget. The target below is a pace-setter, not a quit signal.

**Target pace:** ~12 turns. If you're working efficiently (see tactics below) you should land here. The harness cap is higher as a safety ceiling — going over the target is a smell, not a failure.

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

## Workflow

**MANDATORY CHECK:** For write-path stories, verify no code path allows test traffic to reach external production APIs. Confirm tool-layer adapters are mocked in test mode and REST endpoints detect tool-layer failures.

1. **Dispatch Sub-agents:**
   - `architect` (tier-1, high)
   - `skeptic` (tier-2, medium)
   - `simplifier` (tier-2, low)
   - `rule-reviewer` (tier-2, low)
   - `qa-preflight` (tier-2, low)
2. **Synthesize Findings:** Deduplicate, triage, and record dispositions
3. **Auto-fix Loop:** Address localized Critical/High findings
4. **Produce `code-review-8b.md`**

## Outputs

- `code-review.md` — Findings by severity, dispositions, verdict (APPROVED/CHANGES REQUIRED)
- `.project` — Updated with Phase 8b complete

## Advance
- **Type:** auto
- **Next:** [Phase 9 (Refinement), Phase 10 (Operations)] or Done
