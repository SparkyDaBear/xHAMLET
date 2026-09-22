"""
ReLink runner for xHAMLET.

Builds a ReLink samplesheet from xHAMLET outputs, resolves a FASTA from
TaxID terms in the generated SDRF, and executes the local ReLink submodule
via Nextflow.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import requests

logger = logging.getLogger(__name__)


class ReLinkRunner:
    """Run the ReLink Nextflow pipeline for a single PXD."""

    UNIPROT_FASTA_URL = "https://rest.uniprot.org/uniprotkb/stream"

    @staticmethod
    def _paths_share_device(first: Path, second: Path) -> bool:
        return first.stat().st_dev == second.stat().st_dev

    def __init__(
        self,
        relink_dir: str = "./tools/relink",
        requests_timeout: int = 600,
    ) -> None:
        self.relink_dir = Path(relink_dir).resolve()
        self.requests_timeout = requests_timeout

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
    ) -> Dict[str, Any]:
        """Execute ReLink for a single PXD."""
        if not self.relink_dir.exists():
            raise FileNotFoundError(
                f"ReLink submodule not found at {self.relink_dir}. "
                "Run: git submodule update --init --recursive"
            )

        if shutil.which("nextflow") is None:
            raise RuntimeError("nextflow is not installed or not on PATH")

        # Extract organisms from multiple sources and combine results
        # This ensures we don't miss any organisms if one source is incomplete
        taxids: Set[str] = set()
        
        # Primary source: LLM clustering response (most recent analysis)
        taxids.update(self._taxids_from_pride_metadata(pxd_dir))
        
        # Secondary source: SDRF (if available with NCBITaxon accessions)
        taxids.update(self.extract_taxids_from_sdrf(sdrf_path))
        
        # Tertiary source: file_assignment_map (clustering stage output)
        # Include this to catch organisms that LLM clustering may have missed
        assignment_map = pxd_dir / "llm" / "file_assignment_map.json"
        taxids.update(self._taxids_from_assignment_map(assignment_map))
        
        if not taxids:
            raise ValueError(
                f"No organisms found in PRIDE metadata, SDRF, or file_assignment_map for {pxd}"
            )

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

        crosslinker_groups = self._crosslinker_groups(raw_paths, pxd_dir)
        if crosslinker_groups is None:
            crosslinker_groups = {
                (taxid, None): list(raw_paths)
                for taxid in sorted(taxids)
            }

        all_results = {}
        for (taxid, crosslinker_name), group_raw_paths in sorted(crosslinker_groups.items()):
            run_label = f"taxid {taxid} ({crosslinker_name})" if crosslinker_name else f"taxid {taxid}"
            logger.info("Running ReLink for %s", run_label)
            fasta_path = self.fetch_project_fasta(project_files, fasta_dir)
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

        return {
            "status": "success",
            "taxids_detected": sorted(taxids),
            "taxid_results": all_results,
            "note": "ReLink runs are separated by organism and resolved crosslinker chemistry"
            if len(crosslinker_groups) > 1
            else None,
        }

    @staticmethod
    def _safe_run_name(value: str) -> str:
        """Return a filesystem-safe identifier for a chemistry-specific run."""
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    def _crosslinker_groups(
        self,
        raw_paths: Sequence[Path],
        pxd_dir: Path,
    ) -> Optional[Dict[tuple[str, str], List[Path]]]:
        """Group local RAW files by taxid and cached file-cluster crosslinker."""
        assignments_path = pxd_dir / "llm" / "file_assignment_map.json"
        clusters_path = pxd_dir / "llm" / "file_assignments.json"
        if not assignments_path.exists() or not clusters_path.exists():
            return None

        try:
            with open(assignments_path, encoding="utf-8") as fh:
                assignments = json.load(fh).get("data", {})
            with open(clusters_path, encoding="utf-8") as fh:
                clusters_field = json.load(fh).get("data", {})
            clusters_data = clusters_field.get("parsed", clusters_field)
            clusters = clusters_data.get("clusters", []) if isinstance(clusters_data, dict) else []
            cluster_by_id = {
                cluster.get("cluster_id"): cluster
                for cluster in clusters
                if isinstance(cluster, dict) and cluster.get("cluster_id")
            }
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            logger.warning("Could not load ReLink chemistry groups: %s", exc)
            return None

        groups: Dict[tuple[str, str], List[Path]] = {}
        for raw_path in raw_paths:
            assignment = assignments.get(raw_path.name, {})
            cluster = cluster_by_id.get(assignment.get("cluster_id"), {})
            crosslinker_name = cluster.get("crosslinker")
            raw_taxid = assignment.get("taxid") or cluster.get("taxid")
            taxid = str(raw_taxid or "").replace("NCBITaxon:", "").strip()
            if not crosslinker_name or not taxid.isdigit():
                logger.warning(
                    "No resolved cluster crosslinker for %s; using dataset-level ReLink config",
                    raw_path.name,
                )
                return None
            groups.setdefault((taxid, str(crosslinker_name)), []).append(raw_path)

        return groups or None

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

    def _taxids_from_pride_metadata(self, pxd_dir: Path) -> Set[str]:
        """Extract taxids from LLM file clustering response in responses.json.
        
        The responses.json contains LLM clustering output with organism info.
        Parse it to get all unique taxids from the clusters field.
        """
        import json

        taxids: Set[str] = set()
        responses_path = pxd_dir / "llm" / "responses.json"
        
        if not responses_path.exists():
            return taxids

        try:
            with open(responses_path, encoding="utf-8") as fh:
                payload = json.load(fh)
            
            # responses.json structure: {metadata: {...}, data: {...}}
            # data["clusters"] contains LLM clustering response with organism/taxid info
            data = payload.get("data", {})
            if not isinstance(data, dict):
                return taxids
            
            clusters_field = data.get("clusters", {})
            
            # clusters_field is {response: "...", parsed: {...}, ...}
            # Try "parsed" first, fall back to parsing "response"
            clusters_list = []
            
            if isinstance(clusters_field, dict):
                # Try parsed field first
                if "parsed" in clusters_field and isinstance(clusters_field["parsed"], dict):
                    parsed_data = clusters_field["parsed"]
                    if "clusters" in parsed_data and isinstance(parsed_data["clusters"], list):
                        clusters_list = parsed_data["clusters"]
                
                # Fall back to parsing response string
                if not clusters_list and "response" in clusters_field:
                    try:
                        response_str = clusters_field["response"]
                        if isinstance(response_str, str):
                            # Extract JSON from markdown code block if present
                            if "```json" in response_str:
                                json_start = response_str.find("```json") + 7
                                json_end = response_str.find("```", json_start)
                                response_str = response_str[json_start:json_end]
                            
                            response_data = json.loads(response_str)
                            if "clusters" in response_data and isinstance(response_data["clusters"], list):
                                clusters_list = response_data["clusters"]
                    except (json.JSONDecodeError, ValueError):
                        pass  # Failed to parse, continue
            
            # Extract unique taxids from clusters
            for cluster in clusters_list:
                if isinstance(cluster, dict):
                    taxid = cluster.get("taxid", "")
                    if taxid:
                        # Strip "NCBITaxon:" prefix if present
                        if taxid.startswith("NCBITaxon:"):
                            taxid = taxid.replace("NCBITaxon:", "")
                        if taxid.isdigit():
                            taxids.add(taxid)
                            organism = cluster.get("organism", "?")
                            logger.debug("Found cluster taxid %s for organism: %s", taxid, organism)
            
            if taxids:
                logger.info("Extracted %d taxids from LLM clustering response: %s", len(taxids), ", ".join(sorted(taxids)))
        except Exception as exc:
            logger.debug("Could not extract taxids from PRIDE metadata: %s", exc)

        return taxids

    def _taxids_from_assignment_map(self, assignment_map_path: Path) -> Set[str]:
        """Extract numeric taxids from file_assignment_map.json produced by the clustering stage."""
        import json

        taxids: Set[str] = set()
        if not assignment_map_path.exists():
            return taxids

        try:
            with open(assignment_map_path, encoding="utf-8") as fh:
                payload = json.load(fh)
            data = payload.get("data", payload)
            if not isinstance(data, dict):
                return taxids
            for entry in data.values():
                if not isinstance(entry, dict):
                    continue
                raw_taxid = entry.get("taxid", "")
                if not raw_taxid:
                    continue
                # Strip NCBITaxon: prefix if present
                numeric = str(raw_taxid).replace("NCBITaxon:", "").strip()
                if numeric.isdigit():
                    taxids.add(numeric)
        except Exception as exc:
            logger.warning("Could not read taxids from %s: %s", assignment_map_path, exc)

        return taxids

    def fetch_project_fasta(
        self,
        project_files: Optional[Sequence[Dict[str, Any]]],
        output_dir: Path,
    ) -> Optional[Path]:
        """Download and cache the single FASTA supplied with a PRIDE project."""
        candidates = [
            file_info
            for file_info in project_files or []
            if isinstance(file_info, dict)
            and Path(str(file_info.get("fileName", ""))).suffix.lower()
            in {".fa", ".fas", ".fasta"}
        ]
        if not candidates:
            return None
        if len(candidates) > 1:
            names = ", ".join(str(file_info.get("fileName", "")) for file_info in candidates)
            raise ValueError(
                "Multiple FASTA files were supplied by PRIDE; cannot select one safely: "
                f"{names}"
            )

        file_info = candidates[0]
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
                        if not chunk.lstrip().startswith(b">"):
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
        """Download a UniProt FASTA stream for a taxonomy ID with retry logic."""
        output_dir.mkdir(parents=True, exist_ok=True)
        fasta_path = output_dir / f"taxid_{taxid}.fasta"

        if fasta_path.exists() and fasta_path.stat().st_size > 0:
            logger.info("Using cached FASTA for taxid %s: %s", taxid, fasta_path)
            return fasta_path

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
        tmp_path = fasta_path.with_suffix(".fasta.tmp")
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
        return fasta_path

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

    def _clean_nextflow_state(self, preserve_cache: bool = False) -> None:
        """Remove stale Nextflow session files from the ReLink submodule directory.

        Nextflow writes .nextflow/, .nextflow.log*, and .nextflow.pid into the
        directory where `nextflow run .` is executed (tools/relink/).
        `.nextflow` holds cache metadata needed by `-resume`, so it is retained
        when resuming and otherwise cleared to avoid accidental cross-run reuse.
        """
        import shutil

        nf_dir = self.relink_dir / ".nextflow"
        if nf_dir.exists() and not preserve_cache:
            shutil.rmtree(nf_dir)
            logger.info("Cleaned stale Nextflow session state: %s", nf_dir)
        elif nf_dir.exists():
            logger.info("Preserving Nextflow session state for -resume: %s", nf_dir)

        for log_file in self.relink_dir.glob(".nextflow.log*"):
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
        """Run local ReLink checkout via nextflow run ."""
        outdir.mkdir(parents=True, exist_ok=True)

        # Cache metadata is required to reuse completed tasks with `-resume`.
        self._clean_nextflow_state(preserve_cache=resume)

        profile_key = profile.lower()
        js2_resource_configs = {
            "js2-m3-medium": self._JS2_M3_MEDIUM_RESOURCE_CONFIG,
            "js2-m3-xl": self._JS2_M3_XL_RESOURCE_CONFIG,
        }
        nextflow_profile = "docker" if profile_key in js2_resource_configs else profile
        cmd: List[str] = [
            "nextflow",
            "run",
            ".",
            "-name",
            run_name,
            "-profile",
            "conda,local" if profile_key == "conda" else nextflow_profile,
        ]

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
        proc = subprocess.run(
            cmd,
            cwd=str(self.relink_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout
            text=True,
            env=env,
        )

        if proc.returncode != 0:
            logger.error("Nextflow stdout/stderr:\n%s", (proc.stdout or "")[-4000:])

        cleanup_cmd = ["nextflow", "clean", run_name, "-f"]
        cleanup_proc = subprocess.run(
            cleanup_cmd,
            cwd=str(self.relink_dir),
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
            "stdout_tail": (proc.stdout or "")[-2000:],
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
