# Pre-Deploy Gate Report

**Story:** STORY-XXX — [Story Name]
**Date/Time:** YYYY-MM-DD HH:MM UTC
**Image Tag:** `<registry>/<image>:<tag>`
**Environment:** staging / production
**Overall Status:** <!-- PASS / FAIL / BLOCKED -->

---

## Check Results Summary

| # | Check | Tool | Result | Details |
|---|-------|------|--------|---------|
| 1 | Container CVE Scan | trivy / grype | <!-- PASS / FAIL --> | <!-- e.g., "0 Critical, 0 High" or "2 Critical CVEs found" --> |
| 2 | Dependency Audit | pip-audit / npm audit | <!-- PASS / FAIL --> | <!-- e.g., "0 vulnerabilities" or "3 High vulns in requests" --> |
| 3 | Secrets Scan | gitleaks / trufflehog | <!-- PASS / FAIL --> | <!-- e.g., "0 secrets detected" or "1 API key found in src/config.py" --> |
| 4 | Infrastructure Drift | terraform plan / bicep what-if | <!-- PASS / FAIL --> | <!-- e.g., "No changes" or "3 resources to modify" --> |
| 5 | Monitoring Health | curl + config check | <!-- PASS / FAIL --> | <!-- e.g., "All endpoints healthy" or "/health/ready: 503" --> |
| 6 | Adapter Connections | custom scripts | <!-- PASS / FAIL --> | <!-- e.g., "All adapters reachable" or "Redis: connection refused" --> |
| 7 | Migration Chain | alembic heads | <!-- PASS / FAIL --> | <!-- e.g., "Single head: a1b2c3d4" or "2 heads: a1b2 b3c4" --> |
| 8 | Smoke Tests | pytest / playwright | <!-- PASS / FAIL --> | <!-- e.g., "12/12 passed" or "2/12 failed" --> |

---

## Check 1: Container Image CVE Scan

**Tool:** `trivy` / `grype`
**Ran at:** YYYY-MM-DD HH:MM UTC
**Image:** `<registry>/<image>:<tag>`
**Result:** <!-- PASS / FAIL / BLOCKED -->

```
# Paste tool output here (truncate to critical/high findings if verbose)
```

**Findings:**

| CVE ID | Severity | Package | Fixed In |
|--------|----------|---------|----------|
| <!-- CVE-YYYY-NNNNN --> | <!-- Critical / High --> | <!-- package@version --> | <!-- version --> |

<!-- If PASS, write: "Zero Critical or High CVEs. Full scan output above." -->
<!-- If no findings table needed, delete it -->

---

## Check 2: Dependency Audit

**Tool:** `pip-audit` (Python) / `npm audit` (Node.js)
**Ran at:** YYYY-MM-DD HH:MM UTC
**Result:** <!-- PASS / FAIL / BLOCKED -->

```
# Paste tool output here
```

**Findings:**

| Package | Severity | CVE | Fix |
|---------|----------|-----|-----|
| <!-- package@version --> | <!-- High / Critical --> | <!-- CVE-YYYY-NNNNN --> | <!-- upgrade to X.Y.Z --> |

<!-- If PASS, write: "Zero vulnerabilities found." -->

---

## Check 3: Secrets Scan

**Tool:** `gitleaks` / `trufflehog`
**Ran at:** YYYY-MM-DD HH:MM UTC
**Result:** <!-- PASS / FAIL / BLOCKED -->

```
# Paste tool output here
```

**Findings (DO NOT log actual secret values):**

| File | Line Range | Finding Type |
|------|-----------|--------------|
| <!-- src/config.py --> | <!-- L42-L44 --> | <!-- AWS Access Key --> |

<!-- If PASS, write: "Zero secrets detected." -->

---

## Check 4: Infrastructure Drift Detection

**Tool:** `terraform plan` / `az deployment group what-if`
**Ran at:** YYYY-MM-DD HH:MM UTC
**Result:** <!-- PASS / FAIL / BLOCKED -->

```
# Paste plan output summary here
# For terraform: "Plan: 0 to add, 0 to change, 0 to destroy."
# For bicep: paste what-if summary
```

**Unexpected changes:**

| Resource | Change Type | Details |
|----------|-------------|---------|
| <!-- resource_name --> | <!-- create / modify / destroy --> | <!-- why unexpected --> |

<!-- If PASS, write: "No infrastructure changes detected." -->

---

## Check 5: Monitoring Health

**Ran at:** YYYY-MM-DD HH:MM UTC
**Result:** <!-- PASS / FAIL / BLOCKED -->

| Endpoint | URL | Status Code | Response Time |
|----------|-----|-------------|---------------|
| `/health` | `https://<host>/health` | <!-- 200 --> | <!-- 45ms --> |
| `/health/ready` | `https://<host>/health/ready` | <!-- 200 --> | <!-- 120ms --> |
| `/metrics` | `https://<host>/metrics` | <!-- 200 --> | <!-- 30ms --> |

**Alert rules:**
- Alert rules file: `infra/monitoring/alert-rules.yaml` — <!-- EXISTS / MISSING -->
- Number of alert rules defined: <!-- N -->

<!-- If any endpoint fails, document the error response here -->

---

## Check 6: Adapter and Integration Connections

**Ran at:** YYYY-MM-DD HH:MM UTC
**Result:** <!-- PASS / FAIL / BLOCKED -->

| Adapter | Type | Result | Response Time | Error (if FAIL) |
|---------|------|--------|---------------|-----------------|
| Primary DB | PostgreSQL | <!-- PASS / FAIL --> | <!-- 12ms --> | <!-- error message --> |
| Cache | Redis | <!-- PASS / FAIL --> | <!-- 2ms --> | <!-- error message --> |
| <!-- External API --> | REST | <!-- PASS / FAIL --> | <!-- 250ms --> | <!-- error message --> |

<!-- Add or remove rows for the project's actual adapters -->

---

## Check 7: Migration Chain Verification

**Tool:** `alembic heads`
**Ran at:** YYYY-MM-DD HH:MM UTC
**Result:** <!-- PASS / FAIL / BLOCKED -->

```
# Paste alembic heads output here
# Expected (PASS): single line like "a1b2c3d4e5f6 (head)"
# FAIL: multiple lines indicate a branched chain
```

**Head count:** <!-- 1 (expected) / N (fail) -->
**Head revision(s):** <!-- a1b2c3d4e5f6 -->

---

## Check 8: Smoke Test Dry-Run

**Tool:** `pytest -m smoke` / `npx playwright test --grep @smoke`
**Ran at:** YYYY-MM-DD HH:MM UTC
**Environment:** `$BASE_URL = https://<host>`
**Result:** <!-- PASS / FAIL / BLOCKED -->

**API smoke tests (pytest):**
```
# Paste pytest output summary here
# e.g., "8 passed in 12.34s"
```

**Frontend E2E smoke tests (playwright, if applicable):**
```
# Paste playwright output summary here
# e.g., "12 passed (15s)"
```

**Failed tests (if any):**

| Test | File | Error |
|------|------|-------|
| <!-- test_name --> | <!-- tests/smoke/test_health.py --> | <!-- AssertionError: ... --> |

---

## Remediation Plan

<!-- Complete this section only if any checks FAILED or BLOCKED -->
<!-- If all checks PASS, write: "No remediation required. All checks passed." -->

### Failing Check: [Check Name]

**Issue:** [Describe the specific finding]
**Severity:** [Critical / High / Blocker]
**Owner:** [Who is responsible for the fix]
**Estimated effort:** [< 1 hour / half day / full day]
**Fix:**
1. [Step 1]
2. [Step 2]
3. Re-run: `tests/predeploy/check_<N>.sh`

---

## Re-Run History

<!-- Record re-runs here if checks failed and were re-run after remediation -->

| Date/Time | Checks Re-Run | Result |
|-----------|--------------|--------|
| <!-- YYYY-MM-DD HH:MM --> | <!-- Check 2 (Dep Audit) --> | <!-- PASS --> |

---

## Sign-Off

**Gate status:** <!-- PASS / FAIL / BLOCKED -->
**Approved by:** <!-- [User name or "pending"] -->
**Approval date/time:** <!-- YYYY-MM-DD HH:MM UTC or "pending" -->
**Approval note:** <!-- "Approved to deploy" or blocked reason -->

> **GATE:** Deployment MUST NOT proceed without explicit approval above.
> The Release Engineer presents this report; the human authorizes the deploy.
