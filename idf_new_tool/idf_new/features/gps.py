# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

from .base import FeatureContext, register
from ..paths import FEATURES_DIR

class GPSFeature:
    name = "GPS support"
    flag = "gps"

    def apply(self, ctx: FeatureContext) -> None:
        source_dir = FEATURES_DIR / "gps"

        # Copy gps.c/gps.h into main/
        for fname in ("gps.c", "gps.h"):
            src = source_dir / fname
            dst = ctx.main_dir / fname
            if not src.exists():
                continue
            dst.write_bytes(src.read_bytes())

        # Merge Kconfig snippet (if any) into main/Kconfig.projbuild
        kconfig_src = source_dir / "Kconfig"
        kconfig_dst = ctx.main_dir / "Kconfig.projbuild"
        if kconfig_src.exists():
            snippet = kconfig_src.read_text(encoding="utf-8").rstrip()
            if kconfig_dst.exists():
                existing = kconfig_dst.read_text(encoding="utf-8").rstrip()
                kconfig_dst.write_text(existing + "\n\n" + snippet + "\n", encoding="utf-8")
            else:
                kconfig_dst.write_text(snippet + "\n", encoding="utf-8")

        # CMake patching for gps.c we'll add later once gps.c is real

register(GPSFeature())
