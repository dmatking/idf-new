# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(slots=True)
class Project:
	"""Represents a generated ESP-IDF project on disk."""

	name: str
	root: Path

	@property
	def main_dir(self) -> Path:
		return self.root / "main"

	def replace_text(self, target: Path | str, old: str, new: str, count: int = -1) -> None:
		path = Path(target)
		if not path.is_absolute():
			path = self.root / path
		text = path.read_text(encoding="utf-8")
		if old not in text:
			raise ValueError(f"'{old}' not found in {path}")
		path.write_text(text.replace(old, new, count), encoding="utf-8")

	def copy_into_main(self, source: Path, dest_name: str | None = None) -> Path:
		destination = self.main_dir / (dest_name or source.name)
		shutil.copy2(source, destination)
		return destination


def create_project(name: str, template_dir: Path, destination: Path | None = None) -> Project:
	if not template_dir.exists():
		raise FileNotFoundError(f"Template directory not found: {template_dir}")

	dest_dir = (destination or Path.cwd() / name).resolve()
	if dest_dir.exists():
		raise FileExistsError(f"Destination already exists: {dest_dir}")

	shutil.copytree(template_dir, dest_dir)
	project = Project(name=name, root=dest_dir)
	project.replace_text("CMakeLists.txt", "project(base_project)", f"project({name})", count=1)
	return project


def install_board(project: Project, board_dir: Path, board_id: str) -> Path:
	board_impl = board_dir / "board_impl.c"
	if not board_impl.exists():
		raise FileNotFoundError(f"Board '{board_id}' is missing board_impl.c")

	destination = project.copy_into_main(board_impl, f"board_{board_id}.c")
	project.replace_text(
		project.main_dir / "CMakeLists.txt",
		"board_impl.c",
		destination.name,
		count=1,
	)

	manifest_src = board_dir / "idf_component.yml"
	manifest_dst = project.main_dir / "idf_component.yml"
	if manifest_src.exists():
		shutil.copy2(manifest_src, manifest_dst)

	return destination
# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

