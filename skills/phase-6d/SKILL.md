---
name: phase-6d
description: Run Phase 6d (Ops Review) to review the design for operational readiness — health checks, metrics, logging, alerting, deployment safety.
---

# Phase 6d: Ops Review

Review the design for operational readiness — ensure the system can be deployed, monitored, diagnosed, and recovered.

## Identity
- **Role:** Ops Reviewer
- **Goal:** Identify operational readiness gaps before implementation
- **Persona:** `.sdlc/agents/phase-6d-ops-review.md`

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
/phase-6d
```

## Prerequisites

- Phase 6 (Design) complete
- Design documents exist: `feature-spec.md` or `architecture.md`, `api-design.md`
- `.project` shows Phase 6d as current phase (or `[6b, 6c, 6d]` parallel group active)

> **Note:** Phase 6d runs in parallel with Phase 6b and 6c. All three read Phase 6 design docs independently. None depend on each other's output.

## Steps

1. **Read agent persona** — `agents/phase-6d-ops-review.md`
2. **Adopt the Ops Reviewer persona** — Follow all guidance in the agent file
3. **Establish operational context** — Reliability tier, critical journeys, dependencies, deployment model
4. **Review health & readiness** — Health endpoints, dependency checks, response format
5. **Review metrics & observability** — Golden signals, business metrics, Prometheus endpoint
6. **Review structured logging** — JSON format, correlation IDs, required fields
7. **Review alerting & SLOs** — SLI/SLO definitions, alert conditions, runbook links
8. **Review deployment safety** — Rollback strategy, smoke tests, migration safety
9. **Produce ops acceptance criteria** — Each high+ finding becomes a story AC
10. **Create `ops-review.md`** — Context, findings, acceptance criteria, required ops tests, verdict
11. **Update .project, backlog.md, development-tasks.md, Asana** — All four, no exceptions

## Outputs

- `ops-review.md` — Operational context, findings by severity, ops acceptance criteria, required ops tests, Phase 10 verification items, verdict
- `.project` — Updated with Phase 6d complete

## Gate

Phase 6d is NOT complete until:
- [ ] Operational context established (reliability tier, dependencies, deployment model)
- [ ] Health check design reviewed (at minimum `/health` and `/health/ready`)
- [ ] Metrics requirements reviewed (four golden signals at minimum)
- [ ] Structured logging format reviewed
- [ ] Deployment safety reviewed (rollback, smoke tests)
- [ ] All critical/high ops findings addressed or added as story acceptance criteria
- [ ] Required Ops Tests section populated for Phase 7
- [ ] `ops-review.md` documents findings and verdict
- [ ] All tracking docs updated (.project, backlog.md, development-tasks.md, Asana)

## Advance
- **Type:** auto
- **Next:** Phase 7 (Test Design)
