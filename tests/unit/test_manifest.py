# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Tests for manifest (idf_component.yml) merging logic."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from idf_new.manifest import _merge_dict, merge_manifests


class TestMergeDict:
    def test_populates_empty_target(self):
        target: dict = {}
        _merge_dict(target, {"version": "1.0"})
        assert target == {"version": "1.0"}

    def test_does_not_overwrite_existing_key(self):
        target = {"version": "1.0"}
        _merge_dict(target, {"version": "2.0", "name": "new"})
        assert target["version"] == "1.0"
        assert target["name"] == "new"

    def test_merges_dependencies_dict(self):
        target: dict = {"dependencies": {"idf": ">=5.0"}}
        _merge_dict(target, {"dependencies": {"lvgl": "^9.1"}})
        assert target["dependencies"]["idf"] == ">=5.0"
        assert target["dependencies"]["lvgl"] == "^9.1"

    def test_incoming_dep_overwrites_same_dep(self):
        """Dependency values from incoming replace matching keys in target."""
        target: dict = {"dependencies": {"idf": ">=5.0"}}
        _merge_dict(target, {"dependencies": {"idf": ">=5.5"}})
        assert target["dependencies"]["idf"] == ">=5.5"

    def test_creates_dependencies_key_if_absent(self):
        target: dict = {}
        _merge_dict(target, {"dependencies": {"lvgl": "^9.1"}})
        assert target["dependencies"] == {"lvgl": "^9.1"}

    def test_empty_incoming_leaves_target_unchanged(self):
        target = {"version": "1.0"}
        _merge_dict(target, {})
        assert target == {"version": "1.0"}


class TestMergeManifests:
    def test_creates_dest_from_source_when_dest_missing(self, tmp_path: Path):
        src = tmp_path / "src.yml"
        dst = tmp_path / "dst.yml"
        src.write_text(yaml.safe_dump({"version": "1.0", "dependencies": {"idf": ">=5.0"}}))

        merge_manifests(dst, src)

        assert dst.exists()
        data = yaml.safe_load(dst.read_text())
        assert data["version"] == "1.0"
        assert data["dependencies"]["idf"] == ">=5.0"

    def test_noop_when_source_missing(self, tmp_path: Path):
        dst = tmp_path / "dst.yml"
        dst.write_text(yaml.safe_dump({"version": "1.0"}))

        merge_manifests(dst, tmp_path / "does_not_exist.yml")

        assert yaml.safe_load(dst.read_text()) == {"version": "1.0"}

    def test_merges_dependencies_into_existing_dest(self, tmp_path: Path):
        src = tmp_path / "src.yml"
        dst = tmp_path / "dst.yml"
        dst.write_text(yaml.safe_dump({"version": "1.0", "dependencies": {"idf": ">=5.0"}}))
        src.write_text(yaml.safe_dump({"dependencies": {"lvgl": "^9.1"}}))

        merge_manifests(dst, src)

        data = yaml.safe_load(dst.read_text())
        assert "idf" in data["dependencies"]
        assert "lvgl" in data["dependencies"]

    def test_does_not_overwrite_version_in_dest(self, tmp_path: Path):
        src = tmp_path / "src.yml"
        dst = tmp_path / "dst.yml"
        dst.write_text(yaml.safe_dump({"version": "1.0"}))
        src.write_text(yaml.safe_dump({"version": "2.0"}))

        merge_manifests(dst, src)

        assert yaml.safe_load(dst.read_text())["version"] == "1.0"

    def test_multiple_merges_accumulate_dependencies(self, tmp_path: Path):
        dst = tmp_path / "dst.yml"
        for i, pkg in enumerate(["pkgA", "pkgB", "pkgC"]):
            src = tmp_path / f"src{i}.yml"
            src.write_text(yaml.safe_dump({"dependencies": {pkg: "*"}}))
            merge_manifests(dst, src)

        data = yaml.safe_load(dst.read_text())
        assert {"pkgA", "pkgB", "pkgC"} <= data["dependencies"].keys()

    def test_output_is_valid_yaml(self, tmp_path: Path):
        src = tmp_path / "src.yml"
        dst = tmp_path / "dst.yml"
        src.write_text(yaml.safe_dump({"dependencies": {"idf": ">=5.0"}}))

        merge_manifests(dst, src)

        # Should not raise
        yaml.safe_load(dst.read_text())
