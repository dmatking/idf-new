# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Dict, List


@dataclass
class ModuleContext:
    project_dir: Path
    main_dir: Path
    cmake_extra_path: Path


class Module(Protocol):
    name: str
    flag: str       # e.g. "gps_neo6m"
    category: str   # e.g. "GPS"

    def apply(self, ctx: ModuleContext) -> None: ...


_registry: Dict[str, Module] = {}


def register(module: Module) -> None:
    if module.flag in _registry:
        raise ValueError(f"Module flag '{module.flag}' already registered")
    _registry[module.flag] = module


def get_module(flag: str) -> Module:
    return _registry[flag]


def list_modules() -> List[Module]:
    return list(_registry.values())
