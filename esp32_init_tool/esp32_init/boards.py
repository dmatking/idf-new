# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from .paths import BOARDS_DIR

def list_boards() -> list[str]:
    if not BOARDS_DIR.exists():
        return []
    return sorted(p.name for p in BOARDS_DIR.iterdir() if p.is_dir())

def validate_board(board_id: str) -> Path:
    board_dir = BOARDS_DIR / board_id
    if not board_dir.exists():
        available = list_boards()
        raise SystemExit(
            f"Board '{board_id}' not found.\nAvailable boards: {', '.join(available)}"
        )
    return board_dir
