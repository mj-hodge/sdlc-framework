# Architecture — STORY-591: Critical-Feature SDLC Pattern

## Overview

The critical-feature pattern is an **overlay on the existing SDLC framework** — it does not replace any phase, but adds conditional requirements when `criticality: critical` is set. The architecture is designed so that non-critical features experience zero change to their workflow.

---

## 1. Component Map

```
┌─────────────────────────────────────────────────────────────┐
│                     SDLC Framework (submodule)              │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │templates/│  │ agents/  │  │patterns/ │  │  skills/    │  │
│  │          │  │          │  │  (NEW)   │  │             │  │
│  │seed.md   │  │phase-1   │  │critical- │  │phase-10c/  │  │
│  │output-   │  │phase-7   │  │features  │  │  (NEW)     │  │
│  │contracts │  │phase-10  │  │.md       │  │             │  │
│  │crit-feat │  │phase-11  │  │          │  │             │  │
│  │-index    │  │          │  │          │  │             │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                                                             │
│  ┌─────────────────────────────────┐                        │
│  │ AGENTS.md / software-dev-guidance│                       │
│  │ (Critical Features section)      │                       │
│  └─────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
         │
         │ git submodule
         ▼
┌──────────────────────────────────────────────────────────────┐
│                   Consuming Project                          │
│                                                              │
│  ┌───────────────────┐  ┌──────────────────────────────────┐ │
│  │docs/              │  │tests/                            │ │
│  │  critical-features│  │  critical_features/              │ │
│  │  .md (INDEX)      │  │    <feature-slug>/               │ │
│  └───────────────────┘  │      contracts/                  │ │
│                         │        test_contract_c1.py       │ │
│  ┌───────────────────┐  │        test_contract_c2.py       │ │
│  │features/          │  │        conftest.py               │ │
│  │  story-XXX/       │  └──────────────────────────────────┘ │
│  │    seed.md        │                                       │
│  │    output-        │  ┌──────────────────────────────────┐ │
│  │    contracts.md   │  │src/                              │ │
│  └───────────────────┘  │  status.py (GET /api/status)     │ │
│                         │  contracts/ (runtime checkers)    │ │
│  ┌───────────────────┐  └──────────────────────────────────┘ │
│  │.github/workflows/ │                                       │
│  │  ci.yml           │  ┌──────────────────────────────────┐ │
│  │  (Critical Feature│  │infra/monitoring/                 │ │
│  │   Contracts step) │  │  grafana-critical-features.json  │ │
│  └───────────────────┘  │  alert-rules-critical.yaml       │ │
│                         └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Information Flow

### 2.1 Phase Flow (Critical Feature)

```
Phase 1 (Seed)
  └─ Sets criticality: critical
  └─ Triggers enhanced path

Phase 7 (Test Design)
  └─ Creates tests/critical_features/<slug>/contracts/
  └─ One test file per contract clause
  └─ Mock boundaries enforced (outermost only)
  └─ Lint: no skip/xfail allowed

Phase 10c (Output Contract Hardening) ← NEW
  └─ Reads output-contracts.md
  └─ Maps each contract → test file, metric, alert, runbook
  └─ Updates docs/critical-features.md index
  └─ Verifies 1:1 mapping completeness

Phase 8 (Implementation)
  └─ Implements feature + contract runtime checks
  └─ Makes contract tests GREEN
  └─ Implements violation event emission

Phase 10 (Operations)
  └─ Business-level SLIs from output contracts
  └─ Violation event → Prometheus counter → Grafana → alert rule

Phase 11 (Pre-Deploy Gate)
  └─ Check 13: Critical Feature Contracts
  └─ Verifies: directory exists, tests pass, no skip/xfail, index current
  └─ Fail-closed: blocks deploy on any failure
```

### 2.2 Runtime Data Flow (in consuming project)

```
Feature Code
  │
  ├─ Normal path → produces output → OK
  │
  └─ Violation detected
       │
       ├─ Structured log event: <feature>_<contract>_violation
       │     └─ Fields: severity, timestamp, feature, contract, expected, actual, runbook_url
       │
       ├─ Prometheus counter: <feature>_<contract>_violation_total
       │     └─ Labels: {severity, contract_id}
       │     └─ Scraped by Prometheus → Grafana panel
       │
       ├─ Shared state file (or in-memory dict)
       │     └─ Read by /api/status endpoint
       │     └─ Updates: health=degraded/unhealthy, violation_count_24h++
       │
       └─ Alert rule (optional)
             └─ Fires when: violation_total rate > threshold in window
             └─ Channels: Slack, PagerDuty, email (configurable)
```

### 2.3 Status Endpoint Data Flow

```
Contract violation event
  │
  └─ Updates in-memory state dict
       │
       ├─ GET /api/status → reads dict → returns JSON
       │     └─ Per-feature: health, last_success_at, violation_count_24h, runbook_url
       │
       └─ GET /status → reads dict → renders HTML table
             └─ Auto-refresh 30s, color-coded, links to runbooks
```

---

## 3. Conditional Activation

The critical-feature pattern is **opt-in per story** via the criticality field. The framework detects it at phase routing time:

```
IF seed.md contains "criticality: critical":
  - Phase 7: enforce contract test directory structure
  - Phase 10c: inject into phase path (after 7, before 8)
  - Phase 10: enforce business-level output contracts
  - Phase 11: add Check 13 (Critical Feature Contracts)
  - Require output-contracts.md artifact
  - Require docs/critical-features.md entry
ELSE:
  - Standard SDLC path, no changes
```

**Implementation in the framework:** Phase personas contain `if criticality == critical` conditional sections. The agent reads seed.md at phase start and applies the conditional requirements. No code-level routing changes are needed — the agents already read seed.md as standard practice.

---

## 4. Backward Compatibility

| Concern | Mitigation |
|---------|------------|
| Existing stories without criticality field | Default is `routine` — no additional requirements |
| Existing Phase 7 tests | Unaffected — contract test directory is additional, not replacing |
| Existing Phase 10 operations | Unaffected — output contracts are additional section |
| Existing Phase 11 checks | Check 13 only fires if critical features exist |
| Projects without critical features | `docs/critical-features.md` can be empty or absent |

---

## 5. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pattern lives in framework vs. per-project | **Framework** (submodule) | Single source of truth; all projects inherit updates |
| Phase 10c vs. extending Phase 10 | **New Phase 10c** | Separate phase is unambiguous in routing; Phase 10 is already complex |
| Phase 10c position (after 7, before 8) | **7 → 10c → 8** | Contracts validated before implementation; tests written in 7, mappings verified in 10c |
| Contract tests in separate directory vs. markers | **Separate directory** | Grep-discoverable; lint can target path; no marker discipline needed |
| Status endpoint: in-memory vs. DB | **In-memory / file-backed** | DB dependency makes health endpoint itself a failure surface |
| Per-contract blocking flag | **`blocking: true/false`** | Allows gradual adoption; teams warm up before hard gating |
| Violation event format | **Structured JSON** | Machine-parseable for Prometheus; human-readable in logs |
| `docs/critical-features.md` vs. dynamic index | **Static markdown** | Grepable, works offline, no runtime dependency |
