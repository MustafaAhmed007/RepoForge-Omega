#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"
python3 -m venv "$ROOT/.repoforge-venv"
"$ROOT/.repoforge-venv/bin/python" -m pip install --upgrade pip
"$ROOT/.repoforge-venv/bin/python" -m pip install -e "$OLDPWD"
printf '\nRepoForge installed in %s/.repoforge-venv\n' "$ROOT"
printf 'Run: %s/.repoforge-venv/bin/repoforge inspect %s\n' "$ROOT" "$ROOT"
