#!/usr/bin/env bash

# Copyright 2025 David M. King
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

ROOT_DIR="."

# Directories to skip (add more if needed)
SKIP_DIRS=".git .venv venv build dist"

should_skip_dir() {
    local dir="$1"
    for skip in $SKIP_DIRS; do
        if [[ "$dir" == *"/$skip" ]]; then
            return 0
        fi
    done
    return 1
}

export LC_ALL=C

find "$ROOT_DIR" -type f \( -name "*.c" -o -name "*.h" -o -name "*.py" \) | while read -r file; do
    # Skip files in ignored directories
    dir="$(dirname "$file")"
    if should_skip_dir "$dir"; then
        continue
    fi

    # If the file already has the SPDX line, skip it
    if grep -q "SPDX-License-Identifier: Apache-2.0" "$file"; then
        continue
    fi

    echo "Adding header to: $file"

    tmpfile="$(mktemp)"

    case "$file" in
        *.c|*.h)
            {
                echo "// Copyright 2025 David M. King"
                echo "// SPDX-License-Identifier: Apache-2.0"
                echo
                cat "$file"
            } > "$tmpfile"
            ;;
    *.py)
        # Check if the first line is a shebang
        first_line="$(head -n 1 "$file")"
        if [[ "$first_line" == \#!* ]]; then
            {
                echo "$first_line"
                echo "# Copyright 2025 David M. King"
                echo "# SPDX-License-Identifier: Apache-2.0"
                echo
                tail -n +2 "$file"
            } > "$tmpfile"
        else
            {
                echo "# Copyright 2025 David M. King"
                echo "# SPDX-License-Identifier: Apache-2.0"
                echo
                cat "$file"
            } > "$tmpfile"
        fi
        ;;

    esac

    mv "$tmpfile" "$file"
done
