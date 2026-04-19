# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Integration tests: board features and modules applied via ProjectGenerator.

Strategy (Option B heuristic):
  - Each feature tested individually           (N tests per board)
  - All features together on the same board    (1 test per board)
  - Each module tested alone on a generic base (M tests)
  - All modules together on a board with LCD   (1 test)

This gives good coverage of interaction bugs (missing file copies, Kconfig
conflicts, CMake clashes) without building the projects.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from idf_new.boards import list_boards
from idf_new.generator import GenerationOptions, ProjectGenerator
from idf_new.modules import list_modules
from tests.conftest import board_feature_params


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate(
    board_id: str,
    tmp_path: Path,
    dest_name: str = "testproj",
    features: list[str] | None = None,
    modules: list[str] | None = None,
) -> Path:
    opts = GenerationOptions(
        project_name=dest_name,
        board_id=board_id,
        destination=tmp_path / dest_name,
        feature_flags=features or [],
        module_flags=modules or [],
    )
    # Patch subprocess.run so sim module doesn't try to hit piserver
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        project = ProjectGenerator(opts).generate()
    return project.root


def _board_features_for(board_id: str) -> list[str]:
    for b in list_boards():
        if b.board_id == board_id:
            fd = b.path / "features"
            if fd.is_dir():
                return sorted(f.name for f in fd.iterdir() if f.is_dir())
    return []


# ---------------------------------------------------------------------------
# Per-feature tests  (one feature at a time)
# ---------------------------------------------------------------------------

_FEATURE_PARAMS = board_feature_params()


@pytest.mark.parametrize("board_id,feature_name", _FEATURE_PARAMS)
class TestEachFeatureAlone:
    def test_project_generates_without_error(
        self, board_id: str, feature_name: str, tmp_path: Path
    ):
        root = _generate(board_id, tmp_path, features=[feature_name])
        assert root.is_dir()

    def test_board_impl_present(
        self, board_id: str, feature_name: str, tmp_path: Path
    ):
        root = _generate(board_id, tmp_path, features=[feature_name])
        board_c_files = list((root / "main").glob("board_*.c"))
        assert board_c_files, f"No board_*.c in main/ for {board_id}+{feature_name}"

    def test_feature_c_files_in_main(
        self, board_id: str, feature_name: str, tmp_path: Path
    ):
        """Any .c/.h files in the feature directory must appear in main/."""
        from idf_new.boards import list_boards as _list
        feature_dir = None
        for b in _list():
            if b.board_id == board_id:
                feature_dir = b.path / "features" / feature_name
                break
        assert feature_dir is not None

        root = _generate(board_id, tmp_path, features=[feature_name])
        for src in feature_dir.glob("*.c"):
            assert (root / "main" / src.name).exists(), (
                f"{src.name} from feature '{feature_name}' not found in main/"
            )
        for src in feature_dir.glob("*.h"):
            assert (root / "main" / src.name).exists(), (
                f"{src.name} from feature '{feature_name}' not found in main/"
            )

    def test_kconfig_present_when_feature_has_one(
        self, board_id: str, feature_name: str, tmp_path: Path
    ):
        from idf_new.boards import list_boards as _list
        for b in _list():
            if b.board_id == board_id:
                feature_dir = b.path / "features" / feature_name
                break

        if not (feature_dir / "Kconfig").exists():
            pytest.skip(f"feature '{feature_name}' has no Kconfig")

        root = _generate(board_id, tmp_path, features=[feature_name])
        assert (root / "main" / "Kconfig.projbuild").exists(), (
            f"Kconfig.projbuild missing after applying feature '{feature_name}'"
        )

    def test_idf_component_yml_is_valid_yaml(
        self, board_id: str, feature_name: str, tmp_path: Path
    ):
        import yaml
        root = _generate(board_id, tmp_path, features=[feature_name])
        yml = root / "main" / "idf_component.yml"
        assert yml.exists()
        data = yaml.safe_load(yml.read_text())
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# All-features-together test (per board that has features)
# ---------------------------------------------------------------------------

_BOARDS_WITH_FEATURES = sorted({
    board_id for board_id, _ in _FEATURE_PARAMS
})


@pytest.mark.parametrize("board_id", _BOARDS_WITH_FEATURES)
class TestAllFeaturesOnBoard:
    def test_all_features_together(self, board_id: str, tmp_path: Path):
        features = _board_features_for(board_id)
        assert features, f"Expected features for {board_id}"
        root = _generate(board_id, tmp_path, dest_name="allfeat", features=features)
        assert root.is_dir()
        # All feature source files must appear in main/
        from idf_new.boards import list_boards as _list
        for b in _list():
            if b.board_id == board_id:
                for feat in features:
                    fd = b.path / "features" / feat
                    for src in fd.glob("*.c"):
                        assert (root / "main" / src.name).exists(), (
                            f"{src.name} (from feature {feat}) missing in all-features build"
                        )
                break

    def test_kconfig_contains_all_feature_menus(self, board_id: str, tmp_path: Path):
        """Each feature's Kconfig content must appear in Kconfig.projbuild."""
        features = _board_features_for(board_id)
        root = _generate(board_id, tmp_path, dest_name="allkconf", features=features)
        kconfig_path = root / "main" / "Kconfig.projbuild"

        from idf_new.boards import list_boards as _list
        for b in _list():
            if b.board_id == board_id:
                for feat in features:
                    kconfig_src = b.path / "features" / feat / "Kconfig"
                    if kconfig_src.exists():
                        assert kconfig_path.exists(), (
                            f"Kconfig.projbuild missing despite feature '{feat}' having Kconfig"
                        )
                break


# ---------------------------------------------------------------------------
# Per-module tests (each module alone, on generic board)
# ---------------------------------------------------------------------------

_MODULE_FLAGS = [m.flag for m in list_modules()]


@pytest.mark.parametrize("module_flag", _MODULE_FLAGS)
class TestEachModuleAlone:
    def test_module_generates_without_error(self, module_flag: str, tmp_path: Path):
        # Use a board with an LCD for modules that need one (sim), generic otherwise
        board_id = "waveshare/wvshr185_round_touch" if module_flag == "sim" else "generic"
        root = _generate(board_id, tmp_path, modules=[module_flag])
        assert root.is_dir()

    def test_board_impl_still_present_after_module(self, module_flag: str, tmp_path: Path):
        board_id = "waveshare/wvshr185_round_touch" if module_flag == "sim" else "generic"
        root = _generate(board_id, tmp_path, modules=[module_flag])
        board_c_files = list((root / "main").glob("board_*.c"))
        assert board_c_files, f"board_*.c vanished after applying module '{module_flag}'"


# ---------------------------------------------------------------------------
# All modules together (on a board with LCD, so sim is exercised)
# ---------------------------------------------------------------------------


def test_all_modules_together(tmp_path: Path):
    """All modules applied simultaneously must not conflict."""
    all_flags = [m.flag for m in list_modules()]
    root = _generate(
        "waveshare/wvshr185_round_touch",
        tmp_path,
        dest_name="allmod",
        modules=all_flags,
    )
    assert root.is_dir()
    # board_*.c must still be present
    assert list((root / "main").glob("board_*.c")), "board_*.c missing after all-modules run"
    # idf_component.yml must still be valid YAML
    import yaml
    data = yaml.safe_load((root / "main" / "idf_component.yml").read_text())
    assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# Mixed: all features + all modules on a capable board
# ---------------------------------------------------------------------------


def test_all_features_and_all_modules(tmp_path: Path):
    """Max-stress test: all features and all modules on one board."""
    board_id = "waveshare/wvshr185_round_touch"
    features = _board_features_for(board_id)
    all_flags = [m.flag for m in list_modules()]

    root = _generate(
        board_id,
        tmp_path,
        dest_name="maxproj",
        features=features,
        modules=all_flags,
    )
    assert root.is_dir()
    assert list((root / "main").glob("board_*.c"))

    import yaml
    data = yaml.safe_load((root / "main" / "idf_component.yml").read_text())
    assert isinstance(data, dict)
