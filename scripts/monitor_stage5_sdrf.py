#!/usr/bin/env python3
"""Monitor Stage 5+SDRF batch jobs and report SDRF validity."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Tuple


def _repo_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor Stage5+SDRF jobs and validate generated SDRFs."
    )
    parser.add_argument(
        "jobs_file",
        nargs="?",
        default=str(_repo_dir() / "logs" / "stage5_sdrf" / "jobs.tsv"),
        help="TSV manifest produced by the batch launcher.",
    )
    return parser.parse_args()


def _sdrf_status(sdrf_file: Path) -> str:
    if not sdrf_file.exists() or not sdrf_file.is_file():
        return "MISSING"

    try:
        with sdrf_file.open() as handle:
            line_count = sum(1 for _ in handle)
    except OSError:
        return "MISSING"

    return "VALID" if line_count > 1 else "INVALID"


def _pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _count_config_features(config_file: Path) -> Tuple[bool, int, int]:
    """Return (has_crosslinker, fixed_count, variable_count) for one xi config file."""
    has_crosslinker = False
    fixed_count = 0
    variable_count = 0

    with config_file.open() as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("crosslinker:"):
                has_crosslinker = True
            if line.startswith("modification:fixed"):
                fixed_count += 1
            if line.startswith("modification:variable"):
                variable_count += 1

    return has_crosslinker, fixed_count, variable_count


def _xi_config_checks(pxd_dir: Path) -> Dict[str, str]:
    """Return structured Xi config checks for table-style reporting."""
    configs_dir = pxd_dir / "configs"
    files: Dict[str, Path] = {
        "linear": configs_dir / "xi_linear.conf",
        "crosslink": configs_dir / "xi_crosslinking.conf",
    }

    result: Dict[str, str] = {
        "files_status": "FAIL",
        "crosslinker_status": "NA",
        "linear_fixed": "NA",
        "linear_variable": "NA",
        "crosslink_fixed": "NA",
        "crosslink_variable": "NA",
        "linear_present": "NO",
        "crosslink_present": "NO",
    }

    if files["linear"].exists() and files["linear"].stat().st_size > 0:
        result["linear_present"] = "YES"
    if files["crosslink"].exists() and files["crosslink"].stat().st_size > 0:
        result["crosslink_present"] = "YES"

    missing_or_empty = [
        name for name, path in files.items() if (not path.exists()) or path.stat().st_size == 0
    ]
    if missing_or_empty:
        missing_text = ",".join(missing_or_empty)
        result["files_status"] = f"FAIL({missing_text})"
        return result

    per_file = {}
    for name, path in files.items():
        try:
            has_crosslinker, fixed_count, variable_count = _count_config_features(path)
        except OSError:
            result["files_status"] = f"FAIL(read_error:{name})"
            return result
        per_file[name] = {
            "has_crosslinker": has_crosslinker,
            "fixed": fixed_count,
            "variable": variable_count,
        }

    result["files_status"] = "OK"

    crosslinker_ok = all(v["has_crosslinker"] for v in per_file.values())
    result["crosslinker_status"] = (
        "OK"
        if crosslinker_ok
        else "FAIL("
        + ",".join(name for name, vals in per_file.items() if not vals["has_crosslinker"])
        + ")"
    )

    result["linear_fixed"] = str(per_file["linear"]["fixed"])
    result["linear_variable"] = str(per_file["linear"]["variable"])
    result["crosslink_fixed"] = str(per_file["crosslink"]["fixed"])
    result["crosslink_variable"] = str(per_file["crosslink"]["variable"])

    return result


def main() -> int:
    args = _parse_args()
    jobs_file = Path(args.jobs_file)
    repo_dir = _repo_dir()

    if not jobs_file.exists():
        print(f"Jobs manifest not found: {jobs_file}", file=sys.stderr)
        return 1

    running = completed_ok = failed = 0
    valid_sdrf = invalid_sdrf = missing_sdrf = 0
    linear_config_present = 0
    crosslink_config_present = 0
    valid_crosslinker_lines_pxds = 0
    variable_mod_gt1_pxds = 0

    print(
        "PXD | JOB_STATUS | EXIT | SDRF_STATUS | XI_FILES_STATUS | XI_CROSSLINKER_STATUS | "
        "XI_LINEAR_FIXED | XI_LINEAR_VARIABLE | XI_CROSSLINK_FIXED | XI_CROSSLINK_VARIABLE"
    )
    print(
        "----|-----------|------|------------|-----------------|-----------------------|"
        "-----------------|--------------------|-------------------|----------------------"
    )

    with jobs_file.open() as handle:
        next(handle, None)
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 5:
                continue

            pxd, pid_text, log_file, status_file, command = parts[:5]

            job_status = "UNKNOWN"
            exit_code = "-"

            try:
                pid = int(pid_text)
            except ValueError:
                pid = -1

            if pid > 0 and _pid_running(pid):
                job_status = "RUNNING"
                running += 1
            elif Path(status_file).exists():
                exit_code = Path(status_file).read_text().strip() or "-"
                if exit_code == "0":
                    job_status = "DONE"
                    completed_ok += 1
                else:
                    job_status = "FAILED"
                    failed += 1
            else:
                job_status = "NO_STATUS"
                failed += 1

            sdrf_path = repo_dir / "pxd_data" / pxd / "sdrf" / f"{pxd}.sdrf.tsv"
            sdrf_status = _sdrf_status(sdrf_path)
            xi_checks = _xi_config_checks(repo_dir / "pxd_data" / pxd)
            if sdrf_status == "VALID":
                valid_sdrf += 1
            elif sdrf_status == "INVALID":
                invalid_sdrf += 1
            else:
                missing_sdrf += 1

            if xi_checks["linear_present"] == "YES":
                linear_config_present += 1
            if xi_checks["crosslink_present"] == "YES":
                crosslink_config_present += 1
            if xi_checks["crosslinker_status"] == "OK":
                valid_crosslinker_lines_pxds += 1

            linear_var = int(xi_checks["linear_variable"]) if xi_checks["linear_variable"].isdigit() else 0
            crosslink_var = int(xi_checks["crosslink_variable"]) if xi_checks["crosslink_variable"].isdigit() else 0
            if linear_var > 1 or crosslink_var > 1:
                variable_mod_gt1_pxds += 1

            print(
                f"{pxd} | {job_status} | {exit_code} | {sdrf_status} | "
                f"{xi_checks['files_status']} | {xi_checks['crosslinker_status']} | "
                f"{xi_checks['linear_fixed']} | {xi_checks['linear_variable']} | "
                f"{xi_checks['crosslink_fixed']} | {xi_checks['crosslink_variable']}"
            )

    print()
    print("Summary")
    print(f"Total jobs:            {running + completed_ok + failed}")
    print(f"Running:               {running}")
    print(f"Completed (exit 0):    {completed_ok}")
    print(f"Failed/No status:      {failed}")
    print(f"SDRF valid:            {valid_sdrf}")
    print(f"SDRF invalid:          {invalid_sdrf}")
    print(f"SDRF missing:          {missing_sdrf}")
    print(f"PXDs with xi_linear.conf present:        {linear_config_present}")
    print(f"PXDs with xi_crosslinking.conf present:  {crosslink_config_present}")
    print(f"PXDs with valid has_crosslinker lines:   {valid_crosslinker_lines_pxds}")
    print(f"PXDs with variable modifications > 1:    {variable_mod_gt1_pxds}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())