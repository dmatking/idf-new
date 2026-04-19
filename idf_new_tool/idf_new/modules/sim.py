# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Desktop simulator module (--sim).

Adds a sim/ directory to the project with:
  - CMakeLists.txt wired to esp32-screencap via git submodule
  - main_sim.c starter (gradient smoke-test + screencap loop)
  - screencap added as sim/screencap git submodule

Only meaningful for boards that have an LCD with known dimensions.
For headless boards the module is a no-op (with a printed notice).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .base import ModuleContext, register
from ..paths import MODULES_DIR

_COMMON = MODULES_DIR / "sim" / "_common"

SCREENCAP_URL = "ssh://git@piserver:222/dmatking/esp32-screencap.git"
SCREENCAP_BRANCH = "sim"   # track the sim branch until merged to main


class SimModule:
    name = "Desktop simulator (SDL2 preview + PNG screenshots)"
    flag = "sim"
    category = "Sim"

    def apply(self, ctx: ModuleContext) -> None:
        board = ctx.board_info
        if not board or not board.screen or not board.screen.width:
            print("  [sim] board has no LCD — skipping sim scaffold")
            return

        w = board.screen.width
        h = board.screen.height

        sim_dir = ctx.project_dir / "sim"
        shutil.copytree(_COMMON, sim_dir)

        # Replace placeholders in CMakeLists.txt
        cmake = sim_dir / "CMakeLists.txt"
        text = cmake.read_text(encoding="utf-8")
        text = (text
                .replace("__PROJECT_NAME__", ctx.project_dir.name)
                .replace("__BOARD_WIDTH__",  str(w))
                .replace("__BOARD_HEIGHT__", str(h)))
        cmake.write_text(text, encoding="utf-8")

        # Replace placeholder in main_sim.c
        main_sim = sim_dir / "main_sim.c"
        text = main_sim.read_text(encoding="utf-8")
        text = text.replace("__PROJECT_NAME__", ctx.project_dir.name)
        main_sim.write_text(text, encoding="utf-8")

        # git init the project (idempotent), then add screencap submodule
        subprocess.run(["git", "init"], cwd=ctx.project_dir, capture_output=True)
        result = subprocess.run(
            ["git", "submodule", "add", "--branch", SCREENCAP_BRANCH,
             SCREENCAP_URL, "sim/screencap"],
            cwd=ctx.project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  [sim] sim/ created ({w}x{h}), screencap submodule added")
        else:
            print(f"  [sim] sim/ created ({w}x{h})")
            print(f"  [sim] Could not add submodule: {result.stderr.strip()}")
            print(f"  [sim] Run manually: git submodule add --branch {SCREENCAP_BRANCH} "
                  f"{SCREENCAP_URL} sim/screencap")


register(SimModule())
