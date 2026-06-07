#!/usr/bin/env python3
"""
CLI for PXD Metadata Enhancer
Orchestrates downloading and enriching PRIDE project metadata with LLM-extracted information
"""

import argparse
import logging
import sys
from typing import List, Optional
from pathlib import Path
import pandas as pd

from pxd_enhancer import PXDMetadataEnhancer
from pxd_enhancer.config import Config
from pxd_enhancer.prompt_templates import PromptTemplates


def setup_logging(level: str = "INFO", log_file: str = "pxd_enhancer.log") -> None:
    """Setup logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True) if os.path.dirname(log_file) else None
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers,
    )


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Enhance PRIDE project metadata with LLM-extracted information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single PXD
  python main.py --pxd PXD000001
  
  # Process multiple PXDs
  python main.py --pxd PXD000001 PXD000002 PXD000003
  
  # Process with custom configuration
  python main.py --pxd PXD000001 --config config.yaml
  
  # Force refresh cached data
  python main.py --pxd PXD000001 --force-refresh
  
  # Use specific prompts only
  python main.py --pxd PXD000001 --prompts organism disease
  
  # Create default prompts
  python main.py --create-prompts
        """
    )
    
    parser.add_argument(
        "--pxd",
        nargs="+",
        help="PXD accession(s) to process (e.g., PXD000001 PXD000002)"
    )
    
    parser.add_argument(
        "--config",
        default=None,
        help="Path to configuration YAML file"
    )
    
    parser.add_argument(
        "--data-dir",
        default="./pxd_data",
        help="Base directory for storing data (default: ./pxd_data)"
    )
    
    parser.add_argument(
        "--prompts-dir",
        default="./prompts",
        help="Directory containing prompt files (default: ./prompts)"
    )
    
    parser.add_argument(
        "--prompts",
        nargs="+",
        default=None,
        help="Specific prompts to use (e.g., organism disease)"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-4-turbo",
        help="LLM model to use (default: gpt-4-turbo)"
    )
    
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Reprocess even if cached data exists"
    )

    parser.add_argument(
        "--pxd-file",
        default=None,
        metavar="TSV",
        help="TSV file with an 'Accession' column listing PXD IDs to process"
    )

    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip raw file download, thermorawfileparser, and mzML_assessor (Stages 3-4)"
    )

    parser.add_argument(
        "--skip-spectral",
        action="store_true",
        help="Skip mzML conversion and mzML_assessor (download + metadata JSON still run)"
    )

    parser.add_argument(
        "--clean-raw",
        action="store_true",
        help="Delete each .raw file immediately after thermorawfileparser completes"
    )

    parser.add_argument(
        "--clean-mzml",
        action="store_true",
        help="Delete .mzML files from work/ after mzML_assessor completes"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process only the first N raw files per PXD (useful for testing)"
    )

    parser.add_argument(
        "--aria2c-connections",
        type=int,
        default=16,
        metavar="N",
        help="aria2c connections per file (--max-connection-per-server, default: 16)"
    )

    parser.add_argument(
        "--nproc",
        default="1",
        metavar="N|auto",
        help=(
            "Number of parallel workers for Phase 1 raw file processing "
            "(download + thermorawfileparser) within each PXD job. "
            "Use 'auto' to set floor(cpu_count / num_pxds), minimum 1. "
            "Default: 1 (serial)."
        ),
    )

    parser.add_argument(
        "--assessor-files-per-cluster",
        type=int,
        default=1,
        metavar="N",
        help=(
            "Number of representative files to download and assess per cluster. "
            "After file clustering (Stage 2.5), randomly select N files from each "
            "biological condition cluster for spectral assessment. "
            "Non-selected files have spectral metadata inherited from cluster representative. "
            "Default: 1 (one representative per cluster)."
        ),
    )

    parser.add_argument(
        "--skip-sdrf",
        action="store_true",
        help="Skip SDRF TSV generation (Stage 6)"
    )

    parser.add_argument(
        "--skip-xi",
        action="store_true",
        help="Skip Xi search engine config generation (Stage 8)"
    )

    parser.add_argument(
        "--sdrf-only",
        action="store_true",
        help=(
            "Generate the SDRF TSV (and validate it) from cached data only. "
            "Does not run any download, LLM, or Xi config stages. "
            "Useful for projects processed before Stage 6 was added."
        )
    )

    parser.add_argument(
        "--create-prompts",
        action="store_true",
        help="Create default prompt files and exit"
    )
    
    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List available prompts and exit"
    )
    
    parser.add_argument(
        "--save-config",
        default=None,
        help="Save current configuration to YAML file and exit"
    )
    
    parser.add_argument(
        "--log-file",
        default="pxd_enhancer.log",
        metavar="FILE",
        help="Log file path (default: pxd_enhancer.log). Use '' to disable file logging."
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def load_pxd_file(path: str) -> List[str]:
    """
    Load PXD accession IDs from a TSV file.

    The file must have an 'Accession' column (case-insensitive).  Other columns
    are ignored.  Blank rows and comment lines starting with '#' are skipped.

    Args:
        path: Path to the TSV file.

    Returns:
        List of unique PXD accession strings.
    """
    df = pd.read_csv(path, sep="\t", comment="#")
    # Case-insensitive column lookup
    col_map = {c.lower(): c for c in df.columns}
    if "accession" not in col_map:
        raise ValueError(
            f"TSV file '{path}' has no 'Accession' column. "
            f"Found: {list(df.columns)}"
        )
    accession_col = col_map["accession"]
    pxds = df[accession_col].dropna().astype(str).str.strip()
    pxds = pxds[pxds.str.startswith("PXD")]
    return pxds.unique().tolist()


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level, log_file=args.log_file or "")
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("PXD Metadata Enhancer")
    logger.info("=" * 80)

    # Load configuration
    config = Config(args.config)

    # Override with CLI args
    if args.data_dir:
        config.config["storage"]["base_dir"] = args.data_dir
    if args.prompts_dir:
        config.config["prompts"]["dir"] = args.prompts_dir
    if args.model:
        config.config["llm"]["model"] = args.model

    # Handle special commands
    if args.create_prompts:
        logger.info("Creating default prompts in %s", args.prompts_dir)
        PromptTemplates.create_default_prompts(args.prompts_dir)
        logger.info("Done!")
        return

    if args.list_prompts:
        prompts = PromptTemplates(args.prompts_dir)
        logger.info("Available prompts:")
        for prompt in prompts.list_prompts():
            logger.info("  - %s", prompt)
        return

    if args.save_config:
        logger.info("Saving configuration to %s", args.save_config)
        config.save_yaml(args.save_config)
        logger.info("Done!")
        return

    # Assemble PXD list from --pxd and/or --pxd-file
    pxds: List[str] = []
    if args.pxd:
        pxds.extend(args.pxd)
    if args.pxd_file:
        try:
            file_pxds = load_pxd_file(args.pxd_file)
            logger.info("Loaded %d PXD(s) from %s", len(file_pxds), args.pxd_file)
            pxds.extend(file_pxds)
        except Exception as exc:
            logger.error("Failed to load PXD file '%s': %s", args.pxd_file, exc)
            sys.exit(1)

    # Deduplicate while preserving order
    seen: set = set()
    pxds = [p for p in pxds if not (p in seen or seen.add(p))]

    if not pxds:
        parser.print_help()
        logger.error("No PXDs specified. Use --pxd or --pxd-file.")
        sys.exit(1)

    # Resolve --nproc
    import os as _os
    nproc_str = str(args.nproc).strip().lower()
    if nproc_str == "auto":
        cpu_count = _os.cpu_count() or 1
        nproc = max(1, cpu_count // max(len(pxds), 1))
        logger.info("--nproc auto → %d workers (cpu_count=%d, pxds=%d)", nproc, cpu_count, len(pxds))
    else:
        try:
            nproc = max(1, int(nproc_str))
        except ValueError:
            logger.error("--nproc must be a positive integer or 'auto', got: %s", args.nproc)
            sys.exit(1)

    # Print batch plan
    logger.info("-" * 80)
    logger.info("Batch plan:")
    logger.info("  PXDs to process  : %d", len(pxds))
    logger.info("  Data directory   : %s", config.get("storage.base_dir"))
    logger.info("  LLM model        : %s", config.get("llm.model"))
    if args.sdrf_only:
        logger.info("  Mode             : SDRF-only (generate from cached data)")
    else:
        logger.info("  No download      : %s", args.no_download)
        logger.info("  Skip spectral    : %s", args.skip_spectral)
        logger.info("  Files/cluster    : %d", args.assessor_files_per_cluster)
        logger.info("  Clean .raw       : %s", args.clean_raw)
        logger.info("  Clean .mzML      : %s", args.clean_mzml)
        logger.info("  File limit       : %s", args.limit or "unlimited")
        logger.info("  aria2c conns     : %d", args.aria2c_connections)
        logger.info("  nproc            : %d", nproc)
        logger.info("  Skip SDRF        : %s", args.skip_sdrf)
        logger.info("  Skip Xi          : %s", args.skip_xi)
    logger.info("-" * 80)

    # Create enhancer
    try:
        logger.info("Initializing PXDMetadataEnhancer...")
        enhancer = PXDMetadataEnhancer(
            base_dir=config.get("storage.base_dir"),
            prompts_dir=config.get("prompts.dir"),
            llm_model=config.get("llm.model"),
        )
        logger.info("Initialization successful!")
    except Exception as e:
        logger.error("Failed to initialize: %s", e, exc_info=True)
        sys.exit(1)

    # Process PXDs
    succeeded = []
    failed = []

    for pxd in pxds:
        try:
            if args.sdrf_only:
                result = enhancer.generate_sdrf(pxd)
            else:
                prompt_keys = args.prompts if args.prompts else None
                result = enhancer.process_pxd(
                    pxd,
                    force_refresh=args.force_refresh,
                    prompt_keys=prompt_keys,
                    no_download=args.no_download,
                    skip_spectral=args.skip_spectral,
                    clean_raw=args.clean_raw,
                    clean_mzml=args.clean_mzml,
                    limit=args.limit,
                    aria2c_connections=args.aria2c_connections,
                    nproc=nproc,
                    assessor_files_per_cluster=args.assessor_files_per_cluster,
                    skip_sdrf=args.skip_sdrf,
                    skip_xi=args.skip_xi,
                )
            succeeded.append(pxd)
            logger.info("✓ %s — stages: %s", pxd, result.get("stages", {}))

        except Exception as e:
            failed.append(pxd)
            logger.error("✗ %s failed: %s", pxd, e, exc_info=args.verbose)
            continue

    logger.info("=" * 80)
    logger.info(
        "Processing complete: %d succeeded, %d failed",
        len(succeeded), len(failed),
    )
    if failed:
        logger.warning("Failed PXDs: %s", ", ".join(failed))
    logger.info("Data saved to: %s", config.get("storage.base_dir"))
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
