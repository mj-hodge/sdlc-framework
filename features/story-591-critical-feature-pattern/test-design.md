# Test Design — STORY-591: Critical-Feature SDLC Pattern

**Phase:** 7 — Test Design
**Produced:** 2026-04-25
**RED State Verified:** 47 failed, 14 passed (0.79s)

---

## Overview

This is a documentation story — there is no runtime code. The outermost boundary is the **filesystem**. Every test reads framework files and asserts required content exists. Tests are RED before Phase 8 because the framework files don't yet contain the required content (or don't exist yet).

---

## Test Structure

```
tests/
├── story_591/                          # Story-level acceptance tests
│   ├── __init__.py
│   ├── conftest.py                     # Fixtures: framework_root, agents_dir, templates_dir, patterns_dir
│   ├── test_seed_template.py           # SC-1 (3 tests)
│   ├── test_new_templates.py           # SC-2, SC-9 (8 tests)
│   ├── test_patterns_doc.py            # SC-3, SC-7, SC-8, SC-10 (13 tests)
│   ├── test_agent_personas.py          # SC-4, SC-5, SC-6, SC-10 (11 tests)
│   ├── test_agents_md.py               # SC-10 (4 tests)
│   └── test_lint_enforcement.py        # SC-4, SC-12 (6 tests) ← GREEN from day one
└── critical_features/
    └── critical-feature-pattern/
        ├── README.md
        └── contracts/                  # Contract tests (C1, C2, C3 — self-referential)
            ├── conftest.py             # Fixtures: framework_root (parents[4]), agents_dir, templates_dir, patterns_dir
            ├── test_contract_c1.py     # C1: output-contracts.md complete (4 tests)
            ├── test_contract_c2.py     # C2: patterns doc covers all 10 DPs (4 tests)
            └── test_contract_c3.py     # C3: all 4 personas updated (6 tests)
```

**Total: 61 tests**

---

## Mock Boundary

No DB sessions, no HTTP clients. The outermost boundary is the **filesystem**.

All fixtures return `pathlib.Path` objects:

```python
# tests/story_591/conftest.py
framework_root = Path(__file__).parents[2]   # → sdlc-framework/

# tests/critical_features/critical-feature-pattern/contracts/conftest.py
framework_root = Path(__file__).parents[4]   # → sdlc-framework/
```

No mocks needed. Tests open files and assert content.

---

## Acceptance Criteria Coverage

| AC | Tests | Module |
|----|-------|--------|
| SC-1: Criticality field in seed.md template | 3 | test_seed_template.py |
| SC-2: output-contracts.md template created | 5 | test_new_templates.py |
| SC-3: patterns/critical-features.md created, covers 10 DPs | 13 | test_patterns_doc.py |
| SC-4: Phase 7 persona updated (contract test rules) | 4 | test_agent_personas.py |
| SC-5: Phase 10 persona updated (business contracts) | 3 | test_agent_personas.py |
| SC-6: Phase 11 persona updated (gate behavior) | 3 | test_agent_personas.py |
| SC-7: /api/status fields documented | 2 | test_patterns_doc.py |
| SC-8: Grafana template in pattern doc | 1 | test_patterns_doc.py |
| SC-9: critical-features-index.md template created | 3 | test_new_templates.py |
| SC-10: AGENTS.md + personas updated | 4+2 | test_agents_md.py, test_agent_personas.py |
| SC-11: Zero advertising-amazon specifics in framework | 1 | test_contract_c3.py |
| SC-12: skip/xfail prohibition enforced | 6 | test_lint_enforcement.py |

---

## Contract Tests (Self-Referential)

This story is itself `criticality: critical`, so it applies the pattern to itself. The contract tests in `tests/critical_features/critical-feature-pattern/contracts/` validate the framework's own completeness:

| Contract | Business Assertion | Blocking | Tests |
|----------|--------------------|----------|-------|
| C1 | output-contracts.md template is complete and machine-linkable | true | 4 |
| C2 | patterns/critical-features.md covers all 10 dispatch design points | true | 4 |
| C3 | All four agent personas (1, 7, 10, 11) contain required critical-feature sections | true | 6 |

All 3 contracts are `Blocking: true` — Phase 11 will not pass if any C1/C2/C3 test fails.

---

## RED / GREEN State

### GREEN from day one (14 tests)

These tests pass before Phase 8 because:

| Tests | Reason GREEN |
|-------|--------------|
| `test_lint_enforcement.py` (6) | Test a pure Python utility function `_has_skip_or_xfail()` — no filesystem dependency |
| `test_all_four_personas_exist` | The 4 persona files already exist (guard against deletion) |
| `test_phase7_persona_forbids_skip_xfail_in_contract_tests` | "skip" already appears in phase-7-test-design.md (incidental) |
| `test_phase7_persona_specifies_lint_enforcement_mechanism` | "grep" already appears in phase-7-test-design.md (incidental) |
| `test_phase10_persona_specifies_event_destinations` | "prometheus" already appears in phase-10-operations.md |
| `test_phase11_persona_has_critical_feature_contracts_check` | "contract" already appears in phase-11-predeploy-gate.md |
| `test_phase11_persona_documents_fail_closed_behavior` | "fail" + "missing" already appear in phase-11-predeploy-gate.md |
| `test_no_persona_update_references_advertising_amazon` | No advertising-amazon specifics in persona files |

### RED until Phase 8 (47 tests)

Failures are triggered by:

1. **`templates/output-contracts.md` does not exist** → 9 tests fail (C1 × 4, story_591 × 5)
2. **`patterns/` directory does not exist** → 13 tests fail (C2 × 4, story_591 × 9 including existence checks)
3. **`templates/seed.md` lacks Criticality field** → 3 tests fail
4. **`agents/phase-1-seed.md` lacks criticality classification** → 3 tests fail (C3-b + story_591 × 2)
5. **`agents/phase-7-test-design.md` lacks outermost-boundary/critical_features content** → 2 tests fail (C3-c + story_591)
6. **`agents/phase-10-operations.md` lacks output-contract/violation content** → 3 tests fail (C3-d + story_591 × 2)
7. **`agents/phase-11-predeploy-gate.md` lacks `missing` keyword for fail-closed** → 1 test fails (C3-e)
8. **`AGENTS.md` lacks Critical Features section** → 4 tests fail
9. **`templates/critical-features-index.md` does not exist** → 3 tests fail

All failures are `AssertionError` with `CONTRACT C* VIOLATED` or descriptive messages. No `FileNotFoundError` or import errors — tests are correctly structured to assert existence rather than crash.

---

## Phase 8 Implementation Targets

For all 47 RED tests to turn GREEN, Phase 8 must produce:

| File | Action | Tests unblocked |
|------|--------|-----------------|
| `templates/seed.md` | Add `Criticality: routine\|important\|critical` field after Scope | 3 |
| `templates/output-contracts.md` | Create new template with: ID, Assertion, Degraded Behavior, Blocking, Test File, Metric columns; worked C1 example; true/false blocking values | 9 |
| `templates/critical-features-index.md` | Create new template with feature table and on-call guidance | 3 |
| `patterns/critical-features.md` | Create new canonical pattern doc (>2000 chars) covering all 10 DPs, /api/status fields, lint enforcement script | 13 |
| `agents/phase-1-seed.md` | Add criticality classification: field definition, routine/important/critical levels, justification requirement | 3 |
| `agents/phase-7-test-design.md` | Add: critical_features/ directory path, outermost-boundary mocking rule | 2 |
| `agents/phase-10-operations.md` | Add: business-level output contracts, violation event schema with `_violation` naming | 3 |
| `agents/phase-11-predeploy-gate.md` | Add: explicit `missing` → fail-closed language for contracts directory | 1 |
| `AGENTS.md` | Add `## Critical Features` section: references pattern doc, Phase 10c path, classification rules | 4 |

---

## Naming Conventions

- Test modules: `test_<subject>.py`
- Test functions: `test_<scope>_<what>_<condition>`
- Contract tests: `test_<contract_id>_<assertion>` (e.g., `test_output_contracts_template_exists_and_is_nonempty`)
- Violation event naming in pattern: `<feature>_<contract>_violation`

---

## Lint Policy

Per the lint policy defined in `tests/critical_features/critical-feature-pattern/README.md`:

- No `@pytest.mark.skip`, `@pytest.mark.xfail`, or `pytest.skip()` in any file under `tests/critical_features/`
- Enforced by `test_lint_enforcement.py::_has_skip_or_xfail()` (GREEN from day one)
- CI will run the check script from `patterns/critical-features.md` § 4

---

## Run Commands

```bash
# All tests
pytest

# Contract tests only
pytest tests/critical_features/critical-feature-pattern/contracts/ -v

# Story acceptance tests only
pytest tests/story_591/ -v

# Confirm RED state before Phase 8
pytest --tb=line 2>&1 | tail -5
```
