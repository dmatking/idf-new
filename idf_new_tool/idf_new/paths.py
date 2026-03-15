# Copyright 2025-2026 David M. King
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

# .../idf-new/idf_new_tool/idf_new/paths.py
ROOT = Path(__file__).resolve().parents[2]

BOARDS_DIR    = ROOT / "boards"
TEMPLATES_DIR = ROOT / "idf-templates" / "base_project"
MODULES_DIR   = ROOT / "modules"
