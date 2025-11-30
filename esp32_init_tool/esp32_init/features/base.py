# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Dict, List

@dataclass
class FeatureContext:
    project_dir: Path
    main_dir: Path

class Feature(Protocol):
    name: str
    flag: str  # e.g. "gps"
    def apply(self, ctx: FeatureContext) -> None: ...

_registry: Dict[str, Feature] = {}

def register(feature: Feature) -> None:
    _registry[feature.flag] = feature

def get_feature(flag: str) -> Feature:
    return _registry[flag]

def list_features() -> List[Feature]:
    return list(_registry.values())
