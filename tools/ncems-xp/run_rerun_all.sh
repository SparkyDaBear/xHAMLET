#!/usr/bin/env bash
set -euo pipefail
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
python_bin="${NCEMS_XP_PYTHON:-$HOME/miniconda3/envs/ncems-xp-test/bin/python}"
if [ ! -x "$python_bin" ]; then
    printf '%s\n' "STOP: existing XP Python was not found: $python_bin" >&2
    printf '%s\n' 'Use the existing ncems-xp-test environment; this launcher does not install an environment.' >&2
    exit 2
fi
exec "$python_bin" "$script_dir/rerun_all.py" "$@"
