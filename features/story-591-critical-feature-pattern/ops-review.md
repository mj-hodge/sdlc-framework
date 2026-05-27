# Ops Review — STORY-591: Critical-Feature SDLC Pattern

**Reviewer:** Ops Review Agent (Phase 6d)
**Date:** 2026-04-25
**Story:** STORY-591 — Critical-Feature Pattern Definition
**Scope:** Framework-level pattern; no running code. Review evaluates the operational adequacy of the *pattern specification* and the operational requirements it places on consuming projects.

---

## 1. Operational Readiness Assessment

The pattern specifies five operational components that consuming projects must implement. Each is evaluated below.

| Component | Specified | Adequate | Gap |
|-----------|-----------|----------|-----|
| Health endpoint (`/api/status`) | Yes | Partial | No `/health` separation; restart-loss risk |
| Human dashboard (`/status`) | Yes | Yes | Minor: no auth guidance |
| Structured violation logs | Yes | Yes | Volume control not specified |
| Prometheus counters | Yes | Partial | Cardinality risk with many features |
| Alert rules | Yes (pattern only) | Partial | Thresholds and fatigue mitigation not specified |
| Grafana dashboard template | Yes | Yes | No versioning policy |
| Runbooks | Yes (required) | Yes | No freshness-check mechanism |
| Critical-features index | Yes | Yes | No automated staleness detection |

**Overall readiness rating:** Conditionally Acceptable. The pattern is sound but has six operational gaps that must be closed before consuming projects implement it. None are blockers for STORY-591 (a documentation story) but all must be addressed in the first consuming implementation (STORY-592).

---

## 2. Status Endpoint Resilience

### 2.1 Restart Behavior

The specification mandates in-memory or file-backed state for `/api/status`. This is correct for avoiding DB dependency during outages, but the implications must be explicit.

**On process restart (in-memory state):**
- All `last_success_at` values reset to `null`.
- All `violation_count_24h` values reset to `0`.
- `/api/status` will briefly report healthy even if the feature was degraded pre-restart.

**Risk level:** Medium. A restart after a violation event clears the signal. If the orchestrator checks `/api/status` immediately post-restart, it will see `healthy` and not escalate — hiding the underlying problem.

**Required mitigations (to be added to pattern):**

1. File-backed state must be the default for production. In-memory is acceptable only for local dev.
2. The state file must be written atomically (write to `.tmp`, then `os.rename`) to prevent partial-read on crash.
3. On startup, the process must read the state file if it exists and restore `last_success_at` from it. Fresh start (no file) must initialize health to `degraded`, not `healthy`.
4. The pattern must document a startup grace period (recommended: 2× the shortest feature interval) during which the aggregate status is `degraded` regardless of individual feature state.

### 2.2 Multi-Replica Consistency

The pattern does not address multi-replica deployments (e.g., Azure Container Apps with min-replicas > 1).

**Problem:** Each replica maintains its own in-memory or file-backed state. A violation detected on replica A is invisible to replica B. A load-balanced request may land on replica B and return `healthy` while A holds the actual violation.

**Risk level:** High for multi-replica deployments. Misleading health signals are worse than no signal.

**Required mitigations:**

1. The pattern must explicitly require a shared state store (Redis, Azure Blob, or a shared volume) when replica count > 1.
2. Acceptable fallback: document that `/api/status` is only reliable when replica count = 1 (single-replica background workers). Multi-replica web APIs should not use this pattern for in-memory state.
3. For Azure Container Apps specifically, recommend a sidecar or Azure Blob state store with a short TTL (60s) to bound staleness.

### 2.3 State Persistence Summary

| Scenario | Risk | Mitigation Required |
|----------|------|---------------------|
| Single replica, file-backed | Low | Atomic writes; restore on startup |
| Single replica, in-memory | Medium | Acceptable only for dev/test |
| Multi-replica, per-replica state | High | Shared state store required |
| Replica restart mid-incident | Medium | Startup grace period (degraded default) |

---

## 3. Violation Event Management

### 3.1 Volume Control

The pattern requires emitting a structured log event on every contract breach. If the contract is continuously violated (e.g., a duplicate blob arriving every 30 seconds), the log volume could become:

- A cost problem (log ingestion pricing per GB).
- A noise problem (individual violations buried in flood).
- An alert storm (Prometheus rate counter triggers alert on every scrape).

**Required additions to pattern:**

1. **Per-contract emission rate limit.** Default: at most one violation event per contract per 60 seconds. Subsequent violations within the window increment the counter but suppress the log event body. A "suppression summary" event must fire at the end of the window: `{"event": "..._violation_suppressed", "count": N, "window_seconds": 60}`.
2. **Circuit-breaker state.** If a contract has been continuously violated for > 10 minutes, the feature health must be set to `unhealthy` (not `degraded`). This prevents alert rules from needing to watch log volume.
3. **Retention guidance.** Violation events must be retained for at least 30 days to support SLO calculation. Pattern must state this requirement.

### 3.2 24-Hour Violation Count

The `violation_count_24h` field in `/api/status` implies a rolling 24-hour window. The pattern does not specify how this window is maintained in file-backed state.

**Required:** The pattern must specify that consuming projects implement a simple sliding window (e.g., a list of UTC timestamps in the state file, pruned to the last 24h on each write).

---

## 4. Metric Cardinality Analysis

### 4.1 Label Explosion Risk

The pattern defines Prometheus counters with labels `{severity, contract_id}` per feature. The counter name is `<feature>_<contract>_violation_total`.

For N features, each with M contracts, the total time series count is: N × M × |severity values| = N × M × 2.

At the current scale (estimated 5–15 critical features per project, 2–5 contracts each):
- Low estimate: 5 × 2 × 2 = 20 series — no risk.
- High estimate: 15 × 5 × 2 = 150 series — no risk.

**Finding:** Cardinality is not a risk at the current scale. However, the pattern must guard against future label additions.

**Required constraint in pattern:** The `{severity, contract_id}` label set is fixed. No dynamic or high-cardinality values (user IDs, request IDs, timestamps) may be added as Prometheus labels. This must be a named rule in the metric specification.

### 4.2 Metric Naming

Each feature produces a separate metric name (`<feature>_<contract>_violation_total`). With 15 features × 5 contracts = 75 unique metric names. This is manageable but makes dashboards harder to templatize.

**Recommendation:** Consider an alternative schema using a single metric with a `feature` label:
```
critical_feature_violation_total{feature="sp-report-sync", contract="C1", severity="critical"}
```
This reduces metric count from N×M to 1 and makes the Grafana template variable substitution simpler. This recommendation should be evaluated in STORY-592's implementation.

---

## 5. Alert Design

### 5.1 Alert Fatigue Mitigation

The pattern requires alert rules but does not specify:
- Minimum severity threshold before paging.
- Minimum violation rate (rate threshold).
- Evaluation window.
- Time-of-day routing (business hours vs. on-call).

Without these, consuming teams will likely set overly sensitive rules and disable them after the first false-alarm weekend.

**Required additions to alert rule template:**

| Parameter | Recommended Default | Notes |
|-----------|--------------------|-|
| Evaluation window | 5 minutes | Short enough to catch sustained violations |
| Rate threshold (critical contracts) | > 0 violations in window | Zero tolerance for blocking violations |
| Rate threshold (non-blocking contracts) | > 2 violations in window | Avoids single-event noise |
| Severity routing | `critical` contracts → PagerDuty; `warning` → Slack only | Prevents page fatigue |
| Repeat interval | 30 minutes | Re-notify if still firing |
| Resolve notification | Required | Confirm the problem is cleared |

### 5.2 Blocking vs. Non-Blocking Alert Separation

The pattern defines `blocking: true/false` per contract. This must map directly to alert severity:

- `blocking: true` contract violated → `severity: page` (wakes someone up).
- `blocking: false` contract violated → `severity: warning` (Slack message, no page).

The pattern must state this mapping explicitly. Currently it does not.

### 5.3 Alert Escalation

No escalation path is defined. If the on-call does not acknowledge a `critical` alert within 15 minutes, it must escalate. The pattern should reference the consuming project's incident management tool (PagerDuty escalation policy) rather than defining escalation itself.

---

## 6. Dashboard and Runbook Lifecycle

### 6.1 Grafana Dashboard Versioning

The pattern includes a Grafana JSON template but specifies no versioning policy. As the pattern evolves (new panels, new variables), consuming projects will diverge from the template.

**Required:**
1. The Grafana JSON template must carry a `version` field in its `__inputs` or `meta.version` block.
2. A `DASHBOARD_VERSION` comment must appear at the top of the template file in the framework.
3. The pattern documentation must instruct consuming projects to note which template version they applied.
4. Phase 10c should log a warning if a consuming project's dashboard version is behind the current template.

### 6.2 Runbook Freshness

The `/api/status` response includes `runbook_url` per feature. If the runbook URL is a GitHub permalink to a specific commit or branch, it may return 404 after repo restructuring or branch deletion.

**Required:**
1. Runbook URLs in the status endpoint state must be validated on startup (HTTP HEAD request, non-blocking, logged on failure).
2. The Phase 11 CI gate (Check 13) must validate that all `runbook_url` values in the state file return HTTP 200. A 404 runbook URL is a Check 13 failure.
3. Runbooks must be co-located in the consuming project repo (`docs/runbooks/<slug>.md`) rather than external links, to eliminate external-URL failure risk.

### 6.3 Critical-Features Index Staleness

`docs/critical-features.md` is a static markdown file with a "Last Verified" column. Without automation, this date will become stale.

**Required:** The Phase 11 CI gate must check that each row's "Last Verified" date is within 90 days. Rows older than 90 days fail Check 13.

---

## 7. Separation of Concerns: `/health` vs. `/api/status`

This is the highest-risk operational gap in the current pattern.

### 7.1 The Problem

Orchestrators (Azure Container Apps, Kubernetes, Docker Compose health checks) use a `/health` or `/healthz` endpoint to determine whether to restart or stop routing traffic to a replica. If an orchestrator is configured to use `/api/status` for its health check, the following failure mode occurs:

1. A non-blocking contract is violated (e.g., one duplicate blob in 24h).
2. `/api/status` returns `degraded`.
3. Orchestrator sees non-200 or parses `degraded` as unhealthy.
4. Orchestrator kills and restarts the replica.
5. New replica starts with clean state, briefly reports `healthy`.
6. Orchestrator is satisfied; stops restarting.
7. The underlying contract violation is still occurring — now silently.

This is a restart loop caused by business-level signal being misused as infrastructure-level signal.

### 7.2 Required Separation

The pattern must mandate a strict two-endpoint separation:

| Endpoint | Purpose | HTTP 200 Condition | Orchestrator Health Check? |
|----------|---------|-------------------|---------------------------|
| `GET /health` | Infrastructure liveness | Process is running and can accept connections | **YES — this endpoint only** |
| `GET /api/status` | Business contract health | Always 200 (even when degraded/unhealthy) | **NO — never** |

**Critical rule for `/api/status`:** This endpoint MUST always return HTTP 200 regardless of feature health. The health state is in the JSON body. Returning 503 for a degraded feature would make it unusable as an orchestrator health check replacement — but the pattern currently specifies a 503 response for status check failure. This must be revised: 503 must only be returned if the endpoint itself crashes, not if features are degraded.

**Required pattern additions:**
1. Add a `GET /health` endpoint specification (returns `{"status": "ok"}` and HTTP 200 if the process is running — nothing more).
2. Explicitly state: "Orchestrators MUST use `/health`, not `/api/status`. `/api/status` is for monitoring and dashboards only."
3. The Phase 10c checklist must verify that the consuming project's orchestrator health check points to `/health` not `/api/status`.

---

## 8. Findings Table

| ID | Severity | Finding | Recommendation | Status |
|----|----------|---------|----------------|--------|
| OPS-01 | High | In-memory state lost on restart; health resets to healthy post-crash | Require file-backed state; restore on startup; default to degraded on fresh start | Open |
| OPS-02 | High | Multi-replica deployments have inconsistent violation state per replica | Require shared state store (Redis/Azure Blob) for replica count > 1; document single-replica constraint | Open |
| OPS-03 | High | `/api/status` could be misconfigured as orchestrator health check causing restart loops | Mandate `/health` endpoint separation; state that `/api/status` must always return HTTP 200 | Open |
| OPS-04 | Medium | Continuous contract violations flood logs with no rate limiting | Add per-contract emission rate limit (1/60s default) with suppression summary events | Open |
| OPS-05 | Medium | `violation_count_24h` rolling window not defined; implementation will vary | Specify sliding window implementation in pattern (list of timestamps in state file, pruned on write) | Open |
| OPS-06 | Medium | Alert thresholds, severity routing, and escalation not specified | Add alert rule template with defaults: rate threshold, evaluation window, blocking→page mapping | Open |
| OPS-07 | Medium | Runbook URLs not validated; dead links in `/api/status` response | Add startup URL validation; add Check 13 step for runbook URL reachability | Open |
| OPS-08 | Medium | Grafana dashboard template has no version policy; consuming projects will diverge | Add `version` field to template; require consuming projects to record applied version | Open |
| OPS-09 | Low | Metric naming scheme (per-feature metric names) complicates Grafana templating | Evaluate single-metric-with-labels alternative in STORY-592; keep current scheme if migration cost is high | Open |
| OPS-10 | Low | `docs/critical-features.md` "Last Verified" column will become stale without automation | Phase 11 Check 13 must reject rows older than 90 days | Open |
| OPS-11 | Low | `/api/status` currently specifies HTTP 503 for degraded features; conflicts with OPS-03 fix | Revise: 503 only on endpoint crash, not feature degradation; feature health is in body only | Open |

---

## 9. Required Operational Tests (for Phase 7)

The following tests must be included in Phase 7 of STORY-591 and any consuming implementation (STORY-592):

1. **Restart-loss test:** Simulate a violation, write state, restart process, assert that health initializes to `degraded` (not `healthy`) when state file exists.
2. **Fresh-start test:** Start with no state file; assert that all features initialize to `degraded` (not `healthy`).
3. **Atomic write test:** Kill the process during a state write; assert the state file is not corrupted on next read.
4. **Rate-limit test:** Trigger 100 violations within 60 seconds on a single contract; assert that at most 1 full event body is logged plus 1 suppression summary.
5. **Runbook URL validation test:** Set a `runbook_url` to a non-existent path; assert that startup logs a warning and the Phase 11 check fails.
6. **Orchestrator isolation test:** Assert that `GET /health` returns HTTP 200 and body `{"status": "ok"}` even when a critical feature is `unhealthy`.
7. **Multi-replica consistency test (integration):** Write a violation from replica A's state path; assert replica B reads the same state when using a shared state store.
8. **Aggregate status test:** Assert that one `unhealthy` feature causes the top-level `status` to be `unhealthy`; one `degraded` feature causes `degraded`; all healthy causes `healthy`.
9. **24-hour window pruning test:** Insert 10 timestamps, 5 older than 24h, 5 recent; assert `violation_count_24h` returns 5.
10. **CI lint test:** Add a `@pytest.mark.skip` to a contract test in a test run; assert Check 13 CI step exits non-zero.

---

## 10. Sign-off

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Health checks | Needs work | `/health` vs `/api/status` separation is missing |
| Metrics | Acceptable | Cardinality low; naming scheme is a medium-term concern |
| Logging | Needs work | No volume control specified |
| Alerting | Needs work | No thresholds, severity routing, or escalation defined |
| Deployment safety | Needs work | Restart-loss and multi-replica gaps are high risk |
| Runbook freshness | Needs work | No validation mechanism |
| Dashboard lifecycle | Acceptable | Missing version policy only |

**Conditional approval:** The pattern design is fundamentally sound and the SDLC enforcement gates (Phase 10c, Phase 11 Check 13) are well-structured. The ops review identifies 3 High and 5 Medium gaps that must be resolved before STORY-592 implements this pattern. No gaps block STORY-591 completion (a documentation-only story), but findings OPS-01, OPS-02, and OPS-03 must appear as explicit requirements in the `patterns/critical-features.md` document before that artifact is marked final.

**Required before STORY-592 begins:**
- OPS-01 (restart-loss) — add to pattern spec
- OPS-02 (multi-replica) — add to pattern spec
- OPS-03 (`/health` separation) — add to pattern spec and API design
- OPS-04 (rate limiting) — add to violation event spec
- OPS-06 (alert defaults) — add to alert rule template
