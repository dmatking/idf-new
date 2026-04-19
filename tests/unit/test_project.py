# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Tests for project creation and board/feature installation."""

from __future__ import annotations

from pathlib import Path

import pytest

from idf_new.paths import TEMPLATES_DIR
from idf_new.project import (
    Project,
    _sanitize_board_id,
    create_project,
    install_board,
    install_board_feature,
)


# ---------------------------------------------------------------------------
# _sanitize_board_id
# ---------------------------------------------------------------------------

class TestSanitizeBoardId:
    def test_slashes_become_underscores(self):
        assert _sanitize_board_id("waveshare/wvshr200") == "waveshare_wvshr200"

    def test_backslashes_also_converted(self):
        assert _sanitize_board_id("waveshare\\wvshr200") == "waveshare_wvshr200"

    def test_empty_string_becomes_board(self):
        assert _sanitize_board_id("") == "board"

    def test_simple_name_unchanged(self):
        assert _sanitize_board_id("generic") == "generic"

    def test_triple_nesting(self):
        assert _sanitize_board_id("vendor/family/board") == "vendor_family_board"


# ---------------------------------------------------------------------------
# create_project
# ---------------------------------------------------------------------------

class TestCreateProject:
    def test_creates_project_directory(self, tmp_path: Path):
        project = create_project("myapp", TEMPLATES_DIR, destination=tmp_path / "myapp")
        assert project.root.is_dir()

    def test_project_name_set_correctly(self, tmp_path: Path):
        project = create_project("myapp", TEMPLATES_DIR, destination=tmp_path / "myapp")
        assert project.name == "myapp"

    def test_cmake_lists_contains_project_name(self, tmp_path: Path):
        project = create_project("myapp", TEMPLATES_DIR, destination=tmp_path / "myapp")
        cmake = (project.root / "CMakeLists.txt").read_text()
        assert "project(myapp)" in cmake

    def test_cmake_lists_does_not_contain_base_project(self, tmp_path: Path):
        project = create_project("myapp", TEMPLATES_DIR, destination=tmp_path / "myapp")
        cmake = (project.root / "CMakeLists.txt").read_text()
        assert "project(base_project)" not in cmake

    def test_template_files_copied(self, tmp_path: Path):
        project = create_project("myapp", TEMPLATES_DIR, destination=tmp_path / "myapp")
        assert (project.root / "main" / "main.c").exists()
        assert (project.root / "main" / "board_interface.h").exists()
        assert (project.root / "main" / "idf_component.yml").exists()
        assert (project.root / "main" / "CMakeLists.txt").exists()

    def test_main_dir_property(self, tmp_path: Path):
        project = create_project("myapp", TEMPLATES_DIR, destination=tmp_path / "myapp")
        assert project.main_dir == project.root / "main"
        assert project.main_dir.is_dir()

    def test_raises_file_exists_error_if_dest_exists(self, tmp_path: Path):
        dest = tmp_path / "already_here"
        dest.mkdir()
        with pytest.raises(FileExistsError, match="already exists"):
            create_project("already_here", TEMPLATES_DIR, destination=dest)

    def test_raises_file_not_found_if_template_missing(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match="Template directory"):
            create_project("x", tmp_path / "no_template_here", destination=tmp_path / "x")

    def test_default_destination_is_cwd_subdir(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        project = create_project("myapp", TEMPLATES_DIR)
        assert project.root == tmp_path / "myapp"
        assert project.root.is_dir()


# ---------------------------------------------------------------------------
# Project.replace_text
# ---------------------------------------------------------------------------

class TestProjectReplaceText:
    def _project(self, tmp_path: Path) -> Project:
        return create_project("proj", TEMPLATES_DIR, destination=tmp_path / "proj")

    def test_replaces_text_in_file(self, tmp_path: Path):
        project = self._project(tmp_path)
        target = project.root / "main" / "main.c"
        # Write known content
        target.write_text("hello world\n")
        project.replace_text(target, "hello", "goodbye")
        assert "goodbye world" in target.read_text()

    def test_accepts_relative_path(self, tmp_path: Path):
        project = self._project(tmp_path)
        (project.root / "main" / "main.c").write_text("foo bar\n")
        project.replace_text("main/main.c", "foo", "baz")
        assert "baz bar" in (project.root / "main" / "main.c").read_text()

    def test_raises_if_old_not_found(self, tmp_path: Path):
        project = self._project(tmp_path)
        target = project.root / "main" / "main.c"
        target.write_text("hello\n")
        with pytest.raises(ValueError, match="not found"):
            project.replace_text(target, "NONEXISTENT_XYZ", "replacement")

    def test_count_limits_replacements(self, tmp_path: Path):
        project = self._project(tmp_path)
        target = project.root / "main" / "main.c"
        target.write_text("aa aa aa\n")
        project.replace_text(target, "aa", "bb", count=1)
        assert (project.root / "main" / "main.c").read_text() == "bb aa aa\n"


# ---------------------------------------------------------------------------
# install_board
# ---------------------------------------------------------------------------

class TestInstallBoard:
    def _fake_board(self, tmp_path: Path) -> Path:
        board_dir = tmp_path / "fakeboard"
        board_dir.mkdir()
        (board_dir / "board_impl.c").write_text("// stub\nvoid board_init(void) {}\n")
        return board_dir

    def _project(self, tmp_path: Path) -> Project:
        return create_project("myapp", TEMPLATES_DIR, destination=tmp_path / "myapp")

    def test_board_impl_copied_with_sanitized_name(self, tmp_path: Path):
        project = self._project(tmp_path)
        board_dir = self._fake_board(tmp_path)
        install_board(project, board_dir, "vendor/myboard")
        assert (project.main_dir / "board_vendor_myboard.c").exists()

    def test_original_board_impl_name_not_in_main(self, tmp_path: Path):
        project = self._project(tmp_path)
        board_dir = self._fake_board(tmp_path)
        install_board(project, board_dir, "vendor/myboard")
        assert not (project.main_dir / "board_impl.c").exists()

    def test_cmake_updated_to_reference_renamed_file(self, tmp_path: Path):
        project = self._project(tmp_path)
        board_dir = self._fake_board(tmp_path)
        install_board(project, board_dir, "vendor/myboard")
        cmake = (project.main_dir / "CMakeLists.txt").read_text()
        assert "board_vendor_myboard.c" in cmake
        assert "board_impl.c" not in cmake

    def test_extra_c_files_copied(self, tmp_path: Path):
        project = self._project(tmp_path)
        board_dir = self._fake_board(tmp_path)
        (board_dir / "lcd_helper.c").write_text("// lcd helper")
        (board_dir / "lcd_helper.h").write_text("// lcd header")
        install_board(project, board_dir, "vendor/myboard")
        assert (project.main_dir / "lcd_helper.c").exists()
        assert (project.main_dir / "lcd_helper.h").exists()

    def test_sdkconfig_defaults_copied_to_root(self, tmp_path: Path):
        project = self._project(tmp_path)
        board_dir = self._fake_board(tmp_path)
        (board_dir / "sdkconfig.defaults").write_text("CONFIG_EXAMPLE=y\n")
        (board_dir / "sdkconfig.defaults.esp32s3").write_text("CONFIG_S3_ONLY=y\n")
        install_board(project, board_dir, "vendor/myboard")
        assert (project.root / "sdkconfig.defaults").exists()
        assert (project.root / "sdkconfig.defaults.esp32s3").exists()

    def test_vendored_components_copied(self, tmp_path: Path):
        project = self._project(tmp_path)
        board_dir = self._fake_board(tmp_path)
        comp = board_dir / "components" / "mycomp"
        comp.mkdir(parents=True)
        (comp / "CMakeLists.txt").write_text("# component")
        install_board(project, board_dir, "vendor/myboard")
        assert (project.root / "components" / "mycomp" / "CMakeLists.txt").exists()

    def test_board_impl_missing_raises(self, tmp_path: Path):
        project = self._project(tmp_path)
        empty_dir = tmp_path / "empty_board"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError, match="board_impl.c"):
            install_board(project, empty_dir, "vendor/empty")


# ---------------------------------------------------------------------------
# install_board_feature
# ---------------------------------------------------------------------------

class TestInstallBoardFeature:
    def _project_with_board(self, tmp_path: Path) -> Project:
        project = create_project("myapp", TEMPLATES_DIR, destination=tmp_path / "myapp")
        board_dir = tmp_path / "board"
        board_dir.mkdir()
        (board_dir / "board_impl.c").write_text("")
        install_board(project, board_dir, "test/board")
        return project

    def _make_feature(self, tmp_path: Path, name: str, with_kconfig: bool = True) -> Path:
        fd = tmp_path / name
        fd.mkdir()
        (fd / f"{name}.c").write_text(f"// {name} impl")
        (fd / f"{name}.h").write_text(f"// {name} header")
        if with_kconfig:
            (fd / "Kconfig").write_text(
                f'menu "{name.upper()}"\n'
                f'config {name.upper()}_ENABLE\n'
                f'  bool "Enable {name}"\nendmenu\n'
            )
        return fd

    def test_source_files_copied_to_main(self, tmp_path: Path):
        project = self._project_with_board(tmp_path)
        fd = self._make_feature(tmp_path, "tf_card")
        install_board_feature(project, fd, "tf_card")
        assert (project.main_dir / "tf_card.c").exists()
        assert (project.main_dir / "tf_card.h").exists()

    def test_kconfig_creates_projbuild(self, tmp_path: Path):
        project = self._project_with_board(tmp_path)
        fd = self._make_feature(tmp_path, "speaker")
        install_board_feature(project, fd, "speaker")
        kconfig = project.main_dir / "Kconfig.projbuild"
        assert kconfig.exists()
        assert "SPEAKER_ENABLE" in kconfig.read_text()

    def test_two_features_kconfig_both_present(self, tmp_path: Path):
        project = self._project_with_board(tmp_path)
        fd1 = self._make_feature(tmp_path, "feat_a")
        fd2 = self._make_feature(tmp_path, "feat_b")
        install_board_feature(project, fd1, "feat_a")
        install_board_feature(project, fd2, "feat_b")
        text = (project.main_dir / "Kconfig.projbuild").read_text()
        assert "FEAT_A_ENABLE" in text
        assert "FEAT_B_ENABLE" in text

    def test_feature_without_kconfig_no_projbuild(self, tmp_path: Path):
        project = self._project_with_board(tmp_path)
        fd = self._make_feature(tmp_path, "imu", with_kconfig=False)
        install_board_feature(project, fd, "imu")
        assert not (project.main_dir / "Kconfig.projbuild").exists()

    def test_cmake_extra_appended(self, tmp_path: Path):
        project = self._project_with_board(tmp_path)
        fd = tmp_path / "uart_feat"
        fd.mkdir()
        (fd / "main.cmake.extra").write_text('list(APPEND EXTRA_SRCS "uart_extra.c")\n')
        install_board_feature(project, fd, "uart_feat")
        cmake_extra = project.main_dir / "main.cmake.extra"
        assert cmake_extra.exists()
        assert "uart_extra.c" in cmake_extra.read_text()

    def test_cmake_extra_from_two_features_both_present(self, tmp_path: Path):
        project = self._project_with_board(tmp_path)
        for name in ("feat_x", "feat_y"):
            fd = tmp_path / name
            fd.mkdir()
            (fd / "main.cmake.extra").write_text(f'# {name}\n')
            install_board_feature(project, fd, name)
        text = (project.main_dir / "main.cmake.extra").read_text()
        assert "feat_x" in text
        assert "feat_y" in text
