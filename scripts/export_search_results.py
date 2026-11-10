#!/usr/bin/env python3
"""Export compact rank-1 search CSVs, each strictly below 50 MB.

Run after ReLink, or backfill with --all. Missing/incomplete PXD results are
reported as errors; successful PXDs are listed by --completed-pxd-file.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from sync_result_database import parse_mzid, read_pxds

LIMIT = 50_000_000
LINEAR_COLUMNS = [
    "scan_id", "charge", "peptide", "modified_peptide", "protein_accessions",
    "peptide_starts", "xi_score",
]
CROSS_COLUMNS = [
    "scan_id", "charge", "alpha_peptide", "alpha_modifications", "alpha_positions",
    "alpha_link_sites", "beta_peptide", "beta_modifications", "beta_positions",
    "beta_link_sites", "xi_score",
]
MAP_COLUMNS = ["scan_id", "search_group", "search_stage", "run", "scan", "scan_title"]
REQUIRED_LINEAR = {
    "Run", "Scan", "ScanTitle", "PrecoursorCharge", "BasePeptide1", "Peptide1",
    "Protein1", "Start1", "MatchRank", "match score", "decoy",
}


def export_pxd(pxd_dir: Path, limit: int = LIMIT, result_dirs: list[Path] | None = None) -> dict[str, int]:
    groups = sorted(result_dirs if result_dirs is not None
                    else (pxd_dir / "relink").glob("taxid_*/**/results"))
    if not groups:
        raise ValueError(f"{pxd_dir.name}: no ReLink result groups")
    destination = pxd_dir / "search_results"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".search-export-", dir=pxd_dir) as temp:
        staging = Path(temp)
        paths = {name: staging / f"{name}.csv" for name in ("linear", "crosslinks", "scan_map")}
        counts = dict.fromkeys(paths, 0)
        with paths["linear"].open("w", newline="", encoding="utf-8") as linear_handle, \
                paths["crosslinks"].open("w", newline="", encoding="utf-8") as cross_handle, \
                paths["scan_map"].open("w", newline="", encoding="utf-8") as map_handle:
            linear_writer, cross_writer, map_writer = [
                csv.writer(handle, lineterminator="\n")
                for handle in (linear_handle, cross_handle, map_handle)
            ]
            for writer, columns in (
                (linear_writer, LINEAR_COLUMNS), (cross_writer, CROSS_COLUMNS), (map_writer, MAP_COLUMNS)
            ):
                writer.writerow(columns)
            ids: dict[tuple[str, ...], int] = {}

            def scan_id(group: str, stage: str, run: str, scan: str, title: str) -> int:
                key = (group, stage, run, scan, title)
                if key not in ids:
                    ids[key] = len(ids) + 1
                    map_writer.writerow([ids[key], *key])
                    counts["scan_map"] += 1
                return ids[key]

            for group_dir in groups:
                group = group_dir.parent.relative_to(pxd_dir / "relink").as_posix()
                linear_files = sorted((group_dir / "linear_search").glob("*_linear.csv"))
                mzid = group_dir / "fdr" / "results.mzid"
                if not linear_files or not mzid.is_file():
                    raise ValueError(f"{pxd_dir.name}/{group}: missing linear CSVs or FDR mzIdentML")
                for source in linear_files:
                    with source.open(newline="", encoding="utf-8-sig") as handle:
                        reader = csv.DictReader(handle)
                        missing = REQUIRED_LINEAR - set(reader.fieldnames or [])
                        if missing:
                            raise ValueError(f"{source}: missing columns {sorted(missing)}")
                        for row in reader:
                            if None in row or any(row[k] is None for k in REQUIRED_LINEAR):
                                raise ValueError(f"{source}:{reader.line_num}: malformed CSV row")
                            if row["MatchRank"] != "1" or row["decoy"] != "0":
                                continue
                            if not row["Protein1"] or not row["BasePeptide1"]:
                                raise ValueError(f"{source}:{reader.line_num}: missing target peptide/protein")
                            identifier = scan_id(group, "linear", row["Run"], row["Scan"], row["ScanTitle"])
                            linear_writer.writerow([
                                identifier, row["PrecoursorCharge"], row["BasePeptide1"],
                                row["Peptide1"], row["Protein1"], row["Start1"], row["match score"],
                            ])
                            counts["linear"] += 1
                parsed = parse_mzid(mzid)
                if not parsed["is_complete"] or parsed["metadata"].get("parse_error"):
                    raise ValueError(f"{mzid}: incomplete or invalid mzIdentML")
                for match in parsed["crosslinks"]:
                    if not match["alpha_proteins"] or not match["beta_proteins"]:
                        raise ValueError(f"{mzid}: missing target protein mapping")
                    identifier = scan_id(
                        group, "crosslink", Path(match["source_spectrum"]).name,
                        str(match["scan_number"]) if match["scan_number"] is not None else "",
                        match["spectrum_native_id"],
                    )
                    values: list[object] = [identifier, match["charge_state"]]
                    for side in ("alpha", "beta"):
                        values.extend([
                            match[f"{side}_sequence"],
                            json.dumps(match[f"{side}_modifications"], separators=(",", ":")),
                            ";".join(match[f"{side}_positions"]),
                            ";".join(match[f"{side}_link_sites"]),
                        ])
                    cross_writer.writerow([*values, match["xi_score"]])
                    counts["crosslinks"] += 1
        for path in paths.values():
            if path.stat().st_size >= limit:
                raise ValueError(f"{pxd_dir.name}: {path.name} is {path.stat().st_size} bytes (limit <{limit})")
        destination.mkdir(exist_ok=True)
        for name, path in paths.items():
            os.replace(path, destination / path.name)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("store"))
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--pxd", nargs="+")
    scope.add_argument("--pxd-file", type=Path)
    scope.add_argument("--all", action="store_true")
    parser.add_argument("--completed-pxd-file", type=Path)
    parser.add_argument("--result-dir", type=Path, action="append",
                        help="Exact current-run result group (repeatable; only with a single --pxd)")
    args = parser.parse_args()
    if args.result_dir and (not args.pxd or len(args.pxd) != 1):
        parser.error("--result-dir requires exactly one --pxd")
    if args.all:
        pxds = sorted(p.name for p in args.data_dir.glob("PXD*")
                      if list((p / "relink").glob("taxid_*/**/results")))
    else:
        pxds = read_pxds(args.pxd or [], args.pxd_file)
    completed = []
    errors = 0
    for index, pxd in enumerate(pxds, 1):
        try:
            counts = export_pxd(args.data_dir / pxd, result_dirs=args.result_dir)
        except (OSError, ValueError, csv.Error) as error:
            print(f"[{index}/{len(pxds)}] ERROR {pxd}: {error}", file=sys.stderr, flush=True)
            errors += 1
        else:
            completed.append(pxd)
            print(f"[{index}/{len(pxds)}] {pxd}: {counts}", flush=True)
    if args.completed_pxd_file:
        args.completed_pxd_file.write_text("".join(p + "\n" for p in completed))
    print(f"Completed: {len(completed)} exported, {errors} errors", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
