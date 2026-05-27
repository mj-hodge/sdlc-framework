```markdown
# Site Reliability — PropertySearch API

## System Overview

| Component | Technology | Health Endpoint |
|-----------|-----------|-----------------|
| API Server | FastAPI on Cloud Run | /health, /health/ready |
| Database | PostgreSQL (Neon) | /health/ready checks |
| Cache | Redis (Upstash) | /health/ready checks |
| Search | Elasticsearch | /health/ready checks |
| Background Jobs | Celery + Redis | /health/detailed |

## SLIs and SLOs

| SLI | Measurement | SLO | Error Budget (30d) |
|-----|-------------|-----|-------------------|
| Availability | 2xx+3xx / total | 99.9% | 43 min |
| API Latency | p99 response time | < 500ms | measured per window |
| Search Latency | p99 search response | < 1000ms | measured per window |
| Error Rate | 5xx / total | < 0.1% | 43 min equivalent |

## Health Checks

### GET /health
- Returns: `{"status": "ok"}`
- Used by: Cloud Run health probe
- Timeout: 1s
- No dependency checks

### GET /health/ready
- Checks: PostgreSQL, Redis, Elasticsearch
- Returns 503 if any critical dependency is down
- Used by: Load balancer readiness probe

### GET /health/detailed (requires ops API key)
- Full dependency matrix with latency measurements
- Used by: Operations team for debugging

## Dashboards

### Executive Dashboard
| Panel | Metric | Type |
|-------|--------|------|
| Availability (30d) | SLO compliance % | Stat gauge |
| Error Budget Remaining | Budget consumed vs remaining | Gauge |
| Active Users (24h) | Unique authenticated users | Stat |
| Search Volume (24h) | Total search queries | Stat |

### Service Overview Dashboard
| Panel | Metric | Type |
|-------|--------|------|
| Request Rate | http_requests_total rate(5m) | Time series |
| Error Rate | 5xx / total | Time series + 0.1% threshold |
| Latency p50/p95/p99 | http_request_duration_seconds | Time series + 500ms SLO line |
| Saturation | db_pool_active / db_pool_size | Gauge |
| Active Connections | db_pool_active_connections | Time series |
| Queue Depth | celery_queue_depth | Time series |

## Alert Definitions

### P1: Site Down
- Condition: /health returns non-200 for 2 consecutive minutes
- Route: PagerDuty → On-call engineer
- Runbook: #site-down

### P2: High Error Rate
- Condition: 5xx rate > 1% for 5 minutes
- Route: Slack #ops-alerts
- Runbook: #high-error-rate

### P3: Elevated Latency
- Condition: p99 > 500ms for 10 minutes
- Route: Slack #ops-warnings
- Runbook: #high-latency

## Runbook: Site Down

**Severity:** P1
**Estimated resolution:** 5-15 minutes

### Symptoms
- Health check failures
- Users see 502/503 errors
- External uptime monitor alerts

### Diagnosis
1. Check Cloud Run console — is the service running?
2. Check `/health/ready` — which dependency is failing?
3. Check recent deploys — was there a deploy in the last 30 min?

### Resolution

#### If Cloud Run service is crashed:
1. Check logs: `gcloud logging read "resource.type=cloud_run_revision" --limit=50`
2. If OOM: increase memory limit in service config
3. If crash loop: rollback to previous revision
4. Verify: `curl https://api.example.com/health`

#### If database is unreachable:
1. Check Neon dashboard for outages
2. Check connection pool: `curl https://api.example.com/health/detailed`
3. If connection exhaustion: restart service to reset pool
4. Verify: `curl https://api.example.com/health/ready`

#### If recent deployment:
1. Rollback: `gcloud run services update-traffic api --to-revisions=PREVIOUS=100`
2. Verify: `curl https://api.example.com/health`
3. Investigate failed deploy in next business day

### Escalation
- If not resolved in 15 minutes → escalate to platform team lead
- If data loss suspected → escalate to database team + CTO
```
