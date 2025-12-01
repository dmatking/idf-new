# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Feature registration helpers.

Importing this package automatically loads all submodules so each feature can
register itself with the feature registry.
"""

from importlib import import_module
from pkgutil import iter_modules
from pathlib import Path

from .base import Feature, FeatureContext, register, get_feature, list_features  # noqa: F401

def _auto_register() -> None:
	pkg_path = Path(__file__).resolve().parent
	for module in iter_modules([str(pkg_path)]):
		if module.name in {"__init__", "base"}:
			continue
		import_module(f"{__name__}.{module.name}")


_auto_register()

__all__ = [
	"Feature",
	"FeatureContext",
	"register",
	"get_feature",
	"list_features",
]
