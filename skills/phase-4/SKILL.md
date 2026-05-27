---
name: phase-4
description: Run Phase 4 (Analysis) to evaluate approaches based on technical soundness, business value, and risk profiles.
---

# Phase 4: Analysis Coordinator

The Analysis Coordinator evaluates the generated approaches based on technical soundness, business value, and risk profiles.

## Identity
- **Role:** Analysis Coordinator
- **Goal:** Evaluate and score each approach across 3 dimensions
- **Persona:** `.sdlc/agents/phase-4-analysis.md`

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
1. **Define Analysis Dimensions:** Technical (soundness), Business (value/effort), Risk (profile/register)
2. **Dispatch Sub-agents:**
   - `technical` (tier-2, medium)
   - `business` (tier-2, medium)
   - `risk` (tier-2, medium)
3. **Reconcile Scores:** Apply weights, calculate confidence, rank top 3
4. **Produce `analysis.md`**

## Outputs

- `analysis.md` — Scoring matrix, top 3 ranking, risk register, recommendation
- `.project` — Updated with Phase 4 complete

## Advance
- **Type:** confirm
- **Next:** Phase 5 (Selection)
