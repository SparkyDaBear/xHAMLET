#!/usr/bin/env bash
set -euo pipefail
NCEMS_PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
NCEMS_PYTHON="$HOME/miniconda3/envs/ncems-xp-test/bin/python"
if [ ! -x "$NCEMS_PYTHON" ]; then
  echo "STOP: existing ncems-xp-test environment not found. Run this on Jetstream." >&2
  exit 2
fi
exec "$NCEMS_PYTHON" "$NCEMS_PACKAGE_DIR/run_v33.py" "$@"
