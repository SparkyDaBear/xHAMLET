#!/usr/bin/env python3
"""One command from finished ReLink runs to an AF3 command list (nothing is submitted).

For PXDs you know are complete in the store, this:
  1. checks each has ReLink results (relink/**/results.mzid),
  2. syncs just those PXDs into the result catalog (scripts/sync_result_database.py),
  3. builds the AF3 jobs (scripts/build_af3_ppi_jobs.py) with the cohort defaults:
     each UniProt pair predicted once across all PXDs, combined residues < 1200,
     ambiguous pairs expanded,
  4. writes <out-dir>/commands.txt (one sbatch per line) and <out-dir>/matches.tsv.

Any option not listed here (e.g. --account, --mem, --time, --min-supporting) is forwarded
to build_af3_ppi_jobs.py.

Examples:
    python scripts/prepare_af3_ppi_jobs.py PXD031997 PXD041519
    python scripts/prepare_af3_ppi_jobs.py --pxd-file done_pxds.txt --tag batch2
    python scripts/prepare_af3_ppi_jobs.py --pxd-file done_pxds.txt --dry-run
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

from sync_result_database import read_pxds

REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pxds", nargs="*", metavar="PXD", help="Completed PXD accessions")
    parser.add_argument("--pxd-file", type=Path, help="Text/CSV file of PXDs (any whitespace/comma separated; # comments)")
    parser.add_argument("--data-dir", type=Path, default=Path("store"), help="Result store root (default: store)")
    parser.add_argument("--config", type=Path, default=Path("configs/config.yaml"), help="xHAMLET config for the sync step")
    parser.add_argument("--database-path", type=Path, default=Path("xhamlet-results.sqlite3"), help="SQLite result catalog to sync into")
    parser.add_argument("--out-dir", type=Path, default=Path("af3_ppi_jobs/shared"), help="Shared AF3 job directory (default: af3_ppi_jobs/shared)")
    parser.add_argument("--total-residues-below", type=int, default=1200, help="Only queue pairs with combined residues below N (default: 1200)")
    parser.add_argument("--tag", help="Suffix for commands/matches file names so batches do not overwrite each other")
    parser.add_argument("--no-expand-ambiguous", action="store_true", help="Skip pairs whose protein assignment is ambiguous")
    parser.add_argument("--force-sync", action="store_true", help="Re-import the PXDs even if the catalog is up to date")
    parser.add_argument("--skip-sync", action="store_true", help="Use the catalog as it is (no sync step)")
    parser.add_argument("--dry-run", action="store_true", help="Validate the PXDs and print the commands without running them")
    return parser.parse_known_args()


def has_relink_results(data_dir: Path, pxd: str) -> bool:
    return next((data_dir / pxd / "relink").rglob("results.mzid"), None) is not None


def run(command: list[str], dry_run: bool) -> None:
    print("+ " + " ".join(command), flush=True)
    if not dry_run:
        subprocess.run(command, check=True)


def main() -> int:
    args, builder_extra = parse_args()
    pxds = read_pxds(args.pxds, args.pxd_file)
    if not pxds:
        raise SystemExit("No PXDs given. Pass accessions or --pxd-file.")

    ready = [pxd for pxd in pxds if has_relink_results(args.data_dir, pxd)]
    missing = [pxd for pxd in pxds if pxd not in ready]
    if missing:
        print(f"Skipping {len(missing)} PXD(s) with no relink/**/results.mzid under {args.data_dir}: {', '.join(missing)}", file=sys.stderr)
    if not ready:
        raise SystemExit("None of the PXDs have ReLink results.")
    print(f"{len(ready)} PXD(s) ready for AF3 pair extraction.")

    python = sys.executable
    if not args.skip_sync:
        sync = [python, str(REPO_ROOT / "scripts" / "sync_result_database.py"), "--config", str(args.config), "--data-dir", str(args.data_dir),
                "--database-path", str(args.database_path), "--pxd", *ready]
        run(sync + (["--force"] if args.force_sync else []), args.dry_run)

    suffix = f"_{args.tag}" if args.tag else ""
    commands_file = args.out_dir / f"commands{suffix}.txt"
    matches_file = args.out_dir / f"matches{suffix}.tsv"
    build = [python, str(REPO_ROOT / "scripts" / "build_af3_ppi_jobs.py"), "--database-path", str(args.database_path), "--data-dir", str(args.data_dir),
             "--out-dir", str(args.out_dir), "--pxd", *ready, "--dedupe-pairs",
             "--total-residues-below", str(args.total_residues_below),
             "--commands-file", str(commands_file), "--matches-file", str(matches_file), *builder_extra]
    if not args.no_expand_ambiguous:
        build.append("--expand-ambiguous")
    run(build, args.dry_run)
    if args.dry_run:
        return 0

    with matches_file.open(newline="", encoding="utf-8") as handle:
        jobs = {(row["job_name"], row["status"]) for row in csv.DictReader(handle, delimiter="\t")}
    status = Counter(state for _, state in jobs)
    print("\nUnique protein pairs by status: " + ", ".join(f"{count} {name}" for name, count in sorted(status.items())))
    print(f"Commands (not submitted): {commands_file}\nCompanion table:         {matches_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
