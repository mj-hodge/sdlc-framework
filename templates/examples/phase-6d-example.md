# Ops Review

## Operational Context

| Aspect | Assessment |
|--------|------------|
| Reliability tier | Standard (99.9%, ~43 min downtime/month) |
| Critical journeys | User registration, login, profile access |
| Dependencies | PostgreSQL, external email service |
| Deployment model | Docker containers, single region |
| On-call team | 2 engineers, Slack-based alerting |

---

## Findings

### Critical: None

### High

#### H1: No Health Check Endpoints Designed

| Aspect | Detail |
|--------|--------|
| Severity | High |
| Location | API design — no `/health` or `/health/ready` endpoints |
| Issue | No health check endpoints in the API design. Load balancer cannot probe instance health. Kubernetes/ECS cannot determine readiness. |
| Impact | Unhealthy instances continue receiving traffic; no automated recovery |
| Fix | Add `/health` (liveness, no dependency checks) and `/health/ready` (readiness, checks DB connectivity) to API design |
| Acceptance Criteria | AC: `GET /health` returns 200 with `{"status": "healthy"}`. AC: `GET /health/ready` returns 200 when DB is up, 503 when DB is down. |

#### H2: No Structured Logging Format Defined

| Aspect | Detail |
|--------|--------|
| Severity | High |
| Location | Architecture — logging not addressed in design |
| Issue | No logging format specified. Without structured logs, diagnosing production issues requires SSH and grep. |
| Impact | Incident response takes 10x longer; logs not searchable; no correlation across requests |
| Fix | Define structured JSON logging with required fields: `timestamp`, `level`, `service`, `trace_id`, `endpoint`, `method`, `status_code`, `duration_ms` |
| Acceptance Criteria | AC: All API endpoints emit structured JSON logs. AC: Every log entry includes `trace_id` for request correlation. |

### Medium

#### M1: No Metrics Endpoint Designed

| Aspect | Detail |
|--------|--------|
| Severity | Medium |
| Location | API design — no `/metrics` endpoint |
| Issue | No Prometheus-compatible metrics endpoint. Cannot monitor request rate, error rate, or latency without custom tooling. |
| Impact | No visibility into system health; alerting impossible without metrics |
| Fix | Add `/metrics` endpoint exposing `http_requests_total`, `http_request_duration_seconds`, `http_errors_total`, `db_pool_active_connections` |
| Acceptance Criteria | AC: `GET /metrics` returns Prometheus-compatible text with request, error, and latency counters |

#### M2: No Post-Deploy Smoke Tests Identified

| Aspect | Detail |
|--------|--------|
| Severity | Medium |
| Location | Implementation plan — no deployment verification |
| Issue | No smoke tests defined for post-deployment verification. Failed deployments go undetected until user reports. |
| Impact | Bad deploys serve traffic; rollback delayed |
| Fix | Define smoke test suite: health endpoint check, login flow, core API endpoint. Run automatically after every deploy. |
| Acceptance Criteria | AC: Post-deploy script verifies `/health`, `/auth/login`, `/users/me` respond correctly |

#### M3: No Rollback Strategy Documented

| Aspect | Detail |
|--------|--------|
| Severity | Medium |
| Location | Implementation plan — deployment section |
| Issue | No rollback procedure documented. If a deploy fails, team must improvise. |
| Impact | Extended downtime during bad deploys |
| Fix | Document one-command rollback procedure. Ensure database migrations are forward-compatible (no destructive column drops in same deploy). |
| Acceptance Criteria | AC: Rollback procedure documented with specific commands |

### Low

#### L1: No Alert Thresholds Defined

| Aspect | Detail |
|--------|--------|
| Severity | Low |
| Location | Design — no alerting section |
| Issue | No SLO targets or alert thresholds. Phase 10 will design the full alerting strategy, but basic thresholds should be in the design. |
| Impact | Phase 10 starts from scratch instead of refining |
| Fix | Define baseline SLOs: availability > 99.9%, p99 latency < 500ms, error rate < 0.1% |
| Acceptance Criteria | Documented in design; Phase 10 verifies |

---

## Ops Acceptance Criteria (add to story)

- AC: `GET /health` returns 200 with `{"status": "healthy"}`
- AC: `GET /health/ready` returns 200 when DB is up, 503 when DB is down
- AC: All API endpoints emit structured JSON logs with `trace_id`, `level`, `service`, `endpoint`, `duration_ms`
- AC: `GET /metrics` returns Prometheus-compatible output with request rate, error rate, and latency histograms

---

## Required Ops Tests

```
Test: test_health_endpoint_returns_200
Setup: Application running
Assert: GET /health returns 200 with {"status": "healthy"}
File: tests/test_health.py

Test: test_readiness_checks_database
Setup: Application running, database available
Assert: GET /health/ready returns 200 with db status healthy
File: tests/test_health.py

Test: test_readiness_fails_without_database
Setup: Application running, database connection severed
Assert: GET /health/ready returns 503
File: tests/test_health.py

Test: test_structured_log_output
Setup: Make a request to any API endpoint
Assert: Captured log output is valid JSON with required fields (timestamp, level, trace_id, endpoint, duration_ms)
File: tests/test_logging.py

Test: test_metrics_endpoint_returns_prometheus_format
Setup: Application running, make some API requests
Assert: GET /metrics returns text/plain with http_requests_total and http_request_duration_seconds
File: tests/test_metrics.py
```

---

## Phase 10 Verification Items

Phase 10 should confirm these are fully operational in the deployed environment:
- Health checks integrated with load balancer/orchestrator
- Metrics scraped by monitoring system (Prometheus/Grafana/Datadog)
- Log aggregation configured (ELK/Loki/CloudWatch)
- Alerts configured and routing to on-call channel
- Runbooks written for each alert type
- Smoke tests running in CI/CD pipeline post-deploy

---

## Verdict

**CHANGES REQUIRED**

The design is functionally sound but operationally incomplete. No critical issues, but two high-severity gaps must be addressed.

**Required before Phase 7:**
1. Add `/health` and `/health/ready` endpoints to API design (H1)
2. Define structured JSON logging format with required fields (H2)

**Add to implementation plan:**
- Prometheus metrics endpoint (M1)
- Post-deploy smoke test suite (M2)
- Rollback procedure documentation (M3)

**Phase 10 verifies:**
- Alert thresholds and routing (L1)
- Full dashboard and runbook coverage

Once health checks and logging format are added to the design, proceed to Test Design.
