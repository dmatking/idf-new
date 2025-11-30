# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

# .../esp32-starter/esp32_init_tool/esp32_init/paths.py
ROOT = Path(__file__).resolve().parents[2]

BOARDS_DIR    = ROOT / "boards"
TEMPLATES_DIR = ROOT / "idf-templates" / "base_project"
FEATURES_DIR  = ROOT / "features"
