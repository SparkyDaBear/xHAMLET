"""SYNTHETIC TEST BACKEND ONLY: parse coordinates, write an explicit marker."""
import json
from pathlib import Path
from Bio.PDB import PDBParser
from ._synthetic import trace


def read_PDB_file(path):
    trace("read_PDB_file")
    return PDBParser(QUIET=True).get_structure("SYNTHETIC_ONLY", path)


def write_sasd_to_txt(values, pdb, output):
    trace("write_sasd_to_txt", records=len(values))
    Path(output, "SYNTHETIC_FAKE_DISTANCES_NOT_JWALK.json").write_text(json.dumps({
        "scope": "TEST FIXTURE ONLY; fabricated surface distances; no scientific validation",
        "values": values,
    }, indent=2) + "\n")
