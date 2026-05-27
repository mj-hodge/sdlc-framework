---
name: phase-11
description: Run Phase 11 (Pre-Deploy Gate) to verify the build is safe to deploy — CVE scan, dependency audit, secrets, infra drift, monitoring health, adapter connections.
---

# Phase 11: Pre-Deploy Gate

Run the Pre-Deploy Gate phase to verify the build is safe to deploy before releasing to production.

## Identity
- **Role:** Release Engineer
- **Goal:** Automated verification that the build is safe to deploy
- **Persona:** `.sdlc/agents/phase-11-predeploy-gate.md`

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
/phase-11
```

## Prerequisites

- Phase 8b (Code Review) complete — `code-review.md` exists, all critical/high findings resolved
- Container image built and tagged for the release
- `.project` shows Phase 11 as current phase
- Required tools installed: `trivy` or `grype`, `gitleaks` or `trufflehog`, `terraform` or `bicep` CLI
- Required environment variables set: `DATABASE_URL`, `BASE_URL`, `IMAGE_TAG` (and `REDIS_URL` if applicable)

> **Note:** Phase 11 is a gate phase — it requires explicit user approval before deployment proceeds. "PASS" on all checks is not enough; the user must confirm "Approved to deploy" after reviewing the gate report.

## Steps

**MANDATORY CHECK:** Verify TESTING flag is NOT set in production. Verify test/local environments cannot reach production APIs. Verify write endpoints detect tool-layer failures (not return success on empty results). See agent persona § Check 11.

1. **Read agent persona** — `agents/phase-11-predeploy-gate.md`
2. **Adopt the Release Engineer persona** — Follow all guidance in the agent file
3. **Verify prerequisites:**
   - Confirm Phase 8b is complete (code-review.md exists, no unresolved critical/high findings)
   - Confirm container image is built and tagged
   - Check required tools are installed and env vars are set
4. **Run Check 1: Container Image CVE Scan**
   - `trivy image --exit-code 1 --severity CRITICAL,HIGH <image>:<tag>` or equivalent
   - Record result with tool output summary
5. **Run Check 2: Dependency Audit**
   - `pip-audit` (Python) and/or `npm audit --audit-level=high` (Node.js)
   - Record result with vulnerability count by severity
6. **Run Check 3: Secrets Scan**
   - `gitleaks detect --source . --exit-code 1` or `trufflehog filesystem .`
   - Record result (NEVER log actual secret values — only file paths and finding types)
7. **Run Check 4: Infrastructure Drift Detection**
   - `terraform plan -detailed-exitcode` or `az deployment group what-if`
   - Record result with change summary
8. **Run Check 5: Monitoring Health**
   - Verify `/health`, `/health/ready`, `/metrics` endpoints respond
   - Verify alert rules configuration exists
   - Record result with endpoint response codes and times
9. **Run Check 6: Adapter/Integration Connections**
   - Verify database, cache, and all external API connections are reachable
   - Record result per adapter with connectivity status
10. **Run Check 7: Migration Chain Verification**
    - `alembic heads` — must show exactly one head
    - Record result with head revision ID(s)
11. **Run Check 8: Smoke Test Dry-Run**
    - `pytest -m smoke --tb=short` (API)
    - `npx playwright test --grep @smoke` (frontend projects only)
    - Record result with test counts and any failures
12. **Produce `predeploy-gate.md`**
    - Summary table with all 8 check results
    - Per-check evidence sections with tool output
    - Remediation plan for any failures
    - Overall status: PASS / FAIL / BLOCKED
13. **GATE — present report and wait for explicit user approval**
    - If PASS: present report, ask for "Approved to deploy" confirmation
    - If FAIL/BLOCKED: present report with remediations, stop until fixed
14. **Update .project, backlog.md, development-tasks.md, task tracker** — All four, no exceptions

## Outputs

- `predeploy-gate.md` — Gate report with all 8 check results and sign-off
- `tests/predeploy/` — Automation scripts for all checks (created if not already present)
- `.project` — Updated with Phase 11 complete

## Gate

Phase 11 is NOT complete until:
- [ ] All 8 checks have been run (not assumed or skipped)
- [ ] All 8 checks PASS with recorded tool evidence
- [ ] `predeploy-gate.md` produced with full evidence for each check
- [ ] Overall status is PASS
- [ ] All tracking docs updated (.project, backlog.md, development-tasks.md, task tracker)
- [ ] **Explicit user approval received** — user has confirmed "Approved to deploy"

**This is a GATE phase.** Do NOT advance to deployment or Phase 9/10 without explicit user sign-off on `predeploy-gate.md`.
