#!/usr/bin/env python3
"""
Full pipeline test for xHAMLET including ReLink integration (Stage 9).

Runs the complete pipeline from Stage 1 (PRIDE metadata fetch) through
Stage 9 (ReLink quantification) for a single PXD accession.

Usage:
    python3 test_full_pipeline.py [--pxd PXD042173] [--profile singularity|docker]
                                  [--work-dir /mnt/storage_1/xhamlet_relink_work]
                                  [--queue-size 4] [--limit N] [--resume]
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_PXD = "PXD042173"
DEFAULT_PROFILE = "singularity"
DEFAULT_WORK_DIR = "/mnt/storage_1/xhamlet_relink_work"
DEFAULT_QUEUE_SIZE = 4

REPO_ROOT = Path(__file__).parent.resolve()
MAIN_PY = REPO_ROOT / "src" / "main.py"
LOGS_DIR = REPO_ROOT / "logs"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Full xHAMLET pipeline test with ReLink")
    p.add_argument("--pxd", default=DEFAULT_PXD, help=f"PXD accession (default: {DEFAULT_PXD})")
    p.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        choices=["singularity", "docker", "conda"],
        help=f"Nextflow profile for ReLink (default: {DEFAULT_PROFILE})",
    )
    p.add_argument(
        "--work-dir",
        default=DEFAULT_WORK_DIR,
        help=f"Nextflow work directory (NXF_WORK, default: {DEFAULT_WORK_DIR})",
    )
    p.add_argument(
        "--singularity-cachedir",
        default=None,
        help="Singularity image cache dir (NXF_SINGULARITY_CACHEDIR). "
             "Defaults to <work-dir>/singularity",
    )
    p.add_argument(
        "--queue-size",
        type=int,
        default=DEFAULT_QUEUE_SIZE,
        help=f"Nextflow -qs (max concurrent tasks, default: {DEFAULT_QUEUE_SIZE})",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process only the first N RAW files (for quick testing)",
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="Pass -resume to Nextflow in the ReLink stage",
    )
    p.add_argument(
        "--no-download",
        action="store_true",
        help="Skip raw file download (stages 3-4); use pre-downloaded files",
    )
    p.add_argument(
        "--skip-spectral",
        action="store_true",
        help="Skip mzML conversion and spectral assessment",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging",
    )
    return p.parse_args()


def setup_tee_logging(log_path: Path, verbose: bool) -> logging.Logger:
    """Write INFO+ to console and DEBUG+ to the log file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter(fmt))
    root.addHandler(ch)

    # File handler — always DEBUG
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt))
    root.addHandler(fh)

    return logging.getLogger("test_full_pipeline")


def build_command(args: argparse.Namespace, log_file: Path) -> list[str]:
    """Build the src/main.py command list."""
    cmd = [
        sys.executable,
        str(MAIN_PY),
        "--pxd", args.pxd,
        "--data-dir", str(REPO_ROOT / "pxd_data"),
        "--prompts-dir", str(REPO_ROOT / "prompts"),
        "--relink",
        "--relink-profile", args.profile,
        "--relink-work-dir", args.work_dir,
        "--relink-queue-size", str(args.queue_size),
        "--log-file", str(log_file),
    ]
    if args.resume:
        cmd.append("--relink-resume")
    if args.no_download:
        cmd.append("--no-download")
    if args.skip_spectral:
        cmd.append("--skip-spectral")
    if args.limit:
        cmd += ["--limit", str(args.limit)]
    if args.verbose:
        cmd.append("--verbose")
    return cmd


def build_env(args: argparse.Namespace) -> dict:
    """Build subprocess environment with Nextflow settings."""
    env = os.environ.copy()

    # Singularity image cache (avoids re-pulling containers on every run)
    singularity_cache = args.singularity_cachedir or str(
        Path(args.work_dir) / "singularity"
    )
    env["NXF_SINGULARITY_CACHEDIR"] = singularity_cache
    Path(singularity_cache).mkdir(parents=True, exist_ok=True)

    return env



def main() -> int:
    args = parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"full_pipeline_{args.pxd}_{timestamp}.log"
    logger = setup_tee_logging(log_file, args.verbose)

    logger.info("=" * 80)
    logger.info("xHAMLET Full Pipeline Test")
    logger.info("=" * 80)
    logger.info("PXD             : %s", args.pxd)
    logger.info("ReLink profile  : %s", args.profile)
    logger.info("NXF work dir    : %s", args.work_dir)
    logger.info("NXF singularity : %s",
                args.singularity_cachedir or str(Path(args.work_dir) / "singularity"))
    logger.info("Queue size      : %d", args.queue_size)
    logger.info("File limit      : %s", args.limit or "unlimited")
    logger.info("Resume ReLink   : %s", args.resume)
    logger.info("No download     : %s", args.no_download)
    logger.info("Skip spectral   : %s", args.skip_spectral)
    logger.info("Log file        : %s", log_file)
    logger.info("=" * 80)

    cmd = build_command(args, log_file)
    env = build_env(args)

    t0 = time.monotonic()
    relink_failed = False
    pipeline_output_lines: list[str] = []

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        cwd=str(REPO_ROOT),
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip()
        if not line:
            continue
        pipeline_output_lines.append(line)
        lower = line.lower()
        if " - error - " in lower or "error ~" in lower or "fatal" in lower:
            logger.error("[pipeline] %s", line)
        elif " - warning - " in lower or "warn:" in lower:
            logger.warning("[pipeline] %s", line)
        elif " - debug - " in lower:
            logger.debug("[pipeline] %s", line)
        else:
            logger.info("[pipeline] %s", line)
    proc.wait()
    returncode = proc.returncode

    # Detect ReLink stage failure from pipeline output even when main.py exits 0
    for line in pipeline_output_lines:
        if "'relink': 'failed'" in line or "relink stage failed" in line.lower():
            relink_failed = True
            break
    elapsed = time.monotonic() - t0

    logger.info("=" * 80)
    elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
    if returncode == 0 and not relink_failed:
        logger.info("✅  Pipeline PASSED  (elapsed: %s)", elapsed_str)
    else:
        if relink_failed:
            logger.error("❌  Pipeline FAILED  — ReLink stage failed (elapsed: %s)", elapsed_str)
        else:
            logger.error("❌  Pipeline FAILED  (rc=%d, elapsed: %s)", returncode, elapsed_str)
        returncode = max(returncode, 1)

    # Check output directories and report what was produced
    relink_dir = REPO_ROOT / "pxd_data" / args.pxd / "relink"
    if relink_dir.exists():
        logger.info("-" * 80)
        logger.info("ReLink output summary:")
        for taxid_dir in sorted(relink_dir.iterdir()):
            if not taxid_dir.is_dir() or not taxid_dir.name.startswith("taxid_"):
                continue
            results_dir = taxid_dir / "results"
            linear_dir = results_dir / "linear_search"
            xl_dir = results_dir / "xl_search"
            linear_count = len(list(linear_dir.glob("*.csv"))) if linear_dir.exists() else 0
            xl_count = len(list(xl_dir.glob("*.csv"))) if xl_dir.exists() else 0
            recal_count = len(list((results_dir / "recalibrated").glob("*.mzML"))) \
                if (results_dir / "recalibrated").exists() else 0
            logger.info(
                "  %-20s  linear CSVs: %2d  xl CSVs: %2d  recal mzMLs: %2d",
                taxid_dir.name, linear_count, xl_count, recal_count,
            )
    else:
        logger.info("ReLink output directory not found: %s", relink_dir)

    logger.info("=" * 80)
    logger.info("Full log: %s", log_file)
    logger.info("=" * 80)

    return returncode


if __name__ == "__main__":
    sys.exit(main())
