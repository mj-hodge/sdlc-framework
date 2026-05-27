---
name: phase-10
description: Run Phase 10 (Operations) to define monitoring, dashboards, alerting, runbooks, and deployment safety.
---

# Phase 10: Operational Resilience

Run the Operational Resilience phase to define monitoring, dashboards, alerting, runbooks, and deployment safety for the project.

## Identity
- **Role:** Site Reliability Engineer
- **Goal:** Monitoring, dashboards, alerting, and operational resilience
- **Persona:** `.sdlc/agents/phase-10-operations.md`

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

## Usage

```
/phase-10
```

## Prerequisites

- Phase 8b (Code Review) complete
- Application deployed and running
- `.project` shows Phase 10 as current phase (or `[9, 10]` parallel group active)

> **Note:** Phase 10 runs in parallel with Phase 9. Phase 10 produces `site-reliability.md` only (no code changes). Phase 9 handles code refinement in the main session.

## Steps

1. **Read agent persona** — `~/projects/coding-ai-config/agents/phase-10-operations.md`
2. **Adopt the SRE persona** — Follow all guidance in the agent file
3. **Reliability discovery (FIRST — do not skip):**
   - Ask the user the discovery questions (uptime, resiliency, fallback, economics)
   - Classify into a reliability tier: Essential / Standard / Premium / Critical
   - Document tier, rationale, RTO, RPO, and budget in `site-reliability.md`
4. **Inventory the system** — Services, dependencies, critical user journeys
5. **Define SLIs/SLOs** — Scoped to the chosen tier, with error budgets
6. **Health check endpoints** — `/health`, `/health/ready`, `/health/live`, `/health/detailed` (scoped to tier)
7. **Metrics instrumentation** — Prometheus format: request, error, business, dependency, resource (scoped to tier)
8. **Dashboard specifications** — Executive, service overview, dependency, infrastructure (scoped to tier)
9. **Alerting strategy** — Severity levels, routing, burn rate alerts, every alert links to a runbook
10. **Structured logging** — JSON format, correlation IDs, retention policy
11. **Incident response runbooks** — One per alert type, specific commands, escalation paths
12. **External monitoring** — Uptime checks, synthetic user journeys, status page (scoped to tier)
13. **Deployment safety** — Rollback, canary, post-deploy smoke tests (scoped to tier)
14. **Validate end-to-end** — Test an alert, simulate a failure, check dashboards
15. **Update .project, backlog.md, development-tasks.md, Asana** — All four, no exceptions

## Outputs

- `site-reliability.md` — Single source of truth for all operational resilience
- `.project` — Updated with Phase 10 complete

## Gate

Phase 10 is NOT complete until:
- [ ] Reliability tier classified and documented
- [ ] Every SLI has an SLO with error budget
- [ ] Health check endpoints specified
- [ ] Metrics instrumentation defined
- [ ] Dashboards specified with panel definitions
- [ ] Every alert has a linked runbook
- [ ] Logging strategy documented
- [ ] External monitoring configured
- [ ] Deployment safety procedures documented
- [ ] All tracking docs updated (.project, backlog.md, development-tasks.md, Asana)
