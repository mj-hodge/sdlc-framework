"""
Shared fixtures for STORY-591 tests.
All tests in this package validate that framework files have been updated
with the critical-feature pattern (Phase 8 implementation targets).
"""
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def framework_root() -> Path:
    """Return the sdlc-framework repo root.

    tests/story_591/conftest.py is 2 levels deep from root.
    """
    return Path(__file__).parents[2]


@pytest.fixture(scope="session")
def agents_dir(framework_root: Path) -> Path:
    return framework_root / "agents"


@pytest.fixture(scope="session")
def templates_dir(framework_root: Path) -> Path:
    return framework_root / "templates"


@pytest.fixture(scope="session")
def patterns_dir(framework_root: Path) -> Path:
    return framework_root / "patterns"
