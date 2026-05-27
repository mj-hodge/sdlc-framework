# Seed

## Overview
| Field | Value |
|-------|-------|
| Mode | feature_update |
| Scope | large |
| Criticality | critical |
| Feature Name | Critical-Feature SDLC Pattern |

## Problem Statement

Mark experienced 4 critical-feature failures in advertising-amazon in 72 hours: silent duplicate blobs, missed cron windows, blank email columns, and healthz mis-reporting after revision rolls. These are not ordinary bugs — they are failures in features where incorrectness or downtime has **material business impact** (e.g., missed advertising spend windows, incorrect financial data). The current SDLC framework treats all features equally, with no mechanism to identify, protect, or monitor features where failure is unacceptable. Mark's directive: "there are plenty of features where we simply want to heal and cover, but some that if we miss the window or it is not correct have a material impact and need to be avoided... this might need to be applied at the SDLC level for all systems."

## Target User / Use Case

**Primary users:**
- **Engineering teams** (AI agents and human developers) using the SDLC framework — they need clear guidance on when and how to apply heightened protection to critical features
- **Mark (CTO / repository owner)** — needs a single discoverable index of what is protected across every project, with confidence that each critical feature has contracts, monitoring, and runbooks
- **On-call operators** — need structured `/api/status` endpoints, dashboards, and runbooks so they can detect and respond to critical-feature violations within minutes

**Use case:** When any Gorilla Commerce project identifies a feature as "critical" during Phase 1, the SDLC framework automatically enforces additional gates: output contracts, hardened contract tests, runtime violation events, deploy-blocking CI, status endpoints, Grafana dashboards, and a discoverable index document. This is a generic pattern — not specific to advertising-amazon.

## Success Criteria

- [ ] **SC-1:** Phase 1 seed template includes a `criticality: routine|important|critical` field; the BA persona MUST set it for every story
- [ ] **SC-2:** A new `output-contracts.md` template exists for any `criticality: critical` story (regardless of scope); each contract is a one-line business assertion with expected behavior under degraded inputs
- [ ] **SC-3:** New Phase 10c (Output Contract Hardening) fires automatically for any `criticality: critical` story regardless of scope (Trivial through Large); it maps business assertions to atomic contract tests, runtime metrics, alerts, and runbooks
- [ ] **SC-4:** Phase 7 (Test Design) requires critical features to produce `tests/critical_features/<feature-slug>/contracts/` with one file per contract clause; tests mock at outermost boundaries (DB session factory, httpx client); lint check forbids `@pytest.mark.skip` / `xfail` in this directory
- [ ] **SC-5:** Phase 10 (Operations) requires business-level output contracts (not just system metrics); each contract emits a structured `<feature>_<contract>_violation` event when breached at runtime
- [ ] **SC-6:** Phase 11 (Pre-Deploy Gate) includes a named CI step `Critical Feature Contracts` that blocks deploy on any contract test failure
- [ ] **SC-7:** A generic `/api/status` JSON endpoint pattern is documented: health/last_success_at/violation_count_24h/runbook_url per critical feature; plus an `/status` HTML page (table view, no auth, auto-refresh)
- [ ] **SC-8:** A generic Grafana dashboard template is documented: one row per critical feature with health-color SLO, linked to runbook
- [ ] **SC-9:** Every project MUST maintain `docs/critical-features.md` as the SINGLE INDEX of protected features; top-level README MUST point at it; any contributor can grep this one file
- [ ] **SC-10:** `.sdlc/patterns/critical-features.md` is the canonical pattern documentation; `AGENTS.md` has a Critical Features section; phase personas (1, 7, 10, 11) are updated with the new requirements
- [ ] **SC-11:** Zero behavior change in advertising-amazon — this story is pattern definition only
- [ ] **SC-12:** Error handling: if a critical feature's contract test infrastructure is missing or misconfigured, Phase 11 pre-deploy gate MUST fail closed (block deploy) and log the specific missing artifact

## Constraints
| Constraint | Value |
|------------|-------|
| Budget | $0 — framework documentation and templates only |
| Timeline | days — Mark wants this before STORY-592 (advertising-amazon application) |
| Scale | All Gorilla Commerce projects inheriting the SDLC framework |

## Performance Requirements (Medium+ Scope)
| Metric | Target |
|--------|--------|
| `/api/status` response time (p95) | < 500ms (pattern guidance) |
| `/status` HTML page load | < 2s (pattern guidance) |
| Contract test suite execution | < 30s per feature (pattern guidance) |
| Violation event emission latency | < 5s from detection (pattern guidance) |

_These are recommended targets documented in the pattern, not enforced by this story._

## Security Constraints (Non-Negotiable)

- [x] All database queries MUST use parameterized queries (no string concatenation) — N/A, no DB in this story
- [x] All user input MUST be validated and sanitized before use — N/A, no user input in this story
- [ ] `/api/status` and `/status` endpoints MUST NOT require authentication (pattern specifies public read-only)
- [ ] `/api/status` MUST NOT expose internal implementation details, secrets, or PII — only feature health metadata
- [ ] Status endpoints MUST NOT expose runbook content inline — link to runbook URL only

## Operational Lifecycle

- **What configuration might change after deployment?** SLO thresholds per critical feature, violation event destinations (log vs. metric vs. alert), runbook URLs, dashboard refresh intervals
- **How will operators make those changes?** Environment variables or config files per project (documented in the pattern)
- **What monitoring confirms the feature is working?** Each critical feature's own contract violation metrics; the `/api/status` endpoint itself serves as a health summary; Grafana dashboard provides visual confirmation

## Codebase Context (Feature Updates Only)
| Aspect | Details |
|--------|---------|
| Affected files | `templates/seed.md`, `agents/phase-1-seed.md`, `agents/phase-7-test-design.md`, `agents/phase-10-operations.md`, `agents/phase-11-predeploy-gate.md`, `AGENTS.md`, `software-development-guidance.md` |
| Related components | Phase skill definitions (`skills/`), templates (`templates/`), agent personas (`agents/`) |
| Current behavior | All features treated equally — no criticality classification, no output contracts, no contract-specific test directories, no status endpoint pattern, no critical-features index |
| Desired change | Introduce criticality tiering at Phase 1, enforce output contracts and hardened tests for critical features, add Phase 10c, update Phases 7/10/11, document generic status/dashboard/index patterns |
| Test coverage | N/A — this story produces documentation and templates, not executable code |
| Architecture constraints | Must be generic (not advertising-amazon-specific); must work for any project inheriting the SDLC framework; must not break existing non-critical feature workflows |

## Out of Scope (Explicit)

- **advertising-amazon code changes** — ships in STORY-592
- **Implementing actual status endpoints** — this story defines the pattern; projects apply it
- **Creating actual Grafana dashboards** — this story provides a template; projects instantiate it
- **Retroactively classifying existing features** — future stories per project
- **Automated criticality detection** — the BA (human or AI) makes the classification judgment

## Key Assumptions

1. The SDLC framework is consumed as a git submodule by all Gorilla Commerce projects
2. Projects using the framework have Python/FastAPI backends (status endpoint pattern targets this stack)
3. Grafana is the standard dashboarding tool across projects
4. Prometheus-compatible metrics are the standard observability layer
5. Each project has its own CI pipeline that can include a `Critical Feature Contracts` step

## Error Handling Requirements

- **Missing contract tests at Phase 11:** Pre-deploy gate MUST fail closed — deploy is blocked. Log message: `CRITICAL: Missing contract tests for critical feature <slug>. Expected directory: tests/critical_features/<slug>/contracts/`
- **Contract test failure at deploy:** CI step `Critical Feature Contracts` blocks the deploy pipeline. No partial deploys allowed.
- **Runtime contract violation:** Emit structured event `<feature>_<contract>_violation` with severity, timestamp, feature slug, contract name, actual vs. expected values. Event destination is configurable (log, Prometheus metric, alert webhook).
- **Status endpoint failure:** If the status endpoint itself fails, it should return HTTP 503 with `{"status": "degraded", "error": "status_check_failed"}` — never silently return healthy.

## Design Points (from dispatch)

1. Add `criticality: routine|important|critical` field to seed template
2. New artifact: `output-contracts.md` — one-line business assertions with degraded-input behavior
3. New Phase 10c: Output Contract Hardening — fires for ALL scopes when criticality is critical
4. Phase 7 update: `tests/critical_features/<feature-slug>/contracts/` directory, outermost-boundary mocks, no skip/xfail lint
5. Phase 10 update: business-level output contracts, `<feature>_<contract>_violation` structured events
6. Phase 11 update: `Critical Feature Contracts` named CI step, deploy-blocking
7. Generic `/api/status` JSON + `/status` HTML pattern
8. Generic Grafana dashboard template (one row per critical feature, SLO health-color, runbook link)
9. `docs/critical-features.md` as single discoverable index per project; README points at it
10. `.sdlc/patterns/critical-features.md` canonical pattern doc; AGENTS.md Critical Features section; persona updates

## Deliverables (Framework Files)

| File | Action |
|------|--------|
| `templates/seed.md` | Add criticality field |
| `templates/output-contracts.md` | NEW — output contract template |
| `templates/critical-features-index.md` | NEW — template for `docs/critical-features.md` |
| `agents/phase-1-seed.md` | Add criticality classification requirements |
| `agents/phase-7-test-design.md` | Add critical-feature contract test requirements |
| `agents/phase-10-operations.md` | Add business-level output contract requirements |
| `agents/phase-11-predeploy-gate.md` | Add Critical Feature Contracts CI step |
| `AGENTS.md` | Add Critical Features section |
| `software-development-guidance.md` | Document Phase 10c, update phase paths |
| `patterns/critical-features.md` | NEW — canonical pattern documentation |

## Phase Path

Large scope: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> [6b, 6c, 6d] -> 7 -> 8 -> 8b -> 11 -> [9, 10] -> Done

## Next Phase

**Phase 2 (Research)** — Investigate existing critical-feature / contract-testing patterns in the industry (Design by Contract, Consumer-Driven Contract Testing, SRE error budgets, feature health scoring).
