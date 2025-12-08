# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import BOARDS_DIR


BOARD_IMPL = "board_impl.c"
BOARD_META_FILE = "board.json"


@dataclass(slots=True)
class BoardScreen:
    size_inches: float | None = None
    resolution: str | None = None
    technology: str | None = None
    shape: str | None = None


@dataclass(slots=True)
class BoardInfo:
    board_id: str
    path: Path
    display_name: str
    features: list[str]
    has_touch: bool
    screen: BoardScreen | None
    panel: str | None = None


def _board_dirs() -> list[Path]:
    if not BOARDS_DIR.exists():
        return []
    return sorted(
        impl.parent for impl in BOARDS_DIR.rglob(BOARD_IMPL) if impl.is_file()
    )


def _load_board_info(board_id: str, directory: Path) -> BoardInfo:
    meta_path = directory / BOARD_META_FILE
    data: dict[str, Any] = {}
    if meta_path.exists():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise SystemExit(f"Invalid {BOARD_META_FILE} for board '{board_id}': {exc}") from exc

    screen = None
    screen_data = data.get("screen")
    if isinstance(screen_data, dict):
        screen = BoardScreen(
            size_inches=screen_data.get("size_inches"),
            resolution=screen_data.get("resolution"),
            technology=screen_data.get("technology"),
            shape=screen_data.get("shape"),
        )

    raw_features = data.get("features")
    features: list[str] = []
    if isinstance(raw_features, list):
        features = [str(feature) for feature in raw_features if str(feature).strip()]
    features = list(dict.fromkeys(features))

    display_name = data.get("display_name") or directory.name
    has_touch = bool(data.get("has_touch"))
    panel = data.get("panel")

    return BoardInfo(
        board_id=board_id,
        path=directory,
        display_name=display_name,
        features=features,
        has_touch=has_touch,
        screen=screen,
        panel=panel,
    )


def list_boards() -> list[BoardInfo]:
    """Return board metadata for every directory under boards/."""
    boards: list[BoardInfo] = []
    for directory in _board_dirs():
        board_id = directory.relative_to(BOARDS_DIR).as_posix()
        boards.append(_load_board_info(board_id, directory))
    return boards


def _ensure_within_boards(path: Path) -> None:
    try:
        path.relative_to(BOARDS_DIR.resolve())
    except ValueError as exc:  # pragma: no cover - defensive guardrail
        raise SystemExit("Board path escapes boards/ directory") from exc


def validate_board(board_id: str) -> Path:
    candidate = (BOARDS_DIR / board_id).resolve()
    _ensure_within_boards(candidate)
    if not candidate.exists() or not candidate.is_dir():
        available = [info.board_id for info in list_boards()]
        raise SystemExit(
            f"Board '{board_id}' not found.\nAvailable boards: {', '.join(available)}"
        )
    board_impl = candidate / BOARD_IMPL
    if not board_impl.exists():
        raise SystemExit(f"Board '{board_id}' is missing {BOARD_IMPL}")
    return candidate
