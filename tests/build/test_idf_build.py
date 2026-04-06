# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Tier-3 build tests: generate a project then compile it with idf.py.

Strategy (Option B heuristic — same as integration/test_features.py but with
a real idf.py build):

  1. Every board, baseline (no features, no modules)      — N tests
  2. Every board that has features, all features together  — per-board test
  3. generic board + gps_neo6m module                     — 1 test
  4. generic board + gps_atgm336h module                  — 1 test
  5. One capable board, all features + all modules*       — 1 max-stress test

*The sim module is excluded from IDF build tests because it is a native
 desktop CMake build, not an ESP-IDF build.  It is tested in integration tests.

Each test generates a fresh project in pytest's tmp_path and calls
``idf.py set-target esp32s3 && idf.py build``.  Build output is captured;
on failure the last 100 lines of combined stdout+stderr are shown.

These tests are slow (~1-3 minutes per board).  Run them selectively:

    python -m pytest tests/build/ -v
    python -m pytest tests/build/ -k generic -v
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from idf_new.boards import list_boards
from idf_new.generator import GenerationOptions, ProjectGenerator
from idf_new.modules import list_modules
from tests.conftest import board_feature_params


# ---------------------------------------------------------------------------
# IDF target — all boards in this repo target ESP32-S3
# ---------------------------------------------------------------------------

IDF_TARGET = "esp32s3"
BUILD_TIMEOUT = 600   # seconds per build step


# ---------------------------------------------------------------------------
# Build helper
# ---------------------------------------------------------------------------


def _generate(
    board_id: str,
    tmp_path: Path,
    dest_name: str = "buildproj",
    features: list[str] | None = None,
    modules: list[str] | None = None,
) -> Path:
    """Generate a project, patching subprocess so sim's git calls don't run."""
    opts = GenerationOptions(
        project_name=dest_name,
        board_id=board_id,
        destination=tmp_path / dest_name,
        feature_flags=features or [],
        module_flags=modules or [],
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        project = ProjectGenerator(opts).generate()
    return project.root


def _idf_build(project_dir: Path) -> tuple[int, str]:
    """
    Run ``idf.py set-target <target> && idf.py build`` in project_dir.

    Returns (returncode, combined_output).  Uses the ambient environment so
    IDF_PATH, PATH, and toolchain variables set by export.sh are inherited.
    """
    env = os.environ.copy()
    combined: list[str] = []

    for cmd in (
        ["idf.py", "set-target", IDF_TARGET],
        ["idf.py", "build"],
    ):
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=BUILD_TIMEOUT,
        )
        combined.append(f"$ {' '.join(cmd)}\n{result.stdout}")
        if result.returncode != 0:
            return result.returncode, "\n".join(combined)

    return 0, "\n".join(combined)


def _assert_build(project_dir: Path) -> None:
    """Run the IDF build and fail with the last 100 log lines on error."""
    rc, output = _idf_build(project_dir)
    if rc != 0:
        tail = "\n".join(output.splitlines()[-100:])
        pytest.fail(
            f"idf.py build failed (rc={rc}) in {project_dir}\n\n{tail}"
        )
    # Sanity-check: a .bin must exist somewhere under build/
    bins = list(project_dir.glob("build/*.bin"))
    assert bins, f"Build succeeded (rc=0) but no .bin found under {project_dir / 'build'}"


# ---------------------------------------------------------------------------
# Helper: feature list for a board
# ---------------------------------------------------------------------------


def _board_features(board_id: str) -> list[str]:
    for b in list_boards():
        if b.board_id == board_id:
            fd = b.path / "features"
            if fd.is_dir():
                return sorted(f.name for f in fd.iterdir() if f.is_dir())
    return []


# ---------------------------------------------------------------------------
# 1. Every board, baseline (no features / modules)
# ---------------------------------------------------------------------------

_BOARD_IDS = [b.board_id for b in list_boards()]


@pytest.mark.parametrize("board_id", _BOARD_IDS)
def test_board_baseline_build(board_id: str, tmp_path: Path):
    """Generate and build each board with no features or modules."""
    root = _generate(board_id, tmp_path)
    _assert_build(root)


# ---------------------------------------------------------------------------
# 2. Every board that has features — all features together
# ---------------------------------------------------------------------------

_BOARDS_WITH_FEATURES = sorted({
    board_id for board_id, _ in board_feature_params()
})


@pytest.mark.parametrize("board_id", _BOARDS_WITH_FEATURES)
def test_board_all_features_build(board_id: str, tmp_path: Path):
    """Build each board with all its optional features enabled simultaneously."""
    features = _board_features(board_id)
    assert features, f"Expected features for {board_id}"
    root = _generate(board_id, tmp_path, dest_name="allfeat", features=features)
    _assert_build(root)


# ---------------------------------------------------------------------------
# 3. GPS modules on generic board
# ---------------------------------------------------------------------------


def test_gps_neo6m_build(tmp_path: Path):
    """generic board + gps_neo6m module must compile."""
    root = _generate("generic", tmp_path, modules=["gps_neo6m"])
    _assert_build(root)


def test_gps_atgm336h_build(tmp_path: Path):
    """generic board + gps_atgm336h module must compile."""
    root = _generate("generic", tmp_path, modules=["gps_atgm336h"])
    _assert_build(root)


# ---------------------------------------------------------------------------
# 4. Max-stress: one capable board, all features + all non-sim modules
# ---------------------------------------------------------------------------


def test_max_stress_build(tmp_path: Path):
    """All features and all non-sim modules on a fully-featured board."""
    board_id = "waveshare/wvshr185_round_touch"
    features = _board_features(board_id)
    # Exclude sim: it's a native desktop build, not an IDF build
    idf_modules = [m.flag for m in list_modules() if m.flag != "sim"]

    root = _generate(
        board_id,
        tmp_path,
        dest_name="maxstress",
        features=features,
        modules=idf_modules,
    )
    _assert_build(root)
