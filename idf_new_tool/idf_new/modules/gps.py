# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

"""GPS module descriptors — NEO-6M and ATGM336H.

Both modules use identical NMEA-over-UART drivers. The shared C code lives
under modules/gps/_common/. Each descriptor copies that code and merges the
shared Kconfig into the generated project.
"""

from pathlib import Path

from .base import ModuleContext, register
from ..paths import MODULES_DIR

_GPS_COMMON = MODULES_DIR / "gps" / "_common"


def _apply_gps(ctx: ModuleContext) -> None:
    """Copy shared GPS C code and Kconfig into the project."""
    for fname in ("gps.c", "gps.h"):
        src = _GPS_COMMON / fname
        if src.exists():
            (ctx.main_dir / fname).write_bytes(src.read_bytes())

    kconfig_src = _GPS_COMMON / "Kconfig"
    kconfig_dst = ctx.main_dir / "Kconfig.projbuild"
    if kconfig_src.exists():
        snippet = kconfig_src.read_text(encoding="utf-8").rstrip()
        if kconfig_dst.exists():
            existing = kconfig_dst.read_text(encoding="utf-8").rstrip()
            kconfig_dst.write_text(existing + "\n\n" + snippet + "\n", encoding="utf-8")
        else:
            kconfig_dst.write_text(snippet + "\n", encoding="utf-8")


class Neo6mModule:
    name = "GPS — u-blox NEO-6M / GY-NEO6MV2"
    flag = "gps_neo6m"
    category = "GPS"

    def apply(self, ctx: ModuleContext) -> None:
        _apply_gps(ctx)


class Atgm336hModule:
    name = "GPS — ATGM336H"
    flag = "gps_atgm336h"
    category = "GPS"

    def apply(self, ctx: ModuleContext) -> None:
        _apply_gps(ctx)


register(Neo6mModule())
register(Atgm336hModule())
