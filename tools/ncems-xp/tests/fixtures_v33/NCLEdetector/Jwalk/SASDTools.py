"""SYNTHETIC TEST BACKEND ONLY: fixed fake SASD; real CA arithmetic only."""
import math
from Bio.PDB import PDBParser
from ._synthetic import residues, trace


def parallel_BFS(voxels_a, voxels_b, surface, first, second, pairs, limit, voxel, ncpus, pair_file):
    # Deliberately omit site A3 to test missing-path handling. This is not BFS.
    values = [(a, b, 18.62) for a, b in pairs
              if not any(endpoint[1] == "A" and endpoint[0] == 3 for endpoint in (a, b))]
    trace("parallel_BFS_FAKE_FIXED_VALUES", requested=len(pairs), returned=len(values), limit=limit)
    return values


def get_euclidean_distances(values, pdb, first_kind, second_kind):
    structure = PDBParser(QUIET=True).get_structure("SYNTHETIC_ONLY", pdb)
    lookup = residues(structure)
    result = [(a, b, distance, math.dist(lookup[a]["CA"].coord, lookup[b]["CA"].coord))
              for a, b, distance in values]
    trace("get_euclidean_distances", records=len(result))
    return result
