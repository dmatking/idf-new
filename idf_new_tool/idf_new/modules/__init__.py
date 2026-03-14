# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Module registration helpers.

Importing this package automatically loads all submodules so each module can
register itself with the module registry.
"""

from importlib import import_module
from pkgutil import iter_modules
from pathlib import Path

from .base import Module, ModuleContext, register, get_module, list_modules  # noqa: F401

def _auto_register() -> None:
	pkg_path = Path(__file__).resolve().parent
	for mod in iter_modules([str(pkg_path)]):
		if mod.name in {"__init__", "base"}:
			continue
		import_module(f"{__name__}.{mod.name}")


_auto_register()

__all__ = [
	"Module",
	"ModuleContext",
	"register",
	"get_module",
	"list_modules",
]
