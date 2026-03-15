# Copyright 2025-2026 David M. King
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def _load(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):  # pragma: no cover - defensive
        raise ValueError(f"Manifest at {path} must be a mapping")
    return data


def _merge_dict(target: Dict[str, Any], incoming: Dict[str, Any]) -> None:
    for key, value in incoming.items():
        if key == "dependencies" and isinstance(value, dict):
            dest_deps = target.setdefault("dependencies", {})
            if not isinstance(dest_deps, dict):  # pragma: no cover - defensive
                dest_deps = {}
                target["dependencies"] = dest_deps
            for dep_name, dep_val in value.items():
                dest_deps[dep_name] = dep_val
            continue
        if key not in target:
            target[key] = value


def merge_manifests(dest_path: Path, source_path: Path) -> None:
    """Merge a component manifest into dest_path (create if missing)."""
    if not source_path.exists():
        return
    dest_data = _load(dest_path)
    source_data = _load(source_path)
    _merge_dict(dest_data, source_data)
    dest_path.write_text(
        yaml.safe_dump(dest_data, sort_keys=False),
        encoding="utf-8",
    )
