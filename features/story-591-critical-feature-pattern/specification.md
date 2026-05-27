# Specification — STORY-591: Critical-Feature SDLC Pattern

## Overview

This specification defines a generic "critical-feature" pattern for the SDLC framework. When a feature is classified as `criticality: critical` during Phase 1, the framework enforces additional gates across its lifecycle: output contracts, hardened contract tests, runtime violation events, deploy-blocking CI, status endpoints, Grafana dashboards, and a discoverable index.

**Boundary:** This story modifies framework documentation and templates only. No code changes to any consuming project (advertising-amazon changes ship in STORY-592).

---

## 1. Criticality Classification

### 1.1 Field Definition

Add to the seed template (`templates/seed.md`) Overview table:

```
| Criticality | <routine|important|critical> |
```

### 1.2 Classification Criteria

| Level | Definition | Examples | SDLC Impact |
|-------|-----------|----------|-------------|
| `routine` | Failure is inconvenient but recoverable. No material business impact. Data can be re-fetched or user can retry. | Dashboard display bugs, non-essential notifications, cosmetic issues | Standard SDLC path — no additional gates |
| `important` | Failure degrades user experience or causes moderate business impact. Recovery is possible but requires effort. | Report generation delays, search ranking accuracy, optional integration failures | Standard SDLC path + recommended (not required) output contracts |
| `critical` | Failure has **material business impact**: revenue loss, missed time windows, incorrect financial data, compliance violations, or data corruption. | Ad spend submission, cron-timed financial syncs, billing calculations, compliance reporting, healthz accuracy | Enhanced SDLC path — output contracts, Phase 10c, contract tests, deploy gate, status endpoint, dashboard, index entry **ALL REQUIRED** |

### 1.3 Classification Rules

1. The Phase 1 BA persona **MUST** set the criticality field for every story. Omission is a Phase 1 completion blocker.
2. If the feature involves any of the following, the BA **MUST** justify choosing anything other than `critical`:
   - Writing to external production APIs (financial, advertising, billing)
   - Time-window-dependent operations (cron jobs, scheduled syncs, auction deadlines)
   - Financial calculations or data that feeds financial reports
   - Health check endpoints used by orchestrators or load balancers
   - Data integrity operations (deduplication, reconciliation, migration)
3. A one-line justification is required when setting `criticality: routine` for features touching the above categories.

---

## 2. Output Contracts

### 2.1 Definition

An output contract is a **one-line business assertion** stating what a critical feature MUST produce under both normal and degraded conditions. Contracts are written in business language, not code.

### 2.2 Template Structure (`templates/output-contracts.md`)

```markdown
# Output Contracts — <Feature Name>

## Overview
| Field | Value |
|-------|-------|
| Feature | <feature name> |
| Criticality | critical |
| Story | STORY-XXX |
| Owner | <team/person responsible> |

## Contracts

| ID | Assertion | Degraded Behavior | Blocking | Test File | Metric |
|----|-----------|-------------------|----------|-----------|--------|
| C1 | <business assertion> | <what happens when input is missing/invalid> | true | <test path> | <metric name> |
| C2 | ... | ... | true/false | ... | ... |
```

### 2.3 Contract Writing Rules

1. **Business-level only.** Contracts describe observable business outcomes, not implementation details.
   - GOOD: "Ad spend report contains all campaigns with non-zero spend for the requested date range"
   - BAD: "API returns HTTP 200 with JSON body containing `campaigns` array"
2. **Degraded behavior is mandatory.** Every contract states what happens when inputs are missing, stale, or malformed.
   - GOOD: "If Amazon API returns empty response, the system preserves the last known good data and emits a violation event"
   - BAD: "Handles errors gracefully"
3. **One assertion per contract.** Compound assertions must be split.
4. **`blocking` field:** When `true`, a test failure for this contract blocks deploy (Phase 11 CI gate). When `false`, failure emits a warning but does not block. Default during adoption: `false`. Mature features should have all contracts as `blocking: true`.

### 2.4 Contract Examples (from advertising-amazon failures)

| ID | Assertion | Degraded Behavior | Blocking |
|----|-----------|-------------------|----------|
| C1 | Sponsored Products report blob is deduplicated: no two blobs share the same (report_type, date, profile_id) | If duplicate detected, reject the new blob and emit `sp_report_duplicate_blob_violation` | true |
| C2 | Cron sync completes within its scheduled window (every 6h ± 30min tolerance) | If window missed, emit `cron_sync_missed_window_violation` and trigger immediate retry | true |
| C3 | Email column in campaign report is never blank when campaign has an associated contact | If contact lookup fails, populate with `"LOOKUP_FAILED"` placeholder, never empty string | true |
| C4 | `/health` endpoint reports `unhealthy` within 60s of a revision roll that fails readiness probe | If revision roll detection fails, default to reporting `degraded` (not `healthy`) | true |

---

## 3. Phase 10c — Output Contract Hardening

### 3.1 Phase Definition

| Field | Value |
|-------|-------|
| Phase | 10c |
| Name | Output Contract Hardening |
| Trigger | `criticality: critical` in seed.md |
| Scope gate | **None** — fires for ALL scopes (Trivial through Large) |
| Model | tier-2 (default) |
| Advance | confirm |
| Context group | polish |
| Parallel safe | true (can run alongside Phase 9, 10) |

### 3.2 Phase 10c Workflow

```
1. READ output-contracts.md from story folder
2. FOR EACH contract:
   a. MAP to atomic test → verify test exists in tests/critical_features/<slug>/contracts/
   b. MAP to runtime metric → define Prometheus counter name: <feature>_<contract>_violation
   c. MAP to alert rule → define threshold and notification channel
   d. MAP to runbook → verify runbook URL is valid and content exists
3. VERIFY all mappings are complete (no orphan contracts)
4. PRODUCE Phase 10c section in output-contracts.md (or separate hardening report)
5. UPDATE status endpoint schema with new contracts
6. UPDATE docs/critical-features.md index entry
```

### 3.3 Phase 10c Deliverables

| Artifact | Location | Content |
|----------|----------|---------|
| Updated output-contracts.md | `features/<story>/output-contracts.md` | All columns filled: test file, metric name, alert rule, runbook URL |
| Contract test verification | `tests/critical_features/<slug>/contracts/` | Confirms 1:1 mapping between contracts and test files |
| Metric registration | In the pattern doc (not implemented in this story) | Prometheus counter definitions |
| Alert rules | In the pattern doc (not implemented in this story) | Threshold + channel per contract |
| Index update | `docs/critical-features.md` | New row for this feature |

### 3.4 Phase Path Modifications

Current paths with Phase 10c injected:

```
Trivial + critical:   → 10c → 8 → Done
Small + critical:     1 → 7 → 10c → 8 → Done
Medium + critical:    1 → 4 → 6 → [6b, 6c, 6d] → 7 → 10c → 8 → 8b → 11 → Done
Large + critical:     1 → 2 → 3 → 4 → 5 → 6 → [6b, 6c, 6d] → 7 → 10c → 8 → 8b → 11 → [9, 10] → Done
```

**Phase 10c position:** After Phase 7 (test design), before Phase 8 (implementation). This ensures output contracts and their test mappings are finalized before implementation begins. The contract tests themselves are written in Phase 7; Phase 10c verifies completeness and adds runtime mapping.

---

## 4. Phase 7 Updates — Contract Test Requirements

### 4.1 Directory Structure

For any story with `criticality: critical`, Phase 7 MUST produce:

```
tests/critical_features/<feature-slug>/
├── contracts/
│   ├── conftest.py              # Shared fixtures: DB session factory mock, httpx client mock
│   ├── test_contract_c1.py      # One file per contract clause
│   ├── test_contract_c2.py
│   └── test_contract_c3.py
└── README.md                    # Maps contract IDs to test files, explains mock boundaries
```

### 4.2 Mock Boundary Rules

Contract tests MUST mock at the **outermost boundaries** only:

| Boundary | Mock Pattern | Example |
|----------|-------------|---------|
| Database | Mock the session factory, not individual queries | `@pytest.fixture def db_session(): return AsyncMock(spec=AsyncSession)` |
| HTTP client | Mock the httpx client, not individual endpoints | `@pytest.fixture def http_client(): return AsyncMock(spec=httpx.AsyncClient)` |
| File system | Mock the file handle/path, not individual reads | `@pytest.fixture def temp_dir(): ...` |
| Clock/time | Mock `datetime.now()` or `time.time()`, not sleep | `@patch('datetime.datetime.now', return_value=fixed_time)` |

**Rationale:** Outermost-boundary mocking catches integration failures between the feature code and its real dependencies. Deep mocking (e.g., mocking individual SQL queries) passes even when the actual query is broken.

### 4.3 Lint Rules

The following are **forbidden** within `tests/critical_features/`:

| Forbidden | Reason | Enforcement |
|-----------|--------|-------------|
| `@pytest.mark.skip` | Contract tests must never be skipped | Pre-commit lint + CI check |
| `@pytest.mark.xfail` | Contract tests must never be expected to fail | Pre-commit lint + CI check |
| `pytest.skip()` | Runtime skip is also forbidden | Pre-commit lint + CI check |

**Enforcement script** (documented in pattern, implemented per-project):

```bash
#!/bin/bash
# check_contract_tests.sh — run in CI
if grep -rn "pytest.mark.skip\|pytest.mark.xfail\|pytest.skip()" tests/critical_features/; then
  echo "FAIL: skip/xfail found in contract tests"
  exit 1
fi
echo "PASS: no skip/xfail in contract tests"
```

---

## 5. Phase 10 Updates — Business-Level Output Contracts

### 5.1 Additional Requirements for Critical Features

When `criticality: critical`, Phase 10 (Operations) MUST include:

1. **Business-level output contracts** in `site-reliability.md` — not just system metrics. Each contract from `output-contracts.md` must appear in the SLI/SLO section with:
   - SLI: the measurable indicator (e.g., "deduplication success rate")
   - SLO: the target (e.g., "100% — no duplicates in 30d rolling window")
   - Error budget: when to page vs. when to log

2. **Structured violation events.** Each contract must emit a structured event when breached:

```json
{
  "event": "<feature>_<contract>_violation",
  "severity": "critical|warning",
  "timestamp": "2026-04-25T10:30:00Z",
  "feature": "<feature-slug>",
  "contract": "<contract-id>",
  "expected": "<what should have happened>",
  "actual": "<what actually happened>",
  "runbook_url": "https://..."
}
```

3. **Event destinations** (configurable per project):
   - Structured log (always, minimum)
   - Prometheus counter: `<feature>_<contract>_violation_total` with labels `{severity, contract_id}`
   - Alert webhook (optional): Slack, PagerDuty, email

---

## 6. Phase 11 Updates — Critical Feature Contracts CI Step

### 6.1 Named CI Step

Phase 11 pre-deploy gate MUST include a new check:

**Check 13: Critical Feature Contracts**

```bash
# Step 1: Verify contract test directory exists for each critical feature
for slug in $(grep -l "criticality.*critical" features/*/seed.md | xargs -I{} dirname {} | xargs -I{} basename {}); do
  feature_slug=$(echo "$slug" | sed 's/story-[0-9]*-//')
  if [ ! -d "tests/critical_features/$feature_slug/contracts" ]; then
    echo "FAIL: Missing contract tests for critical feature: $feature_slug"
    echo "Expected: tests/critical_features/$feature_slug/contracts/"
    exit 1
  fi
done

# Step 2: Run contract tests (must all pass)
pytest tests/critical_features/ -v --tb=short
if [ $? -ne 0 ]; then
  echo "FAIL: Contract tests failed"
  exit 1
fi

# Step 3: Verify no skip/xfail in contract tests
if grep -rn "pytest.mark.skip\|pytest.mark.xfail\|pytest.skip()" tests/critical_features/; then
  echo "FAIL: skip/xfail found in contract tests"
  exit 1
fi

# Step 4: Verify critical-features.md index is current
if [ ! -f "docs/critical-features.md" ]; then
  echo "FAIL: docs/critical-features.md missing"
  exit 1
fi

echo "PASS: Critical Feature Contracts"
```

### 6.2 Fail-Closed Behavior

- If ANY step in the Critical Feature Contracts check fails, deploy is **BLOCKED**.
- If the check script itself errors (e.g., grep not found), that is a FAIL, not a PASS.
- Missing `tests/critical_features/` directory when critical features exist = FAIL.
- Log message on failure: `CRITICAL: Missing contract tests for critical feature <slug>. Expected directory: tests/critical_features/<slug>/contracts/`

---

## 7. Generic `/api/status` Pattern

### 7.1 JSON Endpoint: `GET /api/status`

```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2026-04-25T10:30:00Z",
  "features": {
    "<feature-slug>": {
      "health": "healthy|degraded|unhealthy",
      "last_success_at": "2026-04-25T10:25:00Z",
      "violation_count_24h": 0,
      "runbook_url": "https://..."
    }
  }
}
```

**Specification details:** See `api-design.md` for the complete endpoint specification.

### 7.2 HTML Endpoint: `GET /status`

- Auto-refreshing table (30s interval)
- No authentication required
- One row per critical feature
- Color-coded: green (healthy), yellow (degraded), red (unhealthy)
- Links to runbook for each feature
- Violation count in last 24h

---

## 8. Generic Grafana Dashboard Template

### 8.1 Layout

One row per critical feature containing:

| Panel | Type | Content |
|-------|------|---------|
| Health Status | Stat | Current health: healthy/degraded/unhealthy with color |
| SLO Compliance | Gauge | % of time in SLO over 30d rolling window |
| Violation Rate | Time series | `<feature>_<contract>_violation_total` rate over time |
| Last Success | Stat | Time since `last_success_at` |
| Runbook Link | Text | Direct link to feature runbook |

### 8.2 Dashboard JSON Template

Documented in `patterns/critical-features.md` with variable substitution:
- `$feature_slug` — kebab-case feature identifier
- `$prometheus_prefix` — project-specific metric prefix
- `$slo_target` — SLO percentage (default: 99.9%)

---

## 9. Discoverability — `docs/critical-features.md`

### 9.1 Template Structure (`templates/critical-features-index.md`)

```markdown
# Critical Features

> Protected features in this project. Each has output contracts, hardened tests,
> runtime monitoring, and a runbook. If you're on call, start here.

| Feature | Status | Contracts | Tests | Dashboard | Runbook | Last Verified |
|---------|--------|-----------|-------|-----------|---------|---------------|
| <name> | /api/status#<slug> | <count> | tests/critical_features/<slug>/ | <link> | <link> | <date> |
```

### 9.2 Requirements

1. Every project using the SDLC framework MUST maintain `docs/critical-features.md`
2. The project's top-level `README.md` MUST link to it
3. Each critical feature MUST have a row in the index
4. The Phase 10c agent verifies the index entry exists
5. The Phase 11 CI gate verifies the file exists

---

## 10. Framework Artifact Changes

### 10.1 Files to Create (NEW)

| File | Purpose |
|------|---------|
| `patterns/critical-features.md` | Canonical pattern documentation — the "one doc" for the entire pattern |
| `templates/output-contracts.md` | Template for output contract definitions |
| `templates/critical-features-index.md` | Template for `docs/critical-features.md` |

### 10.2 Files to Modify (EXISTING)

| File | Change |
|------|--------|
| `templates/seed.md` | Add `Criticality` row to Overview table |
| `agents/phase-1-seed.md` | Add criticality classification to workflow, discovery questions, anti-patterns |
| `agents/phase-7-test-design.md` | Add contract test directory requirement, mock boundary rules, lint rules |
| `agents/phase-10-operations.md` | Add business-level output contract requirements, violation event schema |
| `agents/phase-11-predeploy-gate.md` | Add Check 13: Critical Feature Contracts |
| `AGENTS.md` | Add Critical Features section with classification rules and phase path modifications |
| `software-development-guidance.md` | Document Phase 10c, update deliverables table, update phase path diagrams |
