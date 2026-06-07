"""
Main PXDMetadataEnhancer orchestrator class
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .pride_client import PrideClient
from .pmc_client import PMCClient
from .ncbi_client import NCBIClient
from .data_store import DataStore
from .llm_client import LLMClient
from .prompt_templates import PromptTemplates
from .xi_config_generator import XiConfigGenerator
from .raw_processor import RawFileProcessor
from .assessor_runner import AssessorRunner
from .sdrf_writer import SDRFWriter

logger = logging.getLogger(__name__)


class PXDMetadataEnhancer:
    """
    Main orchestrator for enriching PRIDE project metadata with LLM-extracted information
    
    Default Workflow:
    1. Fetch PRIDE project metadata
    2. Extract PubMed IDs from PRIDE response
    3. Use PMID to fetch publication text via selected API (PMC or NCBI)
    4. Extract and combine text sections from publication
    5. Query LLM with each configured prompt on the publication text
    6. Cache all API responses and LLM outputs
    7. Compile into final enriched metadata JSON
    
    Supported Data Sources:
    - PRIDE REST API: Proteomics project metadata and accessions
    - PMC BioC API: Full-text publications (default, most reliable for text)
    - NCBI Entrez API: PubMed metadata and summaries (alternative)
    - OpenAI API: LLM-based metadata extraction with configurable prompts
    """
    
    def __init__(self, 
                 base_dir: str = "./pxd_data",
                 prompts_dir: str = "./prompts",
                 llm_model: str = "gpt-4o-mini-2024-07-18",
                 pride_base_url: str = "https://www.ebi.ac.uk/pride/ws/archive/v3",
                 email: Optional[str] = None,
                 ncbi_api_key: Optional[str] = None):
        """
        Initialize PXDMetadataEnhancer
        
        Args:
            base_dir: Base directory for storing cached data
            prompts_dir: Directory containing LLM prompt templates
            llm_model: LLM model to use (e.g., 'gpt-4o-mini-2024-07-18', 'gpt-4')
            pride_base_url: PRIDE REST API base URL
            email: Email for PMC/NCBI API requests
            ncbi_api_key: API key for NCBI requests
        
        Note: Publication source is hardcoded to "pmc" (PMC BioC API)
        """
        self.pride = PrideClient(base_url=pride_base_url)
        self.pmc = PMCClient(email=email, api_key=ncbi_api_key)
        
        # Initialize NCBI client only if email is provided (required for DOI searches)
        try:
            self.ncbi = NCBIClient(email=email, api_key=ncbi_api_key)
        except ValueError:
            logger.warning("NCBI credentials not provided. DOI-based PMID lookup will not be available.")
            self.ncbi = None
        
        self.store = DataStore(base_dir=base_dir)
        self.llm = LLMClient(model=llm_model)
        self.prompts = PromptTemplates(prompts_dir=prompts_dir)
        self.xi_config_gen = XiConfigGenerator()
        self.publication_source = "pmc"  # Hardcoded to PMC for full-text access
        
        logger.info(f"PXDMetadataEnhancer initialized")
        logger.info(f"  PRIDE API: {pride_base_url}")
        logger.info(f"  Publication source: pmc (PMC BioC API - hardcoded for full-text)")
        logger.info(f"  LLM model: {llm_model}")
        logger.info(f"  Xi config generation: enabled")
    
    def process_pxd(
        self,
        pxd: str,
        force_refresh: bool = False,
        prompt_keys: Optional[List[str]] = None,
        no_download: bool = False,
        skip_spectral: bool = False,
        clean_raw: bool = False,
        clean_mzml: bool = False,
        limit: Optional[int] = None,
        aria2c_connections: int = 16,
        nproc: int = 1,
        skip_sdrf: bool = False,
        skip_xi: bool = False,
        assessor_files_per_cluster: int = 1,
    ) -> Dict[str, Any]:
        """
        Main workflow: Process a single PXD end-to-end (9-stage pipeline).

        Stages
        ------
        1  PRIDE fetch          — project metadata + file list
        2  Publication          — PMID → PMCID → PMC full text
        2.5 File clustering     — LLM groups files by biological condition
        3  Raw file processing  — aria2c download → thermorawfileparser → mzML
        4  Spectral merge       — AssessorRunner builds spectral_summary.json
        5  LLM queries          — 23-prompt extraction on publication / PRIDE text
        6  SDRF generation      — SDRFWriter writes {pxd}.sdrf.tsv
        7  SDRF validation      — parse_sdrf crosslinking template check
        8  Xi config generation — crosslinking + linear search configs
        9  Final save           — enhanced/metadata.json

        Args:
            pxd:                        PRIDE project accession (e.g. 'PXD000001').
            force_refresh:              Re-process even if cached data exists.
            prompt_keys:                Subset of prompts to run (default: all).
            no_download:                Skip Stages 3–4 (raw file processing).
            skip_spectral:              Skip mzML conversion and mzML_assessor within Stage 3.
            clean_raw:                  Delete each .raw file after thermorawfileparser runs.
            clean_mzml:                 Delete .mzML files after mzML_assessor completes.
            limit:                      Cap the number of raw files processed in Stage 3.
            aria2c_connections:         TCP connections per file for aria2c (default: 16).
            nproc:                      Parallel workers for Phase 1 per-file processing (default: 1).
            skip_sdrf:                  Skip Stage 6 (SDRF generation).
            skip_xi:                    Skip Stage 8 (Xi config generation).
            assessor_files_per_cluster: How many files per cluster to download+assess (default: 1).

        Returns:
            Dict with complete enriched metadata.

        Raises:
            Exception: On critical failures (missing PRIDE data).
        """
        logger.info("=" * 80)
        logger.info("Processing PXD: %s", pxd)
        logger.info("=" * 80)

        result: Dict[str, Any] = {
            "pxd": pxd,
            "processed_at": datetime.now().isoformat(),
            "stages": {},
        }

        try:
            subdirs = self.store.get_subdirs(pxd)
            pxd_dir = self.store.get_pxd_dir(pxd)

            ###########################################################
            # Stage 1: Fetch PRIDE data (metadata + file list)
            logger.info("[Stage 1/9] Fetching PRIDE project metadata...")
            pride_data = self._fetch_and_cache_pride(pxd, force_refresh)
            result["stages"]["pride"] = "success" if pride_data else "failed"

            if not pride_data:
                logger.error("Failed to fetch PRIDE data. Aborting.")
                raise Exception("PRIDE data fetch failed")

            ###########################################################
            # Stage 2: Get publication info + fetch text
            logger.info("[Stage 2/9] Extracting publication information...")
            doi, pubmed_ids = self._extract_publication_info(pride_data)
            logger.info("Extracted DOI: %s", doi)
            logger.info("Extracted PubMed IDs: %s", pubmed_ids)

            publication_data = None

            if pubmed_ids:
                for pmid in pubmed_ids:
                    logger.info("Attempting PMID %s: converting to PMCID...", pmid)
                    pmcid = self.pmc.pmid_to_pmcid(pmid)
                    if pmcid:
                        logger.info("Converted PMID %s to PMCID %s. Fetching full text...", pmid, pmcid)
                        publication_data = self._fetch_and_cache_publication(pxd, pmcid, force_refresh)
                        if publication_data:
                            logger.info("✓ Successfully fetched publication for PMCID %s", pmcid)
                            break
                        logger.warning("Failed to fetch text for PMCID %s", pmcid)
                    else:
                        logger.warning("Could not convert PMID %s to PMCID", pmid)

            if publication_data is None and doi and not pubmed_ids and self.ncbi:
                logger.info("No PMID/PMCID available. Attempting DOI-based lookup: %s", doi)
                pmid = self.ncbi.search_by_doi(doi)
                if pmid:
                    pmcid = self.pmc.pmid_to_pmcid(pmid)
                    if pmcid:
                        publication_data = self._fetch_and_cache_publication(pxd, pmcid, force_refresh)
                        if publication_data:
                            logger.info("✓ Successfully fetched publication via DOI→PMID→PMCID")

            if publication_data:
                result["stages"]["publication"] = "success"
            else:
                result["stages"]["publication"] = (
                    "failed" if (doi or pubmed_ids) else "skipped_no_pmid"
                )
                logger.warning("No publication text found. Will use PRIDE metadata for LLM analysis.")

            ###########################################################
            # Stage 2.5: File clustering by biological condition
            logger.info("[Stage 2.5/9] Clustering files by biological condition...")
            file_assignments = self._cluster_files(
                pxd=pxd,
                pride_data=pride_data,
                publication_data=publication_data,
                force_refresh=force_refresh,
            )
            result["stages"]["file_clustering"] = (
                "success" if file_assignments else "failed"
            )
            if file_assignments:
                result["file_assignments"] = file_assignments
                # Count files per cluster
                cluster_counts = {}
                cluster_labels = {}
                for fa in file_assignments.values():
                    cid = fa.get("cluster_id", "unknown")
                    cluster_counts[cid] = cluster_counts.get(cid, 0) + 1
                    if cid not in cluster_labels:
                        cluster_labels[cid] = fa.get("cluster_label", "")
                logger.info(
                    "✓ File clustering complete: %d files assigned to %d clusters",
                    len(file_assignments), len(cluster_counts)
                )
                for cid, count in sorted(cluster_counts.items()):
                    label = cluster_labels.get(cid, "")
                    if label:
                        logger.info("  - %s (%s): %d files", cid, label, count)
                    else:
                        logger.info("  - %s: %d files", cid, count)

            ###########################################################
            # Stage 3: Raw file processing (download → thermorawfileparser → mzML)
            if no_download:
                logger.info("[Stage 3/9] Skipped (--no-download)")
                result["stages"]["raw_processing"] = "skipped_no_download"
                file_list = []
                raw_result = None
            else:
                logger.info("[Stage 3/9] Raw file processing...")
                files_meta = pride_data.get("files", {}) or {}
                file_list = files_meta.get("files", []) if isinstance(files_meta, dict) else []

                if file_list:
                    processor = RawFileProcessor(
                        pxd=pxd,
                        pxd_dir=pxd_dir,
                        aria2c_connections=aria2c_connections,
                        clean_raw=clean_raw,
                        clean_mzml=clean_mzml,
                        skip_spectral=skip_spectral,
                        limit=limit,
                        nproc=nproc,
                        file_assignments=file_assignments,
                        assessor_files_per_cluster=assessor_files_per_cluster,
                    )
                    raw_result = processor.run(file_list)
                    result["stages"]["raw_processing"] = (
                        "success" if raw_result.get("files_failed", 0) == 0 else "partial"
                    )
                    result["raw_processing"] = raw_result
                    logger.info(
                        "✓ Raw processing: %d/%d files OK, %d failed",
                        raw_result.get("files_processed", 0),
                        raw_result.get("files_total", 0),
                        raw_result.get("files_failed", 0),
                    )
                else:
                    logger.warning("No file list available in PRIDE data — skipping Stage 3")
                    result["stages"]["raw_processing"] = "skipped_no_files"
                    raw_result = None

            ###########################################################
            # Stage 4: Spectral merge (AssessorRunner)
            assessment_dir = subdirs["assessment"]
            spectral_summary: Optional[Dict[str, Any]] = None

            spectral_summary_path = assessment_dir / "spectral_summary.json"
            if not force_refresh and spectral_summary_path.exists():
                logger.info("[Stage 4/9] Loading cached spectral_summary.json...")
                import json
                with open(spectral_summary_path) as fh:
                    spectral_summary = json.load(fh)
                result["stages"]["spectral_merge"] = "success_cached"
            else:
                # Build summary from any existing per-file assessment JSONs
                logger.info("[Stage 4/9] Building spectral summary from assessment files...")
                runner = AssessorRunner(assessment_dir)
                spectral_summary = runner.build_spectral_summary(
                    pride_data=pride_data,
                    publication_data=(
                        publication_data.get("data") if isinstance(publication_data, dict) else publication_data
                    ),
                )
                result["stages"]["spectral_merge"] = (
                    "success" if spectral_summary else "failed"
                )

            if spectral_summary:
                result["spectral_summary"] = spectral_summary

            ###########################################################
            # Stage 5: LLM extraction
            logger.info("[Stage 5/9] Querying LLM with configured prompts...")
            if publication_data:
                logger.info("Using publication text for LLM analysis")
                text_sections = self.pmc.extract_text_sections(publication_data)
            else:
                logger.info("Using PRIDE metadata for LLM analysis")
                text_sections = self._extract_text_sections_from_pride(pride_data)

            combined_text = self._combine_text_sections(text_sections)
            logger.debug("Combined text prepared, length: %d chars", len(combined_text))

            if not prompt_keys:
                prompt_keys = self.prompts.list_prompts()

            llm_responses = self._query_llm_with_prompts(pxd, combined_text, prompt_keys, force_refresh)
            result["stages"]["llm"] = "success" if llm_responses else "failed"

            ###########################################################
            # Stage 6: SDRF generation
            if skip_sdrf:
                logger.info("[Stage 6/9] Skipped (--skip-sdrf)")
                result["stages"]["sdrf"] = "skipped"
            else:
                logger.info("[Stage 6/9] Generating SDRF TSV...")
                sdrf_dir = subdirs["sdrf"]
                sdrf_path = sdrf_dir / f"{pxd}.sdrf.tsv"
                try:
                    all_files = (pride_data.get("files", {}) or {}).get("files", [])
                    assessed_files: List[str] = []
                    if isinstance(raw_result, dict):
                        for entry in raw_result.get("per_file", []) or []:
                            if entry.get("mzml_converted") is True and entry.get("filename"):
                                assessed_files.append(entry["filename"])

                    writer = SDRFWriter()
                    writer.write(
                        pxd=pxd,
                        file_list=all_files,
                        llm_responses=llm_responses,
                        spectral_summary=spectral_summary,
                        pride_data=pride_data,
                        output_path=sdrf_path,
                        file_assignments=file_assignments,
                        assessed_files=assessed_files,
                    )
                    result["stages"]["sdrf"] = "success"
                    result["sdrf_path"] = str(sdrf_path)
                    logger.info("✓ SDRF written: %s", sdrf_path)
                except Exception as exc:
                    logger.error("SDRF generation failed: %s", exc, exc_info=True)
                    result["stages"]["sdrf"] = "failed"
                    result["sdrf_error"] = str(exc)

            ###########################################################
            # Stage 7: SDRF validation with parse_sdrf
            if skip_sdrf or result["stages"].get("sdrf") != "success":
                result["stages"]["sdrf_validation"] = "skipped"
            else:
                logger.info("[Stage 7/9] Validating SDRF with parse_sdrf...")
                try:
                    val_proc = subprocess.run(
                        [
                            "parse_sdrf",
                            "validate-sdrf",
                            "--sdrf_file", str(sdrf_path),
                            "--template", "crosslinking",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=120,
                    )
                    if val_proc.returncode == 0:
                        result["stages"]["sdrf_validation"] = "success"
                        logger.info("✓ SDRF validation passed")
                    else:
                        warnings_text = (val_proc.stdout or val_proc.stderr or "").strip()
                        if warnings_text:
                            result["stages"]["sdrf_validation"] = "success_with_warnings"
                            result["sdrf_validation_warnings"] = warnings_text
                            logger.warning("SDRF validation warnings:\n%s", warnings_text[:500])
                        else:
                            result["stages"]["sdrf_validation"] = "failed"
                            logger.warning("SDRF validation failed (rc=%d, no output)", val_proc.returncode)
                except FileNotFoundError:
                    result["stages"]["sdrf_validation"] = "skipped_not_installed"
                    logger.info("parse_sdrf not installed — skipping SDRF validation")
                except subprocess.TimeoutExpired:
                    result["stages"]["sdrf_validation"] = "failed_timeout"

            ###########################################################
            # Stage 8: Xi config generation
            if skip_xi:
                logger.info("[Stage 8/9] Skipped (--skip-xi)")
                result["stages"]["xi_configs"] = "skipped"
            else:
                logger.info("[Stage 8/9] Generating Xi configuration files...")
                try:
                    config_xl, config_linear = self.xi_config_gen.generate_configs(
                        pxd, llm_responses, pride_data
                    )
                    xl_path, linear_path = self.xi_config_gen.save_configs(
                        pxd, config_xl, config_linear, self.store.base_dir
                    )
                    result["stages"]["xi_configs"] = "success"
                    result["xi_config_paths"] = {
                        "crosslinking": str(xl_path),
                        "linear": str(linear_path),
                    }
                    logger.info("✓ Xi configs: %s | %s", xl_path, linear_path)
                except Exception as exc:
                    logger.error("Failed to generate Xi configs: %s", exc, exc_info=True)
                    result["stages"]["xi_configs"] = "failed"
                    result["xi_config_error"] = str(exc)

            ###########################################################
            # Stage 9: Compile and save
            logger.info("[Stage 9/9] Compiling and saving enriched metadata...")
            result = self._compile_results(pxd, pride_data, publication_data, llm_responses, result)
            result["stages"]["compilation"] = "success"
            self.store.save_json(result, pxd, "enhanced", "metadata")

            logger.info("✓ Successfully processed %s", pxd)
            logger.info("=" * 80)
            return result

        except Exception as e:
            logger.error("Failed to process %s: %s", pxd, e, exc_info=True)
            result["error"] = str(e)
            raise
    
    def _fetch_and_cache_pride(self, pxd: str, force_refresh: bool = False) -> Optional[Dict]:
        """Fetch PRIDE data and cache it, including file download links"""
        # Check cache first
        if not force_refresh and self.store.file_exists(pxd, "pride", "project_details"):
            logger.info("Loading PRIDE data from cache")
            return self.store.load_json(pxd, "pride", "project_details")
        
        # Fetch fresh
        pride_data = self.pride.fetch_project_details(pxd)
        
        if pride_data:
            # Attempt to fetch file download links
            try:
                logger.info("Fetching file download links...")
                file_links = self.pride.extract_file_download_links(pxd)
                
                if file_links:
                    pride_data["files"] = file_links
                    logger.info(f"Added {file_links['totalCount']} file links to project metadata")
                else:
                    # Graceful failure: set to null if fetch fails
                    pride_data["files"] = None
                    logger.warning("Failed to fetch file links, setting to null")
                    
            except Exception as e:
                logger.error(f"Error fetching file links: {e}")
                pride_data["files"] = None
            
            self.store.save_json(pride_data, pxd, "pride", "project_details")
        
        return pride_data
    
    def _fetch_and_cache_pmc(self, pxd: str, pmid: str, force_refresh: bool = False) -> Optional[Dict]:
        """Fetch PMC data and cache it"""
        # Check cache first
        if not force_refresh and self.store.file_exists(pxd, "pmc", "full_text"):
            logger.info("Loading PMC data from cache")
            return self.store.load_json(pxd, "pmc", "full_text")
        
        # Convert PMID to PMCID
        pmcid = self.pmc.pmid_to_pmcid(pmid)
        if not pmcid:
            logger.warning(f"Could not convert PMID {pmid} to PMCID")
            return None
        
        # Fetch full text
        pmc_data = self.pmc.fetch_full_text(pmcid)
        
        if pmc_data:
            self.store.save_json(pmc_data, pxd, "pmc", "full_text")
            # Also save section extraction
            sections = self.pmc.extract_text_sections(pmc_data)
            self.store.save_json(sections, pxd, "pmc", "sections")
        
        return pmc_data
    
    def _fetch_and_cache_publication(self, pxd: str, pmcid: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Fetch publication text from PMC and cache it
        
        Args:
            pxd: PRIDE project accession
            pmcid: PubMed Central ID (already converted from PMID)
            force_refresh: Force refresh even if cached
            
        Returns:
            Publication data dict or None if fetch fails
        """
        cache_filename = "full_text"
        cache_category = "pmc"
        
        # Check cache first
        if not force_refresh and self.store.file_exists(pxd, cache_category, cache_filename):
            logger.info(f"Loading publication data from cache (PMC)")
            return self.store.load_json(pxd, cache_category, cache_filename)
        
        # Fetch from PMC using PMCID
        logger.info(f"Fetching full text from PMC (PMCID: {pmcid})")
        publication_data = self.pmc.fetch_full_text(pmcid)
        
        # Cache the result
        if publication_data:
            self.store.save_json(publication_data, pxd, cache_category, cache_filename)
            logger.info(f"Cached publication data for {pxd}")
        else:
            logger.warning(f"No data returned from PMC for PMCID {pmcid}")
        
        return publication_data
    
    def _extract_text_sections_from_ncbi(self, ncbi_data: Dict) -> Dict[str, str]:
        """Extract text sections from NCBI response"""
        sections = {}
        
        if "title" in ncbi_data:
            sections["title"] = ncbi_data["title"]
        
        if "abstract" in ncbi_data:
            sections["abstract"] = ncbi_data["abstract"]
        
        # NCBI response has sections dict
        if "sections" in ncbi_data:
            sections.update(ncbi_data["sections"])
        
        return sections
    
    def _extract_text_sections_from_pride(self, pride_data: Dict) -> Dict[str, str]:
        """
        Extract relevant text sections from PRIDE project metadata
        
        Used when publication text is not available (no PMID)
        """
        sections = {}
        
        # Add title
        if "title" in pride_data:
            sections["title"] = pride_data["title"]
        
        # Add project description
        if "projectDescription" in pride_data:
            sections["abstract"] = pride_data["projectDescription"]
        
        # Add sample processing protocol
        if "sampleProcessingProtocol" in pride_data:
            sections["methods"] = pride_data["sampleProcessingProtocol"]
        
        # Add data processing protocol
        if "dataProcessingProtocol" in pride_data:
            sections["data_processing"] = pride_data["dataProcessingProtocol"]
        
        # Add keywords as a section
        if "keywords" in pride_data and pride_data["keywords"]:
            keywords_text = "; ".join(pride_data["keywords"])
            sections["keywords"] = keywords_text
        
        # Add sample attributes and organisms
        organisms = []
        if "organisms" in pride_data:
            for org in pride_data["organisms"]:
                if "name" in org:
                    organisms.append(org["name"])
        
        if organisms:
            sections["organisms"] = "; ".join(organisms)
        
        # Add experiment types
        experiments = []
        if "experimentTypes" in pride_data:
            for exp in pride_data["experimentTypes"]:
                if "name" in exp:
                    experiments.append(exp["name"])
        
        if experiments:
            sections["experiment_types"] = "; ".join(experiments)
        
        # Add quantification methods
        quant_methods = []
        if "quantificationMethods" in pride_data:
            for method in pride_data["quantificationMethods"]:
                if "name" in method:
                    quant_methods.append(method["name"])
        
        if quant_methods:
            sections["quantification_methods"] = "; ".join(quant_methods)
        
        return sections
    
    def _extract_publication_info(self, pride_data: Dict) -> tuple:
        """Extract DOI and PubMed IDs from PRIDE data"""
        doi, pubmed_ids = self.pride.extract_publication_info(pride_data)
        return doi, pubmed_ids
    
    def _combine_text_sections(self, sections: Dict[str, str]) -> str:
        """Combine extracted text sections into single document"""
        text_parts = []
        
        # Order sections logically
        section_order = ["title", "abstract", "introduction", "methods", "results", "discussion", "conclusion"]
        
        for section in section_order:
            if section in sections and sections[section]:
                text_parts.append(f"[{section.upper()}]\n{sections[section].strip()}\n")
        
        return "\n".join(text_parts)
    
    def _query_llm_with_prompts(self, pxd: str, text: str, prompt_keys: List[str],
                               force_refresh: bool = False) -> Dict[str, Any]:
        """Query LLM with grouped prompts and return responses keyed by sdrf_column.

        Each prompt file now covers a thematic group of SDRF terms and asks the
        LLM to return a JSON object whose keys are sdrf_column strings
        (e.g. "characteristics[organism]", "comment[instrument]").

        The returned flat dict maps every extracted sdrf_column to:
          {"response": <raw str>, "parsed": <per-column dict>, "model": ...}

        Backwards-compatibility: if cached data uses old underscore keys
        (pre-TERMS.tsv refactor) it is treated as stale and re-queried.
        """
        import json as _json

        # ---- cache check ----
        if not force_refresh and self.store.file_exists(pxd, "llm", "responses"):
            logger.info("Loading LLM responses from cache")
            cached = self.store.load_json(pxd, "llm", "responses") or {}
            raw = cached.get("data", cached) if "data" in cached else cached
            # New format: keys contain "["; old format used underscores only
            if raw and any("[" in k for k in raw.keys()):
                return raw
            logger.warning(
                "%s: LLM cache is in old format (underscore keys) — re-querying", pxd
            )

        flat_responses: Dict[str, Any] = {}

        for prompt_key in prompt_keys:
            try:
                logger.info("Querying LLM with prompt group: %s", prompt_key)
                prompt_text = self.prompts.get_prompt(prompt_key)
                raw_response = self.llm.query(prompt_text, text)

                if not raw_response:
                    logger.warning("Empty LLM response for prompt: %s", prompt_key)
                    continue

                # Parse the grouped JSON response
                parsed_group = self.llm.parse_json_response(raw_response)
                if not isinstance(parsed_group, dict):
                    logger.warning(
                        "LLM response for '%s' is not a JSON object — skipping", prompt_key
                    )
                    continue

                # Flatten: distribute each sdrf_column into the flat dict
                for sdrf_col, col_data in parsed_group.items():
                    if not isinstance(col_data, dict):
                        # Wrap scalar values
                        col_data = {"value": col_data}
                    flat_responses[sdrf_col] = {
                        "response": raw_response,
                        "parsed": col_data,
                        "model": self.llm.model,
                        "prompt_group": prompt_key,
                    }

            except Exception as exc:
                logger.error("Failed to query with prompt '%s': %s", prompt_key, exc)

        # Cache flat responses
        if flat_responses:
            self.store.save_json(flat_responses, pxd, "llm", "responses")

        return flat_responses
    
    def _cluster_files(
        self,
        pxd: str,
        pride_data: Dict,
        publication_data: Optional[Dict],
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Cluster raw files by biological condition using LLM analysis.

        Reads file_clustering.txt prompt, passes it list of .raw files + publication,
        and returns a dict mapping filename → {cluster_id, cluster_label, organism, taxid}.

        Falls back to single cluster_0 with dataset organism if LLM fails.

        Args:
            pxd: PRIDE project accession
            pride_data: PRIDE project metadata (includes file list)
            publication_data: Publication text (or None if unavailable)
            force_refresh: Force re-clustering even if cached

        Returns:
            Dict[filename, {cluster_id, cluster_label, organism, taxid}] or None on failure.
            Structure of returned dict:
            {
              "sample_Glu_Rep1.raw": {
                "cluster_id": "cluster_1",
                "cluster_label": "yeast_glucose_BS3",
                "organism": "Saccharomyces cerevisiae",
                "taxid": "NCBITaxon:4932"
              },
              ...
            }
        """
        # Check cache first
        if not force_refresh and self.store.file_exists(pxd, "llm", "file_assignments"):
            logger.info("Loading file clustering from cache")
            clustering_response = self.store.load_json(pxd, "llm", "file_assignments")
            return self._parse_file_clustering(clustering_response, pride_data)

        # Get raw filenames from PRIDE
        files_meta = pride_data.get("files", {}) or {}
        file_list = files_meta.get("files", []) if isinstance(files_meta, dict) else []
        raw_files = [f for f in file_list if f.get("fileName", "").lower().endswith(".raw")]

        if not raw_files:
            logger.warning("No .raw files found in PRIDE data")
            return None

        raw_filenames = sorted([f.get("fileName", "") for f in raw_files])
        logger.info("Clustering %d .raw files", len(raw_filenames))

        # Extract organisms with taxids
        organisms_with_taxids = self._extract_organisms_with_taxids(pride_data)

        # Prepare publication text
        if publication_data:
            text_sections = self.pmc.extract_text_sections(publication_data)
        else:
            text_sections = self._extract_text_sections_from_pride(pride_data)

        pub_text = self._combine_text_sections(text_sections)

        # Load and render file_clustering.txt prompt
        try:
            prompt = self.prompts.get_prompt("file_clustering")
            if not prompt:
                logger.error("file_clustering.txt prompt not found")
                return None
        except Exception as e:
            logger.error("Failed to load file_clustering prompt: %s", e)
            return None

        # Render placeholders safely (do not use str.format because the template
        # contains JSON braces that are not escaped).
        prompt_text = (
            prompt.replace("{raw_filenames}", "\n".join(raw_filenames))
            .replace("{publication_text}", pub_text[:10000])
            .replace("{organisms_with_taxids}", organisms_with_taxids)
        )

        # Query LLM
        logger.info("Querying LLM for file clustering...")
        try:
            response_text = self.llm.query(
                "You are an expert proteomics assistant. Return valid JSON only.",
                prompt_text,
            )
            if not response_text:
                logger.error("LLM returned empty response for file clustering")
                return self._fallback_single_cluster(pride_data)
            logger.debug("LLM response (first 500 chars): %s", response_text[:500])
        except Exception as e:
            logger.error("LLM query failed for file clustering: %s", e)
            return self._fallback_single_cluster(pride_data)

        # Cache raw and parsed response for readability.
        parsed_response = self.llm.parse_json_response(response_text)
        self.store.save_json(
            {
                "response": response_text,
                "parsed": parsed_response,
            },
            pxd,
            "llm",
            "file_assignments",
        )

        # Parse JSON response
        clustering_response = response_text
        file_assignments = self._parse_file_clustering(clustering_response, pride_data)

        # Save a flat filename -> cluster mapping for easy human inspection.
        if file_assignments:
            self.store.save_json(file_assignments, pxd, "llm", "file_assignment_map")

        return file_assignments

    def _parse_file_clustering(
        self,
        clustering_response: Any,
        pride_data: Dict,
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Parse LLM clustering response JSON and convert to filename → assignment dict.

        Expected clustering_response structure:
        {
          "clusters": [
            {
              "cluster_id": "cluster_1",
              "cluster_label": "...",
              "files": ["file1.raw", "file2.raw", ...],
              "organism": "...",
              "taxid": "..."
            }
          ],
          "unassigned_files": [...],
          "confidence": "high",
          "evidence_quote": "..."
        }

        Returns:
        {
          "file1.raw": {
            "cluster_id": "cluster_1",
            "cluster_label": "...",
            "organism": "...",
            "taxid": "..."
          },
          ...
        }

        Fallback: If parsing fails, return all files in cluster_0 with dataset organism.
        """
        import json as _json

        # Accept raw string, cached dict payload, or already-parsed dict
        try:
            if isinstance(clustering_response, dict):
                if "parsed" in clustering_response and isinstance(clustering_response["parsed"], dict):
                    data = clustering_response["parsed"]
                elif "data" in clustering_response and isinstance(clustering_response["data"], dict):
                    data = clustering_response["data"]
                elif "response" in clustering_response and isinstance(clustering_response["response"], str):
                    data = _json.loads(clustering_response["response"])
                else:
                    data = clustering_response
            else:
                data = _json.loads(str(clustering_response))
        except _json.JSONDecodeError as e:
            logger.error("Failed to parse clustering JSON: %s", e)
            logger.warning("Falling back to single cluster_0 with dataset organism")
            return self._fallback_single_cluster(pride_data)

        # Extract clusters
        clusters = data.get("clusters", [])
        unassigned = data.get("unassigned_files", [])
        confidence = data.get("confidence", "unknown")

        logger.info(
            "Clustering results: %d clusters, %d unassigned files, confidence=%s",
            len(clusters), len(unassigned), confidence,
        )

        if str(confidence).lower() == "low":
            logger.warning("Clustering confidence is low; using fallback single-cluster assignment")
            return self._fallback_single_cluster(pride_data)

        # Build filename → assignment dict
        file_assignments = {}

        for cluster in clusters:
            cluster_id = cluster.get("cluster_id", "unknown")
            cluster_label = cluster.get("cluster_label", "")
            organism = cluster.get("organism", "")
            taxid = cluster.get("taxid", "")
            files = cluster.get("files", [])

            logger.debug("Cluster %s (%s): %d files", cluster_id, cluster_label, len(files))

            for filename in files:
                file_assignments[filename] = {
                    "cluster_id": cluster_id,
                    "cluster_label": cluster_label,
                    "organism": organism,
                    "taxid": taxid,
                }

        # Handle unassigned files: put them in cluster_0 with dataset organism
        dataset_org = self._resolve_dataset_organism(pride_data)
        if unassigned:
            logger.info("Assigning %d unassigned files to cluster_0", len(unassigned))
            for filename in unassigned:
                file_assignments[filename] = {
                    "cluster_id": "cluster_0",
                    "cluster_label": "unassigned",
                    "organism": dataset_org,
                    "taxid": "",
                }

        return file_assignments if file_assignments else None

    def _fallback_single_cluster(self, pride_data: Dict) -> Dict[str, Dict[str, Any]]:
        """Fallback: put all files in cluster_0 with dataset organism."""
        files_meta = pride_data.get("files", {}) or {}
        file_list = files_meta.get("files", []) if isinstance(files_meta, dict) else []
        raw_files = [f for f in file_list if f.get("fileName", "").lower().endswith(".raw")]

        dataset_org = self._resolve_dataset_organism(pride_data)

        file_assignments = {}
        for f in raw_files:
            filename = f.get("fileName", "")
            if filename:
                file_assignments[filename] = {
                    "cluster_id": "cluster_0",
                    "cluster_label": "all_files_single_condition",
                    "organism": dataset_org,
                    "taxid": "",
                }

        logger.warning("Using fallback: all %d files in cluster_0", len(file_assignments))
        return file_assignments if file_assignments else None

    def _resolve_dataset_organism(self, pride_data: Dict) -> str:
        """Extract primary organism name from PRIDE project metadata."""
        organisms = pride_data.get("organisms", [])
        if organisms and isinstance(organisms, list) and len(organisms) > 0:
            org = organisms[0]
            if isinstance(org, dict):
                return org.get("name", "Unknown organism")
            return str(org)
        return "Unknown organism"

    def _extract_organisms_with_taxids(self, pride_data: Dict) -> str:
        """Format organisms with taxids for LLM prompt."""
        organisms = pride_data.get("organisms", [])
        if not organisms:
            return "Unknown organism"

        org_strs = []
        for org in organisms:
            if isinstance(org, dict):
                name = org.get("name", "")
                taxid = org.get("id", "")  # PRIDE may store taxid as 'id'
                if name:
                    if taxid:
                        org_strs.append(f"{name} (NCBI Taxonomy ID: {taxid})")
                    else:
                        org_strs.append(name)
        
        return "; ".join(org_strs) if org_strs else "Unknown organism"
    
    def _compile_results(self, pxd: str, pride_data: Dict, publication_data: Optional[Dict],
                        llm_responses: Dict, base_result: Dict) -> Dict[str, Any]:
        """
        Compile all data into final enriched metadata
        
        Combines PRIDE metadata, publication text, and LLM-extracted data into single JSON
        Note: Does NOT save to disk - saving happens at end of process_pxd after all stages complete
        """
        result = base_result.copy()
        result.update({
            "pride_data": pride_data,
            "publication_metadata": {
                "source": self.publication_source,
                "data": publication_data
            } if publication_data else None,
            "llm_responses": llm_responses
        })
        
        return result
    
    def generate_sdrf(self, pxd: str) -> Dict[str, Any]:
        """
        Generate the SDRF TSV (and validate it) from cached data only.

        Loads cached PRIDE data, LLM responses, and spectral summary without
        querying any external APIs or processing raw files.  Used for projects
        whose cached LLM/PRIDE data already exists but whose SDRF was never
        written (e.g. processed before Stage 6 was added), or to re-run the
        SDRF writer after logic changes without repeating the full pipeline.

        Stages run:
            6  SDRF generation   — SDRFWriter.write()
            7  SDRF validation   — parse_sdrf validate-sdrf --template crosslinking

        The enhanced/metadata.json is updated in-place to reflect the stage
        outcomes and the sdrf_path field.

        Args:
            pxd: PRIDE project accession (e.g. 'PXD003486').

        Returns:
            Dict with keys: pxd, sdrf_path, stages (sdrf, sdrf_validation),
            and sdrf_validation_warnings if applicable.

        Raises:
            ValueError: If required cached data (PRIDE or LLM) is missing.
        """
        logger.info("=" * 80)
        logger.info("Generating SDRF for: %s (from cached data)", pxd)
        logger.info("=" * 80)

        # ---- Load cached PRIDE data ----
        pride_cache = self.store.load_json(pxd, "pride", "project_details")
        if not pride_cache:
            raise ValueError(
                f"No cached PRIDE data for {pxd}. "
                "Run the full pipeline first (python src/main.py --pxd %s --no-download)." % pxd
            )
        pride_data = pride_cache.get("data", pride_cache) if "data" in pride_cache else pride_cache

        # ---- Load cached LLM responses ----
        llm_cache = self.store.load_json(pxd, "llm", "responses")
        if not llm_cache:
            raise ValueError(
                f"No cached LLM responses for {pxd}. "
                "Run the full pipeline first to generate LLM data."
            )
        llm_responses = llm_cache.get("data", llm_cache) if "data" in llm_cache else llm_cache

        # ---- Load cached spectral summary (optional) ----
        subdirs = self.store.get_subdirs(pxd)
        spectral_summary: Optional[Dict[str, Any]] = None
        spectral_summary_path = subdirs["assessment"] / "spectral_summary.json"
        if spectral_summary_path.exists():
            import json as _json
            with open(spectral_summary_path) as fh:
                spectral_summary = _json.load(fh)
            logger.info("Loaded cached spectral_summary.json")

        # ---- Stage 6: SDRF generation ----
        sdrf_dir = subdirs["sdrf"]
        sdrf_path = sdrf_dir / f"{pxd}.sdrf.tsv"
        result: Dict[str, Any] = {"pxd": pxd, "stages": {}}

        try:
            all_files = (pride_data.get("files", {}) or {}).get("files", [])
            writer = SDRFWriter()
            writer.write(
                pxd=pxd,
                file_list=all_files,
                llm_responses=llm_responses,
                spectral_summary=spectral_summary,
                pride_data=pride_data,
                output_path=sdrf_path,
            )
            result["stages"]["sdrf"] = "success"
            result["sdrf_path"] = str(sdrf_path)
            logger.info("✓ SDRF written: %s", sdrf_path)
        except Exception as exc:
            logger.error("SDRF generation failed: %s", exc, exc_info=True)
            result["stages"]["sdrf"] = "failed"
            result["sdrf_error"] = str(exc)

        # ---- Stage 7: SDRF validation ----
        if result["stages"].get("sdrf") == "success":
            logger.info("Validating SDRF with parse_sdrf...")
            try:
                val_proc = subprocess.run(
                    [
                        "parse_sdrf",
                        "validate-sdrf",
                        "--sdrf_file", str(sdrf_path),
                        "--template", "crosslinking",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=120,
                )
                if val_proc.returncode == 0:
                    result["stages"]["sdrf_validation"] = "success"
                    logger.info("✓ SDRF validation passed")
                else:
                    warnings_text = (val_proc.stdout or val_proc.stderr or "").strip()
                    if warnings_text:
                        result["stages"]["sdrf_validation"] = "success_with_warnings"
                        result["sdrf_validation_warnings"] = warnings_text
                        logger.warning("SDRF validation warnings:\n%s", warnings_text[:500])
                    else:
                        result["stages"]["sdrf_validation"] = "failed"
                        logger.warning("SDRF validation failed (rc=%d, no output)", val_proc.returncode)
            except FileNotFoundError:
                result["stages"]["sdrf_validation"] = "skipped_not_installed"
                logger.info("parse_sdrf not installed — skipping SDRF validation")
            except subprocess.TimeoutExpired:
                result["stages"]["sdrf_validation"] = "failed_timeout"
        else:
            result["stages"]["sdrf_validation"] = "skipped"

        # ---- Patch the existing enhanced/metadata.json in-place ----
        existing = self.store.load_json(pxd, "enhanced", "metadata")
        if existing:
            meta = existing.get("data", existing) if "data" in existing else existing
            meta.setdefault("stages", {})
            meta["stages"]["sdrf"] = result["stages"].get("sdrf", "failed")
            meta["stages"]["sdrf_validation"] = result["stages"].get("sdrf_validation", "skipped")
            if "sdrf_path" in result:
                meta["sdrf_path"] = result["sdrf_path"]
            if "sdrf_validation_warnings" in result:
                meta["sdrf_validation_warnings"] = result["sdrf_validation_warnings"]
            self.store.save_json(meta, pxd, "enhanced", "metadata")
            logger.info("Updated enhanced/metadata.json for %s", pxd)

        logger.info("=" * 80)
        return result

    def get_pxd_metadata(self, pxd: str) -> Optional[Dict[str, Any]]:
        """Retrieve processed metadata for a PXD"""
        return self.store.load_json(pxd, "enhanced", "metadata")
    
    def list_processed_pxds(self) -> List[str]:
        """List all processed PXDs"""
        return self.store.list_pxds()
