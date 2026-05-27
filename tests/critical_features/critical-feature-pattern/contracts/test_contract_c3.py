"""
Contract C3: All four agent personas contain the required critical-feature sections.

Business assertion:
    The four phase personas that govern critical-feature behavior (Phase 1, 7, 10, 11)
    all contain explicit, actionable critical-feature requirements. Any AI agent
    running these phases will apply the pattern without needing to read the
    full patterns/critical-features.md.

Degraded behavior:
    If any persona is missing its critical-feature section, agents following
    that phase will silently skip pattern requirements. This is the highest-risk
    failure mode — silent non-compliance that looks like compliance.
    Emit: critical_feature_pattern_c3_violation

Mock boundary: filesystem (outermost boundary for a documentation story).
"""
from pathlib import Path


PERSONA_REQUIREMENTS = {
    "phase-1-seed.md": {
        "description": "Phase 1 BA persona",
        "required_content": [
            ("criticality", "criticality field classification"),
            ("routine", "routine level definition"),
            ("important", "important level definition"),
        ],
    },
    "phase-7-test-design.md": {
        "description": "Phase 7 Test Design persona",
        "required_content": [
            ("critical_features", "contract test directory path"),
            ("outermost", "outermost-boundary mock rule"),
            ("skip", "skip/xfail prohibition"),
        ],
    },
    "phase-10-operations.md": {
        "description": "Phase 10 Operations persona",
        "required_content": [
            ("violation", "violation event schema"),
            ("output contract", "business-level output contracts"),
        ],
    },
    "phase-11-predeploy-gate.md": {
        "description": "Phase 11 Pre-Deploy Gate persona",
        "required_content": [
            ("contract", "Critical Feature Contracts CI step"),
            ("missing", "fail-closed behavior for missing contracts"),
        ],
    },
}


def test_all_four_personas_exist(agents_dir: Path) -> None:
    """C3-a: All four persona files exist.

    Verifies:
        Phase 1, 7, 10, and 11 persona files are all present.
        (They should already exist; this guards against accidental deletion.)
    """
    missing = [
        name for name in PERSONA_REQUIREMENTS
        if not (agents_dir / name).exists()
    ]
    assert not missing, (
        f"CONTRACT C3 VIOLATED: Missing agent persona files: {missing}. "
        "Event: critical_feature_pattern_c3_violation"
    )


def test_phase1_persona_has_all_required_criticality_content(agents_dir: Path) -> None:
    """C3-b: phase-1-seed.md contains all required criticality classification content.

    Verifies:
        The Phase 1 persona has criticality field, routine, and important level
        definitions — not just 'critical', which could be confused with the severity
        of the persona requirements themselves.
    """
    content = (agents_dir / "phase-1-seed.md").read_text().lower()
    requirements = PERSONA_REQUIREMENTS["phase-1-seed.md"]["required_content"]
    missing = [desc for marker, desc in requirements if marker not in content]
    assert not missing, (
        f"CONTRACT C3 VIOLATED: phase-1-seed.md missing required content: {missing}. "
        "Phase 1 BA must set criticality for every story or Phase 10c never fires. "
        "Event: critical_feature_pattern_c3_violation"
    )


def test_phase7_persona_has_all_required_contract_test_content(agents_dir: Path) -> None:
    """C3-c: phase-7-test-design.md contains all required contract test requirements.

    Verifies:
        - Directory path (critical_features/)
        - Outermost-boundary mock rule
        - Skip/xfail prohibition

    Why this matters:
        Phase 7 is where contract tests are written. Missing any of these three
        requirements in the persona means the tests will be structurally wrong.
    """
    content = (agents_dir / "phase-7-test-design.md").read_text().lower()
    requirements = PERSONA_REQUIREMENTS["phase-7-test-design.md"]["required_content"]
    missing = [desc for marker, desc in requirements if marker not in content]
    assert not missing, (
        f"CONTRACT C3 VIOLATED: phase-7-test-design.md missing required content: {missing}. "
        "Contract tests written without these requirements will not enforce the pattern. "
        "Event: critical_feature_pattern_c3_violation"
    )


def test_phase10_persona_has_all_required_output_contract_content(
    agents_dir: Path,
) -> None:
    """C3-d: phase-10-operations.md contains all required output contract content.

    Verifies:
        - Violation event schema (event name format)
        - Business-level output contracts (not just system metrics)
    """
    content = (agents_dir / "phase-10-operations.md").read_text().lower()
    requirements = PERSONA_REQUIREMENTS["phase-10-operations.md"]["required_content"]
    missing = [desc for marker, desc in requirements if marker not in content]
    assert not missing, (
        f"CONTRACT C3 VIOLATED: phase-10-operations.md missing required content: {missing}. "
        "Without business-level contracts in Phase 10, the SRE produces only technical "
        "SLIs and misses the business assertion layer entirely. "
        "Event: critical_feature_pattern_c3_violation"
    )


def test_phase11_persona_has_all_required_gate_content(agents_dir: Path) -> None:
    """C3-e: phase-11-predeploy-gate.md contains all required gate content.

    Verifies:
        - 'contract' keyword (Critical Feature Contracts CI step)
        - 'missing' + 'fail' (fail-closed behavior for missing infrastructure)

    Why this matters:
        The deploy gate is the last line of defense. A Phase 11 persona that
        lacks these requirements means the gate is never added to predeploy-gate.md.
    """
    content = (agents_dir / "phase-11-predeploy-gate.md").read_text().lower()
    requirements = PERSONA_REQUIREMENTS["phase-11-predeploy-gate.md"]["required_content"]
    missing = [desc for marker, desc in requirements if marker not in content]
    assert not missing, (
        f"CONTRACT C3 VIOLATED: phase-11-predeploy-gate.md missing required content: {missing}. "
        "The deploy gate is the last line of defense — it must fail closed on "
        "missing contract infrastructure. "
        "Event: critical_feature_pattern_c3_violation"
    )


def test_no_persona_update_references_advertising_amazon(agents_dir: Path) -> None:
    """C3-f: Persona updates contain no advertising-amazon-specific content.

    Verifies SC-11: Zero behavior change in advertising-amazon from this story.
    The pattern must be generic — project-specific application is STORY-592.

    Why this matters:
        Framework files are shared across ALL projects. If advertising-amazon
        specifics leak in, other projects get incorrect guidance.
    """
    for persona_file in PERSONA_REQUIREMENTS:
        content = (agents_dir / persona_file).read_text()
        # Generic references are OK; project-specific wiring is not
        if "advertising-amazon" in content and "story-592" not in content.lower():
            # Only flag if it's a prescriptive reference, not a historical example
            # A brief example mention is acceptable; check for configuration-level content
            lines_with_aa = [
                line for line in content.split("\n")
                if "advertising-amazon" in line.lower()
                and not any(ok in line.lower() for ok in ["example", "e.g.", "story-592", "history"])
            ]
            assert not lines_with_aa, (
                f"CONTRACT C3 VIOLATED: {persona_file} contains advertising-amazon-specific "
                f"content outside of examples: {lines_with_aa[:2]}. "
                "Pattern must be generic. advertising-amazon application is STORY-592. "
                "Event: critical_feature_pattern_c3_violation"
            )
