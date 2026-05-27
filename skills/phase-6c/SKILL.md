---
name: phase-6c
description: Run Phase 6c (UX Review) to review the design for user experience, friction, and consistency.
---

# Phase 6c: UX Review

Review the design for user experience — minimum friction, maximum information, consistent themes.

## Identity
- **Role:** UX Strategist
- **Goal:** Friction, information, and consistency review
- **Persona:** `.sdlc/agents/phase-6c-ux-review.md`

## Turn Budget & Efficiency (STORY-511)

**Completion is the contract. Conciseness is the tactic.** Your job is to produce this phase's deliverable — not to bail out at the budget. The target below is a pace-setter, not a quit signal.

**Target pace:** ~10 turns. If you're working efficiently (see tactics below) you should land here. The harness cap is higher as a safety ceiling — going over the target is a smell, not a failure.

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

## Usage

```
/phase-6c
```

## Prerequisites

- Phase 6 (Design) complete
- Design documents exist: `feature-spec.md`, `architecture.md`, `api-design.md`
- `.project` shows Phase 6c as current phase (or `[6b, 6c, 6d]` parallel group active)

> **Note:** Phase 6c runs in parallel with Phase 6b. Both read Phase 6 design docs independently. Neither depends on the other's output.

## Steps

1. **Read agent persona** — `~/projects/coding-ai-config/agents/phase-6c-ux-review.md`
2. **Adopt the UX Strategist persona** — Follow all guidance in the agent file
3. **Understand the user** — Who they are, top tasks, usage frequency, context
4. **Map core user flows** — Every step, every click, friction score per flow
5. **Audit information architecture** — Is the most important info most visible?
6. **Audit consistency** — Terminology, button styles, layout patterns, colors, spacing
7. **Identify friction points** — Unnecessary steps, missing defaults, hidden info
8. **Recommend improvements** — Prioritized by user impact (Critical/High/Medium/Low)
9. **Create `ux-review.md`** — User profile, flow analysis, consistency findings, recommendations
10. **Update .project, backlog.md, development-tasks.md, Asana** — All four, no exceptions

## Outputs

- `ux-review.md` — Flow friction scores, consistency findings, recommendations, verdict
- `.project` — Updated with Phase 6c complete

## Gate

Phase 6c is NOT complete until:
- [ ] Core user flows mapped with friction scores
- [ ] No core flow scores above 3 on friction scale
- [ ] Consistency audit completed (terminology, actions, layout, colors)
- [ ] Design system tokens verified or gaps documented
- [ ] All critical/high UX issues addressed before Phase 7
- [ ] `ux-review.md` documents findings and verdict
- [ ] All tracking docs updated (.project, backlog.md, development-tasks.md, Asana)
