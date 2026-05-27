"""
Tests for SC-1: templates/seed.md must include criticality field.

These tests will FAIL (RED) until Phase 8 adds the criticality field.
"""
from pathlib import Path
import pytest


def test_seed_template_has_criticality_row(templates_dir: Path) -> None:
    """Verifies SC-1: seed template Overview table includes a Criticality row.

    Why this matters:
        Every story classification starts in seed.md. If the criticality field
        is absent, Phase 10c never fires and critical features get no protection.

    Arrange:
        - Read templates/seed.md

    Act:
        - Search for 'Criticality' in the Overview table

    Assert:
        - 'Criticality' appears in the file content
    """
    seed = (templates_dir / "seed.md").read_text()
    assert "Criticality" in seed, (
        "templates/seed.md is missing the 'Criticality' field in the Overview table. "
        "Add: '| Criticality | <routine|important|critical> |'"
    )


def test_seed_template_criticality_lists_all_three_values(templates_dir: Path) -> None:
    """Verifies SC-1: criticality field documents all three valid values.

    Arrange:
        - Read templates/seed.md

    Assert:
        - All three values (routine, important, critical) appear near the Criticality row
    """
    seed = (templates_dir / "seed.md").read_text()
    for value in ("routine", "important", "critical"):
        assert value in seed, (
            f"templates/seed.md is missing criticality value '{value}'. "
            "The field must document all three: routine|important|critical"
        )


def test_seed_template_criticality_positioned_after_scope(templates_dir: Path) -> None:
    """Verifies SC-1: Criticality row appears after Scope in the Overview table.

    Why this matters:
        Scope and Criticality are sibling classifications. Criticality must follow
        Scope so the BA sets both before proceeding.

    Arrange:
        - Read templates/seed.md

    Assert:
        - 'Scope' line appears before 'Criticality' line
    """
    seed = (templates_dir / "seed.md").read_text()
    scope_pos = seed.find("| Scope")
    criticality_pos = seed.find("| Criticality")
    assert scope_pos != -1, "templates/seed.md missing '| Scope' row"
    assert criticality_pos != -1, "templates/seed.md missing '| Criticality' row"
    assert scope_pos < criticality_pos, (
        "Criticality row must appear after Scope row in the Overview table"
    )
