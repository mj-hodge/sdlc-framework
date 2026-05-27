"""
Shared fixtures for critical-feature-pattern contract tests.

Mock boundary: the file system (outermost boundary for a documentation story).
There are no DB sessions or HTTP clients to mock — the feature under test
produces markdown files, so the filesystem IS the outermost boundary.

Contract tests must never use @pytest.mark.skip or @pytest.mark.xfail.
See patterns/critical-features.md § 4 for enforcement policy.
"""
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def framework_root() -> Path:
    """Return the sdlc-framework repo root.

    tests/critical_features/critical-feature-pattern/contracts/conftest.py
    is 4 levels deep from root.
    """
    return Path(__file__).parents[4]


@pytest.fixture(scope="session")
def templates_dir(framework_root: Path) -> Path:
    return framework_root / "templates"


@pytest.fixture(scope="session")
def patterns_dir(framework_root: Path) -> Path:
    return framework_root / "patterns"


@pytest.fixture(scope="session")
def agents_dir(framework_root: Path) -> Path:
    return framework_root / "agents"
