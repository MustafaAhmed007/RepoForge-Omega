#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m venv "$TARGET/.repoforge-venv"
"$TARGET/.repoforge-venv/bin/python" -m pip install --upgrade pip
"$TARGET/.repoforge-venv/bin/python" -m pip install -e "$SOURCE_DIR"
printf '\nRepoForge installed in %s/.repoforge-venv\n' "$TARGET"
printf 'Run: %s/.repoforge-venv/bin/repoforge inspect %s\n' "$TARGET" "$TARGET"
