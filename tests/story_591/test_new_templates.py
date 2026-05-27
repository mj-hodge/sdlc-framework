"""
Tests for SC-2 and SC-9: new template files must exist with correct structure.

SC-2: templates/output-contracts.md — output contract template
SC-9: templates/critical-features-index.md — index template for docs/critical-features.md

These tests will FAIL (RED) until Phase 8 creates both files.
"""
from pathlib import Path
import pytest


# ---------------------------------------------------------------------------
# SC-2: output-contracts.md template
# ---------------------------------------------------------------------------


def test_output_contracts_template_exists(templates_dir: Path) -> None:
    """Verifies SC-2: templates/output-contracts.md file exists.

    Why this matters:
        Without this template, teams have no structured way to define business
        assertions. Ad-hoc markdown will diverge across projects.
    """
    path = templates_dir / "output-contracts.md"
    assert path.exists(), (
        "templates/output-contracts.md does not exist. "
        "Create it from specification.md § 2.2."
    )


def test_output_contracts_template_has_contracts_table(templates_dir: Path) -> None:
    """Verifies SC-2: output-contracts.md contains a contracts table with required columns.

    Required columns: ID, Assertion, Degraded Behavior, Blocking, Test File, Metric

    Why this matters:
        The 'Blocking' column controls the deploy gate. The 'Test File' column
        creates the machine-linkable 1:1 mapping to contract tests. Both are
        essential for Phase 10c and Phase 11 automation.
    """
    content = (templates_dir / "output-contracts.md").read_text()
    required_columns = ["Assertion", "Degraded Behavior", "Blocking", "Test File", "Metric"]
    for col in required_columns:
        assert col in content, (
            f"templates/output-contracts.md is missing required column '{col}'. "
            f"Required columns: {required_columns}"
        )


def test_output_contracts_template_has_overview_table(templates_dir: Path) -> None:
    """Verifies SC-2: output-contracts.md has an Overview table (feature, story, owner).

    Why this matters:
        Without owner + story fields, contracts are orphaned — no one knows which
        story added them or who is responsible for maintaining them.
    """
    content = (templates_dir / "output-contracts.md").read_text()
    for field in ("Feature", "Story", "Owner"):
        assert field in content, (
            f"templates/output-contracts.md missing Overview field '{field}'"
        )


def test_output_contracts_template_has_worked_examples(templates_dir: Path) -> None:
    """Verifies SC-2: output-contracts.md contains worked example rows.

    Why this matters:
        Without examples, engineers write HTTP-level assertions (status 200)
        instead of business-level assertions (ad spend submitted before window).
        Examples are the primary defense against wrong abstraction level (Risk R04).
    """
    content = (templates_dir / "output-contracts.md").read_text()
    # Template must show at least one concrete example assertion
    # (not just the placeholder <assertion> text)
    assert "C1" in content, (
        "templates/output-contracts.md must contain at least one worked example "
        "row (e.g., C1) showing a business-level assertion."
    )


def test_output_contracts_blocking_field_has_true_false_values(templates_dir: Path) -> None:
    """Verifies SC-2: the Blocking column documents true/false values.

    Why this matters:
        The warn→block graduation pattern requires teams to understand
        this field controls whether Phase 11 blocks deploy.
    """
    content = (templates_dir / "output-contracts.md").read_text()
    assert "true" in content.lower() and "false" in content.lower(), (
        "templates/output-contracts.md must show 'true' and 'false' as valid "
        "Blocking field values so teams understand the warn→block graduation pattern."
    )


# ---------------------------------------------------------------------------
# SC-9: critical-features-index.md template
# ---------------------------------------------------------------------------


def test_critical_features_index_template_exists(templates_dir: Path) -> None:
    """Verifies SC-9: templates/critical-features-index.md file exists.

    Why this matters:
        Without a template, each project's docs/critical-features.md will have
        a different structure. Mark cannot grep a consistent format across projects.
    """
    path = templates_dir / "critical-features-index.md"
    assert path.exists(), (
        "templates/critical-features-index.md does not exist. "
        "Create it from specification.md § 9.1."
    )


def test_critical_features_index_has_feature_table(templates_dir: Path) -> None:
    """Verifies SC-9: index template has a feature table with required columns.

    Required columns: Feature, Status, Contracts, Tests, Dashboard, Runbook, Last Verified

    Why this matters:
        Mark must be able to grep one file and see: what's protected, how to
        reach the status endpoint, where the tests are, and how fresh the info is.
    """
    content = (templates_dir / "critical-features-index.md").read_text()
    required_columns = ["Feature", "Runbook", "Last Verified"]
    for col in required_columns:
        assert col in content, (
            f"templates/critical-features-index.md missing column '{col}'. "
            "Mark needs this to assess coverage at a glance."
        )


def test_critical_features_index_has_on_call_guidance(templates_dir: Path) -> None:
    """Verifies SC-9: index template explains its purpose to on-call operators.

    Why this matters:
        During an incident, an operator who has never seen the file must immediately
        understand what it is and how to use it.
    """
    content = (templates_dir / "critical-features-index.md").read_text()
    # File should mention its on-call / incident use case
    assert any(phrase in content.lower() for phrase in ("on-call", "on call", "incident")), (
        "templates/critical-features-index.md should explain its purpose to on-call "
        "operators in the file header."
    )
