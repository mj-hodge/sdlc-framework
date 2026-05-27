"""
Tests for retro 2026-05-01 Tier-A item A-1:
  templates/scripts/check_migrations.py — Alembic revision-collision detector.

Cited evidence: 4 distinct migration-collision incidents in 14 days
(commits eb69a56, d3a376a / PR #228, 6059214, aa2e2f8). The framework
must ship a portable detector + Phase 8 gate text so consumers don't
each re-derive this after their own UAT outage.

These tests run the script as a black box against synthetic
alembic/versions/ directories. They do NOT depend on Alembic itself.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).parents[2] / "templates" / "scripts" / "check_migrations.py"
)


def _run(versions_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--versions-dir", str(versions_dir)],
        capture_output=True,
        text=True,
    )


def _write_migration(
    versions_dir: Path, fname: str, revision: str, down_revision: str | None
) -> None:
    body = [f'revision = "{revision}"']
    if down_revision is None:
        body.append("down_revision = None")
    else:
        body.append(f'down_revision = "{down_revision}"')
    (versions_dir / fname).write_text("\n".join(body) + "\n")


# ---------------------------------------------------------------------------
# Existence + invocation
# ---------------------------------------------------------------------------


def test_check_migrations_template_exists() -> None:
    """The check_migrations.py template must ship in templates/scripts/.

    Why this matters: every Alembic-using consumer hits revision-id collisions
    eventually. Shipping the template means consumers copy + wire CI in one
    step instead of re-deriving after an outage.
    """
    assert SCRIPT.exists(), (
        f"templates/scripts/check_migrations.py is missing at {SCRIPT}. "
        "This is the retro 2026-05-01 Tier-A item A-1 deliverable."
    )


def test_check_migrations_runs_with_python3() -> None:
    """The script must be runnable as `python3 path/to/check_migrations.py`.

    Why this matters: CI environments use system python3 without poetry/venv
    setup at the migration-check step. The script must have zero non-stdlib deps.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "versions-dir" in result.stdout


# ---------------------------------------------------------------------------
# Behavior
# ---------------------------------------------------------------------------


def test_clean_chain_exits_zero(tmp_path: Path) -> None:
    """A linear chain (027 -> 028 -> 029) must exit 0."""
    versions = tmp_path / "versions"
    versions.mkdir()
    _write_migration(versions, "027_initial.py", "027", None)
    _write_migration(versions, "028_add_column.py", "028", "027")
    _write_migration(versions, "029_index.py", "029", "028")

    result = _run(versions)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_duplicate_revision_id_exits_nonzero(tmp_path: Path) -> None:
    """Two files claiming revision='030' must trigger DUPLICATE REVISION (case 1).

    Citation: PR #228 — STORY-576/577/578 BSR migrations all numbered 030
    collided with STORY-325 loader migration 030. `alembic heads` did NOT
    catch this; it surfaced only at production upgrade time as 6h of UAT
    403s. This is the canonical case the script exists to catch.
    """
    versions = tmp_path / "versions"
    versions.mkdir()
    _write_migration(versions, "029_prev.py", "029", None)
    _write_migration(versions, "030_loader_health.py", "030", "029")
    _write_migration(versions, "030_bsr_snapshots.py", "030", "029")

    result = _run(versions)
    assert result.returncode == 1
    assert "DUPLICATE REVISION '030'" in result.stderr


def test_divergent_down_revision_exits_nonzero(tmp_path: Path) -> None:
    """Two files chaining from the same parent must trigger DIVERGENT HEAD (case 2)."""
    versions = tmp_path / "versions"
    versions.mkdir()
    _write_migration(versions, "027_initial.py", "027", None)
    _write_migration(versions, "028_branch_a.py", "028a", "027")
    _write_migration(versions, "028_branch_b.py", "028b", "027")

    result = _run(versions)
    assert result.returncode == 1
    assert "DIVERGENT HEAD at '027'" in result.stderr


def test_underscore_prefixed_files_ignored(tmp_path: Path) -> None:
    """Files starting with `_` (e.g. __pycache__ stubs) must be ignored."""
    versions = tmp_path / "versions"
    versions.mkdir()
    _write_migration(versions, "027_initial.py", "027", None)
    (versions / "_skip_me.py").write_text('revision = "027"\ndown_revision = None\n')

    result = _run(versions)
    assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# Phase 8 agent text — the gate must be referenced from agents/phase-8-implementation.md
# ---------------------------------------------------------------------------


def test_phase8_agent_references_collision_check() -> None:
    """agents/phase-8-implementation.md must reference the new gate.

    Why this matters: the script is useless if no agent knows to run it.
    The Phase 8 implementation agent has a Multi-Head Check section that
    catches divergent down_revisions but NOT duplicate revision IDs;
    this gate fills that gap.
    """
    agent_path = (
        Path(__file__).parents[2] / "agents" / "phase-8-implementation.md"
    )
    text = agent_path.read_text()
    assert "Migration Revision-ID Collision Check" in text or "check_migrations.py" in text, (
        "agents/phase-8-implementation.md does not reference check_migrations.py "
        "or the collision-check gate. The script in templates/scripts/ is unreachable."
    )
