#!/usr/bin/env python3
"""Promote completed AlphaFold3 PPI predictions into the result store.

``scripts/build_af3_ppi_jobs.py`` writes AF3 job inputs and Slurm scripts under
``af3_ppi_jobs/<PXD>/<job_name>/`` (see ``af3_ppi_jobs/manifest.tsv``). That tree
also holds large, display-irrelevant intermediates (the ``*_data.json`` /
``*_data.phase1.json`` MSA and template archives, often 60-200+MB, plus 4
alternate-sample subfolders per job).

This script copies only the small, display-ready subset of a *completed* job's
output into the canonical result store, mirroring how ReLink's Nextflow
``work_dir`` is a separate scratch area from the curated results that land
under ``store/<PXD>/relink/``:

    store/<PXD>/af3_predictions/<job_name>/
        pair.json                   # protein_a, protein_b, supporting_crosslinks,
                                     # max_xi_score, ambiguous (from manifest.tsv)
        model.cif                   # best-ranked structure; AF3 embeds per-atom
                                     # pLDDT as the mmCIF B-factor column
        summary_confidences.json
        ranking_scores.csv

A job is only promoted once its ``model.cif`` actually exists on disk -
``manifest.tsv``'s ``status`` column only means "submittable", not "succeeded".

Examples:
    python scripts/promote_af3_predictions.py
    python scripts/promote_af3_predictions.py --pxd PXD031827
    python scripts/promote_af3_predictions.py --dry-run
    python scripts/promote_af3_predictions.py --force
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import shutil
import sys
from pathlib import Path

DEFAULT_MANIFEST = Path("af3_ppi_jobs/manifest.tsv")
DEFAULT_AF3_JOBS_DIR = Path("af3_ppi_jobs")
DEFAULT_DATA_DIR = Path("store")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Manifest TSV written by build_af3_ppi_jobs.py")
    parser.add_argument("--af3-jobs-dir", type=Path, default=DEFAULT_AF3_JOBS_DIR, help="Root directory containing <PXD>/<job_name>/ AF3 job outputs")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Result store root to promote predictions into")
    parser.add_argument("--pxd", nargs="+", metavar="PXD_OR_MASK", help="Restrict to matching PXD accessions or shell-style masks")
    parser.add_argument("--force", action="store_true", help="Re-copy even if the destination already exists")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be promoted without copying files")
    return parser.parse_args()


def matches_any(accession: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(accession.upper(), pattern.upper()) for pattern in patterns)


def sanitized(job_name: str) -> str:
    return job_name.lower()


def find_model_cif(af3_jobs_dir: Path, pxd: str, job_name: str) -> Path | None:
    sanitized_name = sanitized(job_name)
    candidate = af3_jobs_dir / pxd / job_name / sanitized_name / f"{sanitized_name}_model.cif"
    return candidate if candidate.is_file() else None


def load_manifest_rows(manifest: Path, pxd_filter: list[str] | None) -> list[dict[str, str]]:
    with manifest.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    rows = [row for row in rows if row.get("job_name")]
    if pxd_filter:
        rows = [row for row in rows if matches_any(row["pxd"], pxd_filter)]
    return rows


def promote_one(row: dict[str, str], af3_jobs_dir: Path, data_dir: Path, force: bool, dry_run: bool) -> str:
    pxd, job_name = row["pxd"], row["job_name"]
    model_cif = find_model_cif(af3_jobs_dir, pxd, job_name)
    if model_cif is None:
        return "not_completed"

    sanitized_name = sanitized(job_name)
    source_dir = model_cif.parent
    dest_dir = data_dir / pxd / "af3_predictions" / job_name

    if dest_dir.exists() and not force:
        return "already_promoted"
    if dry_run:
        return "would_promote"

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model_cif, dest_dir / "model.cif")
    shutil.copy2(source_dir / f"{sanitized_name}_summary_confidences.json", dest_dir / "summary_confidences.json")
    shutil.copy2(source_dir / f"{sanitized_name}_ranking_scores.csv", dest_dir / "ranking_scores.csv")

    pair = {
        "job_name": job_name,
        "protein_a": row["protein_a"],
        "protein_b": row["protein_b"],
        "supporting_crosslinks": int(row["supporting_crosslinks"]) if row.get("supporting_crosslinks") else None,
        "max_xi_score": float(row["max_xi_score"]) if row.get("max_xi_score") else None,
        "ambiguous": str(row.get("ambiguous", "")).strip().lower() == "true",
    }
    (dest_dir / "pair.json").write_text(json.dumps(pair, indent=2) + "\n")
    return "promoted"


def main() -> int:
    args = parse_args()
    rows = load_manifest_rows(args.manifest, args.pxd)
    if not rows:
        print("No manifest rows with a job_name matched the given filters.")
        return 0

    counts: dict[str, int] = {}
    for row in rows:
        result = promote_one(row, args.af3_jobs_dir, args.data_dir, args.force, args.dry_run)
        counts[result] = counts.get(result, 0) + 1
        label = {
            "not_completed": "not completed yet (no model.cif found), skipping",
            "already_promoted": "already promoted, skipping (use --force to re-copy)",
            "would_promote": "would promote",
            "promoted": "promoted",
        }[result]
        print(f"{row['pxd']}/{row['job_name']}: {label}")

    summary = ", ".join(f"{count} {key}" for key, count in sorted(counts.items()))
    print(f"Done: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
