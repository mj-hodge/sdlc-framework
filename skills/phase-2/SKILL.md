---
name: phase-2
description: Run Phase 2 (Research) to explore existing solutions, libraries, and market patterns via parallel sub-agents.
---

# Phase 2: Research Coordinator

The Research Coordinator orchestrates the initial exploration of the problem space, looking for existing solutions, libraries, and market patterns.

## Identity
- **Role:** Research Coordinator
- **Goal:** Survey solutions and validate technical feasibility
- **Persona:** `.sdlc/agents/phase-2-research.md`

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

## Workflow
1. **Identify Research Domains:** Market (SaaS/vendors), Library (OSS/packages), Field (community sentiment)
2. **Dispatch Sub-agents:**
   - `market-scout` (tier-2, low)
   - `library-miner` (tier-2, low)
   - `field-reporter` (tier-2, low)
3. **Synthesize Findings:** Corroborate cross-source findings, run dependency health checks
4. **Produce `research.md`**

## Outputs

- `research.md` — Options evaluated, dependency health, buy vs build, top contenders
- `.project` — Updated with Phase 2 complete

## Advance
- **Type:** confirm
- **Next:** Phase 3 (Expansion)
