# Site Reliability -- STORY-591: Critical-Feature SDLC Pattern

**Phase:** 10 -- Operational Resilience
**Date:** 2026-04-25
**Engineer:** Site Reliability Engineer (Phase 10)
**Reliability Tier:** Essential
**Status:** Complete

---

## 1. Reliability Context

### What This Story Is

STORY-591 is a **documentation-only story** in the `sdlc-framework` git submodule. There is no runtime application, no deployed services, no HTTP endpoints, no database. The deliverable is a set of pattern documents, templates, and agent persona updates that consuming projects pull via `git submodule update`.

### What "Operational Resilience" Means for a Pattern

For a running service, operational resilience means uptime, latency, and recovery. For a framework pattern consumed as a git submodule, operational resilience means:

1. **Pattern integrity** -- The 9 framework files remain internally consistent, pass their 61 tests, and do not regress when the framework evolves.
2. **Pattern adoption health** -- Consuming projects correctly implement the pattern. Incorrect or partial adoption is the equivalent of a "service outage" for a pattern.
3. **Pattern prescriptive clarity** -- The operational requirements the pattern places on consuming projects are specific enough to implement without ambiguity. Vague guidance produces inconsistent implementations, which is the pattern equivalent of configuration drift.

### Reliability Tier: Essential

| Field | Value |
|-------|-------|
| Tier | Essential |
| Availability target | N/A -- no running service |
| RTO | N/A |
| RPO | N/A |
| Rationale | This is a git submodule containing markdown files and test scripts. It has no uptime requirement. Its "availability" is the availability of the git repository hosting it, which is managed by GitHub's SLA. |

### Framework File Inventory

The critical-feature pattern consists of 9 files:

| # | File | Purpose |
|---|------|---------|
| 1 | `patterns/critical-features.md` | Canonical pattern reference (317 lines, 10 design points) |
| 2 | `templates/output-contracts.md` | Output contract template for consuming projects |
| 3 | `templates/critical-features-index.md` | Project-level critical features index template |
| 4 | `templates/seed.md` | Updated with Criticality field |
| 5 | `agents/phase-1-seed.md` | Criticality classification in Phase 1 workflow |
| 6 | `agents/phase-7-test-design.md` | Contract test directory and lint enforcement |
| 7 | `agents/phase-10-operations.md` | Violation event schema and output contracts |
| 8 | `agents/phase-11-predeploy-gate.md` | Check 13: Critical Feature Contracts |
| 9 | `AGENTS.md` | Critical Features section with phase paths |

---

## 2. Pattern Health Indicators

Since there is no runtime service, traditional SLIs (latency, error rate, availability) do not apply. Instead, the pattern's health is measured by indicators that track integrity and adoption.

### 2.1 Framework Integrity SLIs

| SLI | Measurement | SLO | Window |
|-----|-------------|-----|--------|
| Test passage rate | 61 tests in `tests/critical_features/` pass on every PR | 100% (all 61 GREEN) | Per PR |
| File completeness | All 9 framework files exist and are non-empty | 9/9 present | Per PR |
| Cross-reference validity | All file path references in pattern docs resolve to existing files | 0 broken references | Per PR |
| Terminology consistency | Key terms ("output contract", "contract test", "violation event", "Phase 10c") used consistently across all 9 files | 0 inconsistencies | Per release |

**Error budget:** There is no error budget for framework integrity. The SLO is 100% -- a broken pattern file shipped to consuming projects is a defect, not an acceptable error rate.

### 2.2 Adoption Health SLIs (Measured Across Consuming Projects)

| SLI | Measurement | SLO | Window |
|-----|-------------|-----|--------|
| Contract test presence | For each critical feature in a consuming project, `tests/critical_features/<slug>/contracts/` exists | 100% of critical features have contract tests | Continuous |
| Phase 10c activation rate | Percentage of stories with `criticality: critical` that actually run Phase 10c | 100% | Per sprint |
| Index completeness | Each consuming project with critical features has `docs/critical-features.md` | 100% of projects with critical features | Per sprint |
| Contract test GREEN rate | Contract tests pass in CI for consuming projects | 100% for `Blocking: true` contracts | Per deploy |

### 2.3 Pattern Prescriptive Clarity SLI

| SLI | Measurement | SLO |
|-----|-------------|-----|
| Implementation ambiguity reports | Number of times a consuming project engineer asks "how do I implement X?" where X is specified in the pattern | 0 per sprint (target) |

This SLI is measured qualitatively via Asana comments and Slack questions. If a consuming project reports ambiguity, it indicates a pattern clarity gap that should be addressed in the next framework release.

---

## 3. Operational Guidance for Consuming Projects

This section specifies the operational requirements that the pattern places on consuming projects. These are the implementation details that consuming engineers must follow. Each subsection addresses a gap identified in Phase 9 refinement.

### 3.1 `/api/status` Endpoint: Always HTTP 200

**Addresses: Phase 9 H5, OPS-11, OPS-03**

The `/api/status` endpoint MUST always return HTTP 200 regardless of feature health. The health state is conveyed exclusively in the JSON response body, never in the HTTP status code.

**Why this matters:** Returning HTTP 503 for degraded features causes orchestrator restart loops. Container orchestrators (Kubernetes, Azure Container Apps, Docker Compose) interpret non-200 responses from health-adjacent endpoints as signals to kill and restart the container. If `/api/status` returns 503 when a business contract is violated:

1. Orchestrator kills the replica.
2. New replica starts with clean state, reports `healthy`.
3. Orchestrator is satisfied.
4. The underlying contract violation is still occurring -- now silently.

**Required behavior:**

| Scenario | HTTP Status | JSON `health` Field |
|----------|-------------|---------------------|
| All contracts healthy | 200 | `"healthy"` |
| One or more contracts violated | 200 | `"degraded"` |
| Feature is non-functional | 200 | `"down"` |
| `/api/status` endpoint itself crashes (unhandled exception) | 500 | N/A (crash response) |

**Orchestrator separation rule:** Orchestrators MUST use `GET /health` (infrastructure liveness), not `GET /api/status` (business contract health). These are separate endpoints with separate purposes. Phase 10c must verify that the consuming project's orchestrator health check points to `/health`, not `/api/status`.

### 3.2 Violation Event Rate Limiting

**Addresses: Phase 9 H4, OPS-04**

When a contract is continuously violated (e.g., duplicate blobs arriving every 30 seconds), unthrottled violation events create three problems: log ingestion cost, alert noise, and event flood obscuring individual failures.

**Required rate limiting:**

| Parameter | Value |
|-----------|-------|
| Maximum emission rate | 1 full violation event per contract per 60 seconds |
| Counter behavior during suppression | Prometheus counter increments on every violation (no suppression of counter) |
| Log body behavior during suppression | Log body is suppressed; only the counter increments |
| Suppression summary | At the end of each 60-second window where suppression occurred, emit a summary event |

**Suppression summary event schema:**

```json
{
  "event": "<feature_slug>_<contract_id>_violation_suppressed",
  "feature": "<feature name>",
  "contract_id": "C1",
  "timestamp": "<ISO 8601 -- end of suppression window>",
  "suppressed_count": 14,
  "window_seconds": 60,
  "severity": "warning"
}
```

**Circuit-breaker escalation:** If a contract has been continuously violated for more than 10 minutes (10 consecutive suppression windows), the feature health MUST be set to `down` (not `degraded`). This prevents alert rules from needing to track log volume patterns.

### 3.3 Rolling 24-Hour Window Algorithm

**Addresses: Phase 9 M7, OPS-05**

The `violation_count_24h` field in the `/api/status` response requires a rolling 24-hour window. The pattern specifies the algorithm to prevent implementation divergence across consuming projects.

**Algorithm: UTC timestamp list, pruned on write**

```
State structure:
  violations: list of ISO 8601 UTC timestamps

On each contract violation:
  1. Append current UTC timestamp to the violations list
  2. Prune: remove all entries older than 24 hours (current_time - 24h)
  3. Set violation_count_24h = len(violations)
  4. Write state atomically (write to .tmp, then os.rename)

On each /api/status read:
  1. Prune the list (same logic as step 2 above)
  2. Return len(violations) as violation_count_24h
```

**Pruning on both write and read** ensures the count is accurate even if no new violations occur for hours. The prune-on-read step handles the case where the last violation was 23 hours ago and the count should decrement to 0 after 24 hours without any write trigger.

**State file format (JSON):**

```json
{
  "feature_slug": {
    "health": "degraded",
    "last_success_at": "2026-04-25T10:30:00Z",
    "violations": [
      "2026-04-25T08:15:00Z",
      "2026-04-25T09:22:00Z",
      "2026-04-25T10:05:00Z"
    ],
    "runbook_url": "https://docs.gorillacommerce.ai/runbooks/feature-slug"
  }
}
```

### 3.4 PII Sanitization Rules for Violation Events

**Addresses: Phase 9 H1, SEC-006**

The pattern specifies "avoid PII" in violation event `detail` fields. This section enumerates the 5 specific sanitization rules that consuming projects MUST enforce.

| Rule | Requirement | Example (BAD) | Example (GOOD) |
|------|-------------|---------------|-----------------|
| **R1 -- No raw API payloads** | The `detail` field MUST NOT contain raw HTTP response bodies. Use counts, types, and field names -- not values. | `"detail": "{\"email\": \"john@example.com\", \"status\": 400}"` | `"detail": "API returned 400; response contained 2 fields (email, status)"` |
| **R2 -- No PII in detail** | Email addresses, customer names, and account identifiers MUST be replaced with redacted placeholders. | `"detail": "Email column blank for customer john.doe@example.com in campaign 88421"` | `"detail": "Email column blank for customer <email-redacted> in campaign <id-redacted>"` |
| **R3 -- No credentials** | API keys, tokens, passwords, and connection strings are forbidden in the `detail` field. | `"detail": "Auth failed with key sk-abc123..."` | `"detail": "Auth failed with key <credential-redacted>"` |
| **R4 -- Structural description only** | Describe the structural anomaly, not the data content. | `"detail": "Duplicate row: profile_id=12345, email=j.doe@co.com"` | `"detail": "Duplicate blob detected: report_type=sp, date=2026-04-24, profile_id=<redacted>"` |
| **R5 -- Log destination access control** | Violation event log streams MUST be treated as sensitive. Do not send to public dashboards or unauthenticated log aggregators. | Violation events sent to a public Grafana Loki instance | Violation events sent to a restricted log stream with team-level access control |

**CI enforcement:** The existing lint check (`check_contract_lint.sh`) that scans for `skip/xfail` in contract tests SHOULD be extended to scan violation event definitions for common secret patterns (API key prefixes, connection string formats). This is recommended for STORY-592 implementation.

### 3.5 Alert Threshold Defaults and Severity Mapping

**Addresses: Phase 9 M3, OPS-06**

The pattern defines `Blocking: true/false` per contract. This flag maps directly to alert severity:

| Contract Blocking Flag | Alert Severity | Routing | Action |
|------------------------|----------------|---------|--------|
| `Blocking: true` | Page (Critical/P1) | PagerDuty or equivalent | Wakes on-call; immediate response required |
| `Blocking: false` | Warning (P3) | Slack ops channel | Next business day; no page |

**Alert rule defaults for consuming projects:**

| Parameter | Default Value | Notes |
|-----------|---------------|-------|
| Evaluation window | 5 minutes | Short enough to catch sustained violations, long enough to avoid single-event noise |
| Rate threshold (blocking contracts) | > 0 violations in window | Zero tolerance -- any violation of a blocking contract pages |
| Rate threshold (non-blocking contracts) | > 2 violations in window | Avoids alerting on a single transient event |
| Repeat interval | 30 minutes | Re-notify if the alert is still firing after 30 minutes |
| Resolve notification | Required | Confirm the alert cleared so on-call knows it is resolved |
| Escalation | Per consuming project's incident management tool | Pattern does not define escalation chains -- defer to PagerDuty/Opsgenie policy |

**Alert rule template (Prometheus Alertmanager format):**

```yaml
# Blocking contract violation -- pages on-call
- alert: CriticalContractViolation
  expr: rate(<feature_slug>_<contract_id>_violation_total[5m]) > 0
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "Blocking contract {{ $labels.contract_id }} violated for {{ $labels.feature }}"
    runbook_url: "https://docs.gorillacommerce.ai/runbooks/{{ $labels.feature }}"

# Non-blocking contract violation -- Slack warning
- alert: ContractViolationWarning
  expr: rate(<feature_slug>_<contract_id>_violation_total[5m]) > 2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Non-blocking contract {{ $labels.contract_id }} elevated for {{ $labels.feature }}"
    runbook_url: "https://docs.gorillacommerce.ai/runbooks/{{ $labels.feature }}"
```

### 3.6 Restart Behavior: Default to Degraded

**Addresses: OPS-01**

On process restart, consuming projects MUST NOT assume the last pre-restart state. The `/api/status` endpoint must initialize with:

| Field | Initial Value on Restart |
|-------|--------------------------|
| `health` | `"degraded"` |
| `last_success_at` | `null` (or value restored from state file if file-backed) |
| `violation_count_24h` | `0` (or restored from state file) |

The feature remains in `degraded` state until it completes its first successful operation after startup. This prevents the false-healthy window that occurs when in-memory state is lost on restart.

**File-backed state (recommended for production):**

1. Write state atomically: write to `<path>.tmp`, then `os.rename()` to `<path>`.
2. On startup, read the state file if it exists and restore `last_success_at` and `violations` list.
3. On fresh start (no state file), initialize `health` to `degraded`.
4. Startup grace period: the feature should remain `degraded` for 2x the shortest feature interval (e.g., if the feature runs every 5 minutes, stay `degraded` for 10 minutes) before allowing transition to `healthy`.

---

## 4. Monitoring the Pattern Itself

### 4.1 CI: Framework Integrity

Every PR to the `sdlc-framework` repository MUST pass:

| Check | Command | Expected Result |
|-------|---------|-----------------|
| All 61 tests | `pytest tests/critical_features/ -v` | 61 passed, 0 failed |
| File presence | Verify all 9 framework files listed in Section 1 exist | All present |
| Lint: no skip/xfail in contract tests | `check_contract_lint.sh` | PASS |

These checks run in the sdlc-framework CI pipeline. A failure on any check blocks the PR from merging.

### 4.2 Per-Project: Phase 11 Check 13

For every consuming project deploying a critical feature:

1. Phase 11 runs Check 13 (Critical Feature Contracts).
2. Check 13 verifies `tests/critical_features/<slug>/contracts/` exists (fail-closed if missing).
3. Check 13 runs all contract tests in the directory.
4. `Blocking: true` failures block the deploy.
5. `Blocking: false` failures emit WARN but do not block.

This is the primary mechanism for ensuring the pattern is applied correctly in consuming projects. If Check 13 is not configured, the pattern is not enforced.

### 4.3 Adoption Metrics

Track the following across the organization to measure pattern adoption:

| Metric | How to Measure | Target |
|--------|----------------|--------|
| Projects with `docs/critical-features.md` | `find` across all project repos | 100% of projects with critical features |
| Contract test count (total across org) | Count files matching `tests/critical_features/*/contracts/test_contract_*.py` | Increasing trend |
| Phase 10c activation count | Count Asana comments mentioning "Phase 10c" on critical stories | 100% of critical stories |
| Blocking graduation rate | Count of contracts that moved from `Blocking: false` to `Blocking: true` | Increasing over time |

These metrics are collected manually during quarterly reviews until automation is justified by scale (more than 10 consuming projects).

---

## 5. Incident Response for Pattern Failures

### Runbook 5.1: Consuming Project Deployed Without Contract Tests

**Severity:** P2 (High)
**Trigger:** A critical feature is deployed to production but `tests/critical_features/<slug>/contracts/` does not exist in the project repository.

**Symptoms:**
- No contract test results in the deploy log
- Phase 11 Check 13 was not run or was misconfigured
- The feature is in production without business-level test coverage

**Diagnosis Steps:**
1. Check the project's CI pipeline configuration -- is Check 13 included?
2. Check the project's `seed.md` -- is `criticality: critical` set?
3. Check if `tests/critical_features/<slug>/contracts/` directory exists in the repo.

**Resolution Steps:**
1. If Check 13 is not in the pipeline: add it. Reference `patterns/critical-features.md` SS6 for the check script.
2. If the contracts directory is missing: this is a Phase 10c gap. Run Phase 10c retroactively to define contracts and create tests.
3. If `criticality` was incorrectly set to `routine`: review the seed.md justification. If the feature handles money, time-sensitive operations, or health reporting, reclassify to `critical`.

**Escalation:** If the feature is already in production without contracts, treat it as an ops debt item. Create an `[OPS]` story to backfill contract tests. Do not roll back the deployment solely for missing contract tests -- the feature itself may be working correctly.

---

### Runbook 5.2: Violation Events Flooding Logs

**Severity:** P2 (High)
**Trigger:** Log volume spikes due to continuous violation event emissions from a single contract.

**Symptoms:**
- Log ingestion cost spike
- Hundreds of identical violation events per minute in the log stream
- Alert storm: repeated alerts for the same contract

**Diagnosis Steps:**
1. Identify the contract generating the flood: search logs for `_violation` event names.
2. Check if rate limiting is implemented: the consuming project should emit at most 1 event per contract per 60 seconds (see Section 3.2).
3. Check if the circuit breaker has activated: after 10 minutes of continuous violation, health should be `down`.

**Resolution Steps:**

If rate limiting is not implemented:
1. Review `patterns/critical-features.md` SS5 and this document Section 3.2 for the rate limiting specification.
2. Implement the 60-second per-contract suppression window.
3. Implement the suppression summary event.
4. Deploy the fix.

If rate limiting is implemented but the volume is still high:
1. Check if multiple contracts are each emitting at their 1/60s rate -- this is expected behavior if many contracts are violated simultaneously.
2. Investigate the root cause of the contract violations rather than further suppressing the signal.

**Escalation:** If log cost is critical (more than 2x normal), temporarily reduce log level for violation events to DEBUG while implementing the rate limiter.

---

### Runbook 5.3: `/api/status` Returning 503

**Severity:** P1 (Critical)
**Trigger:** The `/api/status` endpoint returns HTTP 503 instead of HTTP 200 with health state in the JSON body.

**Symptoms:**
- Monitoring tools report `/api/status` as "down"
- Orchestrator may be restarting containers based on the 503 response
- Restart loop: container starts, briefly reports healthy, then 503 again

**Diagnosis Steps:**
1. Confirm the endpoint is returning 503: `curl -s -o /dev/null -w "%{http_code}" https://<host>/api/status`
2. Check if the 503 is caused by feature degradation (wrong) or an actual endpoint crash (acceptable).
3. Check the orchestrator health check configuration: is it pointed at `/health` or `/api/status`?

**Resolution Steps:**

If 503 is caused by feature degradation:
1. This is a pattern implementation bug. `/api/status` MUST return HTTP 200 regardless of feature health (see Section 3.1).
2. Fix the endpoint to always return 200 with the health state in the JSON body.
3. Verify the orchestrator health check uses `/health`, not `/api/status`.

If 503 is caused by an actual endpoint crash:
1. Check application logs for the unhandled exception.
2. Fix the crash. The `/api/status` endpoint must be resilient -- no DB dependency, no external calls, in-memory or file-backed only.

**Escalation:** If the restart loop is active, immediately reconfigure the orchestrator to use `/health` instead of `/api/status`.

---

### Runbook 5.4: Contract Test Skipped in CI

**Severity:** P2 (High)
**Trigger:** A contract test file contains `@pytest.mark.skip` or `@pytest.mark.xfail`, bypassing the business guarantee.

**Symptoms:**
- CI reports all tests GREEN, but one or more contract tests are actually skipped
- The skipped contract's business assertion is unverified
- Phase 11 Check 13 passes (because the test did not fail -- it was skipped)

**Diagnosis Steps:**
1. Run the lint check: `check_contract_lint.sh` (see `patterns/critical-features.md` SS4).
2. Search for skip/xfail markers: `grep -rn "pytest.mark.skip\|pytest.mark.xfail\|pytest.skip" tests/critical_features/`

**Resolution Steps:**
1. If the lint check is not in CI: add it. It must run before Phase 11 Check 13.
2. Remove the `skip`/`xfail` marker from the contract test.
3. If the test cannot pass because the feature is broken, fix the feature -- do not skip the test.
4. If the test cannot pass because the contract definition is wrong, update the contract in `docs/output-contracts/<slug>.md` and rewrite the test.

**Escalation:** Skipped contract tests are never acceptable. If the team argues that skipping is necessary, escalate to the lead engineer for a contract review. The contract may need to be reclassified as `Blocking: false` during remediation, but the test itself must not be skipped.

---

## 6. Design Gap Analysis

This section documents operational requirements discovered during Phase 10 that were not anticipated during Phase 6 design. These gaps feed into the retrospective as Phase 6 improvement proposals.

### Gaps Identified

| # | Gap | Phase 6 Section | Severity | Recommendation for Phase 6 Process |
|---|-----|-----------------|----------|-------------------------------------|
| G1 | PII sanitization for violation events was specified as "avoid PII" without enumerating specific rules | Phase 6 Specification -- Violation Events | High | Phase 6 must require enumerated sanitization rules (not just "avoid PII") whenever a design includes structured event emission. Add a "Data Sanitization" subsection to the Phase 6 specification template. |
| G2 | Rate limiting for event emission was not considered during design | Phase 6 Specification -- Violation Events | High | Phase 6 must include a "Volume Control" analysis for any design that emits structured events. The question "what happens if this event fires 1000 times per minute?" should be part of the Phase 6d ops review checklist. |
| G3 | `/api/status` HTTP status code behavior was ambiguous -- could be read as returning 503 for degraded state | Phase 6 API Design | High | Phase 6 API design must explicitly specify HTTP status codes for every endpoint state. The phrase "returns health state" is ambiguous -- must say "returns HTTP 200 with health state in JSON body". |
| G4 | Rolling 24-hour window algorithm was not specified, leaving implementation to each consuming project | Phase 6 Specification -- `/api/status` | Medium | When a design includes a "rolling window" metric, Phase 6 must specify the algorithm (data structure, pruning strategy, read/write behavior). Do not assume consuming engineers will independently converge on the same implementation. |
| G5 | Alert threshold defaults and severity-to-blocking mapping were left unspecified | Phase 6d Ops Review | Medium | Phase 6d ops review must include an "Alert Design" section with default thresholds, severity mapping, and evaluation windows for any design that includes alerting. |
| G6 | Secret-scanning CI for test directories was not considered | Phase 6b Security Review | Medium | Phase 6b security review should include a "Test Artifact Security" check for any design that introduces new test directories containing fixtures with external service boundaries. |

### Proposed Phase 6 Process Improvements

1. **Add "Volume Control" to the Phase 6d ops review checklist.** For every structured event, log emission, or metric defined in the design, the ops reviewer must ask: "What is the maximum emission rate? What happens under sustained failure?" This prevents OPS-04-type findings.

2. **Add "Data Sanitization Rules" to the Phase 6 specification template.** Whenever a design includes runtime data in log fields or event payloads, the specification must enumerate which fields can contain PII and what redaction rules apply. "Avoid PII" is not a specification; it is a wish.

3. **Require explicit HTTP status codes in API design.** The Phase 6 API design template should require a "Status Codes" column for every endpoint, including the status code returned in degraded/error states. This prevents the ambiguity that led to OPS-11.

4. **Add "Algorithm Specification" for any rolling-window or time-based metric.** If a design includes a counter with a time window (e.g., "violations in the last 24 hours"), the Phase 6 specification must define the data structure and pruning strategy. This prevents implementation divergence across consuming projects.

---

## 7. Deployment Safety for Framework Updates

### 7.1 Pre-Merge Checklist for sdlc-framework

Before merging any PR that modifies files in `patterns/`, `templates/`, or `agents/`:

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| All 61 tests pass | `pytest tests/critical_features/ -v` | 61 passed, 0 failed |
| Contract lint clean | `bash check_contract_lint.sh` (or equivalent grep) | No skip/xfail in contract test directories |
| Cross-references valid | Manual review: all file paths in pattern docs point to existing files | No broken references |
| Terminology consistent | Manual review: key terms match the list in refinement-report.md Section 3.1 | No new inconsistencies |

### 7.2 Consuming Project Update Process

When a consuming project pulls a new version of the sdlc-framework submodule:

1. **Pull the submodule update:** `git submodule update --remote sdlc-framework`
2. **Run the framework's own tests:** `pytest sdlc-framework/tests/critical_features/ -v` -- confirms the framework files are internally consistent in the context of the consuming project.
3. **Re-run the project's own contract tests:** `pytest tests/critical_features/ -v` -- confirms the consuming project's contract tests still pass. A framework update should not break consuming contract tests, but template changes may require updates.
4. **Review the changelog:** Check `sdlc-framework/CHANGELOG.md` for any breaking changes to `patterns/` or `templates/` files.

### 7.3 Breaking Change Policy

A **breaking change** is any modification to `patterns/critical-features.md`, `templates/output-contracts.md`, or `templates/critical-features-index.md` that requires consuming projects to update their implementation. Examples:

- Adding a required field to the violation event schema
- Changing the contract test directory structure
- Adding a new required section to `docs/output-contracts/<slug>.md`
- Changing the `/api/status` JSON schema

**Breaking changes require:**

1. A migration guide in the PR description explaining what consuming projects must change.
2. A deprecation period of at least 1 sprint -- the old format is accepted alongside the new format during this period.
3. A framework test that validates both old and new formats during the deprecation period.
4. Notification to all consuming project leads via Asana comment on their active critical-feature stories.

### 7.4 Non-Breaking Changes

Non-breaking changes (clarifications, additional examples, new optional fields, test improvements) do not require a migration guide. Consuming projects benefit from these changes without any action on their part.

---

## 8. Operational Checklist

### Framework Maintainer Checklist

- [x] All 61 tests GREEN
- [x] All 9 framework files present and internally consistent
- [x] Cross-references validated (refinement-report.md Section 3.2)
- [x] Terminology consistent (refinement-report.md Section 3.1)
- [x] PII sanitization rules enumerated (Section 3.4, addresses H1)
- [x] Rate limiting specified (Section 3.2, addresses H4/OPS-04)
- [x] `/api/status` HTTP 200 rule documented (Section 3.1, addresses H5/OPS-11)
- [x] Rolling 24h window algorithm specified (Section 3.3, addresses OPS-05)
- [x] Alert threshold defaults documented (Section 3.5, addresses OPS-06)
- [x] Restart behavior specified (Section 3.6, addresses OPS-01)
- [x] Design gap analysis completed (Section 6)
- [x] Deployment safety documented (Section 7)

### Consuming Project Checklist (for Phase 10c)

- [ ] `docs/output-contracts/<slug>.md` populated with contracts
- [ ] `tests/critical_features/<slug>/contracts/` directory created with contract tests
- [ ] `/api/status` endpoint implemented, always returns HTTP 200
- [ ] `/health` endpoint implemented, separate from `/api/status`
- [ ] Orchestrator health check configured to use `/health`, not `/api/status`
- [ ] Violation events implement 60-second per-contract rate limiting
- [ ] Violation event `detail` field follows R1-R5 sanitization rules
- [ ] Rolling 24h window implemented as UTC timestamp list with prune-on-write and prune-on-read
- [ ] Restart behavior defaults to `health: degraded` until first successful operation
- [ ] Alert rules configured with blocking-to-severity mapping (Section 3.5)
- [ ] `docs/critical-features.md` index updated with new feature row
- [ ] Grafana dashboard panel added for violation counter
- [ ] `check_contract_lint.sh` added to CI (no skip/xfail in contract tests)

---

## Summary

STORY-591 is a documentation-only story delivering a framework pattern, not a running service. The operational resilience of this pattern is measured by framework integrity (61 tests, 9 files, cross-references) and adoption health (consuming projects correctly implementing the pattern).

This document addresses 6 gaps identified in Phase 9 refinement (H1, H4, H5, OPS-04, OPS-05, OPS-06) by specifying the operational details that the pattern doc leaves to consuming projects: HTTP 200 rule for `/api/status`, violation event rate limiting, rolling 24h window algorithm, PII sanitization rules, alert threshold defaults, and restart behavior.

Six design gaps were identified (Section 6) that should improve the Phase 6 process for future stories: volume control analysis, data sanitization enumeration, explicit HTTP status codes, algorithm specification for rolling windows, alert design defaults, and test artifact security review.
