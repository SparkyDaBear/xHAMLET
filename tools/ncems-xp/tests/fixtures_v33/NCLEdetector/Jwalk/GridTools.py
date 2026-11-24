"""SYNTHETIC TEST BACKEND ONLY: no voxel grid or solvent surface exists."""
from pathlib import Path
from ._synthetic import residues, trace


def makeGrid(structure, voxel):
    trace("makeGrid", voxel=voxel)
    return {"synthetic_structure": structure}


def mark_CAlphas_pairs(grid, structure, pair_file):
    lookup = {(key[0], key[1]): (key, residue) for key, residue in residues(structure).items()}
    pairs, first, second = [], {}, {}
    for line in Path(pair_file).read_text().splitlines():
        r1, c1, r2, c2, *_ = line.split("|")
        a, ra = lookup[int(r1), c1]
        b, rb = lookup[int(r2), c2]
        pairs.append((a, b))
        first[a], second[b] = ra["CA"].coord, rb["CA"].coord
    trace("mark_CAlphas_pairs", requested_pairs=len(pairs))
    return pairs, first, second


def generate_solvent_accessible_surface(grid, structure, first, second):
    trace("generate_solvent_accessible_surface")
    return {"synthetic_only": True}


def find_surface_voxels(points, surface, pair_file):
    trace("find_surface_voxels")
    return points, []


def remove_duplicates(values):
    trace("remove_duplicates")
    return values
