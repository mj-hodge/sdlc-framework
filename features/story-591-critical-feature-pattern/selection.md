# Selection — STORY-591: Critical-Feature SDLC Pattern

> **Note:** Phase 5 was initially skipped by the phase runner (dispatched directly to Phase 6). This document is produced retroactively to complete the Large-scope artifact set. The design (Phase 6) was already executed; this selection formalizes the decision and MVP scope that drove it.

## Decision

**Selected approach: A4 + A5 + A6 composition — Full Phase 10c with Tiered Blocking, Skeleton Template, and Config-Gated Activation**

This is the approach implemented in Phase 6 (specification.md, architecture.md, api-design.md, implementation-plan.md).

---

## Top 3 Compared

| Criterion | A4 Tiered Warn→Block | A5 Skeleton Phase 10c | A6 Config-Gated | Composition |
|-----------|---------------------|----------------------|-----------------|-------------|
| Prevents the 4 failures | ✅ When graduated | ✅ | ✅ When enabled | ✅ |
| Enforcement strength | High (graduated) | High | High (when on) | High |
| Adoption friction | Medium | Low | Very low | Low |
| Runtime signal | ✅ Violation events | ✅ | ✅ | ✅ |
| Discoverability | ✅ /api/status + index | ✅ | ✅ | ✅ |
| Backward compatible | ✅ | ✅ | ✅ | ✅ |
| Allows gradual rollout | ✅ (warn first) | ✅ (optional cols) | ✅ (opt-in) | ✅ |
| STORY-592 unblockable | ✅ | ✅ | ✅ | ✅ |

**Why composition over single approach:**
- A4 alone requires teams to commit to the full template immediately — the skeleton template (A5) reduces that day-one burden
- A5 alone doesn't address whether new projects opt in — the config gate (A6) makes activation explicit and auditable
- A6 alone without A4's warn→block graduation means the first violation always blocks — teams need the ramp-up period

The composition is not "more complex than any single approach" — it is three orthogonal concerns (enforcement model, template complexity, activation) each handled simply.

---

## Rationale

### Why not A1 (README Badge) or A2 (Checklist)?

Both are human-attestation-only. The four advertising-amazon failures would have passed a checkbox review — each looked "fine" on the surface. Silent deduplication failure and healthz mis-reporting are exactly the class of failure that human attestation misses. Advisory documentation is necessary (README guidance) but never sufficient as the sole gate.

### Why not A3 (pytest marker) alone?

The `@pytest.mark.contract` approach is adopted inside A4's contract tests, but markers are not the directory structure. Marker-based enforcement cannot prevent `skip/xfail` without a lint rule that would require the same infrastructure as the directory-based approach. The directory structure gives grep-discoverability for free; markers do not.

### Why not A7 (PactFlow) or A8 (Feature Health Platform)?

**A7:** PactFlow enforces API shape contracts between services via a broker. The four failures are intra-service behavioral failures (deduplication logic, cron scheduler state, field population, health computation). PactFlow would not have caught any of them. It also requires 3–4 weeks of broker infrastructure setup per project — too expensive for the immediate STORY-592 timeline.

**A8:** A cross-org health platform is the right long-term evolution (see Long-Term Vision in expansion.md) but is premature as v1. Building it before the per-project pattern is proven in production would be solving the wrong abstraction level. The per-project `/api/status` approach provides 80% of the value (operator visibility during incidents) without the platform dependency.

---

## MVP Scope (v1 — This Story)

### In scope

| Item | Rationale |
|------|-----------|
| `criticality: routine\|important\|critical` field in seed template | Gate on which everything else depends |
| `output-contracts.md` template with 3 required + 3 optional fields | Skeleton approach (A5) — low friction |
| `critical-features-index.md` template for `docs/critical-features.md` | Single grep target for Mark |
| `patterns/critical-features.md` canonical doc | One place for the full pattern |
| Phase 1 persona update: criticality classification | Captures at source |
| Phase 7 persona update: contract test directory + lint rules | Hardens testing |
| Phase 10 persona update: business-level output contracts + violation events | Runtime detection |
| Phase 11 persona update: Check 13 Critical Feature Contracts | Deploy gate |
| Phase 10c definition in AGENTS.md + software-dev-guidance | Routing + documentation |
| `AGENTS.md` Critical Features section | Discoverability for agents |
| `/api/status` JSON pattern (specification) | Operator health endpoint |
| `/status` HTML pattern (specification) | Human dashboard |
| Violation event schema | Runtime signal |
| Grafana dashboard template (JSON skeleton) | Visualization |

### Out of scope for v1

| Item | Deferred to |
|------|-------------|
| Implementing `/api/status` in advertising-amazon | STORY-592 |
| Implementing violation event emission in advertising-amazon | STORY-592 |
| Actual Grafana dashboards for advertising-amazon | STORY-592 |
| `docs/critical-features.md` population for advertising-amazon | STORY-592 |
| PactFlow broker integration | Future (if needed) |
| Cross-org Feature Health Platform | Future (A8) |
| LLM-assisted contract inference | Future |
| Phase 10c skill file (`.claude/skills/phase-10c/SKILL.md`) | STORY-592 or follow-up |
| Retroactive contract coverage for existing advertising-amazon features | STORY-592+ |

---

## Migration / Integration Strategy

### For existing projects (pre-pattern)

1. Bump SDLC submodule to pick up framework changes
2. Add `criticality: routine` to existing stories' seeds (no new gates triggered)
3. For any existing feature that *should* be critical: create a new story (`criticality: critical`) with Phase 10c scope — do not retroactively apply Phase 10c to an already-shipped Phase 8
4. First critical feature (advertising-amazon SP report sync) applies the full pattern via STORY-592

### For new projects

1. Initialize with updated `config.yaml` template (includes `critical_features: {}` section placeholder)
2. First `criticality: critical` story automatically triggers Phase 10c in the phase path
3. `docs/critical-features.md` created when first critical feature completes Phase 10c

### For the SDLC framework itself

Phase 10c is added to the phase path documentation **only for `criticality: critical` stories**. Non-critical stories experience zero change. The framework update is additive everywhere.

---

## Risks Accepted

| Risk | Accepted because |
|------|-----------------|
| Agents classify features as `routine` to avoid Phase 10c | Mitigated by Phase 1 persona requiring justification for routine on financial/timing/health features |
| Contracts written at technical level (HTTP 200) not business level | Mitigated by template examples and persona prohibition on code-level assertions |
| Warn-only default means no hard gates initially | Accepted — better to build contract coverage first, then graduate. One prevented incident per quarter pays back the investment. |
| `blocking: false` default could lull teams into false confidence | Mitigated by Phase 11 Check 13 which validates contracts *exist* (not just that they pass) |

---

## Fallback

If the full Phase 10c approach proves too heavyweight after STORY-592 validation:
- **Fallback to A3 (pytest marker):** Remove Phase 10c from the phase path, use `@pytest.mark.contract` with a single CI step. Lose: directory discoverability, runtime violation events, `/api/status` pattern. Keep: contract test enforcement.
- **Fallback to A2 (Phase 11 checklist):** Remove all automated enforcement, keep the Phase 11 checklist items only. Minimum viable protection for projects that cannot absorb the testing overhead.

The fallback decision should be made after STORY-592 validates the pattern on one real project (advertising-amazon).

---

## Next Phase

Phase 6 (Design) — complete. All specification, architecture, API design, and implementation planning done.
Next active phase: **Phase 7 (Test Design)**.
