#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
TEMPLATES_DIR = ROOT / "idf-templates" / "base_project"
BOARDS_DIR = ROOT / "boards"

def copy_tree(src: Path, dst: Path):
    if dst.exists():
        raise SystemExit(f"Destination {dst} already exists.")
    shutil.copytree(src, dst)

def replace_in_file(path: Path, old: str, new: str):
    text = path.read_text(encoding="utf-8")
    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Initialize a new ESP-IDF project.")
    parser.add_argument("project_name", help="Name of the new project directory")
    parser.add_argument("--board", required=True, help="Board ID (folder under boards/)")
    args = parser.parse_args()

    project_name = args.project_name
    board_id = args.board

    if not TEMPLATES_DIR.exists():
        raise SystemExit(f"Template directory not found: {TEMPLATES_DIR}")

    board_dir = BOARDS_DIR / board_id
    if not board_dir.exists():
        available = [p.name for p in BOARDS_DIR.iterdir() if p.is_dir()]
        raise SystemExit(
            f"Board '{board_id}' not found.\nAvailable boards: {', '.join(available)}"
        )

    # Create project in current working directory
    dest_dir = Path.cwd() / project_name
    print(f"Creating project at: {dest_dir}")
    copy_tree(TEMPLATES_DIR, dest_dir)

    # Update top-level CMakeLists.txt with project name
    cmake_top = dest_dir / "CMakeLists.txt"
    replace_in_file(cmake_top, "project(base_project)", f"project({project_name})")

    # Copy board_impl.c into main/ with a nice name
    src_board_impl = board_dir / "board_impl.c"
    if not src_board_impl.exists():
        raise SystemExit(f"Board '{board_id}' has no board_impl.c")

    dest_board_impl = dest_dir / "main" / f"board_{board_id}.c"
    shutil.copy(src_board_impl, dest_board_impl)

    cmake_main = dest_dir / "main" / "CMakeLists.txt"
    replace_in_file(
        cmake_main,
        "board_impl.c",
        f"board_{board_id}.c"
    )

    # NEW: board-specific idf_component.yml, if present
    board_manifest = board_dir / "idf_component.yml"
    dest_manifest = dest_dir / "main" / "idf_component.yml"
    if board_manifest.exists():
        print(f"Using board-specific manifest: {board_manifest}")
        shutil.copy(board_manifest, dest_manifest)

    print("Done.")
    print(f"Next steps:")
    print(f"  cd {project_name}")
    print(f"  idf.py set-target <esp32/esp32s3/etc>")
    print(f"  idf.py build flash monitor")

if __name__ == "__main__":
    main()
