# Copyright 2025-2026 David M. King
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

from .boards import list_boards
from .modules import list_modules
from .generator import GenerationOptions, ProjectGenerator
from .cli import _format_screen, _format_traits


def action_extensions(base_actions: dict, project_path: str) -> dict:
    modules = list_modules()

    def _idfnew_boards(subcommand_name: str, ctx: Any, global_args: Any, **action_args: Any) -> None:
        find = action_args.get('find')
        boards = list_boards()
        if find:
            boards = [b for b in boards if any(find.lower() in t.lower() for t in _format_traits(b))]
        if not boards:
            print(f"No boards found{f' matching {find!r}' if find else ''}.")
            return
        for info in boards:
            print(f"  - {info.board_id}")
            print(f"    Name: {info.display_name}")
            screen_desc = _format_screen(info)
            if screen_desc:
                print(f"    Screen: {screen_desc}")
            if info.board_features:
                print(f"    Features: {', '.join(info.board_features)}")
            print()

    def _idfnew_modules(subcommand_name: str, ctx: Any, global_args: Any, **action_args: Any) -> None:
        if not modules:
            print("No modules registered.")
            return
        by_category: dict[str, list] = {}
        for mod in modules:
            by_category.setdefault(mod.category, []).append(mod)
        print("Available modules:")
        for category, mods in sorted(by_category.items()):
            print(f"  {category}:")
            for mod in mods:
                print(f"    --{mod.flag}\t{mod.name}")

    def _idfnew_find(subcommand_name: str, ctx: Any, global_args: Any, **action_args: Any) -> None:
        _idfnew_boards(subcommand_name, ctx, global_args, find=action_args.get('tag', ''))

    def _idfnew_create(subcommand_name: str, ctx: Any, global_args: Any, **action_args: Any) -> None:
        project_name = action_args.get('name')
        board_id = action_args.get('board')
        raw_dest = action_args.get('dest')
        dest = Path(raw_dest) if raw_dest else None
        features = list(action_args.get('feature') or [])
        module_flags = [m.flag for m in modules if action_args.get(m.flag)]

        options = GenerationOptions(
            project_name=project_name,
            board_id=board_id,
            destination=dest,
            feature_flags=features,
            module_flags=module_flags,
        )
        try:
            project = ProjectGenerator(options).generate()
        except (FileNotFoundError, FileExistsError) as exc:
            raise SystemExit(str(exc)) from exc

        print(f"Project created at {project.root}")
        if features:
            print("Board features: " + ", ".join(features))
        if module_flags:
            print("Modules: " + ", ".join(module_flags))
        print("Next steps:")
        print(f"  cd {project.root}")
        print("  idf.py set-target <esp32/esp32s3/etc>")
        print("  idf.py build flash monitor")

    module_options = [
        {
            "names": [f"--{m.flag}"],
            "is_flag": True,
            "help": f"Include module: {m.name}",
        }
        for m in modules
    ]

    return {
        "version": "1",
        "actions": {
            "idfnew-boards": {
                "callback": _idfnew_boards,
                "short_help": "List available boards",
                "help": "List all available boards. Use --find to filter by tag (e.g. touch, ips, round).",
                "options": [
                    {
                        "names": ["--find", "-f"],
                        "type": str,
                        "default": None,
                        "help": "Filter boards by tag",
                    },
                ],
            },
            "idfnew-modules": {
                "callback": _idfnew_modules,
                "short_help": "List available modules",
                "help": "List all available modules grouped by category.",
            },
            "idfnew-find": {
                "callback": _idfnew_find,
                "short_help": "Find boards by tag",
                "help": "Find boards matching a tag (e.g. touch, ips, round).",
                "options": [
                    {
                        "names": ["--tag", "-t"],
                        "type": str,
                        "required": True,
                        "help": "Tag to search for",
                    },
                ],
            },
            "idfnew-create": {
                "callback": _idfnew_create,
                "short_help": "Generate a new ESP-IDF project",
                "help": "Generate a new ESP-IDF project from a board template.",
                "options": [
                    {
                        "names": ["--name"],
                        "type": str,
                        "required": True,
                        "help": "Project name (new directory will be created with this name)",
                    },
                    {
                        "names": ["--board"],
                        "type": str,
                        "required": True,
                        "help": "Board ID (e.g. m5stack/tab5)",
                    },
                    {
                        "names": ["--dest"],
                        "type": str,
                        "default": None,
                        "help": "Destination directory (default: ./<name>)",
                    },
                    {
                        "names": ["--feature"],
                        "multiple": True,
                        "type": str,
                        "help": "Board feature to include (repeatable)",
                    },
                ] + module_options,
            },
        },
    }
