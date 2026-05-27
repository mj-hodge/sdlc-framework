# Research — STORY-591: Critical-Feature SDLC Pattern

> **Note:** Phase 2 was initially skipped by the phase runner (dispatched directly to Phase 4). This document is produced retroactively to complete the Large-scope artifact set. The design (Phase 6) was already complete; findings here confirm and validate the design choices.

## Research Method

Three parallel sub-agents surveyed three domains:
- `market-scout` — Commercial SaaS and vendor landscape
- `library-miner` — OSS Python/FastAPI ecosystem libraries
- `field-reporter` — Community patterns, SRE literature, incident post-mortems

---

## 1. Market Landscape (market-scout)

### What Exists

| Category | Products | What They Provide | Coverage of Our Pattern |
|----------|---------|-------------------|------------------------|
| Feature flagging | LaunchDarkly, Split.io, Flagsmith | Rollout control, targeting, kill switches | Answers *who* sees a feature, not *whether output is correct* |
| Contract testing (SaaS) | PactFlow | Structural API contracts between services (request/response shape) | API-level only — not business assertion contracts |
| SRE platforms | Cortex, Backstage, Blameless, FireHydrant | Service scorecards, ownership metadata, incident management | Service-level — no per-feature health concept |
| Observability | Datadog SLOs, New Relic Service Levels, Honeycomb | Service/endpoint SLOs with burn-rate alerts | Technical metrics only — cannot declare "this feature has a business output contract" |
| CI/CD gates | Argo Rollouts, Keptn, Spinnaker | Canary analysis on latency/error-rate thresholds | No "contract-gated deploy" in business-assertion sense |
| Incident classification | PagerDuty, OpsGenie | P1–P4 severity, service-scoped routing | Post-hoc, manual, service-scoped — not feature-criticality aware |

### The Market Gap

No product provides a first-class mechanism to:
1. Declare that a specific **feature** (not service) has business-semantic output contracts
2. Enforce those contracts in **CI as a deploy gate**
3. Emit **structured violation events** at runtime keyed to the contract clause
4. Aggregate feature-health into a **single discoverable index** per project

PactFlow is the closest existing offering but operates at HTTP service boundary contracts (structural), not intra-service behavioral contracts. The gap our pattern fills is **above and between** existing tools — it composes them (Prometheus, Grafana, CI pipelines) rather than replacing them.

**Build vs. buy verdict:** Build. No commercial product covers this use case. The pattern is SDLC-process-layer guidance, not a runtime platform.

---

## 2. Library Landscape (library-miner)

### Python Contract Testing Libraries

| Library | Weekly Downloads | Status | Key Capability | Gap |
|---------|-----------------|--------|----------------|-----|
| `deal` | ~14k | Active (2025-11) | `@pre`/`@post`/`@ensure` decorators; `catch` context manager for non-raise capture | No structured JSON emission; no Prometheus integration; no business-language metadata |
| `icontract` | ~83k | Active (2026-01) | Rich violation repr with full expression recomputation; hook interface | Still raise-only; no emission pathway; no per-feature health state |
| `dpcontracts` | ~2k | Abandoned (2018) | Lightweight pre/post/invariant | Dead project |
| `pact-python` | ~173k | Active (2026-04) | Consumer-driven contract testing; consumer stubs + provider verifications | HTTP/broker layer, not function output contracts; requires Pact broker infra |
| `hypothesis` | ~8.4M | Active (2026-04) | Property-based testing; degraded-input via `assume()` | Test-time only — no runtime enforcement; degraded input filtered (skipped), not asserted |
| `pandera` | ~2M | Active (2026-04) | DataFrame schema validation with Check objects | DataFrame domain only; no general output contracts |

### Runtime Emission Libraries

| Library | Weekly Downloads | Verdict |
|---------|-----------------|---------|
| `prometheus-client` | ~37M | **Use this.** Counter with `{feature, contract, severity}` labels. Wiring is custom — library is just the sink. |
| `fastapi-health` | ~58k | Stale (2021). Not recommended — live probes, not in-memory state. |
| `py-healthcheck` | ~41k | Flask/Tornado only. Not applicable. |

### Synthesis

**No existing library covers the full pattern.** The closest composition:
- `deal` as the contract decorator (best Python DbC option; `catch` context manager enables non-raise capture)
- `prometheus-client` for counter emission
- Custom violation event schema (structured JSON → structured log + Prometheus counter)
- Custom `/api/status` endpoint using module-level `dict` for per-feature `HealthStatus` — simpler than any health library

The SDLC pattern layer (templates, phase personas, CI gates) is not a Python library problem — it's a process documentation problem. The library choices above inform the implementation guidance in `patterns/critical-features.md`.

---

## 3. Community Patterns (field-reporter)

### Design by Contract (DbC)

Meyer's DbC (Eiffel, 1986) is theoretically well-regarded but practically rare in mainstream SaaS. Python's contract libraries exist but see modest adoption. Safety-critical domains (avionics DO-178C, automotive ISO 26262, medical FDA 21 CFR Part 11) apply DbC rigorously — but web SaaS has not adopted it at feature granularity. The Python community favors runtime type hints (Pydantic) over assertion-based contracts.

**Implication:** We cannot assume teams know DbC. The pattern must be described in operational language, not contract-theory language.

### Feature-Level SLOs

Google's SRE model operates at service boundaries. Feature-level SLOs are discussed in Charity Majors' observability work (Honeycomb's "SLOs aren't just for services") but no canonical industry pattern exists. This is an **acknowledged gap** in the SRE literature.

**Implication:** Our pattern is adding to the SRE canon, not implementing an existing standard.

### Pre-mortems and FMEA

Amazon's PR/FAQ working-backwards documents implicitly produce output contracts (narrative form), but these are not machine-checkable. FMEA (Failure Mode and Effects Analysis) is standard in hardware manufacturing and regulated software (DO-178C, IEC 62304) but absent from mainstream agile frameworks.

**Implication:** The concept is recognized in regulated industries. Framing our "output contracts" as "machine-checkable pre-mortem assertions" is a useful communication bridge.

### DORA Metrics + Deployment Safety

DORA's Change Failure Rate is a lagging indicator. Pre-deploy **criticality classification** is not formalized in DORA or Accelerate. The closest practitioner analog is LaunchDarkly's "feature flag health" — but that's release control, not behavioral correctness gating.

**Implication:** Our Phase 11 Critical Feature Contracts CI step is ahead of current DORA-aligned practice. This is intentional.

### Chaos Engineering

Netflix GameDay and AWS FIS target infrastructure and service resilience. Feature-specific chaos ("what if deduplication silently fails?") is rare and explicitly acknowledged as a gap by Gremlin's documentation. Our contract tests fill this gap structurally without requiring chaos tooling.

### Incident Post-mortems as Evidence

Stripe, GitHub, and Cloudflare post-mortems consistently identify missing output assertions retroactively:
- "The assumption was never validated"
- "There was no alert on the business metric, only on the technical metric"
- "The failure was silent — no observable signal for 6 hours"

The 2021 Cloudflare BGP incident and GitHub's 2023 Actions outage both cite absent output assertions as root-cause contributors. The pattern of failures in advertising-amazon (silent deduplication, missed cron window, blank required field) is the **exact class of incident** these post-mortems describe.

**Implication:** Feature-level output contracts are a retroactive identification in post-mortems but not yet a proactive discipline. Our pattern formalizes what post-mortems wish had existed.

---

## 4. Cross-Source Synthesis

### Corroborated Findings

| Finding | Market Scout | Library Miner | Field Reporter |
|---------|-------------|---------------|----------------|
| No existing product/library covers feature-level business output contracts | ✅ Gap confirmed | ✅ Gap confirmed | ✅ Gap confirmed |
| Runtime violation emission requires custom wiring (no off-the-shelf) | ✅ | ✅ (prometheus-client is just a sink) | — |
| In-memory health state is the right choice for status endpoint | ✅ | ✅ (fastapi-health probes = wrong pattern) | — |
| Pattern is novel at the SDLC process layer | — | — | ✅ "Genuinely additive" |
| Pact/PactFlow is closest market analogy but operates at wrong level | ✅ | ✅ | — |

### Key Validation of Design Choices

| Design Decision (from Phase 6) | Research Validation |
|-------------------------------|---------------------|
| Use `output-contracts.md` template (human-readable business assertions) | ✅ No library provides this; must be documentation |
| Phase 10c fires for ALL scopes when criticality=critical | ✅ No market product does this; correct to make it scope-agnostic |
| Contract tests mock at outermost boundary | ✅ `pact-python` validates this approach for service contracts; analogous for function contracts |
| In-memory/file-backed status (no DB) | ✅ `fastapi-health` live-probe pattern = stale-probe problem; in-memory is correct |
| Prometheus counters with `{feature, contract, severity}` labels | ✅ `prometheus-client` is the right tool; wiring is custom |
| Separate test directory (not markers) | ✅ `deal`/`icontract` are decorator-based; directory-based enforcement is complementary |
| Pattern is SDLC process layer, not a library | ✅ Confirmed — no library covers the SDLC integration layer |

---

## 5. Dependency Health Summary

| Dependency (for implementing projects) | Health | Recommendation |
|----------------------------------------|--------|----------------|
| `prometheus-client` | ✅ Excellent (37M/wk, active) | Use as metric sink |
| `deal` | ⚠️ Moderate (14k/wk, active) | Optional — can use icontract instead |
| `icontract` | ✅ Good (83k/wk, active) | Alternative to deal |
| `pact-python` | ✅ Good (173k/wk, active) | For inter-service contracts (not this pattern) |
| `fastapi-health` | ❌ Stale (2021) | Do not use — build custom /api/status |

---

## 6. Recommendations

1. **Do not depend on any existing library for the SDLC pattern itself.** Templates and phase personas are the deliverable.
2. **Recommend `deal` or `icontract` in `patterns/critical-features.md`** as optional contract decorator libraries for implementing projects, but do not mandate them — teams may use plain assertion functions.
3. **Mandate `prometheus-client`** as the standard violation counter emission library (it is already nearly universal in Python projects).
4. **Explicitly call out PactFlow** as a complementary tool (for inter-service API contracts), not a substitute — teams using PactFlow still need output contracts for intra-service business assertions.
5. **Frame the pattern using post-mortem language** ("what a post-mortem wishes had existed") when communicating to engineering teams — this is more relatable than DbC theory.

---

## Buy vs. Build Decision

**Build the pattern documentation. Use existing libraries for implementation.**

| Component | Buy / Build / Adapt |
|-----------|-------------------|
| SDLC phase personas | Build (documentation) |
| Output contracts template | Build (documentation) |
| Contract test structure | Build (documentation) |
| Phase 10c workflow | Build (documentation) |
| Violation event emission | Adapt (`prometheus-client` + custom JSON schema) |
| `/api/status` endpoint | Build (custom FastAPI route, no library) |
| Grafana dashboard | Adapt (standard Grafana JSON with custom panels) |
| CI gate script | Build (bash, project-specific) |
