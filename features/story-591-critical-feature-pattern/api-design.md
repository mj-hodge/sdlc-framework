# API Design — STORY-591: Critical-Feature SDLC Pattern

## Overview

This document specifies two endpoint patterns that every consuming project with critical features MUST implement. These are **pattern specifications** — the actual implementation is per-project (e.g., STORY-592 for advertising-amazon).

---

## 1. `GET /api/status` — Critical Feature Health (JSON)

### Purpose

Machine-readable health status of all critical features. Designed for monitoring systems, Grafana dashboards, and automated health checks.

### Request

```
GET /api/status
Accept: application/json
```

- **Authentication:** None required (public read-only)
- **Rate limiting:** Recommended 60 req/min (pattern guidance, not enforced by framework)

### Response — 200 OK (Healthy/Degraded)

```json
{
  "status": "healthy",
  "timestamp": "2026-04-25T10:30:00Z",
  "project": "advertising-amazon",
  "features": {
    "sp-report-sync": {
      "health": "healthy",
      "last_success_at": "2026-04-25T10:25:00Z",
      "violation_count_24h": 0,
      "runbook_url": "https://github.com/org/repo/blob/main/docs/runbooks/sp-report-sync.md"
    },
    "cron-spend-sync": {
      "health": "degraded",
      "last_success_at": "2026-04-25T04:15:00Z",
      "violation_count_24h": 2,
      "runbook_url": "https://github.com/org/repo/blob/main/docs/runbooks/cron-spend-sync.md"
    }
  }
}
```

### Response Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | enum | yes | Aggregate: `healthy` (all features healthy), `degraded` (any feature degraded), `unhealthy` (any feature unhealthy) |
| `timestamp` | ISO 8601 | yes | Time this response was generated |
| `project` | string | yes | Project identifier |
| `features` | object | yes | Map of feature-slug → feature status |
| `features.<slug>.health` | enum | yes | `healthy`, `degraded`, `unhealthy` |
| `features.<slug>.last_success_at` | ISO 8601 | yes | Last time the feature completed successfully |
| `features.<slug>.violation_count_24h` | integer | yes | Number of contract violations in the last 24 hours |
| `features.<slug>.runbook_url` | URL | yes | Direct link to the feature's runbook |

### Aggregate Status Logic

```
if ANY feature.health == "unhealthy":
    status = "unhealthy"
elif ANY feature.health == "degraded":
    status = "degraded"
else:
    status = "healthy"
```

### Response — 503 Service Unavailable (Status Check Failed)

If the status endpoint itself encounters an error (e.g., cannot read contract state):

```json
{
  "status": "degraded",
  "timestamp": "2026-04-25T10:30:00Z",
  "error": "status_check_failed",
  "message": "Unable to read contract state. Defaulting to degraded."
}
```

**Critical rule:** The status endpoint MUST NEVER silently return `"healthy"` when it cannot determine actual health. Fail to degraded, not to healthy.

### Health Determination Rules

| Condition | Health Value |
|-----------|-------------|
| No violations in 24h AND last_success_at within expected interval | `healthy` |
| 1+ violations in 24h but feature is still producing output | `degraded` |
| Feature has not succeeded within 2× expected interval OR blocking violation active | `unhealthy` |
| Cannot determine (state read failure) | `degraded` |

### Implementation Constraints

- **No database calls at request time.** Health state is read from an in-memory dict or local file updated by the contract checker. This prevents the status endpoint from being affected by database outages.
- **No external API calls at request time.** Status is pre-computed, not live-queried.
- **Response time target:** < 500ms (p95).
- **No PII or secrets in response.** Only feature health metadata.
- **No runbook content inline.** Link to runbook URL only.

---

## 2. `GET /status` — Critical Feature Health (HTML)

### Purpose

Human-readable health dashboard for on-call operators and stakeholders. Auto-refreshing table view.

### Request

```
GET /status
Accept: text/html
```

- **Authentication:** None required
- **Content-Type:** `text/html; charset=utf-8`

### Response — HTML Page

```html
<!DOCTYPE html>
<html>
<head>
  <title>Critical Features — {project}</title>
  <meta http-equiv="refresh" content="30">
  <style>
    /* Minimal inline CSS — no external dependencies */
    table { border-collapse: collapse; width: 100%; font-family: monospace; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    .healthy { background-color: #d4edda; }
    .degraded { background-color: #fff3cd; }
    .unhealthy { background-color: #f8d7da; }
    .timestamp { color: #666; font-size: 0.9em; }
  </style>
</head>
<body>
  <h1>Critical Features — {project}</h1>
  <p class="timestamp">Last updated: {timestamp} | Auto-refresh: 30s</p>
  <table>
    <thead>
      <tr>
        <th>Feature</th>
        <th>Health</th>
        <th>Last Success</th>
        <th>Violations (24h)</th>
        <th>Runbook</th>
      </tr>
    </thead>
    <tbody>
      <!-- One row per critical feature, sorted by health (unhealthy first) -->
      <tr class="{health}">
        <td>{feature-name}</td>
        <td>{health}</td>
        <td>{last_success_at}</td>
        <td>{violation_count_24h}</td>
        <td><a href="{runbook_url}">Runbook</a></td>
      </tr>
    </tbody>
  </table>
</body>
</html>
```

### HTML Requirements

| Requirement | Detail |
|-------------|--------|
| Auto-refresh | `<meta http-equiv="refresh" content="30">` — 30 second interval |
| No JavaScript required | Works in any browser, including text-based |
| No external CSS/JS | Inline styles only — no CDN dependencies |
| No authentication | Public page |
| Sort order | Unhealthy first, then degraded, then healthy |
| Color coding | Green (#d4edda) = healthy, Yellow (#fff3cd) = degraded, Red (#f8d7da) = unhealthy |
| Load time target | < 2s |

---

## 3. Violation Event Schema

### Structured Event Format

Emitted when a contract is breached at runtime:

```json
{
  "event": "sp_report_duplicate_blob_violation",
  "severity": "critical",
  "timestamp": "2026-04-25T10:30:00Z",
  "feature": "sp-report-sync",
  "contract": "C1",
  "contract_name": "deduplication",
  "expected": "No duplicate blobs for (report_type, date, profile_id)",
  "actual": "Duplicate blob detected: report_type=sp, date=2026-04-24, profile_id=12345",
  "runbook_url": "https://github.com/org/repo/blob/main/docs/runbooks/sp-report-sync.md"
}
```

### Event Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event` | string | yes | Event name: `<feature_slug>_<contract_name>_violation` |
| `severity` | enum | yes | `critical` (blocking contract breached) or `warning` (non-blocking contract breached) |
| `timestamp` | ISO 8601 | yes | When the violation was detected |
| `feature` | string | yes | Feature slug (kebab-case) |
| `contract` | string | yes | Contract ID from output-contracts.md (e.g., "C1") |
| `contract_name` | string | yes | Human-readable contract name |
| `expected` | string | yes | What should have happened |
| `actual` | string | yes | What actually happened |
| `runbook_url` | URL | yes | Link to the relevant runbook |

### Event Naming Convention

```
<feature_slug>_<contract_name>_violation
```

Examples:
- `sp_report_sync_duplicate_blob_violation`
- `cron_spend_sync_missed_window_violation`
- `campaign_report_blank_email_violation`
- `healthz_revision_roll_misreport_violation`

### Prometheus Counter

```
# HELP <feature>_<contract>_violation_total Count of contract violations
# TYPE <feature>_<contract>_violation_total counter
<feature>_<contract>_violation_total{severity="critical",contract_id="C1"} 1
```

---

## 4. Grafana Dashboard Template

### Dashboard Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `$project` | (required) | Project name |
| `$feature_slug` | (required) | Feature slug |
| `$prometheus_prefix` | (project-specific) | Metric prefix |
| `$slo_target` | `0.999` | SLO target percentage |
| `$runbook_base_url` | (project-specific) | Base URL for runbooks |

### Row Template (per critical feature)

```json
{
  "title": "$feature_slug",
  "panels": [
    {
      "title": "Health",
      "type": "stat",
      "targets": [{"expr": "up{job=\"$project\", feature=\"$feature_slug\"}"}],
      "thresholds": {"steps": [
        {"value": 0, "color": "red"},
        {"value": 0.5, "color": "yellow"},
        {"value": 1, "color": "green"}
      ]}
    },
    {
      "title": "SLO Compliance (30d)",
      "type": "gauge",
      "targets": [{"expr": "1 - (sum(rate(${feature_slug}_violation_total[30d])) / scalar(count_over_time(up{feature=\"$feature_slug\"}[30d])))"}],
      "thresholds": {"steps": [
        {"value": 0, "color": "red"},
        {"value": "$slo_target", "color": "green"}
      ]}
    },
    {
      "title": "Violations (rate)",
      "type": "timeseries",
      "targets": [{"expr": "sum(rate(${feature_slug}_violation_total[5m])) by (contract_id)"}]
    },
    {
      "title": "Last Success",
      "type": "stat",
      "targets": [{"expr": "time() - ${feature_slug}_last_success_timestamp"}],
      "unit": "s"
    },
    {
      "title": "Runbook",
      "type": "text",
      "content": "[$feature_slug Runbook]($runbook_base_url/$feature_slug.md)"
    }
  ]
}
```

---

## 5. Follow-ups

- **STORY-592:** Implement these patterns in advertising-amazon (first consumer)
- **Future:** OpenAPI spec generation from the `/api/status` schema
- **Future:** Slack bot integration that queries `/api/status` on demand
