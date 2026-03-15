# Copyright 2025-2026 David M. King
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .boards import validate_board
from .modules import ModuleContext, get_module
from .paths import TEMPLATES_DIR
from .project import Project, create_project, install_board, install_board_feature


@dataclass(slots=True)
class GenerationOptions:
	project_name: str
	board_id: str
	destination: Path | None = None
	feature_flags: Iterable[str] = field(default_factory=tuple)  # board-local features
	module_flags: Iterable[str] = field(default_factory=tuple)   # generic modules


class ProjectGenerator:
	def __init__(self, options: GenerationOptions):
		self.options = options

	def generate(self) -> Project:
		board_dir = validate_board(self.options.board_id)
		project = create_project(
			name=self.options.project_name,
			template_dir=TEMPLATES_DIR,
			destination=self.options.destination,
		)
		install_board(project, board_dir, self.options.board_id)
		self._apply_board_features(project, board_dir)
		self._apply_modules(project)
		return project

	def _apply_board_features(self, project: Project, board_dir: Path) -> None:
		requested = list(dict.fromkeys(self.options.feature_flags))
		if not requested:
			return

		features_dir = board_dir / "features"
		for name in requested:
			feature_dir = features_dir / name
			if not feature_dir.is_dir():
				raise SystemExit(
					f"Board feature '{name}' not found at {feature_dir}.\n"
					f"Available features are sub-directories of {features_dir}"
				)
			install_board_feature(project, feature_dir, name)

	def _apply_modules(self, project: Project) -> None:
		requested = list(dict.fromkeys(self.options.module_flags))
		if not requested:
			return

		ctx = ModuleContext(
			project_dir=project.root,
			main_dir=project.main_dir,
			cmake_extra_path=project.main_dir / "main.cmake.extra",
		)
		for flag in requested:
			try:
				module = get_module(flag)
			except KeyError as exc:
				raise SystemExit(f"Unknown module: {flag}") from exc
			module.apply(ctx)
