#!/usr/bin/env python3

# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
from pathlib import Path

from .boards import list_boards
from .features import list_features
from .generator import GenerationOptions, ProjectGenerator


def build_parser() -> tuple[argparse.ArgumentParser, list]:
    parser = argparse.ArgumentParser(
        description="Initialize a new ESP-IDF project from esp32-starter templates."
    )
    parser.add_argument("project_name", nargs="?", help="Name of the new project directory")
    parser.add_argument("--board", help="Board ID (folder under boards/)")
    parser.add_argument(
        "--dest",
        type=Path,
        help="Optional destination directory (defaults to ./<project_name>)",
    )
    parser.add_argument(
        "--list-boards",
        action="store_true",
        help="Print available boards and exit",
    )
    parser.add_argument(
        "--list-features",
        action="store_true",
        help="Print available features and exit",
    )

    available_features = list_features()
    for feature in available_features:
        parser.add_argument(
            f"--{feature.flag}",
            action="store_true",
            help=f"Include optional feature: {feature.name}",
        )

    return parser, available_features


def _handle_listing(args: argparse.Namespace, features: list) -> bool:
    if args.list_boards:
        boards = list_boards()
        if boards:
            print("Available boards:")
            for board in boards:
                print(f"  - {board}")
        else:
            print("No boards found under boards/.")
        return True

    if args.list_features:
        if features:
            print("Available features:")
            for feature in features:
                print(f"  --{feature.flag}\t{feature.name}")
        else:
            print("No optional features are currently registered.")
        return True

    return False


def main() -> None:
    parser, features = build_parser()
    args = parser.parse_args()

    if _handle_listing(args, features):
        return

    if not args.project_name:
        parser.error("project_name is required")
    if not args.board:
        parser.error("--board is required")

    enabled_features = [f.flag for f in features if getattr(args, f.flag)]

    options = GenerationOptions(
        project_name=args.project_name,
        board_id=args.board,
        destination=args.dest,
        feature_flags=enabled_features,
    )

    generator = ProjectGenerator(options)

    try:
        project = generator.generate()
    except (FileNotFoundError, FileExistsError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Project created at {project.root}")
    if enabled_features:
        print("Enabled features: " + ", ".join(enabled_features))

    print("Next steps:")
    print(f"  cd {project.root}")
    print("  idf.py set-target <esp32/esp32s3/etc>")
    print("  idf.py build flash monitor")


if __name__ == "__main__":
    main()
