"""
ReLink runner for xHAMLET.

Builds a ReLink samplesheet from xHAMLET outputs, resolves a FASTA from
TaxID terms in the generated SDRF, and executes the local ReLink submodule
via Nextflow.
"""

from __future__ import annotations

import csv
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import requests

logger = logging.getLogger(__name__)


class ReLinkRunner:
    """Run the ReLink Nextflow pipeline for a single PXD."""

    UNIPROT_FASTA_URL = "https://rest.uniprot.org/uniprotkb/stream"

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

        # Extract organisms from PRIDE metadata first (most reliable source)
        taxids = self._taxids_from_pride_metadata(pxd_dir)
        if not taxids:
            # Fallback: try SDRF
            taxids = self.extract_taxids_from_sdrf(sdrf_path)
        if not taxids:
            # Fallback: read taxids from file_assignment_map.json
            assignment_map = pxd_dir / "llm" / "file_assignment_map.json"
            taxids = self._taxids_from_assignment_map(assignment_map)
        
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

        all_results = {}
        for taxid in sorted(taxids):
            logger.info("Running ReLink for taxid %s", taxid)
            fasta_path = self.fetch_fasta_for_taxid(taxid, fasta_dir)

            # Create taxid-specific subdirectory
            taxid_dir = relink_dir / f"taxid_{taxid}"
            taxid_dir.mkdir(parents=True, exist_ok=True)

            samplesheet_path = taxid_dir / "samplesheet.csv"
            self.write_samplesheet(
                samplesheet_path=samplesheet_path,
                raw_paths=raw_paths,
                fasta_path=fasta_path,
                xi_linear_config=xi_linear_config,
                xi_crosslink_config=xi_crosslink_config,
            )

            outdir = taxid_dir / "results"
            run_result = self.run_nextflow(
                input_csv=samplesheet_path,
                outdir=outdir,
                profile=profile,
                resume=resume,
                extra_args=extra_args,
            )

            if run_result.get("returncode") != 0:
                logger.error(
                    "ReLink run failed for %s taxid %s (rc=%s)",
                    pxd,
                    taxid,
                    run_result.get("returncode"),
                )
                all_results[taxid] = {
                    "status": "failed",
                    "error": run_result,
                }
            else:
                all_results[taxid] = {
                    "status": "success",
                    "fasta_path": str(fasta_path),
                    "samplesheet": str(samplesheet_path),
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
            "note": "Multiple taxids detected; ReLink run separately for each organism"
            if len(taxids) > 1
            else None,
        }

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
        """Extract taxids from PRIDE metadata stored in responses.json."""
        import json

        taxids: Set[str] = set()
        responses_path = pxd_dir / "llm" / "responses.json"
        
        if not responses_path.exists():
            return taxids

        # Map common organism names to NCBI taxids
        organism_to_taxid = {
            "Escherichia coli": "562",
            "Homo sapiens": "9606",
            "Homo sapiens (human)": "9606",
            "Saccharomyces cerevisiae": "4932",
            "Mus musculus": "10090",
            "Rattus norvegicus": "10116",
            "Arabidopsis thaliana": "3702",
            "Caenorhabditis elegans": "6239",
            "Drosophila melanogaster": "7227",
            "Danio rerio": "7955",
        }

        try:
            with open(responses_path, encoding="utf-8") as fh:
                payload = json.load(fh)
            
            # Look for PRIDE metadata
            pride_metadata = payload.get("pride_metadata", {})
            if not isinstance(pride_metadata, dict):
                return taxids
            
            organisms = pride_metadata.get("organisms", [])
            if not isinstance(organisms, list):
                return taxids
            
            for organism in organisms:
                organism_str = str(organism).strip()
                # Try direct mapping first
                if organism_str in organism_to_taxid:
                    taxids.add(organism_to_taxid[organism_str])
                    logger.debug("Mapped organism '%s' to taxid %s", organism_str, organism_to_taxid[organism_str])
                else:
                    # Try partial matching
                    for key, taxid in organism_to_taxid.items():
                        if key.lower() in organism_str.lower():
                            taxids.add(taxid)
                            logger.debug("Partially matched organism '%s' to taxid %s", organism_str, taxid)
                            break
            
            if taxids:
                logger.info("Extracted %d taxids from PRIDE metadata: %s", len(taxids), ", ".join(sorted(taxids)))
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

    def fetch_fasta_for_taxid(self, taxid: str, output_dir: Path) -> Path:
        """Download a UniProt FASTA stream for a taxonomy ID."""
        output_dir.mkdir(parents=True, exist_ok=True)
        fasta_path = output_dir / f"taxid_{taxid}.fasta"

        if fasta_path.exists() and fasta_path.stat().st_size > 0:
            logger.info("Using cached FASTA for taxid %s: %s", taxid, fasta_path)
            return fasta_path

        params = {
            "compressed": "false",
            "format": "fasta",
            "query": f"taxonomy_id:{taxid}",
        }

        logger.info("Downloading FASTA for taxid %s from UniProt (timeout: %ds)", taxid, self.requests_timeout)
        try:
            resp = requests.get(
                self.UNIPROT_FASTA_URL,
                params=params,
                timeout=self.requests_timeout,
                stream=True,
            )
            resp.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise RuntimeError(
                f"Timeout downloading FASTA for taxid {taxid} (exceeded {self.requests_timeout}s). "
                "Try increasing requests_timeout or checking UniProt availability."
            ) from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Failed to download FASTA for taxid {taxid}: {e}"
            ) from e

        text = resp.text
        if not text.strip().startswith(">"):
            raise RuntimeError(
                f"No FASTA entries returned for taxid {taxid} (UniProt query)."
            )

        with open(fasta_path, "w", encoding="utf-8") as fh:
            fh.write(text)

        logger.debug("FASTA for taxid %s saved: %s (%d bytes)", taxid, fasta_path, fasta_path.stat().st_size)
        return fasta_path

    def write_samplesheet(
        self,
        samplesheet_path: Path,
        raw_paths: Sequence[Path],
        fasta_path: Path,
        xi_linear_config: Path,
        xi_crosslink_config: Path,
    ) -> None:
        """Write ReLink samplesheet CSV."""
        samplesheet_path.parent.mkdir(parents=True, exist_ok=True)

        with open(samplesheet_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                ["sample", "file", "fasta", "xi_linear_config", "xi_crosslink_config"]
            )
            for raw_path in raw_paths:
                writer.writerow(
                    [
                        raw_path.stem,
                        str(raw_path.resolve()),
                        str(fasta_path.resolve()),
                        str(xi_linear_config.resolve()),
                        str(xi_crosslink_config.resolve()),
                    ]
                )

    def run_nextflow(
        self,
        input_csv: Path,
        outdir: Path,
        profile: str,
        resume: bool,
        extra_args: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """Run local ReLink checkout via nextflow run ."""
        outdir.mkdir(parents=True, exist_ok=True)

        cmd: List[str] = [
            "nextflow",
            "run",
            ".",
            "-profile",
            profile,
            "--input",
            str(input_csv.resolve()),
            "--outdir",
            str(outdir.resolve()),
        ]

        if resume:
            cmd.append("-resume")
        if extra_args:
            cmd.extend(list(extra_args))

        logger.info("Running ReLink: %s", " ".join(cmd))
        proc = subprocess.run(
            cmd,
            cwd=str(self.relink_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        return {
            "returncode": proc.returncode,
            "command": cmd,
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-2000:],
        }
