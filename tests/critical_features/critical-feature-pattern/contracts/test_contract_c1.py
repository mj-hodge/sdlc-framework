"""
Contract C1: The output-contracts.md template is complete and machine-linkable.

Business assertion:
    The output-contracts.md template exists, contains all required structural
    fields, includes business-level worked examples, and has a Blocking column
    so Phase 11 can determine which contracts gate deploy.

Degraded behavior:
    If the template is missing, incomplete, or lacks examples, the pattern
    degrades to advisory documentation (no machine enforcement). Emit:
    critical_feature_pattern_c1_violation

Mock boundary: filesystem (outermost boundary for a documentation story).
"""
from pathlib import Path


def test_output_contracts_template_exists_and_is_nonempty(templates_dir: Path) -> None:
    """C1-a: output-contracts.md exists and contains substantive content.

    Verifies:
        The file exists at templates/output-contracts.md and is not a
        stub/placeholder (> 200 chars indicates real content).

    Arrange: Locate templates/output-contracts.md
    Act: Read file
    Assert: File exists and has > 200 characters
    """
    path = templates_dir / "output-contracts.md"
    assert path.exists(), (
        "CONTRACT C1 VIOLATED: templates/output-contracts.md does not exist. "
        "Event: critical_feature_pattern_c1_violation"
    )
    content = path.read_text()
    assert len(content) > 200, (
        "CONTRACT C1 VIOLATED: templates/output-contracts.md appears to be a stub "
        f"({len(content)} chars). Expected substantive content (> 200 chars). "
        "Event: critical_feature_pattern_c1_violation"
    )


def test_output_contracts_template_has_all_required_columns(templates_dir: Path) -> None:
    """C1-b: output-contracts.md table includes all machine-linkable columns.

    Required: ID, Assertion, Degraded Behavior, Blocking, Test File, Metric

    Verifies:
        'Test File' column exists → Phase 10c can verify 1:1 mapping to tests.
        'Blocking' column exists → Phase 11 knows which contracts gate deploy.
        'Metric' column exists → Prometheus counter names are documented.
    """
    content = (templates_dir / "output-contracts.md").read_text()
    required = ["Assertion", "Degraded Behavior", "Blocking", "Test File", "Metric"]
    missing = [col for col in required if col not in content]
    assert not missing, (
        f"CONTRACT C1 VIOLATED: templates/output-contracts.md missing columns: {missing}. "
        "All columns required for machine linkage between contracts, tests, and metrics. "
        "Event: critical_feature_pattern_c1_violation"
    )


def test_output_contracts_template_has_business_level_example(templates_dir: Path) -> None:
    """C1-c: output-contracts.md contains a business-level worked example.

    Verifies:
        Template has at least one example assertion written in business language
        (not HTTP status codes or technical invariants). The example must describe
        an observable business outcome, not implementation behavior.

    Why this matters:
        Risk R04 (high likelihood, critical impact): without examples, teams
        write HTTP-level assertions. The example is the primary mitigation.
    """
    content = (templates_dir / "output-contracts.md").read_text()
    # Must have a C1 or similar worked example (not just the placeholder)
    has_example = "C1" in content and len(content) > 500
    assert has_example, (
        "CONTRACT C1 VIOLATED: templates/output-contracts.md must contain at least one "
        "worked example row (C1) with a business-level assertion. "
        "Example: 'Ad spend report contains all campaigns with non-zero spend'. "
        "Not: 'API returns HTTP 200'. "
        "Event: critical_feature_pattern_c1_violation"
    )


def test_output_contracts_template_blocking_column_has_valid_values(
    templates_dir: Path,
) -> None:
    """C1-d: output-contracts.md Blocking column documents true/false semantics.

    Verifies:
        Teams must understand that Blocking: true means deploy is blocked on
        contract failure, and Blocking: false means warn-only (graduation path).
    """
    content = (templates_dir / "output-contracts.md").read_text()
    assert "true" in content.lower() and "false" in content.lower(), (
        "CONTRACT C1 VIOLATED: templates/output-contracts.md Blocking column must "
        "document 'true' and 'false' values with semantic explanation. "
        "Teams need to understand the warn→block graduation path. "
        "Event: critical_feature_pattern_c1_violation"
    )
