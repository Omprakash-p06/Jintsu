#!/usr/bin/env bash
# POSIX shell convenience wrapper delegating to universal cross-platform run.py
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ROOT_DIR/run.py" "$@"
