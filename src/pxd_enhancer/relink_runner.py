"""
ReLink runner for xHAMLET.

Builds a ReLink samplesheet from xHAMLET outputs, resolves a FASTA from
TaxID terms in the generated SDRF, and executes the local ReLink submodule
via Nextflow.
"""

from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import requests

from .raw_processor import is_complete_raw

logger = logging.getLogger(__name__)


class ReLinkRunner:
    """Run the ReLink Nextflow pipeline for a single PXD."""

    UNIPROT_FASTA_URL = "https://rest.uniprot.org/uniprotkb/stream"
    DEFAULT_UNIPROT_CACHE = Path(__file__).resolve().parents[2] / "reference_data" / "uniprot_fasta"

    @staticmethod
    def _paths_share_device(first: Path, second: Path) -> bool:
        return first.stat().st_dev == second.stat().st_dev

    def __init__(
        self,
        relink_dir: str = "./tools/relink",
        requests_timeout: int = 600,
        uniprot_cache_dir: Optional[str] = None,
    ) -> None:
        self.relink_dir = Path(relink_dir).resolve()
        self.requests_timeout = requests_timeout
        # Shared across all runs; override with XHAMLET_UNIPROT_FASTA_CACHE or the argument.
        self.uniprot_cache_dir = Path(
            uniprot_cache_dir or os.environ.get("XHAMLET_UNIPROT_FASTA_CACHE") or self.DEFAULT_UNIPROT_CACHE
        ).expanduser().resolve()

    def run_for_pxd(
        self,
        pxd: str,
        sdrf_path: Path,
        raw_paths: Sequence[Path],
        xi_linear_config: Path,
        xi_crosslink_config: Path,
        pxd_dir: Path,
        project_files: Optional[Sequence[Dict[str, Any]]] = None,
        xi_config_generator: Optional[Any] = None,
        llm_responses: Optional[Dict[str, Any]] = None,
        profile: str = "docker",
        resume: bool = False,
        extra_args: Optional[Sequence[str]] = None,
        force_taxid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute ReLink for a single PXD.

        ``force_taxid`` replaces every SDRF-derived taxid with a single NCBITaxon ID.
        """
        incomplete = [str(path) for path in raw_paths if not is_complete_raw(path)]
        if not raw_paths or incomplete:
            raise ValueError(
                "ReLink requires complete RAW files (no .aria2 markers): "
                + (", ".join(incomplete) if incomplete else "no RAW files supplied")
            )
        if not self.relink_dir.exists():
            raise FileNotFoundError(
                f"ReLink submodule not found at {self.relink_dir}. "
                "Run: git submodule update --init --recursive"
            )

        if shutil.which("nextflow") is None:
            raise RuntimeError("nextflow is not installed or not on PATH")

        # Extract organisms from SDRF (dataset-level organism/taxid resolution,
        # see SDRFWriter._resolve_organisms_list / _assign_organisms_per_file).
        taxids: Set[str] = set(self.extract_taxids_from_sdrf(sdrf_path))

        if force_taxid is not None:
            force_taxid = str(force_taxid).strip()
            if not force_taxid.isdigit():
                raise ValueError(f"force_taxid must be a numeric NCBITaxon ID: {force_taxid!r}")
            logger.info(
                "%s: Forcing taxid %s (SDRF taxids: %s)",
                pxd,
                force_taxid,
                ", ".join(sorted(taxids)) or "none",
            )
            taxids = {force_taxid}

        if not taxids:
            # Default to human (file clustering, which previously supplied an
            # additional taxid source here, was removed as legacy logic) -
            # unless a FASTA is explicitly supplied by the PRIDE project, in
            # which case fetch_project_fasta() below is used directly
            # regardless of taxid.
            logger.warning(
                "%s: No organisms found in SDRF - defaulting to human (NCBITaxon:9606)",
                pxd,
            )
            taxids = {"9606"}

        if len(taxids) > 1:
            logger.info(
                "%s: Multi-organism dataset detected. Running ReLink for each of %d organisms: %s",
                pxd,
                len(taxids),
                ", ".join(sorted(taxids)),
            )
        else:
            logger.info(
                "%s: Single organism dataset (taxid %s). Running ReLink.",
                pxd,
                list(taxids)[0],
            )

        relink_dir = pxd_dir / "relink"
        relink_dir.mkdir(parents=True, exist_ok=True)
        fasta_dir = relink_dir / "fasta"

        # Identify all crosslinker chemistries present in the dataset. Do NOT
        # attempt to assign individual RAW files to a chemistry - as with
        # multi-organism datasets, run every identified chemistry against the
        # complete RAW-file set.
        crosslinker_names = self._crosslinker_names(llm_responses, xi_config_generator)

        if crosslinker_names:
            supported_crosslinkers: List[str] = []
            unsupported_crosslinkers: List[str] = []
            for crosslinker_name in crosslinker_names:
                if xi_config_generator is not None and xi_config_generator.get_crosslinker(crosslinker_name):
                    supported_crosslinkers.append(crosslinker_name)
                else:
                    unsupported_crosslinkers.append(crosslinker_name)

            if unsupported_crosslinkers:
                logger.warning(
                    "%s: Skipping unsupported crosslinker chemistries: %s",
                    pxd,
                    ", ".join(unsupported_crosslinkers),
                )

            if not supported_crosslinkers:
                raise ValueError(
                    "No supported crosslinkers remain after filtering identified "
                    f"chemistries: {crosslinker_names}"
                )

            logger.info(
                "%s: Running ReLink for supported crosslinker chemistries: %s",
                pxd,
                ", ".join(supported_crosslinkers),
            )
            crosslinker_groups = {
                (taxid, crosslinker_name): list(raw_paths)
                for taxid in sorted(taxids)
                for crosslinker_name in supported_crosslinkers
            }
        else:
            logger.info(
                "%s: No cluster-level or dataset-level crosslinker chemistries found; "
                "using dataset-level Xi configuration",
                pxd,
            )
            crosslinker_groups = {
                (taxid, None): list(raw_paths)
                for taxid in sorted(taxids)
            }

        project_fasta = self.fetch_project_fasta(project_files, fasta_dir)
        all_results = {}
        for (taxid, crosslinker_name), group_raw_paths in sorted(crosslinker_groups.items()):
            run_label = f"taxid {taxid} ({crosslinker_name})" if crosslinker_name else f"taxid {taxid}"
            logger.info("Running ReLink for %s", run_label)
            fasta_path = project_fasta
            if fasta_path is None:
                fasta_path = self.fetch_fasta_for_taxid(taxid, fasta_dir)

            taxid_dir = relink_dir / f"taxid_{taxid}"
            name_suffix = self._safe_run_name(crosslinker_name) if crosslinker_name else None
            run_dir = taxid_dir / name_suffix if name_suffix else taxid_dir
            run_dir.mkdir(parents=True, exist_ok=True)

            group_linear_config = xi_linear_config
            group_crosslink_config = xi_crosslink_config
            if crosslinker_name:
                if xi_config_generator is None or llm_responses is None:
                    raise ValueError(
                        "Cluster-specific ReLink requires Xi config generation inputs"
                    )
                config_xl, config_linear = xi_config_generator.generate_configs(
                    pxd,
                    llm_responses,
                    crosslinker_name=crosslinker_name,
                )
                group_crosslink_config, group_linear_config = xi_config_generator.save_configs(
                    pxd,
                    config_xl,
                    config_linear,
                    str(pxd_dir.parent),
                    name_suffix=name_suffix,
                )

            # ReLink now expects an SDRF input plus a global FASTA argument.
            # Restrict the SDRF to files assigned to this chemistry.
            sdrf_for_taxid = run_dir / f"{pxd}.sdrf.tsv"
            self.write_filtered_sdrf(
                source_sdrf=sdrf_path,
                output_sdrf=sdrf_for_taxid,
                raw_paths=group_raw_paths,
            )

            outdir = run_dir / "results"
            run_identity = f"{pxd}:{taxid}:{crosslinker_name or 'dataset'}"
            run_digest = hashlib.sha256(run_identity.encode()).hexdigest()[:10]
            run_name = f"xhamlet_{pxd.lower()}_{taxid}_{run_digest}_{time.time_ns()}"
            run_result = self.run_nextflow(
                input_sdrf=sdrf_for_taxid,
                fasta_path=fasta_path,
                raw_root_dir=Path(group_raw_paths[0]).resolve().parent,
                xi_linear_config=group_linear_config,
                xi_crosslink_config=group_crosslink_config,
                outdir=outdir,
                profile=profile,
                resume=resume,
                run_name=run_name,
                extra_args=extra_args,
            )

            result_key = f"{taxid}:{crosslinker_name or 'dataset'}"
            if run_result.get("returncode") != 0:
                logger.error(
                    "ReLink run failed for %s %s (rc=%s)",
                    pxd,
                    run_label,
                    run_result.get("returncode"),
                )
                all_results[result_key] = {
                    "status": "failed",
                    "error": run_result,
                }
            else:
                all_results[result_key] = {
                    "status": "success",
                    "crosslinker": crosslinker_name,
                    "fasta_path": str(fasta_path),
                    "sdrf": str(sdrf_for_taxid),
                    "outdir": str(outdir),
                    "nextflow": run_result,
                }

        # Check if all runs succeeded
        failed_taxids = [t for t, r in all_results.items() if r["status"] == "failed"]
        if failed_taxids:
            raise RuntimeError(
                f"ReLink failed for taxid(s): {', '.join(failed_taxids)}"
            )

        export_command = [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "scripts" / "export_search_results.py"),
            "--data-dir", str(pxd_dir.parent), "--pxd", pxd,
        ]
        for result in all_results.values():
            export_command.extend(["--result-dir", str(result["outdir"])])
        subprocess.run(export_command, check=True)

        return {
            "status": "success",
            "taxids_detected": sorted(taxids),
            "taxid_results": all_results,
            "note": "ReLink runs are separated by organism and/or crosslinker chemistry"
            if len(crosslinker_groups) > 1
            else None,
        }

    @staticmethod
    def _safe_run_name(value: str) -> str:
        """Return a filesystem-safe identifier for a chemistry-specific run."""
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    def _crosslinker_names(
        self,
        llm_responses: Optional[Dict[str, Any]] = None,
        xi_config_generator: Optional[Any] = None,
    ) -> List[str]:
        """Return every distinct crosslinker chemistry identified for this dataset.

        Chemistry names come from the dataset-level LLM metadata response.
        Individual RAW files are deliberately NOT mapped to a specific
        chemistry (file clustering, which previously attempted this, was
        removed as legacy logic) - ReLink runs the complete RAW-file set once
        for every identified crosslinker chemistry (see run_for_pxd), since
        XiSearch should never mix two different crosslinker chemistries into a
        single search.
        """
        names: List[str] = []
        seen: Set[str] = set()

        def add_name(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    add_name(item)
                return
            name = str(value).strip()
            if not name or name.lower() in {"null", "none"}:
                return
            key = name.lower()
            if key not in seen:
                seen.add(key)
                names.append(name)

        # Dataset-level LLM metadata. Prefer xi_config_generator's schema-aware
        # parser (handles every comment[cross-linker] response shape seen
        # across pipeline runs - single NT string, parallel NT/AC/CL/TA lists,
        # or a "value" list of fully-structured per-reagent dicts) over a bare
        # NT-field read, so multi-reagent mentions using the newer response
        # schema are never silently missed here.
        if isinstance(llm_responses, dict):
            if xi_config_generator is not None:
                add_name(xi_config_generator.get_dataset_crosslinker_names(llm_responses))
            else:
                response = llm_responses.get("comment[cross-linker]") or {}
                parsed = response.get("parsed", {}) if isinstance(response, dict) else {}
                if isinstance(parsed, dict):
                    add_name(parsed.get("NT"))

        return names

    def extract_taxids_from_sdrf(self, sdrf_path: Path) -> Set[str]:
        """Extract NCBITaxon IDs from all organism columns in SDRF."""
        taxids: Set[str] = set()

        with open(sdrf_path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh, delimiter="\t")
            headers = next(reader, [])
            organism_idx = [
                idx for idx, name in enumerate(headers) if name == "characteristics[organism]"
            ]

            if not organism_idx:
                raise ValueError(
                    "SDRF does not contain any 'characteristics[organism]' columns"
                )

            for row in reader:
                for idx in organism_idx:
                    if idx >= len(row):
                        continue
                    value = row[idx]
                    if not value:
                        continue
                    # Expected format example: NT=Homo sapiens;AC=NCBITaxon:9606
                    parts = [p.strip() for p in str(value).split(";")]
                    for part in parts:
                        if part.startswith("AC=NCBITaxon:"):
                            taxid = part.split("AC=NCBITaxon:", 1)[1].strip()
                            if taxid.isdigit():
                                taxids.add(taxid)

        return taxids

    def fetch_project_fasta(
        self,
        project_files: Optional[Sequence[Dict[str, Any]]],
        output_dir: Path,
    ) -> Optional[Path]:
        """Use all supplied FASTAs, concatenating multiple databases for search."""
        candidates = [
            file_info
            for file_info in project_files or []
            if isinstance(file_info, dict)
            and Path(str(file_info.get("fileName", ""))).suffix.lower()
            in {".fa", ".fas", ".fasta"}
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda info: str(info["fileName"]))
        names = [Path(str(info["fileName"])).name for info in candidates]
        if len(set(names)) != len(names):
            raise ValueError("PRIDE FASTA filenames must be unique within the project")
        paths = [self._download_project_fasta(info, output_dir) for info in candidates]
        for path in paths:
            self._normalize_fasta(path)
            with path.open("rb") as handle:
                if not handle.read(4096).lstrip().startswith(b">"):
                    raise RuntimeError(f"PRIDE FASTA '{path.name}' is not a FASTA file")
        if len(candidates) > 1:
            signature = json.dumps(
                [(str(info["fileName"]), str(info.get("ftpUrl") or "")) for info in candidates]
            )
            digest = hashlib.sha256(signature.encode()).hexdigest()[:16]
            combined = output_dir / f"combined_pride_{digest}.fasta"
            temporary = combined.with_suffix(".fasta.tmp")
            try:
                with temporary.open("wb") as output:
                    for path in paths:
                        with path.open("rb") as source:
                            shutil.copyfileobj(source, output)
                        output.write(b"\n")
                temporary.replace(combined)
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
            logger.info("Combined %d PRIDE-supplied FASTAs into %s", len(paths), combined)
            return combined
        return paths[0]

    @staticmethod
    def _normalize_fasta(path: Path) -> None:
        """Strip a UTF-8 BOM and convert CRLF line endings, rewriting only if needed."""
        with path.open("rb") as handle:
            head = handle.read(1 << 20)
        if not (head.startswith(b"\xef\xbb\xbf") or b"\r" in head):
            return
        temporary = path.with_suffix(path.suffix + ".norm.tmp")
        try:
            with path.open("rb") as source, temporary.open("wb") as output:
                for index, line in enumerate(source):
                    if index == 0 and line.startswith(b"\xef\xbb\xbf"):
                        line = line[3:]
                    output.write(line.rstrip(b"\r\n") + b"\n" if line.endswith((b"\n", b"\r")) else line)
            temporary.replace(path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        logger.info("Normalized FASTA line endings/BOM: %s", path)

    def _download_project_fasta(self, file_info: Dict[str, Any], output_dir: Path) -> Path:
        """Download one source database atomically, reusing its cached copy."""
        filename = Path(str(file_info["fileName"])).name
        source_url = str(file_info.get("ftpUrl") or "")
        if not source_url:
            raise RuntimeError(f"PRIDE FASTA '{filename}' does not provide a download URL")

        output_dir.mkdir(parents=True, exist_ok=True)
        fasta_path = output_dir / filename
        if fasta_path.exists() and fasta_path.stat().st_size > 0:
            logger.info("Using cached PRIDE-supplied FASTA: %s", fasta_path)
            return fasta_path

        download_url = source_url.replace("ftp://", "https://", 1)
        tmp_path = fasta_path.with_suffix(fasta_path.suffix + ".tmp")
        logger.info("Downloading PRIDE-supplied FASTA: %s", filename)
        try:
            response = requests.get(
                download_url,
                timeout=self.requests_timeout,
                stream=True,
            )
            response.raise_for_status()
            first_chunk_checked = False
            with open(tmp_path, "wb") as fh:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    if not chunk:
                        continue
                    if not first_chunk_checked:
                        if not chunk.removeprefix(b"\xef\xbb\xbf").lstrip().startswith(b">"):
                            raise RuntimeError(
                                f"PRIDE download for '{filename}' is not a FASTA file"
                            )
                        first_chunk_checked = True
                    fh.write(chunk)
            if not first_chunk_checked:
                raise RuntimeError(f"PRIDE FASTA '{filename}' is empty")
            tmp_path.rename(fasta_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

        logger.info("Using PRIDE-supplied FASTA: %s", fasta_path)
        return fasta_path

    def fetch_fasta_for_taxid(self, taxid: str, output_dir: Path) -> Path:
        """Return <output_dir>/taxid_<taxid>.fasta, downloading UniProt only if no run has before.

        Downloads go to a cache shared by every run (``uniprot_cache_dir``); the per-PXD file is a
        hard link (or copy) so each PXD directory stays self-contained for downstream scripts.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        fasta_path = output_dir / f"taxid_{taxid}.fasta"

        if fasta_path.exists() and fasta_path.stat().st_size > 0:
            logger.info("Using cached FASTA for taxid %s: %s", taxid, fasta_path)
            return fasta_path

        cache_path = self.uniprot_cache_dir / f"taxid_{taxid}_reviewed.fasta"
        self.uniprot_cache_dir.mkdir(parents=True, exist_ok=True)
        if not (cache_path.exists() and cache_path.stat().st_size > 0):
            with self._cache_lock(cache_path):
                # Another run may have finished the download while this one waited for the lock.
                if cache_path.exists() and cache_path.stat().st_size > 0:
                    logger.info("UniProt FASTA for taxid %s was cached by another run", taxid)
                else:
                    self._download_uniprot_fasta(taxid, cache_path)
        else:
            logger.info("Using shared UniProt FASTA cache for taxid %s: %s", taxid, cache_path)

        self._link_or_copy(cache_path, fasta_path)
        return fasta_path

    @staticmethod
    @contextmanager
    def _cache_lock(cache_path: Path):
        """Serialize downloads of one cache file across concurrent jobs (best effort on NFS)."""
        lock_path = cache_path.with_suffix(cache_path.suffix + ".lock")
        with open(lock_path, "a") as lock_file:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX)
            except OSError:
                logger.warning("Could not lock %s; continuing without a lock", lock_path)
            try:
                yield
            finally:
                try:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
                except OSError:
                    pass

    @staticmethod
    def _link_or_copy(source: Path, destination: Path) -> None:
        temporary = destination.with_name(destination.name + f".{os.getpid()}.link")
        temporary.unlink(missing_ok=True)
        try:
            try:
                os.link(source, temporary)
            except OSError:
                shutil.copy2(source, temporary)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

    def _download_uniprot_fasta(self, taxid: str, cache_path: Path) -> None:
        """Download into the cache, restarting the whole download if the stream breaks mid-way."""
        attempts, base_delay = 3, 5
        for attempt in range(1, attempts + 1):
            try:
                self._download_uniprot_fasta_once(taxid, cache_path)
                break
            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as error:
                if attempt == attempts:
                    raise RuntimeError(
                        f"UniProt FASTA stream for taxid {taxid} failed {attempts} times: {error}"
                    ) from error
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "UniProt FASTA stream for taxid %s broke (attempt %d/%d): %s. Retrying in %ds",
                    taxid, attempt, attempts, error, delay,
                )
                time.sleep(delay)
        digest = hashlib.sha256()
        sequences = 0
        with cache_path.open("rb") as handle:
            for line in handle:
                digest.update(line)
                sequences += line.startswith(b">")
        cache_path.with_suffix(".json").write_text(json.dumps({
            "taxid": taxid, "url": self.UNIPROT_FASTA_URL,
            "query": f"taxonomy_id:{taxid} AND reviewed:true",
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "bytes": cache_path.stat().st_size, "sequences": sequences, "sha256": digest.hexdigest(),
        }, indent=2) + "\n", encoding="utf-8")

    def _download_uniprot_fasta_once(self, taxid: str, fasta_path: Path) -> None:
        """Download a UniProt FASTA stream for a taxonomy ID with retry logic for the connection."""
        fasta_path.parent.mkdir(parents=True, exist_ok=True)

        # Use reviewed:true (SwissProt only) to keep the FASTA small enough for
        # XiSearch to load into memory.  The full TrEMBL proteome for taxid 9606
        # is ~107 MB / ~94M peptides and causes XiSearch to OOM during fragment
        # tree construction.  SwissProt-only is ~15 MB and processes reliably.
        params = {
            "compressed": "false",
            "format": "fasta",
            "query": f"taxonomy_id:{taxid} AND reviewed:true",
        }

        max_retries = 3
        base_delay = 5  # Start with 5 seconds
        transient_error_codes = {502, 503, 504}  # Bad Gateway, Service Unavailable, Gateway Timeout

        logger.info("Downloading FASTA for taxid %s from UniProt (timeout: %ds, max_retries: %d)", 
                   taxid, self.requests_timeout, max_retries)
        
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(
                    self.UNIPROT_FASTA_URL,
                    params=params,
                    timeout=self.requests_timeout,
                    stream=True,
                )
                
                # Handle transient HTTP errors with retry
                if resp.status_code in transient_error_codes:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff
                        logger.warning(
                            "UniProt returned %d (transient error). Retrying in %ds (attempt %d/%d)",
                            resp.status_code, delay, attempt, max_retries
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise RuntimeError(
                            f"Failed to download FASTA for taxid {taxid} after {max_retries} retries: "
                            f"HTTP {resp.status_code}"
                        )
                
                resp.raise_for_status()
                break  # Success, exit retry loop
                
            except requests.exceptions.Timeout as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Timeout downloading FASTA for taxid %s (attempt %d/%d). Retrying in %ds",
                        taxid, attempt, max_retries, delay
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise RuntimeError(
                        f"Timeout downloading FASTA for taxid {taxid} after {max_retries} retries "
                        f"(exceeded {self.requests_timeout}s per attempt). "
                        "Try increasing requests_timeout or checking UniProt availability."
                    ) from e
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Connection error downloading FASTA for taxid %s (attempt %d/%d): %s. Retrying in %ds",
                        taxid, attempt, max_retries, str(e), delay
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise RuntimeError(
                        f"Connection error downloading FASTA for taxid {taxid} after {max_retries} retries: {e}"
                    ) from e
                    
            except requests.exceptions.RequestException as e:
                raise RuntimeError(
                    f"Failed to download FASTA for taxid {taxid}: {e}"
                ) from e

        # Stream response to disk in chunks to avoid loading large proteomes into RAM.
        # Use a temp file so an incomplete download never leaves a corrupt FASTA behind.
        tmp_path = fasta_path.with_suffix(f".fasta.{os.getpid()}.tmp")
        bytes_written = 0
        first_chunk_checked = False
        chunk_size = 1 << 20  # 1 MiB
        logger.info("Streaming FASTA for taxid %s to %s ...", taxid, fasta_path)
        try:
            with open(tmp_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    if not first_chunk_checked:
                        # Validate that the response looks like FASTA
                        first_chars = chunk.lstrip()
                        if not first_chars.startswith(b">"):
                            tmp_path.unlink(missing_ok=True)
                            raise RuntimeError(
                                f"No FASTA entries returned for taxid {taxid} (UniProt query)."
                            )
                        first_chunk_checked = True
                    fh.write(chunk)
                    bytes_written += len(chunk)
            if not first_chunk_checked:
                tmp_path.unlink(missing_ok=True)
                raise RuntimeError(
                    f"No FASTA entries returned for taxid {taxid} (UniProt query)."
                )
            tmp_path.rename(fasta_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

        logger.info("FASTA for taxid %s saved: %s (%.1f MB)", taxid, fasta_path, bytes_written / (1 << 20))

    # Path to the custom Nextflow config that fixes Singularity container pulls.
    # Relative to the repo root (two levels above tools/relink).
    _SINGULARITY_DOCKER_PULL_CONFIG = (
        Path(__file__).parent.parent.parent
        / "assets"
        / "nextflow_singularity_docker_pull.config"
    )

    _LOCAL_RESOURCE_CONFIG = (
        Path(__file__).parent.parent.parent
        / "assets"
        / "relink_local_resources.config"
    )

    _JS2_M3_MEDIUM_RESOURCE_CONFIG = (
        Path(__file__).parent.parent.parent
        / "assets"
        / "relink_js2_m3_medium.config"
    )

    _JS2_M3_XL_RESOURCE_CONFIG = (
        Path(__file__).parent.parent.parent
        / "assets"
        / "relink_js2_m3_xl.config"
    )

    def _clean_nextflow_state(self, launch_dir: Path, preserve_cache: bool = False) -> None:
        """Remove stale session files from this group's private launch directory.

        Nextflow writes .nextflow/, .nextflow.log*, and .nextflow.pid into the
        directory where Nextflow is executed.
        `.nextflow` holds cache metadata needed by `-resume`, so it is retained
        when resuming and otherwise cleared to avoid accidental cross-run reuse.
        """
        import shutil

        nf_dir = launch_dir / ".nextflow"
        if nf_dir.exists() and not preserve_cache:
            shutil.rmtree(nf_dir)
            logger.info("Cleaned stale Nextflow session state: %s", nf_dir)
        elif nf_dir.exists():
            logger.info("Preserving Nextflow session state for -resume: %s", nf_dir)

        for log_file in launch_dir.glob(".nextflow.log*"):
            log_file.unlink()
            logger.debug("Removed stale Nextflow log: %s", log_file)

    def run_nextflow(
        self,
        input_sdrf: Path,
        fasta_path: Path,
        raw_root_dir: Path,
        xi_linear_config: Path,
        xi_crosslink_config: Path,
        outdir: Path,
        profile: str,
        resume: bool,
        run_name: str,
        extra_args: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """Run the ReLink checkout with session state isolated per output group."""
        outdir.mkdir(parents=True, exist_ok=True)
        launch_dir = outdir.resolve() / ".nextflow-run"
        launch_dir.mkdir(parents=True, exist_ok=True)

        # Cache metadata is required to reuse completed tasks with `-resume`.
        self._clean_nextflow_state(launch_dir, preserve_cache=resume)

        profile_key = profile.lower()
        js2_resource_configs = {
            "js2-m3-medium": self._JS2_M3_MEDIUM_RESOURCE_CONFIG,
            "js2-m3-xl": self._JS2_M3_XL_RESOURCE_CONFIG,
        }
        nextflow_profile = "docker" if profile_key in js2_resource_configs else profile
        cmd: List[str] = [
            "nextflow",
            "run",
            str(self.relink_dir),
            "-name",
            run_name,
            "-profile",
            "conda,local" if profile_key == "conda" else nextflow_profile,
        ]

        if os.environ.get("SLURM_JOB_ID"):
            for variable in ("SLURM_CPUS_PER_TASK", "SLURM_MEM_PER_NODE"):
                if int(os.environ.get(variable, "0")) <= 0:
                    raise ValueError(f"{variable} must be positive for a ReLink Slurm run")
            cmd += ["-c", str(self._LOCAL_RESOURCE_CONFIG.with_name("relink_slurm_resources.config"))]

        if profile_key == "conda":
            resource_config = self._LOCAL_RESOURCE_CONFIG
            if resource_config.exists():
                cmd += ["-c", str(resource_config)]
                logger.debug("Injecting local ReLink resource config: %s", resource_config)
            else:
                logger.warning(
                    "Local ReLink resource config not found at %s; "
                    "using submodule defaults.",
                    resource_config,
                )

        if profile_key in js2_resource_configs:
            resource_config = js2_resource_configs[profile_key]
            if resource_config.exists():
                cmd += ["-c", str(resource_config)]
                logger.debug("Injecting JS2 ReLink resource config: %s", resource_config)
            else:
                logger.warning(
                    "JS2 ReLink resource config not found at %s; "
                    "using submodule defaults.",
                    resource_config,
                )

        # When using Singularity, inject a custom config that forces Nextflow to
        # pull containers via docker:// rather than oras://.  The oras:// images
        # at ghcr.io/bigbio/relink-sif are plain Docker manifests and cannot be
        # fetched by Singularity's OCI/ORAS client.
        if "singularity" in profile_key:
            sif_config = self._SINGULARITY_DOCKER_PULL_CONFIG
            if sif_config.exists():
                cmd += ["-c", str(sif_config)]
                logger.debug("Injecting Singularity docker-pull config: %s", sif_config)
            else:
                logger.warning(
                    "Singularity docker-pull config not found at %s; "
                    "container pull may fail with oras:// errors.",
                    sif_config,
                )

        cmd += [
            "--search_engine",
            "xisearch",
            "--input",
            str(input_sdrf.resolve()),
            "--fasta",
            str(fasta_path.resolve()),
            "--root_folder",
            str(raw_root_dir.resolve()),
            "--xi_linear_config",
            str(xi_linear_config.resolve()),
            "--xi_crosslink_config",
            str(xi_crosslink_config.resolve()),
            "--outdir",
            str(outdir.resolve()),
        ]

        if resume:
            cmd.append("-resume")
        if extra_args:
            cmd.extend(list(extra_args))

        work_dir = None
        if "-work-dir" in cmd:
            work_dir = Path(cmd[cmd.index("-work-dir") + 1])
        if work_dir and not self._paths_share_device(work_dir, outdir):
            cmd += ["--publish_dir_mode", "copy"]
            logger.info(
                "ReLink work and output directories use different filesystems; "
                "publishing final files with copy mode"
            )

        logger.info("Running ReLink: %s", " ".join(cmd))
        env = os.environ.copy()
        virtualenv = env.pop("VIRTUAL_ENV", None)
        if virtualenv:
            virtualenv_bin = str(Path(virtualenv) / "bin")
            env["PATH"] = os.pathsep.join(
                entry for entry in env.get("PATH", "").split(os.pathsep)
                if entry != virtualenv_bin
            )
        stdout_path = launch_dir / f"{run_name}.stdout.log"
        logger.info("Live Nextflow output: %s", stdout_path)
        with stdout_path.open("w") as stdout_file:
            proc = subprocess.run(
                cmd,
                cwd=str(launch_dir),
                stdout=stdout_file,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
        with stdout_path.open("rb") as stdout_file:
            stdout_file.seek(max(0, stdout_path.stat().st_size - 4000))
            stdout_tail = stdout_file.read().decode("utf-8", errors="replace")

        if proc.returncode != 0:
            logger.error("Nextflow stdout/stderr (%s):\n%s", stdout_path, stdout_tail)

        cleanup_cmd = ["nextflow", "clean", run_name, "-f"]
        cleanup_proc = subprocess.run(
            cleanup_cmd,
            cwd=str(launch_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        cleanup_result = {
            "returncode": cleanup_proc.returncode,
            "stdout_tail": (cleanup_proc.stdout or "")[-2000:],
        }
        if cleanup_proc.returncode == 0:
            logger.info("Cleaned Nextflow work for completed run %s", run_name)
        else:
            logger.warning(
                "Could not clean completed Nextflow run %s (rc=%d): %s",
                run_name,
                cleanup_proc.returncode,
                (cleanup_proc.stdout or "")[-1000:],
            )

        return {
            "returncode": proc.returncode,
            "run_name": run_name,
            "command": cmd,
            "stdout_tail": stdout_tail[-2000:],
            "stdout_log": str(stdout_path),
            "stderr_tail": "",
            "cleanup": cleanup_result,
        }

    def write_filtered_sdrf(
        self,
        source_sdrf: Path,
        output_sdrf: Path,
        raw_paths: Sequence[Path],
    ) -> None:
        """Write an SDRF containing only rows that match local RAW files."""
        output_sdrf.parent.mkdir(parents=True, exist_ok=True)

        raw_names = {p.name for p in raw_paths}
        if not raw_names:
            raise ValueError("No RAW files provided to filter SDRF")

        kept_rows: List[List[str]] = []
        with open(source_sdrf, "r", encoding="utf-8", newline="") as in_fh:
            reader = csv.reader(in_fh, delimiter="\t")
            header = next(reader, None)
            if not header:
                raise ValueError(f"Empty SDRF file: {source_sdrf}")

            for row in reader:
                keep = False
                for value in row:
                    cell = str(value).strip()
                    if not cell:
                        continue
                    if cell in raw_names:
                        keep = True
                        break
                    # Handle URI/path cells by comparing basename.
                    basename = cell.split("/")[-1].split("?")[0]
                    if basename in raw_names:
                        keep = True
                        break
                if keep:
                    kept_rows.append(row)

        if not kept_rows:
            raise ValueError(
                "Filtered SDRF has no rows matching local RAW files. "
                f"Source: {source_sdrf}"
            )

        with open(output_sdrf, "w", encoding="utf-8", newline="") as out_fh:
            writer = csv.writer(out_fh, delimiter="\t")
            writer.writerow(header)
            writer.writerows(kept_rows)

        logger.info(
            "Wrote filtered SDRF: %s (%d rows from %d local RAW files)",
            output_sdrf,
            len(kept_rows),
            len(raw_names),
        )
