# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Integration tests: run ProjectGenerator for every board and verify output structure.

These tests exercise the full generation pipeline (validate_board → create_project →
install_board → _apply_modules) but stop short of running idf.py build.  They
prove that the generator produces a sane, consistent project tree for every
board in the repo.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from idf_new.boards import list_boards
from idf_new.generator import GenerationOptions, ProjectGenerator


# ---------------------------------------------------------------------------
# Parametrize over every board in the repo
# ---------------------------------------------------------------------------

_BOARD_IDS = [b.board_id for b in list_boards()]


@pytest.mark.parametrize("board_id", _BOARD_IDS)
class TestScaffoldPerBoard:
    """Run the generator for each board and check the output layout."""

    def _generate(self, board_id: str, tmp_path: Path, **kwargs) -> Path:
        opts = GenerationOptions(
            project_name="testproj",
            board_id=board_id,
            destination=tmp_path / "testproj",
            **kwargs,
        )
        project = ProjectGenerator(opts).generate()
        return project.root

    # -- Root-level files --

    def test_root_cmake_exists(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        assert (root / "CMakeLists.txt").exists(), "CMakeLists.txt missing at project root"

    def test_root_cmake_contains_project_name(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        cmake = (root / "CMakeLists.txt").read_text()
        assert "project(testproj)" in cmake, "project name not set in root CMakeLists.txt"

    def test_root_cmake_does_not_contain_base_project(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        cmake = (root / "CMakeLists.txt").read_text()
        assert "project(base_project)" not in cmake

    # -- main/ directory --

    def test_main_dir_exists(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        assert (root / "main").is_dir()

    def test_main_c_exists(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        assert (root / "main" / "main.c").exists()

    def test_board_interface_header_exists(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        assert (root / "main" / "board_interface.h").exists()

    def test_idf_component_yml_exists(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        assert (root / "main" / "idf_component.yml").exists()

    def test_main_cmake_exists(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        assert (root / "main" / "CMakeLists.txt").exists()

    # -- Board implementation --

    def test_board_impl_file_in_main(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        board_c_files = list((root / "main").glob("board_*.c"))
        assert board_c_files, (
            f"No board_*.c file found in main/ for board '{board_id}'"
        )

    def test_original_board_impl_name_not_used(self, board_id: str, tmp_path: Path):
        """board_impl.c must be renamed to board_<sanitized_id>.c."""
        root = self._generate(board_id, tmp_path)
        assert not (root / "main" / "board_impl.c").exists(), (
            "board_impl.c was not renamed after installation"
        )

    def test_main_cmake_references_board_file(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        cmake = (root / "main" / "CMakeLists.txt").read_text()
        board_c_files = list((root / "main").glob("board_*.c"))
        assert board_c_files, "no board_*.c in main/"
        assert board_c_files[0].name in cmake, (
            f"{board_c_files[0].name} not referenced in main/CMakeLists.txt"
        )

    def test_main_cmake_no_raw_board_impl_ref(self, board_id: str, tmp_path: Path):
        root = self._generate(board_id, tmp_path)
        cmake = (root / "main" / "CMakeLists.txt").read_text()
        assert '"board_impl.c"' not in cmake, (
            'main/CMakeLists.txt still references "board_impl.c" literally'
        )

    # -- Idempotency: generating twice to the same dest raises --

    def test_second_generation_raises_file_exists(self, board_id: str, tmp_path: Path):
        dest = tmp_path / "testproj"
        opts = GenerationOptions(
            project_name="testproj",
            board_id=board_id,
            destination=dest,
        )
        ProjectGenerator(opts).generate()
        with pytest.raises((FileExistsError, SystemExit)):
            ProjectGenerator(opts).generate()
