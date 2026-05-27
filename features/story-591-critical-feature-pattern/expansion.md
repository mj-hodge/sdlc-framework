# Expansion — STORY-591: Critical-Feature SDLC Pattern

> **Note:** Phase 3 was initially skipped by the phase runner (dispatched directly to Phase 4). This document is produced retroactively to complete the Large-scope artifact set. The design (Phase 6) was already decided; this expansion records the approach spectrum that informed — and validates — that decision.

## Research Method

Three parallel sub-agents generated 9 approaches across the pragmatist → optimizer → futurist spectrum. After deduplication, 8 distinct approaches remain.

---

## Approach Spectrum

### A1 — Criticality Label + README Badge *(Pragmatist — Minimal)*

**Summary:** Tag the feature and document the human contract — no tooling required.

**How it works:**
- Add `criticality: critical` to `seed.md` Overview table
- Require a `## Critical Behaviors` section in feature README listing invariants
- Engineers read before touching; PR checklist requires reviewer verification
- No new phases, no new CI steps, no templates

**Covers from failures:** All four (dedup, cron, blank fields, healthz) — if the contract was written, the failure would have been visible in review.

**Adoption cost:** 1–2 hours per project

**Sacrifices:** All enforcement — nothing breaks if the section is wrong, stale, or absent. Advisory only.

---

### A2 — Checklist Gate at Phase 11 *(Pragmatist — Minimal)*

**Summary:** Bolt a mandatory sign-off checklist onto the existing pre-deploy gate for critical features.

**How it works:**
- When `criticality: critical`, Phase 11 `predeploy-gate.md` gains four mandatory human-verified checkboxes
- Engineer signs off: dedup logic verified, timing/cron window verified, required fields verified, health endpoint accuracy verified
- PR cannot merge until all boxes ticked and reviewer confirms
- No automation — human attestation only

**Covers from failures:** All four directly — each maps to one checkbox.

**Adoption cost:** 2–3 hours (template edit + PR rule)

**Sacrifices:** Automation — a rushed engineer can tick boxes without checking. No runtime signal.

---

### A3 — Output Contract Annotation + CI Smoke *(Pragmatist — Moderate)*

**Summary:** Write `output-contracts.md` and enforce it with a single CI pytest marker — no new phases.

**How it works:**
- Author `output-contracts.md` listing invariants as one-liners
- Write corresponding tests tagged `@pytest.mark.contract`
- Add one CI step: `pytest -m contract` blocks merge on failure
- No Phase 10c, no directory restructuring, no persona changes

**Covers from failures:** Dedup, blank fields, healthz (testable); cron timing partially (fixture-based window test).

**Adoption cost:** 4–6 hours per project

**Sacrifices:** Discoverability (markers not grep-obvious), runtime monitoring (no violation events, no `/api/status`), lint enforcement of skip/xfail requires separate tooling.

---

### A4 — Tiered Enforcement (Warn → Block) *(Optimizer — Hybrid)*

**Summary:** Full Phase 10c with contract tests and CI gate, but contracts start warn-only and auto-graduate to blocking after 30 consecutive green runs.

**How it works:**
- All 10 design points implemented from day one
- Each contract has `blocking: false` by default; CI emits warnings but does not block
- CI script tracks green-run streak per contract in a committed state file
- After 30 green CI runs, contract auto-graduates to `blocking: true`
- Manual override available (`blocking: true/false` in output-contracts.md)

**Covers from failures:** All four — once graduated to blocking.

**Adoption cost:** 1–2 days initial setup; graduation is automated

**Evolves to:** Full hard gates without requiring a separate migration; mature projects can start at `blocking: true`.

---

### A5 — Skeleton Phase 10c (3-Field Template) *(Optimizer — Hybrid)*

**Summary:** Phase 10c fires but `output-contracts.md` requires only three fields — lower cognitive load with full machine linkage.

**How it works:**
- Minimal template: `assertion`, `violation_event`, `test_file` — three required fields only
- CI links `violation_event` to Prometheus counter without extra config
- Optional columns (degraded behavior, runbook URL, SLO target) added incrementally
- Schema versioning allows old contracts to remain valid as template evolves

**Covers from failures:** All four — assertion captures the invariant, violation_event enables runtime detection, test_file links to enforcement.

**Adoption cost:** 2–4 hours per feature (30 min authoring, rest test writing)

**Evolves to:** Full 6-column table as feature matures; no re-migration needed.

---

### A6 — Per-Project Config-Gated Pattern *(Optimizer — Hybrid)*

**Summary:** A `critical_features.enabled` flag in `config.yaml` activates the full pattern; disabled projects get zero overhead.

**How it works:**
- Single boolean in `config.yaml` gates all 10 design points
- When `false`: framework ships docs/templates as optional guidance; CI step is a no-op
- When `true`: all requirements enforced — Phase 10c, contract tests, CI gate, status endpoint, Grafana template, index
- Future: `enabled: strict` mode for zero-tolerance projects (all contracts blocking: true from day one)

**Covers from failures:** All four — when enabled.

**Adoption cost:** 30 min to flip flag; 1–2 days to backfill contracts for existing critical features

**Evolves to:** Mandated `enabled: true` for financial/advertising projects as the pattern matures across the org.

---

### A7 — Contract-as-Code with PactFlow Integration *(Futurist — Scalable)*

**Summary:** Machine-readable Pact contracts replace markdown, stored in a central broker with full versioning and cross-team visibility.

**How it works:**
- Each critical feature declares typed output contracts in a `.pact` file committed alongside code
- PactFlow broker (self-hosted or SaaS) stores and versions all contracts centrally
- Phase 10c verification sends results to the broker; CI fails on unverified or broken contracts
- Violation events are structured, queryable, and feed dashboards from the broker

**Covers from failures:** Silent dup blobs (schema contract), blank email columns (nullability contract), healthz mis-reporting (response contract). Cron timing requires custom extension.

**Adoption cost:** 3–4 weeks initial setup; ~2 days per project onboarding

**Enables beyond immediate problem:** Cross-team contract visibility, versioned contract history, consumer-driven contract testing at integration layer. Enables multiple projects to share contract definitions.

---

### A8 — Feature Health Platform *(Futurist — Scalable)*

**Summary:** A shared internal service all GC projects register critical features with, providing portfolio-level health visibility.

**How it works:**
- Projects push violation events via lightweight webhook after each contract check
- Platform aggregates a unified `/status` page, SLO compliance history, and trend graphs across ALL projects
- Slack/PagerDuty routing rules live in the platform, not scattered per-repo
- Single source of truth: "is anything critical degraded right now?" across all Gorilla Commerce systems

**Covers from failures:** All four — centralized detection and cross-project alerting.

**Adoption cost:** 4–6 weeks to build platform; 1 day per project to integrate

**Enables beyond immediate problem:** Portfolio-level SLO reporting, cross-project incident correlation, executive-level health dashboard for Mark. Naturally extends to STORY-592 and future projects.

---

## Deduplication and Overlap Analysis

| Approach | Core Mechanism | Enforcement | Runtime Signal | Adoption Cost |
|----------|---------------|-------------|----------------|---------------|
| A1 — README Badge | Human contract | None | None | Hours |
| A2 — Phase 11 Checklist | Human checklist | Manual | None | Hours |
| A3 — Contract Marker + CI | pytest marker | Soft CI | None | Hours |
| A4 — Tiered Warn→Block | Full pattern + graduation | Graduated hard | Violation events | Days |
| A5 — Skeleton Phase 10c | 3-field template | Hard CI | Violation events | Hours |
| A6 — Config-Gated | Full pattern, opt-in | Hard CI (when on) | Violation events | Hours (flip) |
| A7 — PactFlow | .pact files + broker | Hard CI | Broker queryable | Weeks |
| A8 — Health Platform | Shared platform | Platform-enforced | Platform | Weeks |

**A1 and A2** overlap: both are human-attestation-only; A2 is slightly more structured. Neither provides runtime signal.

**A3 and A4** are adjacent; A4 extends A3 with runtime emission and a graduation pathway. A3 is a subset of A4.

**A5 and A6** are complementary; A5 reduces template burden while A6 controls activation. They compose naturally (config-gated skeleton template).

**A7 and A8** are mutually independent forward-looking options; A8 could consume A7's contract artifacts.

---

## Top 3 Ranked (by enforcement strength × adoption feasibility)

| Rank | Approach | Why |
|------|----------|-----|
| 1 | **A4 — Tiered Warn→Block** | Full enforcement from day one, graduated adoption. Covers all failures. No adoption cliff. Matches the selected Approach A from Phase 4 analysis. |
| 2 | **A6 — Config-Gated** | Clean opt-in for existing projects; mandatory for new. Composes with A4/A5. |
| 3 | **A5 — Skeleton Phase 10c** | Lowest per-feature authoring overhead while maintaining machine linkage. Evolves gracefully. |

**The selected design (Approach A in Phase 4)** is the composition of A4 + A5 + A6: full Phase 10c with tiered blocking, a practical template, and per-project config opt-in. This validates the design decision retroactively.

---

## Discarded Approaches

| Approach | Reason Discarded |
|----------|-----------------|
| A1 — README Badge | No enforcement path. Identical to doing nothing with extra documentation. |
| A2 — Phase 11 Checklist | Human attestation is not a reliable gate. The four failures all would have passed a checkbox review ("looks fine"). |
| A7 — PactFlow Integration | 3–4 week setup cost; requires external broker infrastructure; overkill for intra-service business contracts. Better for inter-service API contracts (separate concern). |
| A8 — Feature Health Platform | 4–6 week build; platform becomes a dependency; single point of failure for cross-project health. Better as a future evolution once per-project patterns are established. |

---

## Long-Term Vision (for Expansion Agent context)

**Phase 1 (now — STORY-591/592):** Per-project pattern, config-gated, full Phase 10c + warn-by-default contracts.

**Phase 2 (future):** Skeleton Phase 10c becomes the default template; teams graduate contracts to blocking as they accumulate confidence.

**Phase 3 (future):** A8-style internal health platform aggregates per-project violation feeds into a cross-org dashboard for Mark. No per-project platform dependency needed until then.

**Phase 4 (future):** LLM-assisted contract inference (futurist A9 — not generated here but implied by A8 evolution) reduces authoring burden to review-only.
