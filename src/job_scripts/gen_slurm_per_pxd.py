#!/usr/bin/env python3
"""Select PRIDE datasets and generate/submit one xHAMLET Slurm job per PXD."""

import argparse
import csv
import math
import re
import shlex
import subprocess
import time
from pathlib import Path


PXD_PATTERN = re.compile(r"PXD\d{6}")
REPO_DIR = Path(__file__).resolve().parents[2]


def read_datasets(csv_path):
    """Read an accession/PXDs CSV, or a headerless first-column PXD list."""
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.reader(handle) if row and any(c.strip() for c in row)]
    if not rows:
        raise ValueError("No PXDs found in CSV file")
    if PXD_PATTERN.fullmatch(rows[0][0].strip()):
        header = ["accession"] + [f"column_{i}" for i in range(1, len(rows[0]))]
    else:
        header = [cell.strip() for cell in rows.pop(0)]
    accession_column = next(
        (i for i, name in enumerate(header) if name.lower() in {"accession", "pxds", "pxd"}),
        0,
    )
    datasets = []
    seen = set()
    for row in rows:
        if len(row) != len(header):
            raise ValueError(f"CSV row has {len(row)} columns; expected {len(header)}: {row}")
        pxd = row[accession_column].strip()
        if not PXD_PATTERN.fullmatch(pxd):
            raise ValueError(f"Invalid PXD accession: {pxd!r}")
        if pxd in seen:
            raise ValueError(f"Duplicate PXD accession: {pxd}")
        seen.add(pxd)
        dataset = dict(zip(header, row))
        dataset["accession"] = pxd
        datasets.append(dataset)
    if not datasets:
        raise ValueError("No PXDs found in CSV file")
    return datasets


def select_datasets(datasets, exclude=(), count=None, sort_by_raw_count=False):
    excluded = set(exclude)
    for pxd in excluded:
        if not PXD_PATTERN.fullmatch(pxd):
            raise ValueError(f"Invalid excluded PXD accession: {pxd!r}")
    selected = [row for row in datasets if row["accession"] not in excluded]
    if sort_by_raw_count:
        for row in selected:
            if "raw_file_count" not in row:
                raise ValueError("--sort-by-raw-count requires a raw_file_count column")
            try:
                int(row["raw_file_count"])
            except ValueError as exc:
                raise ValueError(f"Invalid raw_file_count for {row['accession']}") from exc
        selected = [row for row in selected if int(row["raw_file_count"]) > 0]
        selected.sort(key=lambda row: (int(row["raw_file_count"]), row["accession"]))
    if count is not None:
        if count < 1:
            raise ValueError("Dataset count must be >= 1")
        if len(selected) < count:
            raise ValueError(f"Requested {count} PXDs, but only {len(selected)} are eligible")
        selected = selected[:count]
    if not selected:
        raise ValueError("No eligible PXDs remain after filtering")
    return selected


def generate_slurm_files(template_path, pxd_csv_path, output_dir, *,
                         exclude=(), count=None, sort_by_raw_count=False):
    template_content = Path(template_path).read_text()
    if "{{PXD}}" not in template_content:
        raise ValueError("Template must contain the {{PXD}} placeholder")
    datasets = select_datasets(
        read_datasets(pxd_csv_path), exclude, count, sort_by_raw_count
    )
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = []
    rendered = []
    for row in datasets:
        pxd = row["accession"]
        run_dir = output_dir / "runs" / pxd
        replacements = {
            "{{PXD}}": pxd,
            "{{REPO_DIR}}": shlex.quote(str(REPO_DIR)),
            "{{RUN_DIR}}": shlex.quote(str(run_dir)),
            "{{SLURM_LOG}}": shlex.quote(str(run_dir / "slurm_%j.log")),
        }
        content = template_content
        for token, value in replacements.items():
            content = content.replace(token, value)
        if re.search(r"\{\{[^{}]+\}\}", content):
            raise ValueError(f"Unresolved template placeholder for {pxd}")
        output_file = output_dir / f"{pxd}.slurm"
        if output_file.exists() and output_file.read_text() != content:
            raise FileExistsError(f"Refusing to overwrite a different job script: {output_file}")
        rendered.append((output_file, run_dir, content))
    for output_file, run_dir, content in rendered:
        # Slurm opens its log before the script can create directories.
        run_dir.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content)
        output_files.append(output_file)
    with (output_dir / "selected_pxds.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(datasets[0]))
        writer.writeheader()
        writer.writerows(datasets)
    print(f"Generated {len(output_files)} Slurm scripts in {output_dir}")
    return output_files


def submit_slurm_files(slurm_files, batch_size, dwell, max_concurrent=None):
    """Persist each successful job ID immediately; retries skip recorded jobs."""
    if batch_size < 1 or not math.isfinite(dwell) or dwell < 0:
        raise ValueError("batch_size must be >= 1 and dwell must be finite and >= 0")
    if not slurm_files:
        raise ValueError("No Slurm files to submit")
    if max_concurrent is not None and max_concurrent < 1:
        raise ValueError("max_concurrent must be >= 1")
    manifest = Path(slurm_files[0]).parent / "submitted_jobs.csv"
    submitted = {}
    if manifest.exists():
        with manifest.open(newline="") as handle:
            submitted = {row["pxd"]: row["job_id"] for row in csv.DictReader(handle)}
    pending = [Path(path) for path in slurm_files if Path(path).stem not in submitted]
    job_ids = [
        submitted[Path(path).stem] for path in slurm_files if Path(path).stem in submitted
    ]
    with manifest.open("a", newline="", buffering=1) as handle:
        writer = csv.writer(handle)
        if handle.tell() == 0:
            writer.writerow(["pxd", "job_id", "script"])
        for index, slurm_file in enumerate(pending):
            command = ["sbatch", "--parsable"]
            if max_concurrent is not None and len(job_ids) >= max_concurrent:
                command.append(f"--dependency=afterany:{job_ids[-max_concurrent]}")
            command.append(str(slurm_file))
            result = subprocess.run(
                command,
                capture_output=True, text=True, check=True,
            )
            job_id = result.stdout.strip().split(";")[0]
            if not job_id.isdigit():
                raise RuntimeError(f"Unexpected sbatch response for {slurm_file}: {result.stdout!r}")
            writer.writerow([slurm_file.stem, job_id, str(slurm_file)])
            handle.flush()
            job_ids.append(job_id)
            print(f"Submitted {slurm_file.stem}: {job_id}", flush=True)
            if (index + 1) % batch_size == 0 and index + 1 < len(pending) and dwell:
                time.sleep(dwell)
    print(f"Submission records: {manifest} ({len(submitted)} previously recorded jobs skipped)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", help="Slurm template with {{PXD}} placeholders")
    parser.add_argument("pxd_csv", help="Dataset CSV or headerless PXD list")
    parser.add_argument("-o", "--output", required=True, help="Job output directory")
    parser.add_argument("--exclude", nargs="+", default=[], help="PXDs to exclude")
    parser.add_argument("--count", type=int, help="Require exactly this many eligible PXDs")
    parser.add_argument(
        "--sort-by-raw-count", action="store_true",
        help="Keep positive RAW counts, sorted by count then accession",
    )
    parser.add_argument("--submit", action="store_true", help="Submit jobs using sbatch")
    parser.add_argument(
        "--max-concurrent", type=int,
        help="Limit active PXD jobs using independent afterany dependency chains",
    )
    parser.add_argument("--batch", type=int, default=1, help="Submissions per batch (default: 1)")
    parser.add_argument("--dwell", type=float, default=0, help="Seconds between batches")
    args = parser.parse_args()
    if args.batch < 1 or not math.isfinite(args.dwell) or args.dwell < 0:
        parser.error("--batch must be >= 1; --dwell must be finite and >= 0")
    if args.max_concurrent is not None and args.max_concurrent < 1:
        parser.error("--max-concurrent must be >= 1")
    try:
        paths = generate_slurm_files(
            args.template, args.pxd_csv, args.output, exclude=args.exclude,
            count=args.count, sort_by_raw_count=args.sort_by_raw_count,
        )
        if args.submit:
            submit_slurm_files(paths, args.batch, args.dwell, args.max_concurrent)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Error: {exc}\n{getattr(exc, 'stderr', '') or ''}")


if __name__ == "__main__":
    main()
