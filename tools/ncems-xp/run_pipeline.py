#!/usr/bin/env python3
"""Compatibility name: always invoke the chemistry-aware v3.3 runner."""
from run_v33 import main
if __name__ == "__main__":
    raise SystemExit(main())
