#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
python -m unittest discover -s tests -p "test_*v33.py"
python tests/test_v33_independent.py
echo "SOFTWARE CHECKS PASSED. This is not full PXD or experimental validation."
