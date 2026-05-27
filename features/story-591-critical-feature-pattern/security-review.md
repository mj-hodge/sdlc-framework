# Security Review — STORY-591: Critical-Feature SDLC Pattern

**Reviewer:** Security Review Agent (Phase 6b)
**Date:** 2026-04-25
**Story:** STORY-591 — Critical-Feature SDLC Pattern
**Scope:** Documentation and templates only. No executable code ships in this story. Security review covers the patterns being documented, whose security implications inherit to every consuming project.

---

## 1. Threat Model

The critical-feature pattern introduces five distinct attack surfaces across consuming projects. Each is analyzed using STRIDE categories.

### 1.1 Components

| Component | Description |
|-----------|-------------|
| `/api/status` | Public JSON health endpoint, no authentication |
| `/status` | Public HTML health dashboard, no authentication, auto-refresh |
| Violation event logs | Structured JSON emitted to log streams and Prometheus |
| `docs/critical-features.md` | Public markdown index listing all critical features |
| Contract test fixtures | Test code in `tests/critical_features/<slug>/contracts/` |

### 1.2 STRIDE Analysis

| Component | Threat | Category | Notes |
|-----------|--------|----------|-------|
| `/api/status` | Exposes feature names, health status, runbook URLs, violation counts | **Information Disclosure** | Primary threat. Reveals operational state and internal doc structure to any caller. |
| `/api/status` | Unauthenticated; no rate-limit enforcement in pattern | **DoS** | Pattern recommends 60 req/min but does not enforce it. Pattern doc must make this a MUST, not a SHOULD. |
| `/api/status` | 503 message leaks internal error details (`"error": "status_check_failed"`) | **Information Disclosure** | Error messages may reveal implementation details. |
| `/status` HTML page | `<meta http-equiv="refresh">` pulls fresh data on every cycle | **DoS** | High-frequency browser tabs (e.g., NOC wall display) amplify load. |
| `/status` HTML page | Runbook URLs rendered as clickable `<a href>` — XSS if runbook_url is writable | **Tampering / XSS** | If the state file is writable by a lower-privilege process, a crafted runbook_url could inject JavaScript via the `href` attribute. |
| Violation events | `"actual"` field populated from runtime data — may contain PII or secrets | **Information Disclosure** | E.g., `profile_id`, customer email, API keys embedded in error payloads. |
| Violation events | Prometheus counter labels include `contract_id` — low risk, but label cardinality unbounded if contract IDs are user-generated | **DoS** | Label explosion in Prometheus. |
| `docs/critical-features.md` | Public file lists all critical features, test paths, dashboard links, and runbook URLs | **Information Disclosure** | Provides attackers a prioritized map of highest-value targets. |
| Contract test fixtures | Fixtures may reference real credentials, API keys, or PII from production debugging sessions | **Information Disclosure** | Test files committed to repo may leak secrets. |
| Contract test fixtures | CI runs contract tests in a shared runner environment | **Elevation of Privilege** | If fixtures use real credentials, a compromised CI runner gains production access. |

---

## 2. Information Disclosure Assessment

### 2.1 What `/api/status` Exposes

The JSON response in its current form reveals:

| Field | Sensitivity | Risk |
|-------|------------|------|
| `project` | Low | Confirms project identity to unauthenticated callers |
| Feature slugs (map keys) | Medium | Enumerates all critical features by name — attack surface inventory |
| `health` per feature | Medium | Reveals which subsystems are currently degraded or unhealthy |
| `last_success_at` | Medium | Reveals operational rhythm (cron intervals, batch windows) — aids timing attacks |
| `violation_count_24h` | Medium | Confirms a feature is actively failing; useful for coordinated exploitation during degraded state |
| `runbook_url` | Medium-High | Links to internal documentation; exposes repo structure and may reveal private GitHub org paths |

### 2.2 Findings

**SEC-001 — Feature enumeration via `/api/status`**
The endpoint names every critical feature in a machine-readable format. An attacker can enumerate which subsystems exist and which are currently weakened, then time attacks against degraded features.

**Recommendation:** The pattern documentation MUST include guidance that `/api/status` should be served behind a network boundary (internal load balancer, VPN, or IP allowlist) unless there is an explicit business requirement for public exposure. The current pattern states "no authentication required" as an absolute — this must be qualified.

**SEC-002 — Runbook URL exposure**
Runbook URLs in `/api/status` responses point directly to internal documentation (e.g., `https://github.com/org/repo/blob/main/docs/runbooks/...`). For private GitHub repositories, this exposes the repo name, org, and documentation structure to any external caller who can reach the endpoint.

**Recommendation:** The pattern must specify that `runbook_url` may be omitted from public-facing responses or replaced with a generic support contact. Add a `runbook_url_public` vs. `runbook_url_internal` field split, or add an `include_runbook_urls` flag on the endpoint.

**SEC-003 — Timing information via `last_success_at`**
Publishing the exact timestamp of last successful execution reveals cron schedule intervals. For financial syncs and ad-spend submissions, this information aids an attacker in timing window-based attacks.

**Recommendation:** Consider rounding `last_success_at` to the nearest 5-minute boundary, or replacing it with a relative field (`"last_success_age_minutes": 5`) that conveys staleness without pinpointing schedule intervals.

---

## 3. Violation Event Sanitization

### 3.1 Risk

The `"expected"` and `"actual"` fields in violation events are populated at runtime from business data. Examples in the specification already show `profile_id=12345` embedded in the `"actual"` field. In practice, these fields may contain:

- Customer email addresses (contract C3 explicitly references email columns)
- Advertiser profile IDs (which may be treated as confidential under API ToS)
- API response bodies containing authentication tokens in error payloads
- SQL query results containing PII from failed deduplication checks
- File paths revealing infrastructure layout

### 3.2 Required Sanitization Rules

The pattern documentation MUST mandate the following rules for all consuming projects:

| Rule | Requirement |
|------|-------------|
| **R1 — No raw API payloads** | `"actual"` MUST NOT contain raw HTTP response bodies. Summarize: counts, types, field names — not values. |
| **R2 — No PII in actual/expected** | Email addresses, customer names, and account identifiers MUST be replaced with redacted placeholders: `<email-redacted>`, `<profile-id-redacted>`. |
| **R3 — No credentials** | API keys, tokens, passwords, and connection strings are forbidden in both `"expected"` and `"actual"`. Pattern enforcement: the CI lint check (currently targeting `skip/xfail`) MUST be extended to scan violation event definitions for common secret patterns. |
| **R4 — Structural description only** | `"actual"` MUST describe the structural anomaly, not the data content. GOOD: `"Duplicate blob detected: report_type=sp, date=2026-04-24, profile_id=<redacted>"`. BAD: `"Email column blank for customer john.doe@example.com in campaign 88421"`. |
| **R5 — Log destination access control** | Structured violation event logs MUST be treated as sensitive logs (restricted access). The pattern doc must note that violation event streams should not be sent to public dashboards or unauthenticated log aggregators. |

### 3.3 Prometheus Label Safety

Counter labels `{severity, contract_id}` are safe. However, consuming projects MUST NOT add `{feature_value}` or `{actual_value}` labels. The pattern documentation MUST explicitly forbid embedding business data values in Prometheus label dimensions.

---

## 4. Runbook URL Policy

### 4.1 Risk

Runbook URLs appear in three places:
1. `/api/status` JSON responses (public)
2. `/status` HTML page as clickable links (public)
3. Violation event log entries (internal, but may be forwarded to external systems)

### 4.2 Policy Requirements

The pattern documentation MUST include the following runbook URL policy:

| Scenario | Required Behavior |
|----------|------------------|
| **Private GitHub repository** | Runbook URLs MUST NOT appear in public `/api/status` or `/status` responses. Omit or replace with a generic contact reference. |
| **Public GitHub repository** | Runbook URLs MAY appear in responses, but teams MUST review that runbooks do not contain sensitive operational details (IP addresses, credentials, API endpoints). |
| **Violation event logs** | Runbook URLs in structured logs are acceptable since log access is access-controlled. |
| **HTML rendering** | The `/status` page MUST HTML-encode runbook URLs before rendering in `<a href>` attributes to prevent XSS if the URL is sourced from a writable state file. |
| **URL validation** | The pattern MUST require that runbook URLs are validated against an allowlist of permitted domains before being included in any response. Acceptable: `github.com/<org>`, internal wiki domains. Reject: arbitrary URLs. |

### 4.3 XSS Mitigation for `/status` HTML

The pattern template for the HTML endpoint MUST specify:

```
runbook_url MUST be HTML-attribute-escaped before insertion into href.
MUST validate URL scheme is https:// — reject javascript:, data:, and relative URLs.
MUST validate URL host against an allowlist before rendering.
```

This is especially critical because the state file backing `/status` is written by the contract checker process, which runs as part of the feature service. If that process has a bug or is compromised, a crafted URL in the state file could produce a stored XSS in the status page.

---

## 5. Critical Features Index Visibility

### 5.1 Risk

`docs/critical-features.md` is a static markdown file committed to the consuming project's repository. In a public repository, it publishes:

- A complete list of all features classified as `critical` — the highest-value attack targets
- Links to contract test directories (revealing test coverage boundaries)
- Links to Grafana dashboards (revealing monitoring infrastructure)
- Links to runbooks (revealing internal documentation)
- `last_verified` dates (revealing when security-critical features were last audited)

This is effectively a published attack surface map: an attacker can read it to learn which features are considered most business-critical, where their tests live, and what monitoring exists.

### 5.2 Recommendations

**SEC-004 — Public repo risk disclosure**
The pattern documentation MUST include a warning:

> If this project is in a public repository, `docs/critical-features.md` will be publicly readable. Review its contents for sensitive information before committing. Consider omitting dashboard links and runbook URLs from the public version.

**SEC-005 — Sensitive fields in the index**
The index template MUST mark the `Dashboard` and `Runbook` columns as optional, with guidance that these links SHOULD be omitted from public repos or replaced with generic references.

**SEC-006 — Attack surface mapping risk**
Teams MUST understand that listing features as `critical` in a public file provides adversaries a prioritized target list. This is an accepted trade-off for operational visibility, but it must be a conscious decision, not an accidental one. The pattern documentation MUST require explicit team sign-off when `docs/critical-features.md` is in a public repository.

---

## 6. Contract Test Security

### 6.1 Risk

Contract tests in `tests/critical_features/<slug>/contracts/` are written during Phase 7 by engineers who may be working from real production data to understand failure modes. Common risks:

- Real API keys or tokens hardcoded in test fixtures while debugging locally, then committed
- Real customer data (emails, IDs, account names) used as fixture values
- Real production endpoints used in `conftest.py` environment setup

### 6.2 Required Controls

The pattern documentation MUST mandate:

| Control | Requirement |
|---------|-------------|
| **No real credentials** | `conftest.py` and all `test_contract_*.py` files MUST NOT contain real API keys, tokens, or connection strings. Use placeholder values: `"fake-api-key-for-testing"`, `os.environ.get("API_KEY", "test-key")`. |
| **No real PII** | Fixture data MUST use synthetic values. GOOD: `profile_id=999999` (clearly fake). BAD: `profile_id=12345` (could be real). Prefer values that are obviously synthetic. |
| **Secret scanning in CI** | The Phase 11 Critical Feature Contracts CI step MUST include a secret-scanning pass over `tests/critical_features/`. Acceptable tools: `detect-secrets`, `truffleHog`, or `gitleaks`. |
| **No production endpoint calls** | Contract tests MUST mock at the outermost boundary (already specified). The pattern must explicitly state: "Contract tests MUST NOT make network calls to production systems, staging systems, or any external service." |
| **Fixture review in 8b Code Review** | The Phase 8b code review checklist MUST include: "Verify no PII or credentials in contract test fixtures." |

### 6.3 Mock Boundary and Credential Interaction

The current specification correctly requires outermost-boundary mocking. This is also the correct security control: a mock at the DB session factory level prevents tests from needing real DB credentials, and a mock at the httpx client level prevents tests from needing real API keys. The pattern must make this security implication explicit, not just cite "rationale: catches integration failures."

---

## 7. Required Security Tests

Phase 7 MUST include the following security-specific tests for any project implementing the critical-feature pattern. These tests belong in `tests/critical_features/<slug>/contracts/` alongside the business contract tests.

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| SEC-T1 | `test_status_no_secrets_in_response` | Assert that `/api/status` response body does not contain patterns matching common secrets (tokens, keys, passwords) |
| SEC-T2 | `test_status_no_pii_in_response` | Assert that `/api/status` response body does not contain email addresses or raw customer IDs in field values |
| SEC-T3 | `test_violation_event_actual_field_redacted` | Assert that when a violation is emitted for a contract involving customer data, the `actual` field contains `<redacted>` placeholders, not raw values |
| SEC-T4 | `test_status_html_runbook_url_escaped` | Assert that the `/status` HTML page HTML-encodes the runbook URL in the `href` attribute — specifically that `<`, `>`, `"`, and `&` are escaped if present in a crafted URL |
| SEC-T5 | `test_status_html_rejects_javascript_scheme` | Assert that a `javascript:` URL in the state file does not render as a live link in the `/status` page |
| SEC-T6 | `test_status_html_rejects_relative_url` | Assert that a relative URL (e.g., `../../etc/passwd`) in the state file is rejected or rendered as plain text, not a link |
| SEC-T7 | `test_status_endpoint_rate_limit_header_present` | Assert that `/api/status` responses include rate-limit headers (or a note if enforcement is upstream) |
| SEC-T8 | `test_status_503_does_not_leak_stack_trace` | Assert that the 503 degraded response body contains only the documented fields and no stack trace, exception type, or internal path information |

---

## 8. Findings Table

| ID | Severity | Finding | Recommendation | Status |
|----|----------|---------|----------------|--------|
| SEC-001 | Medium | `/api/status` enumerates all critical features by name to unauthenticated callers | Pattern doc MUST recommend network-boundary protection (IP allowlist / VPN) unless public access is explicitly justified | Open |
| SEC-002 | Medium | Runbook URLs in `/api/status` and `/status` expose internal GitHub repo structure | Add `runbook_url` omission guidance for public endpoints; require domain allowlist validation | Open |
| SEC-003 | Low | `last_success_at` reveals operational schedule intervals | Round to 5-minute boundaries or replace with relative age field | Open |
| SEC-004 | Medium | `docs/critical-features.md` in public repos is a published attack surface map | Add explicit public-repo warning and team sign-off requirement to pattern doc | Open |
| SEC-005 | Low | Index template includes dashboard and runbook columns that leak internal infrastructure links | Mark columns as optional in template; add guidance to omit from public repos | Open |
| SEC-006 | High | Violation event `actual` field may contain PII, customer data, or API response payloads | Mandate sanitization rules R1–R5 in pattern documentation; add SEC-T3 to Phase 7 test requirements | Open |
| SEC-007 | High | Contract test fixtures may contain real credentials or PII if written from production debugging sessions | Mandate secret-scanning CI step over `tests/critical_features/`; add credential-check to Phase 8b review checklist | Open |
| SEC-008 | Medium | `/status` HTML page vulnerable to stored XSS if state file runbook_url is writable by a compromised process | Pattern template MUST specify URL HTML-encoding, scheme allowlisting (`https://` only), and host allowlisting | Open |
| SEC-009 | Low | Prometheus violation counter labels MUST NOT include business data values | Explicitly forbid `{actual_value}`, `{email}`, or similar labels in pattern documentation | Open |
| SEC-010 | Low | 503 error response `message` field may evolve to include internal error details | Specify that error responses MUST contain only the documented fields; add SEC-T8 to Phase 7 | Open |

---

## 9. Sign-off

**Security review scope:** Pattern documentation and templates for STORY-591. No executable code reviewed.

**Primary threat surface:** Information disclosure — the pattern's public endpoints and public index file expose operational metadata to unauthenticated callers. All high-severity findings (SEC-006, SEC-007) concern data sanitization, not authentication bypass.

**Blocking findings for Phase 6 advancement:** None. All findings are recommendations to strengthen the pattern documentation before Phase 7 test design begins.

**Required actions before Phase 7:**
1. Resolve SEC-006 (violation event sanitization rules) — add R1–R5 to the pattern doc before test design, so test authors know what sanitization tests to write.
2. Resolve SEC-007 (contract test credentials policy) — add to Phase 7 and Phase 8b agent personas before implementation.
3. Resolve SEC-008 (XSS mitigation for `/status` HTML) — update the HTML template in `api-design.md` to include URL encoding and scheme allowlist requirements.

**Findings that may be deferred to per-project implementation (STORY-592+):**
SEC-001 (network boundary), SEC-002 (runbook URL split), SEC-003 (timestamp rounding), SEC-004/SEC-005 (public index guidance), SEC-009 (label policy), SEC-010 (error response spec).

**Reviewer sign-off:** Security Review Agent, Phase 6b, 2026-04-25.
