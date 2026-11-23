#!/usr/bin/env python3
"""Build the ReLink retry-array manifest for a prepared Slurm batch.

A PXD is retried when it was submitted or cancelled in the batch, is not
complete, is not queued/running under Slurm, and is not excluded.
Failures whose newest log shows a xiSEARCH divide-by-zero are also skipped,
since retrying cannot fix them.
"""

from __future__ import annotations

import argparse
import csv
import getpass
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_BATCH = REPO / "assets" / "slurm" / "remaining394"
SUCCESS_LINE = re.compile(r"Processing complete: [1-9]\d* succeeded, 0 failed")
GROUP_LINE = re.compile(r"Running ReLink for taxid (\d+)(?: \((.+)\))?\s*$", re.MULTILINE)
NON_RETRYABLE_LOG_PATTERNS = {"ArithmeticException: / by zero": "xiSEARCH divide-by-zero"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def newest_log(run_dir: Path) -> Path | None:
    logs = sorted(run_dir.glob("slurm_*.log"), key=lambda p: p.stat().st_mtime)
    return logs[-1] if logs else None


def group_mzid(store: Path, pxd: str, taxid: str, crosslinker: str | None) -> Path:
    group_dir = store / pxd / "relink" / f"taxid_{taxid}"
    if crosslinker:
        group_dir /= re.sub(r"[^a-z0-9]+", "_", crosslinker.lower()).strip("_")
    return group_dir / "results" / "fdr" / "results.mzid"


def completed_run(store: Path, pxd: str, run_dir: Path) -> bool:
    """True only if the newest log reports success and every group it ran left an mzid.

    Any single results.mzid is not enough: a PXD writes one per taxid/crosslinker
    group as it goes, and files from earlier or partial runs are never removed.
    """
    log = newest_log(run_dir)
    if log is None:
        return False
    text = log.read_text(errors="replace")
    if not SUCCESS_LINE.search(text):
        return False
    groups = set(GROUP_LINE.findall(text))
    return all(
        (mzid := group_mzid(store, pxd, taxid, crosslinker or None)).is_file() and mzid.stat().st_size > 0
        for taxid, crosslinker in groups
    )


def active_job_names() -> set[str]:
    result = subprocess.run(
        ["squeue", "-h", "-u", getpass.getuser(), "-o", "%j"],
        capture_output=True, text=True, check=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def non_retryable_reason(run_dir: Path) -> str | None:
    for path in (newest_log(run_dir), run_dir / "pipeline.log"):
        if path is None or not path.exists():
            continue
        text = path.read_text(errors="replace")
        for pattern, reason in NON_RETRYABLE_LOG_PATTERNS.items():
            if pattern in text:
                return reason
    return None


def build(batch: Path, store: Path, active: set[str]) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    scripts: dict[str, str] = {}
    for submitted in sorted(batch.glob("*/submitted_jobs.csv")):
        for row in read_csv(submitted):
            scripts.setdefault(row["pxd"], row["script"])
    for row in read_csv(batch / "cancelled_pending_20261118.csv"):
        scripts.setdefault(row["pxd"], row["script"])
    excluded = {row["pxd"]: row["reason"] for row in read_csv(batch / "retry_exclusions.csv")}

    include: list[tuple[str, str]] = []
    skipped: list[tuple[str, str]] = []
    for pxd, script in sorted(scripts.items()):
        script_path = Path(script)
        if not script_path.is_absolute():
            script_path = (batch / script_path) if (batch / script_path).exists() else REPO / script_path
        run_dir = script_path.parent / "runs" / pxd
        if completed_run(store, pxd, run_dir):
            skipped.append((pxd, "completed"))
        elif f"xHAMLET_{pxd}" in active:
            skipped.append((pxd, "queued or running"))
        elif pxd in excluded:
            skipped.append((pxd, excluded[pxd]))
        elif reason := non_retryable_reason(run_dir):
            skipped.append((pxd, reason))
        elif not script_path.exists():
            skipped.append((pxd, f"missing script {script_path}"))
        else:
            include.append((pxd, str(script_path.resolve())))
    return include, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-dir", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--store", type=Path, default=REPO / "store")
    parser.add_argument("--output", type=Path, help="Manifest TSV (default: <batch>/retry_array_manifest.tsv)")
    args = parser.parse_args()

    output = args.output or args.batch_dir / "retry_array_manifest.tsv"
    include, skipped = build(args.batch_dir, args.store, active_job_names())
    with output.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["pxd", "script"])
        writer.writerows(include)
    with output.with_name(output.stem + "_skipped.tsv").open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["pxd", "reason"])
        writer.writerows(skipped)

    reasons: dict[str, int] = {}
    for _, reason in skipped:
        reasons[reason] = reasons.get(reason, 0) + 1
    print(f"Retry tasks: {len(include)} -> {output}")
    for reason, count in sorted(reasons.items(), key=lambda item: -item[1]):
        print(f"  skipped {count:4d}  {reason}")
    if include:
        print(f"Submit: sbatch --array=1-{len(include)}%10 {args.batch_dir / 'retry_array.slurm'} {output}")


if __name__ == "__main__":
    main()
