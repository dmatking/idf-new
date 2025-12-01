# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .boards import validate_board
from .features import FeatureContext, get_feature
from .paths import TEMPLATES_DIR
from .project import Project, create_project, install_board


@dataclass(slots=True)
class GenerationOptions:
	project_name: str
	board_id: str
	destination: Path | None = None
	feature_flags: Iterable[str] = field(default_factory=tuple)


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
		self._apply_features(project)
		return project

	def _apply_features(self, project: Project) -> None:
		requested = list(dict.fromkeys(self.options.feature_flags))
		if not requested:
			return

		ctx = FeatureContext(project_dir=project.root, main_dir=project.main_dir)
		for flag in requested:
			try:
				feature = get_feature(flag)
			except KeyError as exc:  # pragma: no cover - defensive
				raise SystemExit(f"Unknown feature flag: {flag}") from exc
			feature.apply(ctx)
# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

