# Copyright 2026 David M. King
# SPDX-License-Identifier: Apache-2.0

"""Build-test fixtures.

All tests in tests/build/ are automatically skipped unless ESP-IDF is
available in the environment.  Source export.sh before running:

    source ~/esp/esp-idf-v5.5.1/export.sh
    python -m pytest tests/build/ -v
"""

from __future__ import annotations

import os
import shutil

import pytest


def _idf_available() -> bool:
    return bool(os.environ.get("IDF_PATH")) and bool(shutil.which("idf.py"))


@pytest.fixture(autouse=True)
def require_idf():
    """Skip every test in this directory if IDF_PATH is not set."""
    if not _idf_available():
        pytest.skip(
            "ESP-IDF not available — run:  source ~/esp/esp-idf-v5.5.1/export.sh"
        )
