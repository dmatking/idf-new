# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Tests for module registry and module.apply() implementations."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from idf_new.boards import BoardInfo, BoardScreen
from idf_new.modules import ModuleContext, get_module, list_modules
from idf_new.paths import TEMPLATES_DIR
from idf_new.project import Project, create_project, install_board


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(tmp_path: Path, board_info=None) -> ModuleContext:
    """Create a ModuleContext backed by a real (but minimal) project on disk."""
    project = create_project("modtest", TEMPLATES_DIR, destination=tmp_path / "modtest")
    board_dir = tmp_path / "_fakeboard"
    board_dir.mkdir()
    (board_dir / "board_impl.c").write_text("")
    install_board(project, board_dir, "test/fakeboard")
    return ModuleContext(
        project_dir=project.root,
        main_dir=project.main_dir,
        cmake_extra_path=project.main_dir / "main.cmake.extra",
        board_info=board_info,
    )


def _lcd_board(width: int = 240, height: int = 320) -> BoardInfo:
    return BoardInfo(
        board_id="test/lcd_board",
        path=Path("/tmp"),
        display_name="Test LCD",
        traits=[],
        board_features=[],
        has_touch=False,
        screen=BoardScreen(
            width=width,
            height=height,
            size_inches=2.0,
            resolution=f"{width}x{height}",
        ),
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_list_modules_returns_nonempty(self):
        assert len(list_modules()) > 0

    def test_all_known_module_flags_present(self):
        flags = {m.flag for m in list_modules()}
        assert "gps_neo6m" in flags
        assert "gps_atgm336h" in flags
        assert "sim" in flags

    def test_get_module_by_flag(self):
        mod = get_module("gps_neo6m")
        assert mod.flag == "gps_neo6m"

    def test_get_unknown_module_raises_key_error(self):
        with pytest.raises(KeyError):
            get_module("totally_unknown_module_xyz")

    def test_each_module_has_name(self):
        for mod in list_modules():
            assert mod.name, f"module {mod.flag} has empty name"

    def test_each_module_has_category(self):
        for mod in list_modules():
            assert mod.category, f"module {mod.flag} has empty category"

    def test_flags_are_unique(self):
        flags = [m.flag for m in list_modules()]
        assert len(flags) == len(set(flags)), "duplicate module flags found"


# ---------------------------------------------------------------------------
# GPS modules
# ---------------------------------------------------------------------------


class TestGpsNeo6m:
    def test_apply_copies_gps_c(self, tmp_path: Path):
        ctx = _make_context(tmp_path)
        get_module("gps_neo6m").apply(ctx)
        assert (ctx.main_dir / "gps.c").exists()

    def test_apply_copies_gps_h(self, tmp_path: Path):
        ctx = _make_context(tmp_path)
        get_module("gps_neo6m").apply(ctx)
        assert (ctx.main_dir / "gps.h").exists()

    def test_apply_creates_kconfig_projbuild(self, tmp_path: Path):
        ctx = _make_context(tmp_path)
        get_module("gps_neo6m").apply(ctx)
        kconfig = ctx.main_dir / "Kconfig.projbuild"
        assert kconfig.exists()
        assert kconfig.stat().st_size > 0

    def test_apply_appends_to_existing_kconfig(self, tmp_path: Path):
        ctx = _make_context(tmp_path)
        kconfig = ctx.main_dir / "Kconfig.projbuild"
        kconfig.write_text('menu "Pre-existing"\nconfig PRE_EXISTING\n  bool\nendmenu\n')
        get_module("gps_neo6m").apply(ctx)
        text = kconfig.read_text()
        assert "PRE_EXISTING" in text
        # GPS content must also be present
        assert kconfig.stat().st_size > len('menu "Pre-existing"\nconfig PRE_EXISTING\n  bool\nendmenu\n')

    def test_gps_c_content_is_nonempty(self, tmp_path: Path):
        ctx = _make_context(tmp_path)
        get_module("gps_neo6m").apply(ctx)
        assert (ctx.main_dir / "gps.c").stat().st_size > 0


class TestGpsAtgm336h:
    def test_apply_copies_gps_files(self, tmp_path: Path):
        ctx = _make_context(tmp_path)
        get_module("gps_atgm336h").apply(ctx)
        assert (ctx.main_dir / "gps.c").exists()
        assert (ctx.main_dir / "gps.h").exists()

    def test_same_files_as_neo6m(self, tmp_path: Path):
        """Both GPS modules share the same driver code."""
        ctx1 = _make_context(tmp_path / "neo6m")
        ctx2 = _make_context(tmp_path / "atgm")
        get_module("gps_neo6m").apply(ctx1)
        get_module("gps_atgm336h").apply(ctx2)
        assert (ctx1.main_dir / "gps.c").read_bytes() == (ctx2.main_dir / "gps.c").read_bytes()


# ---------------------------------------------------------------------------
# Sim module
# ---------------------------------------------------------------------------


class TestSimModule:
    def test_skipped_when_no_board_info(self, tmp_path: Path, capsys):
        ctx = _make_context(tmp_path, board_info=None)
        get_module("sim").apply(ctx)
        assert not (ctx.project_dir / "sim").exists()
        assert "skipping" in capsys.readouterr().out.lower()

    def test_skipped_when_board_has_no_screen(self, tmp_path: Path, capsys):
        headless = BoardInfo(
            board_id="generic",
            path=Path("/tmp"),
            display_name="Headless",
            traits=[],
            board_features=[],
            has_touch=False,
            screen=None,
        )
        ctx = _make_context(tmp_path, board_info=headless)
        get_module("sim").apply(ctx)
        assert not (ctx.project_dir / "sim").exists()

    def test_creates_sim_dir_for_lcd_board(self, tmp_path: Path):
        ctx = _make_context(tmp_path, board_info=_lcd_board())
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            get_module("sim").apply(ctx)
        assert (ctx.project_dir / "sim").is_dir()

    def test_sim_cmake_lists_created(self, tmp_path: Path):
        ctx = _make_context(tmp_path, board_info=_lcd_board())
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            get_module("sim").apply(ctx)
        assert (ctx.project_dir / "sim" / "CMakeLists.txt").exists()

    def test_sim_main_c_created(self, tmp_path: Path):
        ctx = _make_context(tmp_path, board_info=_lcd_board())
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            get_module("sim").apply(ctx)
        assert (ctx.project_dir / "sim" / "main_sim.c").exists()

    def test_cmake_placeholders_replaced(self, tmp_path: Path):
        ctx = _make_context(tmp_path, board_info=_lcd_board(240, 320))
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            get_module("sim").apply(ctx)
        text = (ctx.project_dir / "sim" / "CMakeLists.txt").read_text()
        assert "__BOARD_WIDTH__" not in text
        assert "__BOARD_HEIGHT__" not in text
        assert "240" in text
        assert "320" in text

    def test_project_name_placeholder_replaced_in_cmake(self, tmp_path: Path):
        ctx = _make_context(tmp_path, board_info=_lcd_board())
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            get_module("sim").apply(ctx)
        text = (ctx.project_dir / "sim" / "CMakeLists.txt").read_text()
        assert "__PROJECT_NAME__" not in text

    def test_project_name_placeholder_replaced_in_main_sim_c(self, tmp_path: Path):
        ctx = _make_context(tmp_path, board_info=_lcd_board())
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            get_module("sim").apply(ctx)
        text = (ctx.project_dir / "sim" / "main_sim.c").read_text()
        assert "__PROJECT_NAME__" not in text

    def test_graceful_when_submodule_add_fails(self, tmp_path: Path, capsys):
        ctx = _make_context(tmp_path, board_info=_lcd_board())
        with patch("subprocess.run") as mock_run:
            # First call (git init) succeeds, second (submodule add) fails
            mock_run.side_effect = [
                MagicMock(returncode=0, stderr=""),
                MagicMock(returncode=128, stderr="fatal: not a git repository"),
            ]
            get_module("sim").apply(ctx)
        # sim/ should still be created even if submodule failed
        assert (ctx.project_dir / "sim").is_dir()
        out = capsys.readouterr().out
        assert "sim" in out.lower()
