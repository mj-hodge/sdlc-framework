# Development Tasks

Active tasks for SDLC Framework — STORY-591: Critical-Feature Pattern.

---

## TASK 1: Update Seed Template with Criticality Field

**Status:** [ ] Not Started

**Problem:** The seed template has no way to classify feature criticality. All features are treated equally.

**File(s) to Edit:** `templates/seed.md`

**Steps:**
1. Add `Criticality` row to the Overview table: `routine|important|critical`
2. Add guidance comment explaining when to use each level

**Verification:**
- [ ] Criticality field present in template
- [ ] Phase 1 persona references the field

---

## TASK 2: Create Output Contracts Template

**Status:** [ ] Not Started

**Problem:** No template exists for business-level output assertions.

**File(s) to Edit:** `templates/output-contracts.md` (NEW)

**Steps:**
1. Create template with one-line business assertions format
2. Include columns: contract name, assertion, degraded-input behavior, test file mapping, metric name

**Verification:**
- [ ] Template file exists at `templates/output-contracts.md`

---

## TASK 3: Create Critical Features Index Template

**Status:** [ ] Not Started

**Problem:** No discoverable index of protected features per project.

**File(s) to Edit:** `templates/critical-features-index.md` (NEW)

**Steps:**
1. Create template for `docs/critical-features.md` with feature table
2. Include: feature name, status endpoint, dashboard link, runbook, contract count, last verified

**Verification:**
- [ ] Template file exists at `templates/critical-features-index.md`

---

## TASK 4: Create Canonical Pattern Document

**Status:** [ ] Not Started

**Problem:** No central documentation of the critical-feature pattern.

**File(s) to Edit:** `patterns/critical-features.md` (NEW)

**Steps:**
1. Create `patterns/` directory
2. Document full pattern: criticality classification, output contracts, Phase 10c, test structure, CI gates, status endpoints, dashboards, index
3. Include `/api/status` JSON schema and `/status` HTML specification
4. Include Grafana dashboard template

**Verification:**
- [ ] Pattern doc exists at `patterns/critical-features.md`
- [ ] Covers all 10 design points from dispatch

---

## TASK 5: Update Agent Personas

**Status:** [ ] Not Started

**Problem:** Phase 1, 7, 10, 11 personas don't know about critical features.

**File(s) to Edit:** `agents/phase-1-seed.md`, `agents/phase-7-test-design.md`, `agents/phase-10-operations.md`, `agents/phase-11-predeploy-gate.md`

**Steps:**
1. Phase 1: Add criticality classification to workflow, anti-patterns, scope guide
2. Phase 7: Add critical-feature test directory requirements, mock boundaries, lint rules
3. Phase 10: Add business-level output contracts, violation event requirements
4. Phase 11: Add Critical Feature Contracts CI step, fail-closed behavior

**Verification:**
- [ ] Each persona file references critical-feature requirements
- [ ] Phase 10c agent persona created if needed

---

## TASK 6: Update AGENTS.md

**Status:** [ ] Not Started

**Problem:** AGENTS.md has no Critical Features section.

**File(s) to Edit:** `AGENTS.md`

**Steps:**
1. Add Critical Features section with: classification rules, phase path modifications, output contract requirements
2. Update phase path table to show Phase 10c for critical features
3. Reference `patterns/critical-features.md` for full details

**Verification:**
- [ ] Critical Features section exists in AGENTS.md
- [ ] Phase paths updated

---

## TASK 7: Update software-development-guidance.md

**Status:** [ ] Not Started

**Problem:** Main guidance doc doesn't document Phase 10c or critical-feature requirements.

**File(s) to Edit:** `software-development-guidance.md`

**Steps:**
1. Add Phase 10c documentation
2. Update deliverables table
3. Update phase path diagrams

**Verification:**
- [ ] Phase 10c documented
- [ ] Deliverables table includes output-contracts.md and Phase 10c artifacts

---

## Completed Tasks

<details>
<summary>Click to expand</summary>

### Phase 1: Seed
- Completed: 2026-04-25
- Summary: Created seed.md with full problem statement, 12 acceptance criteria, design points, and deliverable inventory. Scope: Large. Criticality: Critical.

</details>
