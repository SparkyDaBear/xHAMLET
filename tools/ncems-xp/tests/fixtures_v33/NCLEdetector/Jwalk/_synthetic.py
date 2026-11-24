"""Utilities for the opt-in synthetic subprocess test; never scientific data."""
import json
import os
from pathlib import Path


def trace(event, **details):
    if os.environ.get("NCEMS_ALLOW_SYNTHETIC_BACKEND") != "YES_FOR_TESTS":
        raise RuntimeError("Synthetic backend was not explicitly authorized for a test")
    path = Path(os.environ["NCEMS_SYNTHETIC_BACKEND_TRACE"])
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": event, "scope": "SYNTHETIC FAKE BACKEND; NOT JWALK", **details}) + "\n")


def residues(structure):
    return {(r.id[1], chain.id, r.resname): r
            for chain in structure[0] for r in chain if r.id[0] == " "}
