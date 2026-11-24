#!/usr/bin/env python3
"""Static-structure XP research draft; no changes to xHAMLET or NCLEdetector.

Scoring follows the user-supplied order_params.py: CalculateOP.score_XL.
Jwalk call order follows CalculateOP.runJwalk. Original software: O'Brien Lab
NCLEdetector and the Jwalk authors. See README.md for scope and validation.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
import sys
from datetime import datetime, timezone

AA = {"LYS": "K", "SER": "S", "THR": "T", "TYR": "Y", "MET": "M"}
SIDECHAIN = {
    "ALA": "CB", "ARG": "CB CG CD NE CZ NH1 NH2", "ASN": "CB CG OD1 ND2",
    "ASP": "CB CG OD1 OD2", "CYS": "CB SG", "GLN": "CB CG CD OE1 NE2",
    "GLU": "CB CG CD OE1 OE2", "GLY": "", "HIS": "CB CG ND1 CD2 CE1 NE2",
    "ILE": "CB CG1 CG2 CD1", "LEU": "CB CG CD1 CD2", "LYS": "CB CG CD CE NZ",
    "MET": "CB CG SD CE", "PHE": "CB CG CD1 CD2 CE1 CE2 CZ", "PRO": "CB CG CD",
    "SER": "CB OG", "THR": "CB OG1 CG2", "TRP": "CB CG CD1 CD2 NE1 CE2 CE3 CZ2 CZ3 CH2",
    "TYR": "CB CG CD1 CD2 CE1 CE2 CZ OH", "VAL": "CB CG1 CG2",
}
SC_LENGTH = {"K": 6.3, "S": 2.5, "T": 2.5, "Y": 6.5, "M": 1.5}
REFERENCE_SHA256 = "c09b3af28a3df8ba8299b23b6f0bb72819891134d40782a90180c200692c24a2"
MODEL_ID = "NCLEdetector_uploaded_score_XL_offset_1.1"
Residue = tuple[int, str, str]  # PDB residue number, chain ID, three-letter name
Pair = tuple[Residue, Residue]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_parameters(aa1: str, aa2: str) -> tuple[float, float, float]:
    """Return mu, sigma, cutoff in angstrom, exactly as in supplied score_XL."""
    if aa1 not in SC_LENGTH or aa2 not in SC_LENGTH:
        raise ValueError("XP model supports only K, S, T, Y, M.")
    offset = 1.1
    kk_mu = 18.6 + offset
    kk_sigma = (offset + 3 * 6.0) / 3
    kk_threshold = 33.0 + offset
    mu = kk_mu + (SC_LENGTH[aa1] + SC_LENGTH[aa2]) - 2 * SC_LENGTH["K"]
    sigma = (mu - (kk_mu - 3 * kk_sigma)) / 3
    threshold = kk_threshold + mu - kk_mu
    return mu, sigma, threshold


def score_xl(aa1: str, aa2: str, sasd: float) -> float:
    """Gaussian density, NOT a calibrated experimental probability.

    Missing/nonfinite distances are errors, not zeros. -1 is the explicit
    special distance value accepted by the supplied reference implementation.
    """
    mu, sigma, threshold = model_parameters(aa1, aa2)
    if not math.isfinite(sasd) or (sasd < 0 and sasd != -1):
        raise ValueError("SASD must be finite and nonnegative, or explicit -1.")
    if sasd == -1 or sasd > threshold:
        return 0.0
    return math.exp(-0.5 * ((sasd - mu) / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))


def pair_key(pair: Pair) -> Pair:
    return tuple(sorted(pair))


def load_structure(path: Path):
    """Validate a single-model, standard-residue full-atom PDB conservatively."""
    if path.suffix.lower() != ".pdb":
        raise ValueError("This draft accepts .pdb coordinates only. Sequence needs a structure; mmCIF needs reviewed conversion.")
    from Bio.PDB import PDBParser
    structure = PDBParser(PERMISSIVE=False, QUIET=True).get_structure(path.stem, str(path))
    models = list(structure.get_models())
    if len(models) != 1:
        raise ValueError("Supply exactly one coordinate model per PDB file.")
    residues = {}
    for chain in models[0]:
        if len(chain.id) != 1 or not chain.id.isalnum():
            raise ValueError("Use explicit one-character alphanumeric PDB chain IDs; no silent remapping.")
        for res in chain:
            hetero, number, insertion = res.id
            if hetero.strip():
                raise ValueError(f"Nonstandard/water/ligand record at {chain.id}:{number}; prepare a reviewed protein-only PDB first.")
            if insertion.strip() or not (1 <= number <= 9999):
                raise ValueError(f"Unsupported insertion code or numbering at {chain.id}:{res.id}; mapping must be reviewed.")
            name = res.get_resname().upper()
            if name not in SIDECHAIN:
                raise ValueError(f"Unsupported residue {name} at {chain.id}:{number}.")
            if res.is_disordered() or any(a.is_disordered() for a in res):
                raise ValueError(f"Alternate conformations at {chain.id}:{number}; select a conformer explicitly first.")
            missing = (set("N CA C O".split()) | set(SIDECHAIN[name].split())) - set(res.child_dict)
            if missing:
                raise ValueError(f"Missing heavy atoms at {chain.id}:{number}: {', '.join(sorted(missing))}.")
            if any(not all(math.isfinite(float(x)) for x in a.coord) for a in res):
                raise ValueError(f"Nonfinite coordinates at {chain.id}:{number}.")
            if name in AA:
                residues[number, chain.id, name] = res
    if len(residues) < 2:
        raise ValueError("Need at least two residues of types K/S/T/Y/M in the structure.")
    return structure, residues


def select_pairs(residues: dict, pairs_csv: Path | None, max_pairs: int) -> list[Pair]:
    if pairs_csv is None:
        n = len(residues)
        if n * (n - 1) // 2 > max_pairs:
            raise ValueError(f"All-pairs exceeds --max-pairs {max_pairs}; start with a small --pairs CSV.")
        return list(itertools.combinations(sorted(residues), 2))
    lookup = {(r[1], r[0]): r for r in residues}
    pairs = []
    with pairs_csv.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fields = {"chain1", "residue1", "chain2", "residue2"}
        if not fields.issubset(reader.fieldnames or []):
            raise ValueError("Pairs CSV needs chain1,residue1,chain2,residue2 using PDB numbering.")
        for line, row in enumerate(reader, 2):
            try:
                first = lookup[row["chain1"].strip(), int(row["residue1"])]
                second = lookup[row["chain2"].strip(), int(row["residue2"])]
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Pairs CSV line {line}: endpoint absent or outside K/S/T/Y/M.") from exc
            if first == second:
                raise ValueError(f"Pairs CSV line {line}: a residue cannot pair with itself.")
            pairs.append(pair_key((first, second)))
            if len(pairs) > max_pairs:
                raise ValueError("Pairs file exceeds --max-pairs.")
    if not pairs or len(set(pairs)) != len(pairs):
        raise ValueError("Pairs CSV must contain nonempty, unique unordered pairs.")
    return pairs


def run_jwalk(pdb: Path, pairs_file: Path, outdir: Path, ncpus: int):
    """Call only NCLEdetector's Jwalk modules; never initialize a trajectory."""
    from NCLEdetector.Jwalk import PDBTools, GridTools, SurfaceTools, SASDTools
    modules = (PDBTools, GridTools, SurfaceTools, SASDTools)
    hashes = {m.__name__: sha256(Path(m.__file__)) for m in modules}
    structure = PDBTools.read_PDB_file(str(pdb))
    grid = GridTools.makeGrid(structure, 1)
    pairs, first, second = GridTools.mark_CAlphas_pairs(grid, structure, str(pairs_file))
    # aa_dict is used for messages only when xl_list == 'NULL'; here a list is supplied.
    first, second = SurfaceTools.check_solvent_accessibility_freesasa_both(
        str(pdb), first, second, str(pairs_file), {}, ncpus)
    surface = GridTools.generate_solvent_accessible_surface(grid, structure, first, second)
    vox1, removed1 = GridTools.find_surface_voxels(first, surface, str(pairs_file))
    vox2, removed2 = GridTools.find_surface_voxels(second, surface, str(pairs_file))
    pairs = SurfaceTools.update_crosslink_pairs(pairs, first, second, removed1, removed2)
    sasds = SASDTools.parallel_BFS(vox1, vox2, surface, first, second, pairs, 50.0, 1, ncpus, str(pairs_file))
    sasds = GridTools.remove_duplicates(sasds)
    sasds = SASDTools.get_euclidean_distances(sasds, str(pdb), "NULL", "NULL")
    PDBTools.write_sasd_to_txt(sasds, str(pdb), str(outdir))
    distances = {}
    for a, b, sasd, euclidean in sasds:
        key = pair_key((tuple(a), tuple(b)))
        value = (float(sasd), float(euclidean))
        if key in distances and distances[key] != value:
            raise ValueError("Conflicting Jwalk distances for the same pair; review jwalk.log.")
        distances[key] = value
    return distances, hashes


def write_results(path: Path, model: str, pairs: list[Pair], distances: dict) -> dict:
    expected = {pair_key(p) for p in pairs}
    if set(distances) - expected:
        raise ValueError("Jwalk returned endpoints outside the requested structure/pair list.")
    counts = {}
    fields = ["structure_id", "chain1", "residue1", "aa1", "chain2", "residue2", "aa2",
              "sasd_A", "euclidean_A", "xp", "status", "score_model"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for a, b in pairs:
            row = dict(structure_id=model, chain1=a[1], residue1=a[0], aa1=AA[a[2]],
                       chain2=b[1], residue2=b[0], aa2=AA[b[2]], score_model=MODEL_ID)
            result = distances.get(pair_key((a, b)))
            if result is None:
                row.update(sasd_A="", euclidean_A="", xp="", status="NO_SASD_RETURNED")
            else:
                d, euclidean = result
                if not math.isfinite(euclidean) or euclidean < 0:
                    raise ValueError("Invalid Euclidean distance returned by Jwalk.")
                score = score_xl(AA[a[2]], AA[b[2]], d)
                cutoff = model_parameters(AA[a[2]], AA[b[2]])[2]
                status = "JWALK_MINUS_ONE" if d == -1 else ("ABOVE_SCORE_CUTOFF" if d > cutoff else "SCORED")
                row.update(sasd_A=d, euclidean_A=euclidean, xp=score, status=status)
            counts[row["status"]] = counts.get(row["status"], 0) + 1
            writer.writerow(row)
    return counts


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure", type=Path, required=True, help="One full-atom, single-model, protein-only PDB.")
    parser.add_argument("--outdir", type=Path, required=True, help="NEW output directory; existing directories are refused.")
    parser.add_argument("--pairs", type=Path, help="Optional small CSV in PDB chain/residue numbering; otherwise all K/S/T/Y/M pairs.")
    parser.add_argument("--ncpus", type=int, default=1)
    parser.add_argument("--max-pairs", type=int, default=50000)
    parser.add_argument("--check-only", action="store_true", help="Validate and prepare input without running Jwalk; no XP values.")
    args = parser.parse_args(argv)
    report = {}
    created = False
    try:
        if args.ncpus < 1 or args.max_pairs < 1:
            raise ValueError("ncpus and max-pairs must be positive.")
        path = args.structure.expanduser().resolve(strict=True)
        if args.outdir.exists():
            raise ValueError("Output directory already exists; use a new name to preserve previous results.")
        structure, residues = load_structure(path)
        pairs = select_pairs(residues, args.pairs, args.max_pairs)
        args.outdir.mkdir(parents=True, exist_ok=False)
        created = True
        from Bio.PDB import PDBIO
        normalized = args.outdir / "input_structure.pdb"
        writer = PDBIO()
        writer.set_structure(structure)
        writer.save(str(normalized))
        pairs_file = args.outdir / "residue_pairs.txt"
        pairs_file.write_text("".join(f"{a[0]}|{a[1]}|{b[0]}|{b[1]}|\n" for a, b in pairs))
        versions = {}
        for name in ("NCLEdetector", "biopython", "numpy", "freesasa"):
            try:
                versions[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                versions[name] = "not installed as distribution"
        report = {"state": "CHECK_ONLY" if args.check_only else "STARTED",
                  "created_utc": datetime.now(timezone.utc).isoformat(), "structure": str(path),
                  "structure_sha256": sha256(path), "normalized_pdb_sha256": sha256(normalized),
                  "wrapper_sha256": sha256(Path(__file__)), "reference_order_params_sha256": REFERENCE_SHA256,
                  "score_model": MODEL_ID, "xl_offset_A": 1.1, "jwalk_max_dist_A": 50.0,
                  "voxel_A": 1, "ncpus": args.ncpus, "n_pairs_requested": len(pairs),
                  "pair_mode": "selected" if args.pairs else "all_KSTYM", "versions": versions,
                  "pairs_sha256": sha256(pairs_file), "input_pairs_csv_sha256": sha256(args.pairs) if args.pairs else None,
                  "note": "XP is a pair-level density score, not experimental probability or a single protein score. Missing SASD is blank, not zero."}
        if not args.check_only:
            with (args.outdir / "jwalk.log").open("w") as log:
                with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                    distances, module_hashes = run_jwalk(normalized, pairs_file, args.outdir, args.ncpus)
            report["jwalk_module_sha256"] = module_hashes
            report["status_counts"] = write_results(args.outdir / "xp_pairs.csv", path.stem, pairs, distances)
            report["state"] = "COMPLETED_WITH_UNSCORED_PAIRS" if report["status_counts"].get("NO_SASD_RETURNED") else "COMPLETED"
        (args.outdir / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"{report['state']}: {len(pairs)} requested pairs; output: {args.outdir}")
        return 0
    except Exception as exc:
        if created:
            report.update(state="FAILED", error=f"{type(exc).__name__}: {exc}")
            (args.outdir / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
