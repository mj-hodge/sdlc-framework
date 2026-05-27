# Shared MCP Monitoring Templates

Reusable Prometheus + Grafana monitoring templates for MCP server deployments.
Extracted from datalake and advertising-amazon patterns (EPIC-002, STORY-022).

## Contents

| File | Purpose |
|------|---------|
| `prometheus/prometheus.yml.template` | Prometheus scrape config with MCP job and alert rules |
| `grafana/dashboards/mcp-base-dashboard.json` | Grafana dashboard with 4 rows: tool calls, error rate, latency, adapter health |
| `grafana/alerts/mcp-base-rules.yml` | 8 Prometheus alert rules covering availability, error rate, latency, error budget, auth |

## Quick Start

### 1. Copy and configure templates

```bash
# In your project root:
mkdir -p monitoring/prometheus monitoring/grafana/dashboards monitoring/grafana/alerts

cp ~/.sdlc/templates/monitoring/prometheus/prometheus.yml.template monitoring/prometheus.yml
cp ~/.sdlc/templates/monitoring/grafana/dashboards/mcp-base-dashboard.json monitoring/grafana/dashboards/
cp ~/.sdlc/templates/monitoring/grafana/alerts/mcp-base-rules.yml monitoring/grafana/alerts/mcp-rules.yml

# Replace placeholders
# SERVER_NAME follows the pattern: {type}-{dept}-{product} for MCP servers
#   e.g. datalake-mcp, mcp-advertising-amazon
SERVER_NAME="datalake-mcp"
sed -i "s/<SERVER_NAME>/$SERVER_NAME/g; s/<JOB_NAME>/$SERVER_NAME/g" \
  monitoring/prometheus.yml \
  monitoring/grafana/alerts/mcp-rules.yml
```

### 2. Set your server's metrics host and port

Edit `monitoring/prometheus.yml`:
```yaml
static_configs:
  - targets: ["localhost:8000"]  # or your ACA FQDN
```

### 3. Start Prometheus + Grafana

```bash
# Using docker compose (add to your compose.yml or compose.override.yaml):
services:
  prometheus:
    image: prom/prometheus:v2.52.0
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/grafana/alerts:/etc/prometheus/alerts:ro
    ports: ["9090:9090"]
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.retention.time=30d

  grafana:
    image: grafana/grafana:11.1.0
    environment:
      GF_SECURITY_ADMIN_PASSWORD: "${GRAFANA_PASSWORD:-admin}"
    volumes:
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
      - grafana-data:/var/lib/grafana
    ports: ["3000:3000"]
```

### 4. Import the dashboard

**Option A: Auto-provision** (recommended)
```yaml
# monitoring/grafana/provisioning/dashboards.yml
apiVersion: 1
providers:
  - name: mcp-dashboards
    folder: MCP
    type: file
    options:
      path: /var/lib/grafana/dashboards
```

**Option B: Manual import**
Grafana → Dashboards → Import → Upload `mcp-base-dashboard.json`

## Dashboard Template Variables

The dashboard uses two template variables configured in Grafana UI:

| Variable | Type | Query | Description |
|----------|------|-------|-------------|
| `$datasource` | Datasource | `prometheus` | Prometheus datasource to use |
| `$job` | Query | `label_values(mcp_tool_calls_total, job)` | MCP server job name |

These auto-populate from your Prometheus data — no manual configuration needed after import.

## Alert Rules Reference

| Alert | Severity | Condition | Window |
|-------|----------|-----------|--------|
| `MCPServerDown` | critical | `up == 0` | 2m |
| `MCPHighErrorRate` | warning | error rate > 1% | 5m |
| `MCPCriticalErrorRate` | critical | error rate > 10% | 2m |
| `MCPHighLatency` | warning | p99 > 10s | 5m |
| `MCPCriticalLatency` | critical | p99 > 30s | 2m |
| `MCPErrorBudgetBurn6x` | warning | 6x SLO burn (1h window) | 5m |
| `MCPErrorBudgetBurn14x` | critical | 14x SLO burn (5m window) | 2m |
| `MCPAuthFailureSpike` | warning | > 10 failures/min | 3m |
| `MCPAuthFailureCritical` | critical | > 50 failures/min | 2m |

**SLO baseline:** 99% success rate (1% error budget per week).

## Required Metrics

Your MCP server must expose these metrics for the templates to work:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `mcp_tool_calls_total` | counter | `job`, `tool_name`, `status` | Tool call count by outcome |
| `mcp_tool_call_duration_seconds` | histogram | `job`, `tool_name` | Tool call latency |
| `mcp_auth_failures_total` | counter | `job`, `reason` | Auth rejection count |
| `mcp_adapter_query_duration_seconds` | histogram | `job`, `adapter` | Adapter query latency |
| `mcp_adapter_errors_total` | counter | `job`, `adapter`, `error_type` | Adapter-level errors |
| `mcp_active_connections` | gauge | `job` | Active MCP connections |

**Label policy:** Never include PII in labels. No `user_id`, `caller_id`, `email`, or IP in metric labels.
See `cross-project-standards.md` for the full label policy.

## Multi-Project Tech Dashboard

The tech dashboard (`multi-project-overview.json`) provides an org-wide single pane of glass showing the health, error rate, and latency of every registered project simultaneously.

### What it shows

- **Fleet Overview** — how many projects are up vs. down, and total tool call volume across the fleet in the last hour
- **Error Rate by Project** — per-project error rate timeseries plus a gauge showing the worst current error rate across all projects
- **Latency by Project** — p95 latency timeseries per project
- **Health Status** — one stat panel per project (green=UP, red=DOWN), auto-repeated from the `$job` variable

### Setup

**Step 1: Configure Prometheus to scrape all projects**

Add a separate scrape job for each project in `prometheus.yml`. See the `# Multi-project monitoring (tech dashboard)` section in `prometheus/prometheus.yml.template` for static and file-discovery options.

**Step 2: Register projects in the registry**

Add each project to `project-registry.yaml` so the catalog stays current:

```yaml
projects:
  - name: datalake-mcp
    job_name: datalake-mcp
    type: mcp-server
    tier: standard
    team: platform
    metrics_endpoint: https://mcp-datalake.gorillacommerce.ai/metrics
    health_endpoint: https://mcp-datalake.gorillacommerce.ai/health
    repo: https://github.com/hpi-gorillacommerce/datalake
```

**Step 3: Import the dashboard**

```bash
# Option A: Auto-provision (copy alongside mcp-base-dashboard.json)
cp ~/.sdlc/templates/monitoring/grafana/dashboards/multi-project-overview.json \
   monitoring/grafana/dashboards/

# Option B: Manual import
# Grafana → Dashboards → Import → Upload multi-project-overview.json
```

**Step 4: Select all projects**

The `$job` variable defaults to `All` (regex `.*`), so the dashboard shows every scraped job immediately after import. Use the variable dropdown to filter to a subset of projects.

### Template variables

| Variable | Type | Query | Default |
|----------|------|-------|---------|
| `$datasource` | Datasource | `prometheus` | — (auto-selected) |
| `$job` | Query | `label_values(up, job)` | All (multi-select) |

### Dashboard metadata

| Field | Value |
|-------|-------|
| UID | `tech-dashboard-001` |
| Title | Tech Dashboard — All Projects |
| Tags | `tech-dashboard`, `multi-project`, `overview` |
| Refresh | 30s |

---

## Alertmanager Routing (example)

```yaml
# alertmanager.yml — route MCP alerts to the platform team
route:
  receiver: default
  routes:
    - matchers:
        - team = platform
      receiver: platform-slack
    - matchers:
        - severity = critical
        - security = true
      receiver: security-pagerduty

receivers:
  - name: platform-slack
    slack_configs:
      - api_url: "${SLACK_WEBHOOK_URL}"
        channel: "#platform-alerts"
        title: "{{ .CommonLabels.alertname }} — {{ .CommonLabels.server }}"
  - name: security-pagerduty
    pagerduty_configs:
      - routing_key: "${PAGERDUTY_KEY}"
```
