"""
Tests for the lint enforcement logic that forbids skip/xfail in contract test directories.

These tests validate the enforcement function itself (pure logic, no file system).
They will be GREEN immediately and stay GREEN — they test a utility function
that Phase 8 must implement or that we document for per-project adoption.

SC-4: Phase 7 update — lint forbids @pytest.mark.skip / xfail in contracts/
SC-12: Fail-closed behavior when contract infrastructure is misconfigured
"""
import re
from pathlib import Path


def _has_skip_or_xfail(content: str) -> bool:
    """Return True if content contains skip or xfail markers that are forbidden
    in contract test files.

    This is the core lint logic documented in patterns/critical-features.md.
    Projects implement this as a pre-commit hook or CI script.
    """
    forbidden_patterns = [
        r"@pytest\.mark\.skip",
        r"@pytest\.mark\.xfail",
        r"pytest\.skip\(",
    ]
    return any(re.search(p, content) for p in forbidden_patterns)


# ---------------------------------------------------------------------------
# Unit tests for the lint logic (these are GREEN from day one)
# ---------------------------------------------------------------------------


def test_lint_check_detects_pytest_mark_skip() -> None:
    """Verifies lint correctly identifies @pytest.mark.skip decorator.

    Arrange: Content containing @pytest.mark.skip
    Act: Run lint check
    Assert: Returns True (violation found)
    """
    content = """
@pytest.mark.skip(reason="not implemented yet")
def test_contract_c1():
    pass
"""
    assert _has_skip_or_xfail(content) is True


def test_lint_check_detects_pytest_mark_xfail() -> None:
    """Verifies lint correctly identifies @pytest.mark.xfail decorator.

    Why this matters:
        xfail is a subtle way to suppress contract test failures. A contract
        test that is "expected to fail" provides no protection.
    """
    content = """
@pytest.mark.xfail(strict=False)
def test_contract_deduplication():
    assert result.is_deduplicated()
"""
    assert _has_skip_or_xfail(content) is True


def test_lint_check_detects_pytest_skip_call() -> None:
    """Verifies lint correctly identifies pytest.skip() runtime call.

    Arrange: Content with conditional pytest.skip() call
    """
    content = """
def test_contract_cron_window():
    if not feature_enabled:
        pytest.skip("feature not enabled")
    assert cron_ran_within_window()
"""
    assert _has_skip_or_xfail(content) is True


def test_lint_check_passes_clean_contract_test() -> None:
    """Verifies lint passes clean contract test files (no false positives).

    Arrange: Clean contract test with no skip/xfail
    Assert: Returns False (no violation)
    """
    content = """
def test_contract_deduplication_prevents_duplicate_blobs(db_session):
    # Arrange
    insert_blob(db_session, report_type="sp", date="2026-04-25", profile_id=123)

    # Act
    result = insert_blob(db_session, report_type="sp", date="2026-04-25", profile_id=123)

    # Assert
    assert result.is_duplicate_rejected
"""
    assert _has_skip_or_xfail(content) is False


def test_lint_check_passes_content_mentioning_skip_in_comments() -> None:
    """Verifies lint does not trigger on 'skip' appearing in docstrings/comments.

    Why this matters:
        A comment explaining WHY skip is forbidden should not itself trigger the lint.

    Arrange: File with 'skip' only in a comment
    Assert: Returns False (no violation)

    Implementation note:
        The regex matches @pytest.mark.skip and pytest.skip( specifically,
        not bare 'skip' substrings. This prevents false positives on docstrings
        that explain the policy.
    """
    content = """
def test_contract_c1():
    # Note: do not use pytest.mark.skip here — contract tests must never be skipped.
    # See patterns/critical-features.md for the lint enforcement policy.
    assert output_contracts_template_exists()
"""
    assert _has_skip_or_xfail(content) is False


def test_lint_check_passes_xfail_mention_in_documentation() -> None:
    """Verifies lint does not trigger on xfail mentioned in a string literal."""
    content = """
POLICY = "Contract tests must not use xfail or skip markers."

def test_contract_c2():
    assert patterns_doc_covers_all_design_points()
"""
    assert _has_skip_or_xfail(content) is False
