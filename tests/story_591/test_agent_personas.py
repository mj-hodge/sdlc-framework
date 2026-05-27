"""
Tests for SC-4, SC-5, SC-6, SC-10: agent personas must include critical-feature sections.

Affected personas:
  - agents/phase-1-seed.md (SC-1, SC-10)
  - agents/phase-7-test-design.md (SC-4, SC-10)
  - agents/phase-10-operations.md (SC-5, SC-10)
  - agents/phase-11-predeploy-gate.md (SC-6, SC-10, SC-12)

These tests will FAIL (RED) until Phase 8 updates all four persona files.
"""
from pathlib import Path
import pytest


# ---------------------------------------------------------------------------
# Phase 1 persona — SC-1, SC-10
# ---------------------------------------------------------------------------


def test_phase1_persona_includes_criticality_classification(agents_dir: Path) -> None:
    """Verifies SC-1/SC-10: phase-1-seed.md includes criticality classification step.

    Why this matters:
        The Phase 1 BA sets criticality for every story. Without explicit
        instructions in the persona, agents will omit the field.
    """
    content = (agents_dir / "phase-1-seed.md").read_text()
    assert "criticality" in content.lower(), (
        "agents/phase-1-seed.md must include criticality classification. "
        "Add to Workflow and Discovery Questions sections."
    )


def test_phase1_persona_documents_all_three_criticality_levels(agents_dir: Path) -> None:
    """Verifies SC-1: phase-1-seed.md documents routine/important/critical levels."""
    content = (agents_dir / "phase-1-seed.md").read_text()
    for level in ("routine", "important", "critical"):
        assert level in content.lower(), (
            f"agents/phase-1-seed.md must document criticality level '{level}' "
            "with criteria for when to use it."
        )


def test_phase1_persona_requires_justification_for_routine_on_critical_systems(
    agents_dir: Path,
) -> None:
    """Verifies SC-1: persona requires justification when classifying financial/timing
    features as routine.

    Why this matters:
        Risk R02 — teams default to 'routine' to skip Phase 10c. The persona must
        explicitly block this for high-risk categories.
    """
    content = (agents_dir / "phase-1-seed.md").read_text()
    # Persona must mention justification requirement for routine classification
    assert "justif" in content.lower(), (
        "agents/phase-1-seed.md must require a justification when classifying "
        "financial/timing/health features as 'routine'."
    )


# ---------------------------------------------------------------------------
# Phase 7 persona — SC-4, SC-10
# ---------------------------------------------------------------------------


def test_phase7_persona_requires_contract_test_directory_for_critical_features(
    agents_dir: Path,
) -> None:
    """Verifies SC-4: phase-7-test-design.md requires tests/critical_features/ directory.

    Why this matters:
        Without explicit persona instructions, agents will put contract tests
        in the regular tests/ directory where they're not grep-discoverable.
    """
    content = (agents_dir / "phase-7-test-design.md").read_text()
    assert "critical_features" in content, (
        "agents/phase-7-test-design.md must require the "
        "tests/critical_features/<slug>/contracts/ directory structure."
    )


def test_phase7_persona_specifies_outermost_boundary_mocking(agents_dir: Path) -> None:
    """Verifies SC-4: phase-7-test-design.md specifies outermost-boundary mock rule.

    Why this matters:
        Deep mocking (mocking individual SQL queries) passes even when the
        actual query is broken. Outermost-boundary mocking catches real failures.
    """
    content = (agents_dir / "phase-7-test-design.md").read_text()
    assert "outermost" in content.lower() or "session factory" in content.lower(), (
        "agents/phase-7-test-design.md must specify that contract tests mock "
        "at the outermost boundaries only (DB session factory, httpx client)."
    )


def test_phase7_persona_forbids_skip_xfail_in_contract_tests(agents_dir: Path) -> None:
    """Verifies SC-4: phase-7-test-design.md forbids @pytest.mark.skip/xfail in contracts.

    Why this matters:
        Skipped contract tests provide false confidence. The pattern breaks down
        if engineers can suppress failing contracts without removing them.
    """
    content = (agents_dir / "phase-7-test-design.md").read_text()
    assert "skip" in content.lower() and "xfail" in content.lower(), (
        "agents/phase-7-test-design.md must explicitly forbid @pytest.mark.skip "
        "and @pytest.mark.xfail in the contracts/ directory."
    )


def test_phase7_persona_specifies_lint_enforcement_mechanism(agents_dir: Path) -> None:
    """Verifies SC-4: phase-7-test-design.md documents how lint is enforced.

    Assert: Contains a reference to the lint check script or CI enforcement
    """
    content = (agents_dir / "phase-7-test-design.md").read_text()
    assert "lint" in content.lower() or "check_contract" in content.lower(), (
        "agents/phase-7-test-design.md must document the lint enforcement mechanism "
        "(pre-commit or CI script) that blocks skip/xfail in contracts/."
    )


# ---------------------------------------------------------------------------
# Phase 10 persona — SC-5, SC-10
# ---------------------------------------------------------------------------


def test_phase10_persona_requires_business_level_output_contracts(agents_dir: Path) -> None:
    """Verifies SC-5: phase-10-operations.md requires business-level output contracts.

    Why this matters:
        Without explicit persona instructions, the SRE will define only technical
        SLIs (latency, error rate), missing the business assertion layer.
    """
    content = (agents_dir / "phase-10-operations.md").read_text()
    assert "output contract" in content.lower() or "criticality" in content.lower(), (
        "agents/phase-10-operations.md must require business-level output contracts "
        "for critical features, not just system metrics."
    )


def test_phase10_persona_documents_violation_event_schema(agents_dir: Path) -> None:
    """Verifies SC-5: phase-10-operations.md documents the structured violation event format.

    Assert: Contains violation event naming convention or schema
    """
    content = (agents_dir / "phase-10-operations.md").read_text()
    assert "violation" in content.lower(), (
        "agents/phase-10-operations.md must document the <feature>_<contract>_violation "
        "structured event schema for runtime contract breach detection."
    )


def test_phase10_persona_specifies_event_destinations(agents_dir: Path) -> None:
    """Verifies SC-5: phase-10-operations.md specifies violation event destinations.

    Assert: Mentions structured log, Prometheus counter, or alert webhook
    """
    content = (agents_dir / "phase-10-operations.md").read_text()
    destinations_mentioned = any(
        d in content.lower()
        for d in ("prometheus", "structured log", "alert", "webhook")
    )
    assert destinations_mentioned, (
        "agents/phase-10-operations.md must specify violation event destinations: "
        "structured log (always), Prometheus counter, optional alert webhook."
    )


# ---------------------------------------------------------------------------
# Phase 11 persona — SC-6, SC-10, SC-12
# ---------------------------------------------------------------------------


def test_phase11_persona_has_critical_feature_contracts_check(agents_dir: Path) -> None:
    """Verifies SC-6: phase-11-predeploy-gate.md contains Check 13 or equivalent.

    Why this matters:
        The deploy gate is the last line of defense. Without a named, explicit
        check in the Phase 11 persona, agents won't add it to predeploy-gate.md.
    """
    content = (agents_dir / "phase-11-predeploy-gate.md").read_text()
    assert "Critical Feature Contracts" in content or "contract" in content.lower(), (
        "agents/phase-11-predeploy-gate.md must contain a 'Critical Feature Contracts' "
        "CI step (Check 13) that blocks deploy on failure."
    )


def test_phase11_persona_documents_fail_closed_behavior(agents_dir: Path) -> None:
    """Verifies SC-12: phase-11-predeploy-gate.md documents fail-closed behavior.

    Why this matters:
        If contract infrastructure is missing (no contracts/ directory), the gate
        must FAIL (block deploy) — not silently pass. This is SC-12.

    Assert: Contains fail-closed language for missing contract tests
    """
    content = (agents_dir / "phase-11-predeploy-gate.md").read_text()
    assert "missing" in content.lower() and "fail" in content.lower(), (
        "agents/phase-11-predeploy-gate.md must document fail-closed behavior: "
        "missing contract tests for a critical feature = deploy blocked."
    )


def test_phase11_persona_specifies_contracts_directory_check(agents_dir: Path) -> None:
    """Verifies SC-12: phase-11-predeploy-gate.md verifies contracts directory exists.

    Assert: Contains a check for the contracts/ directory
    """
    content = (agents_dir / "phase-11-predeploy-gate.md").read_text()
    assert "contracts" in content.lower() and ("critical_features" in content or "critical-features" in content), (
        "agents/phase-11-predeploy-gate.md must check that "
        "tests/critical_features/<slug>/contracts/ exists for each critical feature."
    )
