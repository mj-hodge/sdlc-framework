# Implementation Plan — STORY-591: Critical-Feature SDLC Pattern

## Overview

All changes are to framework documentation and templates. No executable code is modified.

---

## Implementation Order

Work is ordered to minimize forward references: templates first, then personas, then top-level docs.

### Group 1: New Templates (independent, can be parallel)

#### Task 1.1: Update `templates/seed.md` — Add Criticality Field

**File:** `templates/seed.md`
**Change:** Add `| Criticality | <routine|important|critical> |` row to the Overview table after Scope.

**Effort:** 1 line change.

#### Task 1.2: Create `templates/output-contracts.md`

**File:** `templates/output-contracts.md` (NEW)
**Content:** Output contracts template per specification.md § 2.2. Includes:
- Overview table (feature, criticality, story, owner)
- Contracts table (ID, assertion, degraded behavior, blocking, test file, metric)
- 4 worked examples from advertising-amazon failures (C1-C4)
- Contract writing rules (business-level only, degraded behavior mandatory, one assertion per contract)

**Effort:** ~40 lines.

#### Task 1.3: Create `templates/critical-features-index.md`

**File:** `templates/critical-features-index.md` (NEW)
**Content:** Template for `docs/critical-features.md` per specification.md § 9.1. Includes:
- Header with purpose statement
- Feature table (name, status endpoint, contracts count, tests, dashboard, runbook, last verified)
- Instructions for maintaining the index

**Effort:** ~20 lines.

---

### Group 2: Pattern Document (depends on Group 1 for template references)

#### Task 2.1: Create `patterns/critical-features.md`

**File:** `patterns/critical-features.md` (NEW)
**Directory:** Create `patterns/` directory first.
**Content:** Canonical pattern documentation. This is the "one doc" that explains the entire critical-feature pattern. References:
- Criticality classification (from specification.md § 1)
- Output contracts (from specification.md § 2)
- Phase 10c workflow (from specification.md § 3)
- Contract test directory structure (from specification.md § 4)
- Phase 10 output contract requirements (from specification.md § 5)
- Phase 11 CI gate (from specification.md § 6)
- `/api/status` pattern (from api-design.md)
- Grafana dashboard template (from api-design.md § 4)
- Discoverability index (from specification.md § 9)
- Phase path modifications (from specification.md § 3.4)
- Lint enforcement script (from specification.md § 4.3)

**Effort:** ~200 lines. This is the largest single artifact.

---

### Group 3: Agent Persona Updates (depends on Group 2 for pattern references)

#### Task 3.1: Update `agents/phase-1-seed.md`

**File:** `agents/phase-1-seed.md`
**Changes:**
1. Add to Discovery Questions section: "Criticality classification" subsection with the 3-level criteria and classification rules
2. Add to Workflow: step between 7 and 8 — "CLASSIFY CRITICALITY" with the trigger categories
3. Add to Anti-Patterns table: "Classifying a financial-data feature as routine without justification"
4. Add to Constraints table: "Skip criticality classification | Every story needs this for Phase 10c routing"
5. Mention in Scope Classification Guide: criticality is orthogonal to scope — a Small feature can be critical

**Effort:** ~30 lines of additions across 5 locations.

#### Task 3.2: Update `agents/phase-7-test-design.md`

**File:** `agents/phase-7-test-design.md`
**Changes:**
1. Add new section: "## Critical Feature Contract Tests (criticality: critical)" after the Defensive Test Gates section
2. Content: directory structure requirement, mock boundary rules table, lint rules table, enforcement script
3. Add to Workflow: step between 5 and 6 — "IF criticality == critical: create contract test structure"
4. Add to Review & Optimization Checklist: "Contract tests for critical features" subsection
5. Add to Constraints table: "Skip contract test directory for critical features | Deploy gate will block"

**Effort:** ~50 lines of additions.

#### Task 3.3: Update `agents/phase-10-operations.md`

**File:** `agents/phase-10-operations.md`
**Changes:**
1. Add new section: "## Business-Level Output Contracts (criticality: critical)" in the SLI/SLO area
2. Content: contract-to-SLI mapping, violation event schema, event destination configuration
3. Add to Tier-Based Scope table: "Output contracts" row (N/A for routine, optional for important, required for critical)
4. Add to Workflow: step for output contract verification

**Effort:** ~40 lines of additions.

#### Task 3.4: Update `agents/phase-11-predeploy-gate.md`

**File:** `agents/phase-11-predeploy-gate.md`
**Changes:**
1. Add Check 13: Critical Feature Contracts (after Check 12)
2. Content: 4-step verification script (directory exists, tests pass, no skip/xfail, index current)
3. Add to Automated Checks list header
4. Add to Pre-Deploy Gate Checklist: Check 13 items
5. Add to `tests/predeploy/` directory listing: `check_critical_contracts.sh`

**Effort:** ~40 lines of additions.

---

### Group 4: Top-Level Documentation (depends on Groups 1-3)

#### Task 4.1: Update `AGENTS.md` — Critical Features Section

**File:** `AGENTS.md`
**Changes:**
1. Add new section "## Critical Features" after the "External API Write Safety" section
2. Content: classification rules summary, phase path modifications, output contract requirements, Phase 10c trigger, reference to `patterns/critical-features.md`
3. Update phase path table to show Phase 10c variants
4. Update Skills table to include `/phase-10c`

**Effort:** ~40 lines.

#### Task 4.2: Update `software-development-guidance.md`

**File:** `software-development-guidance.md`
**Changes:**
1. Add Phase 10c to the deliverables table
2. Add `output-contracts.md` to the deliverables table
3. Update phase path diagrams with `+ critical` variants
4. Add Phase 10c description section

**Effort:** ~20 lines.

---

## Dependency Graph

```
Group 1 (parallel)     Group 2           Group 3 (parallel)      Group 4 (parallel)
├── 1.1 seed.md    ──► 2.1 patterns/ ──► 3.1 phase-1 persona ──► 4.1 AGENTS.md
├── 1.2 output-        critical-         3.2 phase-7 persona     4.2 software-dev-
│   contracts.md       features.md       3.3 phase-10 persona        guidance.md
└── 1.3 crit-feat-                       3.4 phase-11 persona
    index.md
```

---

## Verification Checklist

After all tasks:

- [ ] `templates/seed.md` has criticality field
- [ ] `templates/output-contracts.md` exists with contract examples
- [ ] `templates/critical-features-index.md` exists with feature table template
- [ ] `patterns/critical-features.md` exists as canonical pattern doc
- [ ] `agents/phase-1-seed.md` includes criticality classification
- [ ] `agents/phase-7-test-design.md` includes contract test requirements
- [ ] `agents/phase-10-operations.md` includes business-level output contracts
- [ ] `agents/phase-11-predeploy-gate.md` includes Check 13
- [ ] `AGENTS.md` has Critical Features section
- [ ] `software-development-guidance.md` has Phase 10c and updated deliverables
- [ ] Zero references to advertising-amazon in framework files (pattern is generic)
- [ ] All examples use generic slugs or clearly marked as "example from advertising-amazon"
- [ ] Existing non-critical feature workflows are not broken (additive changes only)

---

## Commit Strategy

One commit per group:

```
commit 1: phase 8: [critical-feature-pattern] new templates — seed criticality, output contracts, features index
commit 2: phase 8: [critical-feature-pattern] canonical pattern doc — patterns/critical-features.md
commit 3: phase 8: [critical-feature-pattern] agent persona updates — phases 1, 7, 10, 11
commit 4: phase 8: [critical-feature-pattern] top-level docs — AGENTS.md + software-dev-guidance
```
