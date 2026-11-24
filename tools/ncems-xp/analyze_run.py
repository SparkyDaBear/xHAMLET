"""Compatibility imports for v3.3; old filtered runs require a fresh intake."""
from analyze_v33 import analyze, main
from geometry_audit_v33 import CoordinateAudit, read_csv, write_csv, write_json, pair_key
if __name__ == "__main__":
    raise SystemExit(main())
