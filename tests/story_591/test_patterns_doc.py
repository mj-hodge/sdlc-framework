"""
Tests for SC-3, SC-7, SC-8, SC-10: patterns/critical-features.md must exist
and cover all 10 design points.

These tests will FAIL (RED) until Phase 8 creates the patterns doc.
"""
from pathlib import Path
import pytest


def test_patterns_directory_exists(framework_root: Path) -> None:
    """Verifies SC-10: patterns/ directory exists in the framework.

    Why this matters:
        The patterns/ directory is a new top-level framework concept.
        It must exist before any pattern doc can live there.
    """
    patterns = framework_root / "patterns"
    assert patterns.is_dir(), (
        "patterns/ directory does not exist at the framework root. "
        "Create it and add patterns/critical-features.md."
    )


def test_critical_features_pattern_doc_exists(patterns_dir: Path) -> None:
    """Verifies SC-10: patterns/critical-features.md exists.

    Why this matters:
        This is the canonical 'one doc' for the entire pattern.
        All other files reference it; it must exist first.
    """
    path = patterns_dir / "critical-features.md"
    assert path.exists(), (
        "patterns/critical-features.md does not exist. "
        "Create it from implementation-plan.md Task 2.1."
    )


def test_pattern_doc_covers_criticality_classification(patterns_dir: Path) -> None:
    """Verifies SC-1/SC-10: patterns doc explains criticality classification.

    Arrange: Read patterns/critical-features.md
    Assert: Contains classification criteria for routine/important/critical
    """
    content = (patterns_dir / "critical-features.md").read_text()
    for level in ("routine", "important", "critical"):
        assert level in content, (
            f"patterns/critical-features.md missing criticality level '{level}'. "
            "Must document all three levels with classification criteria."
        )


def test_pattern_doc_covers_output_contracts(patterns_dir: Path) -> None:
    """Verifies SC-2/SC-10: patterns doc explains output contracts.

    Assert: Contains 'output contract' or 'output-contract' concept
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "output contract" in content.lower() or "output-contract" in content.lower(), (
        "patterns/critical-features.md must explain the output contract concept."
    )


def test_pattern_doc_covers_phase_10c(patterns_dir: Path) -> None:
    """Verifies SC-3/SC-10: patterns doc documents Phase 10c.

    Why this matters:
        Phase 10c is a new phase not in the existing framework. Without documentation
        in the canonical pattern doc, agents won't know it exists.
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "10c" in content or "Phase 10c" in content, (
        "patterns/critical-features.md must document Phase 10c (Output Contract Hardening)."
    )


def test_pattern_doc_covers_contract_test_directory(patterns_dir: Path) -> None:
    """Verifies SC-4/SC-10: patterns doc specifies contract test directory structure.

    Assert: Contains reference to tests/critical_features/ directory
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "critical_features" in content or "critical-features" in content, (
        "patterns/critical-features.md must document the contract test directory: "
        "tests/critical_features/<slug>/contracts/"
    )


def test_pattern_doc_covers_api_status_pattern(patterns_dir: Path) -> None:
    """Verifies SC-7/SC-10: patterns doc documents the /api/status endpoint pattern.

    Why this matters:
        Without specification in the canonical doc, every project will implement
        a different status endpoint schema. Mark cannot aggregate across projects.
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "/api/status" in content, (
        "patterns/critical-features.md must document the /api/status JSON endpoint pattern."
    )


def test_pattern_doc_covers_violation_events(patterns_dir: Path) -> None:
    """Verifies SC-5/SC-10: patterns doc documents structured violation events.

    Assert: Contains violation event schema
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "violation" in content.lower(), (
        "patterns/critical-features.md must document the structured violation event schema."
    )


def test_pattern_doc_covers_grafana_dashboard(patterns_dir: Path) -> None:
    """Verifies SC-8/SC-10: patterns doc documents the Grafana dashboard template.

    Why this matters:
        Without a template, each project builds a different dashboard.
        Mark needs consistent health-color SLO panels across all projects.
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "grafana" in content.lower() or "dashboard" in content.lower(), (
        "patterns/critical-features.md must document the Grafana dashboard template."
    )


def test_pattern_doc_covers_critical_features_index_requirement(patterns_dir: Path) -> None:
    """Verifies SC-9/SC-10: patterns doc mandates docs/critical-features.md per project.

    Why this matters:
        The single-index requirement must be documented in the canonical pattern
        so teams know it's mandatory, not optional.
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "docs/critical-features.md" in content, (
        "patterns/critical-features.md must mandate docs/critical-features.md "
        "as the single index of protected features per project."
    )


def test_pattern_doc_covers_ci_gate(patterns_dir: Path) -> None:
    """Verifies SC-6/SC-10: patterns doc documents the Critical Feature Contracts CI step.

    Assert: Contains the named CI step or deploy gate requirement
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "Critical Feature Contracts" in content or "deploy" in content.lower(), (
        "patterns/critical-features.md must document the 'Critical Feature Contracts' "
        "CI step that blocks deploy."
    )


def test_pattern_doc_covers_phase_path_modifications(patterns_dir: Path) -> None:
    """Verifies SC-3/SC-10: patterns doc shows modified phase paths for critical features.

    Assert: Contains updated phase path showing 10c injection
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "10c" in content, (
        "patterns/critical-features.md must show modified phase paths with Phase 10c "
        "injected for critical features."
    )


def test_pattern_doc_covers_lint_enforcement(patterns_dir: Path) -> None:
    """Verifies SC-4: patterns doc documents lint rule forbidding skip/xfail in contracts.

    Why this matters:
        Without lint enforcement, developers under time pressure will skip failing
        contract tests. The pattern must document how to prevent this.
    """
    content = (patterns_dir / "critical-features.md").read_text()
    assert "skip" in content.lower() and ("xfail" in content.lower() or "forbid" in content.lower()), (
        "patterns/critical-features.md must document the lint rule forbidding "
        "@pytest.mark.skip and @pytest.mark.xfail in contract test directories."
    )
