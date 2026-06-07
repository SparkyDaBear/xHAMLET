"""
Raw file processor for XL-MS datasets.

Handles per-file aria2c download, thermorawfileparser metadata extraction,
optional mzML conversion, and optional file cleanup.

Phase 1 (per file, parallel up to nproc workers):
  1. Download .raw with aria2c (multi-connection for speed)
  2. thermorawfileparser -f 4 (metadata JSON)
  3. [unless --skip-spectral] thermorawfileparser -f 2 (mzML conversion)
  4. [if --clean-raw] delete .raw immediately

Phase 2 (once, after all Phase 1 files):
  5. [unless --skip-spectral] mzML_assessor on all .mzML in work/
  6. [if --clean-mzml] delete all .mzML from work/
"""

import json
import logging
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum consecutive per-file failures before aborting Phase 1
MAX_CONSECUTIVE_FAILURES = 3


class RawFileProcessor:
    """
    Processes raw Thermo instrument files for a single PXD dataset.

    aria2c is used with multiple TCP connections per file (-x / --split) to
    saturate available bandwidth even for a single large file.  The default of
    16 connections is a safe value; raise with --aria2c-connections on a fast
    local network.

    Phase 1 files are processed with up to *nproc* parallel threads.  Each
    thread runs download → thermorawfileparser independently.  Because all
    heavy work is subprocess-bound (not GIL-bound), threads give true
    parallelism here.
    """

    def __init__(
        self,
        pxd: str,
        pxd_dir: Path,
        aria2c_connections: int = 16,
        clean_raw: bool = False,
        clean_mzml: bool = False,
        skip_spectral: bool = False,
        limit: Optional[int] = None,
        nproc: int = 1,
        assessor_script: Optional[Path] = None,
        file_assignments: Optional[Dict[str, Dict[str, str]]] = None,
        assessor_files_per_cluster: int = 1,
    ) -> None:
        self.pxd = pxd
        self.pxd_dir = Path(pxd_dir)
        self.work_dir = self.pxd_dir / "work"
        self.assessment_dir = self.pxd_dir / "assessment"
        self.aria2c_connections = aria2c_connections
        self.clean_raw = clean_raw
        self.clean_mzml = clean_mzml
        self.skip_spectral = skip_spectral
        self.limit = limit
        self.nproc = max(1, nproc)
        self.file_assignments = file_assignments or {}
        self.assessor_files_per_cluster = assessor_files_per_cluster

        # Resolve assessor script path
        if assessor_script is None:
            assessor_script = Path(__file__).parent.parent / "assessor" / "mzML_assessor.py"
        self.assessor_script = Path(assessor_script)

        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.assessment_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_files_for_assessment(self, raw_files: List[Dict[str, Any]]) -> set:
        """
        Select which raw files should be downloaded and assessed.

        If file_assignments is provided, randomly select assessor_files_per_cluster
        files from each cluster. Otherwise, return all filenames.

        Args:
            raw_files: List of raw file dicts with 'fileName' key

        Returns:
            Set of filenames (str) that should be assessed.
        """
        import random

        if not self.file_assignments:
            # No clustering info — assess all files
            return {f.get("fileName", "") for f in raw_files}

        # Group files by cluster
        clusters: Dict[str, List[str]] = {}
        for f in raw_files:
            filename = f.get("fileName", "")
            if filename in self.file_assignments:
                cluster_id = self.file_assignments[filename].get("cluster_id", "unknown")
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(filename)

        # Select assessor_files_per_cluster from each cluster
        to_assess = set()
        for cluster_id, files in clusters.items():
            num_to_select = min(self.assessor_files_per_cluster, len(files))
            selected = random.sample(files, num_to_select)
            to_assess.update(selected)
            logger.info(
                "Cluster %s: selecting %d/%d files for assessment",
                cluster_id, num_to_select, len(files)
            )

        # Also include any files not in clustering (shouldn't happen, but be safe)
        all_filenames = {f.get("fileName", "") for f in raw_files}
        unassigned = all_filenames - set(self.file_assignments.keys())
        to_assess.update(unassigned)

        logger.info(
            "Assessment selection: %d/%d files will be assessed",
            len(to_assess), len(all_filenames)
        )
        return to_assess

    def run(self, file_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run full raw file processing for a list of file dicts.

        Args:
            file_list: List of dicts with 'fileName' and 'ftpUrl' keys,
                       as returned by PrideClient.extract_file_download_links().

        Returns:
            Summary dict with per-file results and overall status.
        """
        raw_files = [
            f for f in file_list
            if f.get("fileName", "").lower().endswith(".raw")
        ]

        if not raw_files:
            logger.warning("No .raw files found in file list for %s", self.pxd)
            return {"status": "no_raw_files", "files_processed": 0, "files_failed": 0}

        if self.limit is not None:
            logger.info("Limiting to %d of %d raw files (--limit)", self.limit, len(raw_files))
            raw_files = raw_files[: self.limit]

        total = len(raw_files)
        total_size_gb = sum(
            f.get("fileSizeBytes", 0) for f in raw_files
        ) / 1024 ** 3

        # Select which files to assess based on clustering
        files_to_assess = self.select_files_for_assessment(raw_files)

        logger.info(
            "Phase 1: %d .raw files to process for %s (~%.1f GB total, %d workers)",
            total, self.pxd, total_size_gb, self.nproc,
        )

        per_file_results: List[Dict[str, Any]] = [None] * total  # type: ignore[list-item]
        failed_count = 0
        # Thread-safe failure tracking (consecutive abort only used in serial mode)
        _lock = threading.Lock()
        _consec = [0]  # mutable container for thread-safe increment
        _abort = [False]

        def _process(args_tuple):
            idx, file_info = args_tuple
            filename = file_info.get("fileName", "")
            ftp_url = file_info.get("ftpUrl", "")

            # Only check abort flag in serial mode (nproc==1)
            if self.nproc == 1:
                with _lock:
                    if _abort[0]:
                        return idx, {"filename": filename, "status": "aborted"}

            if not ftp_url:
                logger.warning("[%d/%d] No FTP URL for %s — skipping", idx, total, filename)
                return idx, {"filename": filename, "status": "skipped_no_url"}

            result = self._process_single_file(filename, ftp_url, idx, total, files_to_assess)

            # Serial mode only: track consecutive failures and abort early
            if self.nproc == 1:
                with _lock:
                    if result["status"] == "failed":
                        _consec[0] += 1
                        if _consec[0] >= MAX_CONSECUTIVE_FAILURES:
                            logger.error(
                                "%d consecutive failures — aborting Phase 1 early",
                                MAX_CONSECUTIVE_FAILURES,
                            )
                            _abort[0] = True
                    else:
                        _consec[0] = 0

            return idx, result

        indexed_files = list(enumerate(raw_files, 1))

        if self.nproc == 1:
            # Serial path — keeps log output ordered
            for idx, file_info in indexed_files:
                if _abort[0]:
                    break
                _, result = _process((idx, file_info))
                per_file_results[idx - 1] = result
                if result["status"] == "failed":
                    failed_count += 1
        else:
            with ThreadPoolExecutor(max_workers=self.nproc) as executor:
                futures = {executor.submit(_process, item): item for item in indexed_files}
                for future in as_completed(futures):
                    try:
                        idx, result = future.result()
                        per_file_results[idx - 1] = result
                        if result["status"] == "failed":
                            with _lock:
                                failed_count += 1
                    except Exception as exc:
                        logger.error("Unexpected error in Phase 1 worker: %s", exc)

        # Filter out any None slots (aborted entries)
        per_file_results = [r for r in per_file_results if r is not None]

        processed = sum(1 for r in per_file_results if r["status"] in ("success", "skipped_existing"))
        logger.info(
            "Phase 1 complete: %d/%d files processed, %d failed",
            processed, total, failed_count,
        )

        # Phase 2: mzML assessor
        assessor_result = None
        if not self.skip_spectral:
            mzml_files = list(self.work_dir.glob("*.mzML"))
            if mzml_files:
                logger.info("Phase 2: mzML_assessor on %d file(s)", len(mzml_files))
                assessor_result = self._run_assessor()
                if self.clean_mzml:
                    logger.info("Removing .mzML files from work/ (--clean-mzml)")
                    for f in mzml_files:
                        self._safe_delete(f)
            else:
                logger.warning("Phase 2: no .mzML files in work/ — skipping assessor")
        else:
            logger.info("Phase 2: skipped (--skip-spectral)")

        return {
            "status": "complete",
            "files_total": total,
            "files_processed": processed,
            "files_failed": failed_count,
            "skip_spectral": self.skip_spectral,
            "assessor_ran": assessor_result is not None,
            "per_file": per_file_results,
        }

    # ------------------------------------------------------------------
    # Per-file processing
    # ------------------------------------------------------------------

    def _process_single_file(
        self, filename: str, ftp_url: str, idx: int, total: int, files_to_assess: Optional[set] = None
    ) -> Dict[str, Any]:
        """Download → metadata JSON → optional mzML → optional .raw cleanup."""
        if files_to_assess is None:
            files_to_assess = set()  # If not provided, don't assess any

        raw_path = self.work_dir / filename
        base_name = Path(filename).stem
        metadata_json = self.assessment_dir / f"{base_name}-metadata.json"

        result: Dict[str, Any] = {"filename": filename, "status": "failed"}

        # Resume support: skip if metadata already produced
        if metadata_json.exists():
            logger.info("[%d/%d] %s: metadata already exists — skipping", idx, total, filename)
            result["status"] = "skipped_existing"
            result["metadata_json"] = str(metadata_json)
            return result

        # ① Download with aria2c
        logger.info("[%d/%d] Downloading %s ...", idx, total, filename)
        if not self._download_file(ftp_url, filename):
            logger.error("[%d/%d] Download failed for %s", idx, total, filename)
            return result

        # ② thermorawfileparser: metadata JSON only (-f 4)
        logger.info("[%d/%d] Extracting instrument metadata from %s ...", idx, total, filename)
        if not self._run_thermorawfileparser_metadata(raw_path):
            logger.error("[%d/%d] Metadata extraction failed for %s", idx, total, filename)
            self._safe_delete(raw_path)
            return result

        result["status"] = "success"
        result["metadata_json"] = str(metadata_json)

        # ③ thermorawfileparser: mzML conversion (-f 2)
        # Only convert to mzML if this file is selected for assessment
        should_assess = filename in files_to_assess
        if not self.skip_spectral and should_assess:
            logger.info("[%d/%d] Converting %s to mzML (selected for assessment) ...", idx, total, filename)
            mzml_ok = self._run_thermorawfileparser_mzml(raw_path)
            result["mzml_converted"] = mzml_ok
            if not mzml_ok:
                logger.warning(
                    "[%d/%d] mzML conversion failed for %s (metadata JSON still saved)",
                    idx, total, filename,
                )
        elif not self.skip_spectral:
            logger.info("[%d/%d] %s: skipping mzML conversion (not selected for assessment)", idx, total, filename)
            result["mzml_converted"] = False
        else:
            result["mzml_converted"] = False

        # ④ Delete .raw if requested
        if self.clean_raw:
            logger.info("[%d/%d] Deleting %s (--clean-raw)", idx, total, filename)
            self._safe_delete(raw_path)

        return result

    # ------------------------------------------------------------------
    # Tool wrappers
    # ------------------------------------------------------------------

    def _download_file(self, ftp_url: str, filename: str) -> bool:
        """Download a single file using aria2c with multiple TCP connections."""
        n = self.aria2c_connections
        cmd = [
            "aria2c",
            f"--max-connection-per-server={n}",
            f"--split={n}",
            "--min-split-size=1M",
            "--allow-overwrite=true",
            "--auto-file-renaming=false",
            f"--dir={self.work_dir}",
            f"--out={filename}",
            ftp_url,
        ]
        logger.debug("aria2c: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3600,
            )
            if proc.returncode != 0:
                logger.error(
                    "aria2c failed (rc=%d): %s", proc.returncode, proc.stderr[-500:]
                )
                return False
            dest = self.work_dir / filename
            if not dest.exists() or dest.stat().st_size == 0:
                logger.error("Downloaded file missing or empty: %s", dest)
                return False
            logger.info(
                "Downloaded %s (%.1f MB)", filename, dest.stat().st_size / 1024 / 1024
            )
            return True
        except subprocess.TimeoutExpired:
            logger.error("aria2c timed out for %s", filename)
            return False
        except Exception as exc:
            logger.error("aria2c error for %s: %s", filename, exc)
            return False

    def _run_thermorawfileparser_metadata(self, raw_path: Path) -> bool:
        """
        Run thermorawfileparser to produce instrument metadata JSON.

        Flags:
          --format 4  → metadata JSON output
          --metadata 0 → no separate index file
        Output file name is <stem>-metadata.json in assessment_dir.
        """
        out_file = self.assessment_dir / f"{raw_path.stem}-metadata.json"
        cmd = [
            "thermorawfileparser",
            "--input", str(raw_path),
            "--output_directory", str(self.assessment_dir),
            "--format", "4",
            "--metadata", "0",
            "--metadata_output_file", str(out_file),
        ]
        logger.debug("thermorawfileparser metadata: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=600,
            )
            if proc.returncode != 0:
                logger.error(
                    "thermorawfileparser metadata failed (rc=%d): %s",
                    proc.returncode, proc.stderr[-300:],
                )
                return False
            if not out_file.exists():
                logger.error("Metadata JSON not created: %s", out_file)
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("thermorawfileparser timed out for %s", raw_path.name)
            return False
        except Exception as exc:
            logger.error("thermorawfileparser error: %s", exc)
            return False

    def _run_thermorawfileparser_mzml(self, raw_path: Path) -> bool:
        """
        Run thermorawfileparser to convert .raw → .mzML.

        Flags:
          --format 2  → mzML output
          --metadata 0 → no separate index file
        Output is written to work_dir with the same stem.
        """
        cmd = [
            "thermorawfileparser",
            "--input", str(raw_path),
            "--output_directory", str(self.work_dir),
            "--format", "2",
            "--metadata", "2",
        ]
        logger.debug("thermorawfileparser mzML: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3600,
            )
            if proc.returncode != 0:
                logger.error(
                    "thermorawfileparser mzML failed (rc=%d): %s",
                    proc.returncode, proc.stderr[-300:],
                )
                return False
            mzml_path = self.work_dir / f"{raw_path.stem}.mzML"
            if not mzml_path.exists():
                logger.error("mzML file not created: %s", mzml_path)
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("mzML conversion timed out for %s", raw_path.name)
            return False
        except Exception as exc:
            logger.error("mzML conversion error: %s", exc)
            return False

    def _run_assessor(self) -> Optional[Dict[str, Any]]:
        """
        Run mzML_assessor on all .mzML files currently in work_dir.

        The assessor script is run with its own directory as cwd so that its
        relative import of metadata_handler works correctly.

        Returns parsed study_metadata.json content, or None on failure.
        """
        if not self.assessor_script.exists():
            logger.error("mzML_assessor script not found: %s", self.assessor_script)
            return None

        cmd = [
            "python3",
            str(self.assessor_script),
            "--inpath", str(self.work_dir.resolve()),
            "--outpath", str(self.assessment_dir.resolve()),
        ]
        logger.info("Running mzML_assessor: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=7200,
                cwd=str(self.assessor_script.parent),
            )
            if proc.returncode != 0:
                logger.error(
                    "mzML_assessor failed (rc=%d): %s",
                    proc.returncode, proc.stderr[-500:],
                )
                return None
            study_meta_path = self.assessment_dir / "study_metadata.json"
            if not study_meta_path.exists():
                logger.warning("study_metadata.json not produced by mzML_assessor")
                return None
            with open(study_meta_path) as fh:
                return json.load(fh)
        except subprocess.TimeoutExpired:
            logger.error("mzML_assessor timed out")
            return None
        except Exception as exc:
            logger.error("mzML_assessor error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_delete(path: Path) -> None:
        """Delete a file, logging warnings instead of raising."""
        try:
            if path.exists():
                path.unlink()
                logger.debug("Deleted %s", path)
        except Exception as exc:
            logger.warning("Could not delete %s: %s", path, exc)
