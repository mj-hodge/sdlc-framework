# Pattern: Critical Features

> **Canonical reference.** Read this document to understand the full critical-feature pattern.
> All SDLC agents operating on a story with `criticality: critical` MUST follow this pattern.
> See also: `templates/output-contracts.md`, `templates/critical-features-index.md`.

---

## 1. Criticality Classification (DP1)

Every story's `seed.md` includes a `Criticality` field set by the Phase 1 BA:

| Level | Criteria | SDLC impact |
|-------|----------|-------------|
| **routine** | No financial transaction, no time-window dependency, no health reporting, no data deduplication | Standard phase path |
| **important** | Affects user experience or system integration but degrades gracefully | Standard phase path + heightened test requirements |
| **critical** | Involves financial transactions, time-window operations (cron jobs, campaign windows), deduplication of write operations, or external health reporting that operators depend on | **Phase 10c fires** — Output Contract Hardening required |

**Default-to-critical rule:** If the feature handles money, advertising spend, time-sensitive submissions, idempotency of writes, or a `/health` endpoint that operators rely on for on-call decisions — classify as `critical`. When in doubt, escalate to `important` or `critical`, never down to `routine`.

**Justification required:** If a feature touches financial data, timing operations, or external health reporting but is classified `routine`, the BA MUST write an explicit justification in `seed.md` explaining why Phase 10c is not needed. This justification is reviewed at Phase 6b (Security Review).

---

## 2. Output Contracts (DP2)

An **output contract** is a business-level assertion about what a critical feature promises to deliver. Unlike technical assertions (HTTP status codes, latency targets), output contracts describe observable business outcomes.

**Template:** `templates/output-contracts.md` — copy to `docs/output-contracts/<feature-slug>.md` in the consuming project.

### Output Contract Structure

Each contract has:
- **ID** (C1, C2, …) — stable identifier used in test file names and metric names
- **Assertion** — business-level statement of what the feature promises
- **Degraded Behavior** — what happens when the contract is violated
- **Blocking** — `true` (blocks deploy) or `false` (warn-only during adoption)
- **Test File** — path to the corresponding contract test
- **Metric** — Prometheus counter name: `<feature>_<contract_id>_violation`

### Business-level vs technical assertions

| Business-level (correct) | Technical (wrong abstraction) |
|--------------------------|-------------------------------|
| "All ad spend records are submitted before the campaign deadline" | "API returns 200 OK" |
| "No duplicate records are inserted for the same source event" | "INSERT does not throw an exception" |
| "Health endpoint reflects actual campaign submission status" | "/healthz returns 200" |

---

## 3. Phase 10c: Output Contract Hardening (DP3)

**Phase 10c** is a new SDLC phase that fires for ALL scope sizes when `seed.md` contains `criticality: critical`. It is positioned between Phase 7 (Test Design) and Phase 8 (Implementation).

### Modified Phase Paths

```
Small (critical):      1 → 7 → 10c → 8 → Done
Medium (critical):     1 → 4 → 6 → [6b, 6c, 6d] → 7 → 10c → 8 → 8b → 11 → Done
Large/New (critical):  1 → 2 → 3 → 4 → 5 → 6 → [6b, 6c, 6d] → 7 → 10c → 8 → 8b → 11 → [9, 10] → Done
```

### What Phase 10c produces

1. **Output contracts defined** — `docs/output-contracts/<slug>.md` populated with C1…Cn
2. **Contract tests written** — `tests/critical_features/<slug>/contracts/test_contract_c*.py` in RED state
3. **Violation event schema** — event names, destinations, Prometheus metric names confirmed
4. **`/api/status` endpoint specified** — JSON schema documented (see §7)
5. **Blocking flags set** — initial `Blocking: false`; graduation schedule noted

Phase 10c is a **gate advance**: it does not auto-advance. The lead engineer confirms all contracts are defined and contract tests are in RED state before Phase 8 begins.

---

## 4. Contract Test Directory (DP4)

All contract tests live under a standardized directory structure:

```
tests/
└── critical_features/
    └── <feature-slug>/
        ├── README.md            # Contract table, mock boundary explanation, run command
        └── contracts/
            ├── __init__.py
            ├── conftest.py      # Outermost-boundary fixtures only
            ├── test_contract_c1.py
            └── test_contract_c2.py
```

### Directory naming

`<feature-slug>` is the kebab-case slug from the story folder: `features/story-XXX-<slug>/`.

Example: `tests/critical_features/ad-spend-submission/contracts/`

### Mock boundary rule

Contract tests mock at the **outermost boundary only**:
- **Database:** Mock the session factory (e.g., `AsyncSession`), not individual queries
- **External HTTP:** Mock the httpx client, not individual endpoints
- **Time:** Mock `datetime.now()` or equivalent at the module level

This ensures contract tests catch failures caused by actual query/schema changes, not just broken mocks.

### Lint enforcement: skip/xfail forbidden (DP4 enforcement)

`@pytest.mark.skip` and `@pytest.mark.xfail` are **forbidden** in all `contracts/` directories. A skipped contract test provides false confidence — it looks GREEN in CI while the business guarantee is unverified.

**Enforcement script** — add to CI and pre-commit:

```bash
#!/bin/bash
# check_contract_lint.sh — fails if skip/xfail found in contracts/ directories
set -e
VIOLATIONS=$(grep -rn --include="*.py" \
  -e "@pytest.mark.skip" \
  -e "@pytest.mark.xfail" \
  -e "pytest.skip(" \
  tests/critical_features/ 2>/dev/null || true)

if [ -n "$VIOLATIONS" ]; then
  echo "ERROR: skip/xfail forbidden in contract tests:"
  echo "$VIOLATIONS"
  exit 1
fi
echo "Contract lint: PASS"
```

Run this in CI before Phase 11 gate. Any xfail or skip marker in `tests/critical_features/` causes CI to fail.

---

## 5. Violation Events (DP5)

When a critical feature breaches an output contract at runtime, it emits a structured violation event:

```json
{
  "event": "<feature_slug>_<contract_id>_violation",
  "feature": "<feature name>",
  "contract_id": "C1",
  "timestamp": "2026-04-25T10:30:00Z",
  "detail": "<what was detected — avoid PII>",
  "severity": "critical"
}
```

**Naming convention:** `<feature_slug>_<contract_id_lowercase>_violation`

Examples:
- `ad_spend_c1_violation`
- `email_column_c2_violation`
- `cron_window_c1_violation`

**Event destinations:**

| Destination | Required | Notes |
|-------------|----------|-------|
| Structured log | Always | Use `structlog` or equivalent; NEVER include PII |
| Prometheus counter | Required | `<event_name>_total` — increment on each violation |
| Alert webhook | Optional | Configure per-project; recommended for `Blocking: true` contracts |

**Direct coupling to `/api/status`:** Emitting a violation event MUST also update the `/api/status` response to reflect `health: degraded` and increment `violation_count_24h`.

---

## 6. Phase 11 CI Gate: Critical Feature Contracts (DP6)

Phase 11 (Pre-Deploy Gate) includes **Check 13: Critical Feature Contracts** as a hard deploy gate.

**Check 13 behavior:**

1. For each story with `criticality: critical` being deployed:
   - Verify `tests/critical_features/<slug>/contracts/` directory exists
   - If the directory is **missing** → **FAIL** (fail-closed: deploy blocked)
   - Run all tests in `contracts/` directory
   - For any contract with `Blocking: true` → test failure **blocks deploy**
   - For any contract with `Blocking: false` → test failure emits `WARN` but does not block

2. **Fail-closed rule:** A missing `contracts/` directory for a critical feature is treated as a failing gate, not a skip. The absence of contract tests is itself a contract violation.

3. **Check script:**

```bash
# check_critical_contracts.sh
SLUG="$1"  # e.g., "ad-spend-submission"
CONTRACTS_DIR="tests/critical_features/${SLUG}/contracts"

if [ ! -d "$CONTRACTS_DIR" ]; then
  echo "FAIL: contracts/ directory missing for critical feature: $SLUG"
  echo "Deploy blocked. Create tests/critical_features/${SLUG}/contracts/ with contract tests."
  exit 1
fi

pytest "$CONTRACTS_DIR" -v --tb=short
```

**Phase 11 gate status:** FAIL if contracts directory missing OR if any `Blocking: true` contract test fails.

This check is referenced in the `Critical Feature Contracts` row of the Phase 11 predeploy-gate checklist.

---

## 7. `/api/status` Endpoint Pattern (DP7)

Every critical feature MUST expose a `/api/status` JSON endpoint. This endpoint:
- Is **publicly readable** (no auth required — on-call operators need it during incidents)
- Is **separate** from `/health` or `/healthz` (health endpoints check infrastructure; `/api/status` checks business feature state)
- Is **in-memory or file-backed** (no DB dependency — must return even when DB is down)

### Required JSON schema

```json
{
  "health": "healthy | degraded | down",
  "last_success_at": "2026-04-25T10:30:00Z",
  "violation_count_24h": 3,
  "runbook_url": "https://docs.gorillacommerce.ai/runbooks/ad-spend-submission"
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `health` | string | `healthy`, `degraded`, or `down` |
| `last_success_at` | ISO 8601 string | Timestamp of the last successful feature operation |
| `violation_count_24h` | integer | Number of contract violation events in the last 24 hours |
| `runbook_url` | string | URL to the runbook for this feature |

**On restart:** Default to `health: degraded` and `last_success_at: null` until the feature completes its first successful operation after startup. Never assume the last pre-restart state.

**Multi-replica note:** Each replica maintains independent in-memory state. Use a shared file or Redis for `violation_count_24h` if replica consistency is required.

### `/status` HTML page

In addition to the JSON endpoint, expose a `/status` HTML page for browser-based on-call triage:
- Auto-refreshes every 30 seconds
- Color-coded by health state (use accessibility symbols, not color alone: ✓ = healthy, ⚠ = degraded, ✗ = down)
- No authentication required
- Links to the runbook URL

---

## 8. Grafana Dashboard Template (DP8)

Each critical feature should have a Grafana dashboard panel showing:
- `violation_count_24h` as a gauge or time series
- Health state transitions as annotations
- `last_success_at` as a stat panel

**Variable-substituted dashboard JSON template:**

```json
{
  "panels": [
    {
      "title": "${FEATURE_SLUG} Violations (24h)",
      "type": "stat",
      "targets": [{ "expr": "${FEATURE_SLUG}_violation_total" }]
    },
    {
      "title": "${FEATURE_SLUG} Health",
      "type": "gauge",
      "targets": [{ "expr": "up{job=\"${FEATURE_SLUG}\"}" }]
    }
  ]
}
```

Replace `${FEATURE_SLUG}` with the feature slug (e.g., `ad_spend`). Import into Grafana via the Dashboard → Import → JSON model flow.

---

## 9. `docs/critical-features.md` Project Index (DP9)

Every consuming project MUST maintain `docs/critical-features.md` — the single discoverable index of all critical features in that project.

- **Template:** `templates/critical-features-index.md` → copy to `docs/critical-features.md`
- **README link required:** The project README must link to this file: `[Critical Features](docs/critical-features.md)`
- **On-call use:** During incidents, operators open this file to find status endpoints and runbooks in under 30 seconds

The index is updated at Phase 10c completion for each new critical feature story.

---

## 10. AGENTS.md and Persona Updates (DP10)

The framework's `AGENTS.md` and the following agent persona files are updated to embed critical-feature requirements:

| File | What was added |
|------|---------------|
| `AGENTS.md` | `## Critical Features` section with classification rules, Phase 10c in phase paths, link to this document |
| `agents/phase-1-seed.md` | Criticality classification step in Workflow; all three levels with criteria; justification requirement for `routine` on financial/timing features |
| `agents/phase-7-test-design.md` | Contract test directory structure (`tests/critical_features/<slug>/contracts/`); outermost-boundary mock rule; skip/xfail prohibition; lint enforcement mechanism |
| `agents/phase-10-operations.md` | Business-level output contracts section; violation event schema; event destinations |
| `agents/phase-11-predeploy-gate.md` | Check 13 (Critical Feature Contracts); fail-closed behavior for missing contracts/ directory |

**Purpose:** Agents running these phases will apply the pattern automatically without reading the full pattern document. The persona updates make the pattern self-enforcing across all Gorilla Commerce projects that consume this framework.

---

## Summary: 10 Design Points

| DP | What | Where |
|----|------|-------|
| DP1 | Criticality field in `seed.md` — routine/important/critical | `templates/seed.md` |
| DP2 | Output contracts template — business assertions, Blocking flag | `templates/output-contracts.md` |
| DP3 | Phase 10c (Output Contract Hardening) in SDLC phase paths | `AGENTS.md`, this doc |
| DP4 | Contract test directory: `tests/critical_features/<slug>/contracts/` | Consuming project |
| DP5 | Structured violation events — naming, destinations, Prometheus | Consuming project |
| DP6 | Phase 11 CI gate: Critical Feature Contracts — fail-closed | `agents/phase-11-predeploy-gate.md` |
| DP7 | `/api/status` JSON endpoint — standardized schema | Consuming project |
| DP8 | Grafana dashboard template — violation counter, health panels | This doc |
| DP9 | `docs/critical-features.md` project index — on-call reference | `templates/critical-features-index.md` |
| DP10 | `AGENTS.md` + persona updates — self-enforcing pattern | Framework files |
