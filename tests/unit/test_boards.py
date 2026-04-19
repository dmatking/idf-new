# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Tests for board discovery, loading, and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from idf_new.boards import BoardInfo, _load_board_info, list_boards, validate_board
from idf_new.paths import BOARDS_DIR


class TestListBoards:
    def test_returns_nonempty_list(self):
        assert len(list_boards()) > 0

    def test_all_boards_have_board_id(self):
        for b in list_boards():
            assert b.board_id, f"board at {b.path} has empty board_id"

    def test_all_boards_have_display_name(self):
        for b in list_boards():
            assert b.display_name, f"board {b.board_id} has empty display_name"

    def test_all_board_paths_exist(self):
        for b in list_boards():
            assert b.path.is_dir(), f"{b.board_id}: path {b.path} is not a directory"

    def test_all_boards_have_board_impl(self):
        for b in list_boards():
            assert (b.path / "board_impl.c").exists(), (
                f"{b.board_id}: missing board_impl.c"
            )

    def test_known_board_ids_present(self):
        ids = {b.board_id for b in list_boards()}
        assert "generic" in ids
        assert "waveshare/wvshr185_round_touch" in ids

    def test_board_ids_are_relative_to_boards_dir(self):
        for b in list_boards():
            # board_id should be a posix relative path, no leading slash
            assert not b.board_id.startswith("/"), (
                f"{b.board_id} looks like an absolute path"
            )

    def test_traits_are_strings(self):
        for b in list_boards():
            for t in b.traits:
                assert isinstance(t, str), f"{b.board_id}: non-string trait {t!r}"

    def test_board_features_are_strings(self):
        for b in list_boards():
            for f in b.board_features:
                assert isinstance(f, str), (
                    f"{b.board_id}: non-string feature {f!r}"
                )


class TestLoadBoardInfo:
    def _make_board_dir(self, tmp_path: Path) -> Path:
        board_dir = tmp_path / "testboard"
        board_dir.mkdir()
        (board_dir / "board_impl.c").write_text("")
        return board_dir

    def test_parses_full_board_json(self, tmp_path: Path):
        board_dir = self._make_board_dir(tmp_path)
        (board_dir / "board.json").write_text(json.dumps({
            "display_name": "My Test Board",
            "has_touch": True,
            "panel": "ST7789",
            "traits": ["ips", "spi"],
            "board_features": ["tf_card", "speaker"],
            "screen": {
                "size_inches": 2.0,
                "resolution": "240x320",
                "technology": "IPS",
                "shape": "rect",
            },
        }))

        info = _load_board_info("vendor/testboard", board_dir)

        assert info.display_name == "My Test Board"
        assert info.has_touch is True
        assert info.panel == "ST7789"
        assert "ips" in info.traits
        assert "spi" in info.traits
        assert "tf_card" in info.board_features
        assert "speaker" in info.board_features
        assert info.screen is not None
        assert info.screen.size_inches == 2.0
        assert info.screen.technology == "IPS"
        assert info.screen.shape == "rect"

    def test_resolution_parsed_into_width_height(self, tmp_path: Path):
        board_dir = self._make_board_dir(tmp_path)
        (board_dir / "board.json").write_text(json.dumps({
            "screen": {"resolution": "240x320"},
        }))

        info = _load_board_info("test/resboard", board_dir)

        assert info.screen is not None
        assert info.screen.width == 240
        assert info.screen.height == 320

    def test_missing_board_json_uses_defaults(self, tmp_path: Path):
        board_dir = self._make_board_dir(tmp_path)

        info = _load_board_info("test/bare", board_dir)

        assert info.display_name == board_dir.name   # falls back to directory name
        assert info.has_touch is False
        assert info.traits == []
        assert info.board_features == []
        assert info.screen is None
        assert info.panel is None

    def test_malformed_resolution_does_not_raise(self, tmp_path: Path):
        board_dir = self._make_board_dir(tmp_path)
        (board_dir / "board.json").write_text(json.dumps({
            "screen": {"resolution": "notvalid"},
        }))

        info = _load_board_info("test/badres", board_dir)

        assert info.screen is not None
        assert info.screen.width is None
        assert info.screen.height is None

    def test_duplicate_traits_deduplicated(self, tmp_path: Path):
        board_dir = self._make_board_dir(tmp_path)
        (board_dir / "board.json").write_text(json.dumps({
            "traits": ["ips", "ips", "spi"],
        }))

        info = _load_board_info("test/dups", board_dir)

        assert info.traits.count("ips") == 1

    def test_invalid_json_raises_system_exit(self, tmp_path: Path):
        board_dir = self._make_board_dir(tmp_path)
        (board_dir / "board.json").write_text("{bad json}")

        with pytest.raises(SystemExit):
            _load_board_info("test/badjson", board_dir)


class TestValidateBoard:
    def test_valid_board_returns_path(self):
        path = validate_board("generic")
        assert path.is_dir()
        assert (path / "board_impl.c").exists()

    def test_valid_nested_board_returns_path(self):
        path = validate_board("waveshare/wvshr185_round_touch")
        assert path.is_dir()

    def test_unknown_board_raises_system_exit(self):
        with pytest.raises(SystemExit, match="not found"):
            validate_board("vendor/does_not_exist")

    def test_path_traversal_raises_system_exit(self):
        with pytest.raises(SystemExit, match="escapes"):
            validate_board("../../etc/passwd")

    def test_path_traversal_with_encoded_slash_raises(self):
        with pytest.raises(SystemExit):
            validate_board("../boards/../etc/passwd")
