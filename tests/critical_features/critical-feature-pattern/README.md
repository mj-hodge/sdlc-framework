# Critical Feature: critical-feature-pattern

This directory contains contract tests for STORY-591: Critical-Feature SDLC Pattern.

The story itself has `criticality: critical` because if the framework pattern is wrong
or incomplete, every downstream project (advertising-amazon and beyond) will implement
the pattern incorrectly, defeating the purpose.

## Contracts

| ID | File | Assertion | Blocking |
|----|------|-----------|----------|
| C1 | test_contract_c1.py | The output-contracts.md template is complete and machine-linkable | true |
| C2 | test_contract_c2.py | patterns/critical-features.md covers all 10 dispatch design points | true |
| C3 | test_contract_c3.py | All four agent personas (1, 7, 10, 11) contain required critical-feature sections | true |

## Mock Boundary

This is a documentation story — there are no DB sessions or HTTP clients.
The outermost boundary is the **filesystem**. Contract tests read framework
files and assert required content exists.

## Running Contract Tests

```bash
pytest tests/critical_features/critical-feature-pattern/contracts/ -v
```

## Lint Policy

No `@pytest.mark.skip`, `@pytest.mark.xfail`, or `pytest.skip()` are permitted
in this directory. See `patterns/critical-features.md` § 4 for enforcement policy.
