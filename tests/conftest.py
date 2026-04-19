# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Shared pytest fixtures for idf-new tests."""

from __future__ import annotations

from pathlib import Path
from typing import Generator
import shutil

import pytest

from idf_new.boards import BoardInfo, list_boards
from idf_new.paths import BOARDS_DIR, TEMPLATES_DIR
from idf_new.project import Project, create_project, install_board


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Session-scoped helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def all_boards() -> list[BoardInfo]:
    """All BoardInfo objects discovered from the boards/ directory."""
    return list_boards()


# ---------------------------------------------------------------------------
# Function-scoped project factory
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_project(tmp_path: Path) -> Project:
    """A project created from the base template with a fake board installed."""
    board_dir = tmp_path / "_fakeboard"
    board_dir.mkdir()
    (board_dir / "board_impl.c").write_text("// stub\nvoid board_init(void) {}\n")

    project = create_project("testapp", TEMPLATES_DIR, destination=tmp_path / "testapp")
    install_board(project, board_dir, "test/fakeboard")
    return project


# ---------------------------------------------------------------------------
# Board feature discovery helper (used by parametrize)
# ---------------------------------------------------------------------------


def board_feature_params() -> list[tuple[str, str]]:
    """Return (board_id, feature_name) pairs for every feature on every board."""
    params: list[tuple[str, str]] = []
    for board in list_boards():
        features_dir = board.path / "features"
        if features_dir.is_dir():
            for feature in sorted(features_dir.iterdir()):
                if feature.is_dir():
                    params.append((board.board_id, feature.name))
    return params
