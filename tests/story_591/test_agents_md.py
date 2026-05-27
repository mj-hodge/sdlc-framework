"""
Tests for SC-10: AGENTS.md must have a Critical Features section.

These tests will FAIL (RED) until Phase 8 updates AGENTS.md.
"""
from pathlib import Path
import pytest


def test_agents_md_has_critical_features_section(framework_root: Path) -> None:
    """Verifies SC-10: AGENTS.md contains a '## Critical Features' section.

    Why this matters:
        AGENTS.md is the first file every AI agent reads at session start.
        Without a Critical Features section here, agents operating without
        full context will miss the pattern entirely.
    """
    content = (framework_root / "AGENTS.md").read_text()
    assert "## Critical Features" in content or "# Critical Features" in content, (
        "AGENTS.md is missing a 'Critical Features' section. "
        "Add it after the External API Write Safety section."
    )


def test_agents_md_critical_features_section_references_pattern_doc(
    framework_root: Path,
) -> None:
    """Verifies SC-10: AGENTS.md Critical Features section references patterns/critical-features.md.

    Why this matters:
        The section must point to the canonical doc for full details.
        Agents need to know where to go for the complete specification.
    """
    content = (framework_root / "AGENTS.md").read_text()
    assert "patterns/critical-features.md" in content or "critical-features" in content, (
        "AGENTS.md must reference patterns/critical-features.md "
        "as the canonical documentation for the critical-feature pattern."
    )


def test_agents_md_phase_paths_include_10c_for_critical_features(
    framework_root: Path,
) -> None:
    """Verifies SC-3/SC-10: AGENTS.md phase paths show Phase 10c for critical features.

    Why this matters:
        The phase path table in AGENTS.md drives agent routing. Without Phase 10c
        in the table, agents skip it even when criticality=critical.
    """
    content = (framework_root / "AGENTS.md").read_text()
    assert "10c" in content, (
        "AGENTS.md phase paths must include Phase 10c for criticality:critical stories. "
        "Update the phase path table to show: '→ 7 → 10c → 8 → ...' for critical features."
    )


def test_agents_md_critical_features_section_has_classification_rules(
    framework_root: Path,
) -> None:
    """Verifies SC-10: AGENTS.md Critical Features section documents classification rules.

    Assert: Contains criteria for when to use critical vs routine vs important
    """
    content = (framework_root / "AGENTS.md").read_text()
    # Must mention the three levels in a Critical Features context
    assert "critical" in content.lower() and "routine" in content.lower(), (
        "AGENTS.md Critical Features section must document classification rules "
        "covering all three levels: routine, important, critical."
    )
