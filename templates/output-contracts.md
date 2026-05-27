# Output Contracts

## Overview

| Field | Value |
|-------|-------|
| Feature | <feature name, e.g., "Ad Spend Submission"> |
| Story | <story ID, e.g., STORY-592> |
| Owner | <team/person responsible for maintaining these contracts> |
| Criticality | critical |
| Contracts defined | <N> |

## What is an Output Contract?

An output contract is a **business-level assertion** about what a critical feature promises to deliver. It is NOT an HTTP-level invariant (e.g., "returns status 200"). It describes an **observable business outcome** — what a user or downstream system can count on being true.

**Good example:** "Ad spend is submitted to Amazon Ads API before the campaign window closes."
**Bad example:** "API returns 200 OK."

Output contracts are defined here and enforced by contract tests in `tests/critical_features/<slug>/contracts/`.

---

## Contracts Table

| ID | Assertion | Degraded Behavior | Blocking | Test File | Metric |
|----|-----------|-------------------|----------|-----------|--------|
| C1 | <business-level assertion, e.g., "All ad spend records are submitted before the campaign deadline"> | <what happens when the contract is violated, e.g., "Emit violation event; operator paged; retries exhausted before next window"> | false | `tests/critical_features/<slug>/contracts/test_contract_c1.py` | `<feature>_c1_violation` |
| C2 | <next assertion> | <degraded behavior> | false | `tests/critical_features/<slug>/contracts/test_contract_c2.py` | `<feature>_c2_violation` |

**Worked example (C1 — Ad Spend Submission):**

| ID | Assertion | Degraded Behavior | Blocking | Test File | Metric |
|----|-----------|-------------------|----------|-----------|--------|
| C1 | All ad spend records ingested in the current window are submitted to Amazon Ads API before the window deadline | If the API is unreachable, emit `ad_spend_c1_violation`, set health to degraded, retry up to 3x with backoff; alert on-call if all retries fail | true | `tests/critical_features/ad-spend-submission/contracts/test_contract_c1.py` | `ad_spend_c1_violation` |

---

## Blocking Field Semantics

| Value | Meaning |
|-------|---------|
| `true` | Contract failure **blocks deploy** at Phase 11 gate. Use after the contract is proven stable in production. |
| `false` | Contract failure emits a warning but does **not block deploy**. Use during initial adoption while the pattern is new. Graduate to `true` once the test has been GREEN for 2+ sprints. |

**Graduation path:** Start all new contracts at `Blocking: false`. After the contract test runs GREEN for two consecutive sprints in CI, change to `Blocking: true` and merge.

---

## Violation Events

Each contract maps to a structured violation event emitted at runtime when the contract is breached:

```json
{
  "event": "<feature>_<contract_id>_violation",
  "feature": "<feature name>",
  "contract_id": "C1",
  "timestamp": "<ISO 8601>",
  "detail": "<what was detected>",
  "severity": "critical"
}
```

**Event naming convention:** `<feature_slug>_<contract_id_lowercase>_violation`

Example: `ad_spend_c1_violation`

Events are emitted to:
1. Structured log (always)
2. Prometheus counter (`<event_name>_total`)
3. Alert webhook (optional; configure in project's ops config)

---

## Contract Test Structure

Each row in the Contracts Table has a corresponding test file:

```
tests/critical_features/<feature-slug>/contracts/
├── __init__.py
├── conftest.py          # Fixtures: mock boundaries at outermost layer only
├── test_contract_c1.py  # C1: <assertion summary>
└── test_contract_c2.py  # C2: <assertion summary>
```

**Rules:**
- `@pytest.mark.skip` and `@pytest.mark.xfail` are **forbidden** in `contracts/` directories
- Mock boundaries are outermost only: DB session factory and httpx client — never individual queries
- Contract tests must fail for a meaningful business reason, not for import errors

---

## Instructions

1. Copy this template to `docs/output-contracts/<feature-slug>.md` in the consuming project
2. Fill in the Overview table
3. Define at least one contract (C1) with a business-level assertion
4. Create the corresponding test file in `tests/critical_features/<slug>/contracts/`
5. Set `Blocking: false` initially; graduate to `true` after 2 sprints GREEN
6. Link from `docs/critical-features.md` (the project index)
