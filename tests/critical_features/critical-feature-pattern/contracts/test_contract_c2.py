"""
Contract C2: patterns/critical-features.md covers all 10 dispatch design points.

Business assertion:
    The canonical pattern document exists and covers all 10 design points
    from the dispatch. Any contributor can read this one file and understand
    the full critical-feature pattern without reading the SDLC story artifacts.

Degraded behavior:
    If the pattern doc is missing or incomplete, projects implementing STORY-592+
    will have no authoritative reference, leading to inconsistent implementations.
    Emit: critical_feature_pattern_c2_violation

Mock boundary: filesystem (outermost boundary for a documentation story).
"""
from pathlib import Path

# The 10 dispatch design points mapped to required content markers
DESIGN_POINT_MARKERS = {
    "DP1 criticality field": ["criticality", "routine", "important", "critical"],
    "DP2 output-contracts.md": ["output-contracts", "output contracts"],
    "DP3 Phase 10c": ["10c", "Phase 10c"],
    "DP4 contract test directory": ["critical_features", "contracts/"],
    "DP5 violation events": ["violation", "_violation"],
    "DP6 Phase 11 CI gate": ["Critical Feature Contracts", "deploy"],
    "DP7 /api/status pattern": ["/api/status"],
    "DP8 Grafana template": ["grafana", "dashboard"],
    "DP9 docs/critical-features.md index": ["docs/critical-features.md"],
    "DP10 AGENTS.md + personas updated": ["AGENTS.md", "persona"],
}


def test_patterns_doc_exists_and_is_comprehensive(patterns_dir: Path) -> None:
    """C2-a: patterns/critical-features.md exists and is substantively complete.

    Verifies:
        File exists and has > 2000 chars — a comprehensive canonical document,
        not a stub.

    Arrange: Locate patterns/critical-features.md
    Act: Read file
    Assert: Exists, > 2000 chars
    """
    path = patterns_dir / "critical-features.md"
    assert path.exists(), (
        "CONTRACT C2 VIOLATED: patterns/critical-features.md does not exist. "
        "Event: critical_feature_pattern_c2_violation"
    )
    content = path.read_text()
    assert len(content) > 2000, (
        "CONTRACT C2 VIOLATED: patterns/critical-features.md appears to be a stub "
        f"({len(content)} chars). The canonical pattern doc must be comprehensive. "
        "Event: critical_feature_pattern_c2_violation"
    )


def test_patterns_doc_covers_all_10_design_points(patterns_dir: Path) -> None:
    """C2-b: patterns/critical-features.md covers all 10 dispatch design points.

    Verifies:
        Each of the 10 design points from the story dispatch has at least one
        matching content marker in the canonical pattern doc.

    Why this matters:
        Mark specified 10 design points. A pattern doc that misses any one of
        them is incomplete and will lead to inconsistent project implementations.
    """
    content = (patterns_dir / "critical-features.md").read_text().lower()
    missing_points = []
    for point_name, markers in DESIGN_POINT_MARKERS.items():
        if not any(marker.lower() in content for marker in markers):
            missing_points.append(point_name)

    assert not missing_points, (
        f"CONTRACT C2 VIOLATED: patterns/critical-features.md missing coverage for: "
        f"{missing_points}. All 10 design points must be documented. "
        "Event: critical_feature_pattern_c2_violation"
    )


def test_patterns_doc_api_status_schema_is_specific(patterns_dir: Path) -> None:
    """C2-c: patterns doc specifies the /api/status response field names.

    Verifies:
        The required JSON fields are documented by name so all projects
        implement the same schema (Mark can aggregate across projects).

    Required fields: health, last_success_at, violation_count_24h, runbook_url
    """
    content = (patterns_dir / "critical-features.md").read_text()
    required_fields = ["last_success_at", "violation_count_24h", "runbook_url"]
    missing_fields = [f for f in required_fields if f not in content]
    assert not missing_fields, (
        f"CONTRACT C2 VIOLATED: patterns/critical-features.md missing /api/status "
        f"field names: {missing_fields}. All projects must implement the same schema. "
        "Event: critical_feature_pattern_c2_violation"
    )


def test_patterns_doc_lint_enforcement_is_actionable(patterns_dir: Path) -> None:
    """C2-d: patterns doc provides actionable lint enforcement (a script or command).

    Verifies:
        The lint rule for forbidding skip/xfail includes a concrete script or
        command that projects can copy-paste, not just a policy statement.

    Why this matters:
        A policy without an enforcement mechanism is advisory. SC-4 requires
        the lint to be machine-enforced.
    """
    content = (patterns_dir / "critical-features.md").read_text()
    # Must contain either a bash/shell snippet or a reference to a script
    has_enforcement = "#!/bin/bash" in content or "grep" in content or "check_contract" in content
    assert has_enforcement, (
        "CONTRACT C2 VIOLATED: patterns/critical-features.md must provide an actionable "
        "lint enforcement script (bash snippet or script reference), not just a policy "
        "statement about forbidding skip/xfail. "
        "Event: critical_feature_pattern_c2_violation"
    )
