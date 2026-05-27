# Analysis — STORY-591: Critical-Feature SDLC Pattern

## Overview

Three implementation approaches were evaluated by parallel technical, business, and risk sub-agents.

**Trigger:** 4 critical-feature failures in advertising-amazon in 72h (silent dup blobs, missed cron windows, blank email columns, healthz mis-reporting). All reflect the same root cause: the SDLC framework has no mechanism to distinguish features where failure has material business impact from features where failure is tolerable.

---

## Approaches Evaluated

| ID | Name | Description |
|----|------|-------------|
| A | Full Phase 10c (prescribed) | New phase + mandatory artifacts + deploy-blocking CI for all criticality=critical stories |
| B | Annotation-Only (lightweight) | Criticality field only; Phase 10 absorbs requirements; advisory enforcement; no deploy gate |
| C | Separate Audit Script | `scripts/critical-audit.sh` outside phase flow; YAML manifest; phases unchanged |

---

## Scoring Matrix

### Technical Dimension (sub-agent: technical)

| Dimension | A | B | C |
|-----------|---|---|---|
| Implementation feasibility | 7 | 9 | 5 |
| Enforcement strength | 9 | 5 | 6 |
| Backward compatibility | 7 | 9 | 8 |
| Discoverability | 9 | 6 | 5 |
| Agent cognitive load | 6 | 8 | 4 |
| Incrementality | 6 | 9 | 7 |
| **Total** | **44** | **46** | **35** |

### Business Dimension (sub-agent: business)

| Dimension | A | B | C |
|-----------|---|---|---|
| Business value delivered | 9 | 5 | 6 |
| Time-to-protection | 6 | 9 | 7 |
| Maintenance burden | 6 | 8 | 5 |
| Executive confidence | 9 | 5 | 6 |
| Team adoption friction | 6 | 8 | 7 |
| STORY-592 unblocking | 7 | 8 | 6 |
| **Total** | **43** | **43** | **37** |

### Risk Profile (sub-agent: risk)

| Category | A | B | C |
|----------|---|---|---|
| Adoption risks | Medium-High | Medium (no enforcement) | Medium-High |
| Pattern correctness risks | Mitigable | High (permanent) | High (permanent) |
| Framework breakage risks | Low-Medium | Low | Low |
| Governance risks | Medium (mitigable) | N/A | Medium |
| Operational risks | Medium (mitigable) | N/A | N/A |
| **Aggregate** | **Medium-High, mitigable** | **Medium, unresolvable** | **Medium-High, unresolvable** |

---

## Composite Ranking

| Rank | Approach | Technical | Business | Risk Mitigability | Overall |
|------|----------|-----------|----------|-------------------|---------|
| 1 | **A — Full Phase 10c** | 44 | 43 | ✅ Mitigations buildable | **Recommended** |
| 2 | B — Annotation-Only | 46 | 43 | ❌ R01, R04 permanent | Not recommended |
| 3 | C — Audit Script | 35 | 37 | ❌ Tooling drift permanent | Not recommended |

**Tie-breaker rationale:** Approach B scores marginally higher on technical dimensions, but that advantage comes entirely from lower enforcement strength — i.e., B scores well on "implementation feasibility" because it doesn't actually implement enforcement. The 4 failures that triggered this story were all cases where advisory patterns failed. B accepts that failure mode permanently. A closes it.

---

## Risk Register (Top 15)

| ID | Description | Likelihood | Impact | Mitigation |
|----|-------------|------------|--------|------------|
| R01 | Agents ignore criticality field (no mechanical enforcement) | High | High | Lint: CI rejects seed.md with missing/invalid criticality |
| R02 | Teams default to "routine" to skip Phase 10c | High | High | Require justification comment for routine; lightweight product-owner field |
| R03 | Phase 10c overhead causes routing workarounds | Medium | Medium | Scope 10c narrowly; template is fill-in-the-blank, not freeform |
| R04 | Contracts written at wrong abstraction (HTTP 200 vs "ad spend submitted") | High | Critical | Template ships with business-level examples; persona forbids code-level assertions |
| R05 | Contract tests mock too deep; miss real integration failures | Medium | High | Mandate outermost boundaries; concrete fixture pattern in Phase 7 persona |
| R06 | Status endpoint decoupled from actual violations (reports healthy when violated) | Medium | Critical | Contract runner writes to shared state file that `/api/status` reads directly |
| R07 | Phase persona updates break existing non-critical workflows | Medium | High | Additive-only changes; new steps gated behind `if criticality == critical` |
| R08 | Mid-story submodule updates create partial patterns | Medium | Medium | Document: submodule bumps apply at story boundary, not mid-story |
| R09 | Submodule propagation breaks downstream projects | Low | High | Semantic versioning; breaking changes in major version; opt-in minor bumps |
| R10 | critical-features.md becomes stale (nobody maintains it) | High | Medium | CI step verifies every critical story has an entry; fails build if missing |
| R11 | Runbook URLs in status endpoints go dead | Medium | Medium | URL reachability check in Phase 11 pre-deploy gate |
| R12 | Grafana dashboard template drifts from framework | Medium | Low | Template versioned in repo; bumps required on breaking changes |
| R13 | Violation events flood logs; ops team tunes them out | Medium | High | Rate-limit events per contract per hour; aggregate in Grafana panel |
| R14 | CI deploy-block too sensitive; halts routine deploys | Medium | High | Per-contract `blocking: true` flag; default is warn-only until pattern is proven |
| R15 | Status endpoint becomes a failure point | Low | Medium | Status handler must be dependency-free (no DB/network at request time) |

---

## Top 5 Risks Requiring Mitigation in Design

1. **R04 — Wrong abstraction level in contracts** (Critical impact). Design must ship the output-contracts.md template with concrete worked examples and an explicit prohibition on HTTP/code-level assertions in the Phase 7 persona.

2. **R06 — Status endpoint decoupled from violation detection** (Critical impact). The architecture must wire contract violation events directly to the health flag — no manual plumbing.

3. **R01 — No mechanical enforcement of criticality field** (High likelihood + impact). The Phase 11 pre-deploy gate must check for the field's presence and validity, not just document it.

4. **R02 — Routine classification escape hatch** (High likelihood + impact). The seed template must require a one-line justification when criticality=routine for features that touch financial data, timing windows, or external writes.

5. **R14/R13 — Alert fatigue + deploy-block sensitivity** (Paired risks). Introduce a `blocking: true` opt-in per contract clause, defaulting to warn-only. This lets teams build confidence in the pattern before elevating to hard gates.

---

## Key Technical Decisions

| Decision | Chosen direction | Rationale |
|----------|-----------------|-----------|
| New phase vs. extending Phase 10 | **New Phase 10c** | Separate phase makes the hardening step unambiguous and phase-routable; extending Phase 10 creates ambiguity about what's required |
| Separate test directory vs. marker-based | **`tests/critical_features/<slug>/contracts/`** | Grep-discoverable; lint can target the directory; path-based enforcement is simpler than marker-based |
| Violation events: log-only vs. Prometheus | **Structured log + Prometheus counter** | Logs for human debugging; Prometheus for Grafana panel and alert rule; both emitted together |
| Status endpoint: DB-backed vs. in-memory | **In-memory / file-backed** | DB dependency makes the health endpoint itself a failure surface (R15) |
| Blocking: all-or-nothing vs. per-contract flag | **Per-contract `blocking: true`** | Allows gradual adoption; teams can warm-up with warn-only before hard gating |
| Framework delivery: new artifacts vs. in-place edits | **Mixed: new templates + additive persona edits** | New files are cleaner; persona edits must be additive to preserve backward compatibility (R07) |

---

## Effort Estimate (Approach A)

| Work item | Estimate |
|-----------|----------|
| Framework documentation (patterns/critical-features.md) | 1.5d |
| Template files (seed.md update, output-contracts.md, critical-features-index.md) | 0.5d |
| Agent persona updates (phase-1, 7, 10, 11) | 1d |
| AGENTS.md Critical Features section + phase routing updates | 0.5d |
| software-development-guidance.md Phase 10c documentation | 0.5d |
| **Total** | **~4d** |

_Note: This is documentation-only. Implementation of actual status endpoints, dashboards, and contract tests is per-project work (STORY-592+)._

---

## Recommendation

**Approach A — Full Phase 10c with Dedicated Phase.**

The decisive factor is enforcement. The 4 incidents that triggered this story all occurred in a system that had monitoring but no structural obligation to define and gate on observable invariants. Approach B adds a label without obligation. Approach A creates obligation through phase structure, deploy gates, and lint rules.

The mitigations for Approach A's risks are all buildable within the pattern design itself (see Top 5 above). Approach B's critical risks (R01, R04) are permanent by design — they cannot be mitigated because enforcement is the feature.

### Mitigations to incorporate into Phase 6 design:

1. `output-contracts.md` template includes 3 worked examples at business level (not HTTP level)
2. Phase 7 persona includes a concrete 2-line fixture pattern for outermost-boundary mocking
3. `/api/status` handler reads from a file written by the contract runner — no manual health-flag wiring
4. Per-contract `blocking: true` field; default warn-only during adoption period
5. Phase 11 gate checks: (a) criticality field present in seed.md, (b) contracts directory exists if critical, (c) runbook URLs return HTTP 200, (d) `docs/critical-features.md` entry exists

---

## Next Phase

**Phase 5 (Selection)** — Present recommendation and finalize scope. Given the prescriptive dispatch and the unanimous sub-agent agreement on Approach A, Phase 5 should be a confirmatory pass focused on scoping the MVP (which templates and persona updates ship in this story vs. deferred to STORY-592).
