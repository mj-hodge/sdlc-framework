# Critical Features Index

> **On-call quick reference.** During an incident, find the relevant feature here to reach its status endpoint, runbook, and contract tests in under 30 seconds.
>
> **Incident triage:** If you're responding to a production alert and don't know which feature is affected, scan the Status column. Any feature showing `degraded` or `down` is your starting point.
>
> Copy this template to `docs/critical-features.md` in the consuming project.
> README must link to this file: `[Critical Features](docs/critical-features.md)`.

---

## Protected Features

| Feature | Story | Criticality | Status Endpoint | Contracts | Tests | Dashboard | Runbook | Last Verified |
|---------|-------|-------------|-----------------|-----------|-------|-----------|---------|---------------|
| <Feature Name> | STORY-XXX | critical | `GET /api/status` | `docs/output-contracts/<slug>.md` | `tests/critical_features/<slug>/contracts/` | [Grafana](#) | [Runbook](#) | YYYY-MM-DD |

---

## How to Add a New Feature

1. Add a row to the table above when a story with `criticality: critical` completes Phase 10c
2. Link the Status Endpoint, Contracts doc, Tests directory, Dashboard, and Runbook
3. Set Last Verified to the date Phase 10c was completed
4. Update Last Verified each time contracts are reviewed

---

## On-Call Guidance

### If a feature shows degraded status:

1. Open the **Runbook** link for the affected feature
2. Check the **Status Endpoint** (`GET /api/status`) — read `violation_count_24h` and `last_success_at`
3. Check the **Dashboard** for the violation counter trend
4. If `violation_count_24h > 0`, the feature has breached one or more output contracts

### Status endpoint fields:

```json
{
  "health": "healthy | degraded | down",
  "last_success_at": "<ISO 8601 timestamp of last successful operation>",
  "violation_count_24h": <integer — number of contract violations in last 24h>,
  "runbook_url": "<link to runbook for this feature>"
}
```

### Incident response:

- `health: healthy` — feature operating normally; check other signals
- `health: degraded` — feature degraded; partial functionality may be intact; check runbook
- `health: down` — feature non-functional; escalate immediately per runbook

---

## Maintenance

- **Review frequency:** Update Last Verified after each sprint demo or whenever contracts change
- **Ownership:** The team who owns the story is responsible for keeping the row current
- **Decommissioning:** If a feature is removed, strike through the row and add `(decommissioned YYYY-MM-DD)` — do not delete; the history is useful during incident post-mortems
