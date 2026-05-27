# MCP Cross-Project Deployment Standards

Canonical reference for shared patterns across all MCP server deployments.
Extracted from datalake and advertising-amazon (formerly mcp-datalake and mcp-advertising-amazon; EPIC-002, STORY-023).
Apply these standards when building or reviewing any new MCP server.

---

## Health Endpoint Pattern

Every MCP server MUST implement both endpoints:

| Endpoint | Purpose | ACA probe type | Returns 200 when |
|----------|---------|---------------|-----------------|
| `GET /health` | Liveness — is the process alive? | Liveness | Process is running and can handle requests |
| `GET /health/ready` | Readiness — can traffic be routed? | Readiness | All adapters/connections are healthy |

**Liveness response (minimal):**
```json
{"status": "ok", "uptime_seconds": 3600}
```

**Readiness response (detailed):**
```json
{
  "status": "ready",
  "checks": {
    "sql_adapter": "ok",
    "blob_adapter": "ok",
    "auth_jwks": "ok"
  }
}
```

**Rules:**
- `GET /health` MUST NOT check external dependencies (SQL, APIs) — only process health
- `GET /health/ready` MUST check all adapters and return 503 if any are down
- Both endpoints MUST be exempt from auth middleware (unauthenticated access required for ACA probes)
- Use Python `urllib` for Dockerfile HEALTHCHECK, not `curl` (curl not available in slim images)

**Dockerfile pattern:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

---

## Metrics Label Policy (No PII)

**Rule:** Prometheus metric labels MUST NEVER contain personally identifiable information.

| Allowed labels | Forbidden labels |
|---------------|-----------------|
| `tool_name`, `status`, `adapter`, `error_type` | `user_id`, `caller_id`, `email`, `username` |
| `job`, `instance`, `environment` | `ip_address`, `session_id`, `tenant_id` (if maps to a person) |
| `reason` (generic, e.g. "invalid_token") | Any value that could identify an individual |

**Rationale:** Prometheus data is often scraped by monitoring systems with broad access. PII in labels creates GDPR/data handling risk and may violate data residency requirements.

**Example — correct instrumentation:**
```python
# CORRECT — generic status
mcp_tool_calls_total.labels(tool_name="query_dataset", status="error").inc()

# WRONG — caller identity in label
mcp_tool_calls_total.labels(tool_name="query_dataset", caller_id="user@company.com").inc()
```

---

## Log Redaction Pattern (ScrubProcessor)

All MCP servers MUST redact sensitive values from structured logs using a `ScrubProcessor`.

> **Drop-in module available:** For a complete drop-in logging module with correlation IDs, environment-based configuration, and sensitive key redaction, copy `templates/backend/core-logging.py` into your project's `core/logging.py`. The pattern below is a minimal reference; prefer the full module for new projects.

**Pattern (Python + structlog):**
```python
import re
import structlog

SCRUB_PATTERNS = [
    # Connection strings (ODBC, JDBC, SQLAlchemy)
    re.compile(r'(password|pwd|Password)=[^;]+', re.IGNORECASE),
    re.compile(r'AccountKey=[A-Za-z0-9+/=]+', re.IGNORECASE),
    # Bearer tokens
    re.compile(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', re.IGNORECASE),
    # Azure SAS tokens
    re.compile(r'sig=[A-Za-z0-9%]+'),
]
REDACTED = "[REDACTED]"

class ScrubProcessor:
    """Structlog processor that redacts secrets from log values."""

    def __call__(self, logger, method, event_dict):
        for key, value in event_dict.items():
            if isinstance(value, str):
                for pattern in SCRUB_PATTERNS:
                    value = pattern.sub(REDACTED, value)
                event_dict[key] = value
        return event_dict

# Registration
structlog.configure(
    processors=[
        ScrubProcessor(),
        structlog.processors.JSONRenderer(),
    ]
)
```

**What to scrub:**
- SQL connection strings (passwords, AccountKey, SAS tokens)
- Bearer tokens and API keys
- Azure storage connection strings
- Any value containing `password`, `secret`, `key`, `token` in the key name

---

## Alert Rule Naming Convention

Alert names use PascalCase with the prefix `MCP` + server scope:

```
MCP<Scope><Condition>

Examples:
  MCPServerDown
  MCPHighErrorRate
  MCPCriticalLatency
  MCPErrorBudgetBurn6x
  MCPAuthFailureSpike
```

**Required labels on all MCP alerts:**

| Label | Value | Description |
|-------|-------|-------------|
| `severity` | `warning` or `critical` | Routing to notification channel |
| `server` | `{dept}-{product}` | Which server/app fired (repo name, e.g. `advertising-amazon`) |
| `team` | `platform` | Owning team for routing |

**Optional labels:**

| Label | When to use |
|-------|------------|
| `slo` | SLO burn rate alerts (e.g. `99-availability`) |
| `security` | Auth anomaly alerts that may indicate attacks |

**Severity definitions:**

| Severity | Meaning | Response time |
|----------|---------|--------------|
| `warning` | Degraded but not down, budget burning | < 30 min |
| `critical` | Down or imminent SLO breach | < 5 min, page on-call |

---

## Bicep Module Usage

All MCP server infrastructure MUST use the shared Bicep modules from `.sdlc/templates/infra/modules/`.

**Standard resource set for every MCP server:**

| Module | Resource name pattern | Notes |
|--------|--------------------|-------|
| `managed-identity.bicep` | `id-{dept}-{product}` | Required — ACR pull + KV read |
| `log-analytics.bicep` | `log-{dept}-{product}` | Required — ACA log destination |
| `container-registry.bicep` | `acr{dept}{product}` | Required — image storage |
| `key-vault.bicep` | `kv-{dept}-{product}` | Required — secrets at rest |
| `container-app.bicep` | `ca-{dept}-{product}` | Required — runtime |

**Inline resources (not modularized — tightly coupled):**
- `Microsoft.App/managedEnvironments` — defined in `main.bicep` (needs log analytics shared key)
- `Microsoft.Authorization/roleAssignments` — defined in `main.bicep` (scope varies per project)

**Process:**
1. Copy `main.bicep.template` → `infra/main.bicep`
2. Copy `modules/` → `infra/modules/`
3. Replace placeholders (see template TODOs)
4. Add project-specific parameters and secrets

---

## CI/CD Pipeline Pattern

Every MCP server MUST implement this GitHub Actions pipeline structure:

```
push to main
  └── test          (pytest, --tb=short, coverage gate 80%)
  └── build         (docker buildx, multi-platform if needed)
  └── push          (docker push to ACR, tag: sha + latest)
  └── deploy        (az containerapp update --image)
  └── smoke         (GET /health/ready returns 200, GET /metrics returns 200)
```

**Required smoke tests (minimum):**
```bash
# Health check
curl -f "https://${APP_FQDN}/health/ready"

# Metrics endpoint
curl -f "https://${APP_FQDN}/metrics" | grep -q "mcp_tool_calls_total"

# Optional: tool call smoke test (unauthenticated tools/list)
curl -s -X POST "https://${APP_FQDN}/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | jq -e '.result.tools | length > 0'
```

**Infra preview on PRs:**
- Run `az deployment group what-if` on every PR that changes `infra/*.bicep`
- Block merge if what-if fails (misconfigured Bicep)
- Post what-if diff as PR comment

---

## Docker Image Standards

| Requirement | Pattern |
|------------|---------|
| Base image | `python:3.12-slim` (or `mcr.microsoft.com/devcontainers/python:3.12-bookworm` for dev) |
| ODBC driver | Install `msodbcsql18` in Dockerfile if SQL adapters are needed |
| HEALTHCHECK | Use Python `urllib`, not `curl` |
| Non-root user | Run as `appuser` (UID 1000), not root |
| Multi-stage | `build` stage → `runtime` stage (no dev deps in final image) |
| Image tags | Always tag with git SHA + `latest`; never deploy untagged images |

---

## Standardized Logging Requirements (All Projects)

Every project (not just MCP servers) MUST implement structured logging following these standards:

### Required Fields

Every log event MUST include:

| Field | Source | Example |
|-------|--------|---------|
| `timestamp` | Auto (structlog TimeStamper) | `2026-03-23T14:30:00Z` |
| `level` | Auto (structlog add_log_level) | `info`, `error`, `warning` |
| `service` | Set at startup via `configure_logging()` | `mcp-datalake` |
| `logger` | Auto (structlog add_logger_name) | `app.routes.datasets` |
| `event` | First argument to log call | `tool_call_completed` |
| `trace_id` | Auto (CorrelationIdProcessor) | `550e8400-e29b-41d4-a716-446655440000` |

### Log Level Policy

| Level | When to Use | Example |
|-------|------------|---------|
| `DEBUG` | Detailed diagnostic info (disabled in production) | SQL queries, request payloads |
| `INFO` | Normal operations worth recording | Request handled, task completed, startup/shutdown |
| `WARNING` | Unexpected but recoverable situations | Retry triggered, deprecated API used, slow query |
| `ERROR` | Failures requiring attention | Unhandled exception, external API failure, data corruption |
| `CRITICAL` | System-wide failures | Database unreachable, out of memory, data loss |

### Setup Checklist

- [ ] Copy `templates/backend/core-logging.py` → `core/logging.py` (or equivalent path)
- [ ] Call `configure_logging(service_name="your-service")` at app startup
- [ ] Add correlation ID middleware (see template docstring for FastAPI example)
- [ ] Set `LOG_LEVEL` env var in deployment config (default: INFO)
- [ ] Set `LOG_FORMAT=console` for local development (colored output)
- [ ] Verify no secrets appear in log output (ScrubProcessor handles common patterns)
- [ ] Add project-specific SCRUB_PATTERNS if needed (e.g., custom API keys)

---

## Tech Dashboard Registration

Every project MUST be registered in the org-wide tech dashboard during Phase 10 (Operations). This is a hard requirement — unregistered projects are invisible to on-call responders and org-level SLO tracking.

### Requirements

| Requirement | Details |
|-------------|---------|
| Register in `project-registry.yaml` | Add an entry to `templates/monitoring/project-registry.yaml` in the SDLC framework repo |
| Expose `/metrics` | Prometheus-format metrics endpoint — required for scraping |
| Expose `/health` | Liveness endpoint — used by the Health Status row of the tech dashboard |
| Add Prometheus scrape job | Add the project as a named job in the org-level `prometheus.yml` |

### How to register

1. Open `templates/monitoring/project-registry.yaml` in the SDLC framework repo.
2. Add your project entry following the schema:

```yaml
- name: mcp-your-server
  job_name: mcp-your-server          # Must match the Prometheus job_name exactly
  type: mcp-server                   # mcp-server | backend-api | frontend | worker
  tier: standard                     # essential | standard | premium | critical
  team: platform                     # Owning team — used for alert routing
  metrics_endpoint: https://ca-mcp-your-server.example.com/metrics
  health_endpoint: https://ca-mcp-your-server.example.com/health
  repo: https://github.com/YOUR-ORG/mcp-your-server
```

3. Add the corresponding Prometheus scrape job (see `prometheus/prometheus.yml.template` — Multi-project section).
4. Commit both changes together so the registry and scrape config stay in sync.
5. Verify the project appears in the **Tech Dashboard — All Projects** dashboard (`tech-dashboard-001`) in Grafana.

### The tech dashboard

The tech dashboard (`grafana/dashboards/multi-project-overview.json`, UID `tech-dashboard-001`) is the single pane of glass for the entire org. It aggregates:

- Fleet-wide up/down count and total tool call volume
- Per-project error rates (timeseries + worst-case gauge)
- Per-project p95 latency
- Per-project health status (green/red stat panels)

The `$job` template variable selects all registered projects by default (multi-select, `includeAll: true`). On-call engineers use this dashboard as their first stop during incident triage.

**Failure to register blocks Phase 10 sign-off.**

---

## Version History

| Date | Change | Story |
|------|--------|-------|
| 2026-03-23 | Added tech dashboard registration and multi-project standards | — |
| 2026-03-23 | Added standardized logging module and all-project logging requirements | — |
| 2026-03-21 | Initial extraction from mcp-datalake + mcp-advertising-amazon | STORY-023 |
