#!/usr/bin/env python3
"""
Batch runner for condensate_detection prompt
Processes PXDs using PRIDE metadata + PMC publication text with LLM (no raw file downloads)
"""

import sys
import json
import logging
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pxd_enhancer import PXDMetadataEnhancer
from pxd_enhancer.config import Config
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_condensate_detection(sample_size: int = None, config_path: str = "configs/config_condensate_detection.yaml", resume: bool = False):
    """
    Run condensate_detection prompt on PXDs (LLM-only, no raw downloads)
    
    Args:
        sample_size: Number of PXDs to process (None = all)
        config_path: Path to configuration file
        resume: If True, skip PXDs that have already been processed
    """
    
    # Load the crosslinking datasets subset (CSV format)
    csv_path = Path("assets/crosslinking_datasets_subset.csv")
    if not csv_path.exists():
        logger.error(f"CSV not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    # Column is 'accession' (lowercase) in this file
    all_pxds = df['accession'].tolist()
    
    # If sample_size not specified, process all
    if sample_size is None:
        pxds_to_test = all_pxds
    else:
        pxds_to_test = all_pxds[:sample_size]
    
    # Filter out already-processed if resuming
    if resume:
        pxd_data_dir = Path("pxd_data_condensate")
        already_done = set()
        for pxd_dir in pxd_data_dir.glob("PXD*"):
            if (pxd_dir / "llm" / "responses.json").exists():
                already_done.add(pxd_dir.name)
        
        original_count = len(pxds_to_test)
        pxds_to_test = [p for p in pxds_to_test if p not in already_done]
        logger.info(f"Resume mode: Skipping {original_count - len(pxds_to_test)} already-processed PXDs")
    
    logger.info(f"Processing {len(pxds_to_test)} PXDs with condensate_detection prompt (LLM-only, no raw downloads)")
    
    # Load configuration
    config = Config(config_path=config_path if Path(config_path).exists() else None)
    llm_model = config.config.get("llm", {}).get("model", "gpt-4o-mini-2024-07-18")
    base_dir = config.config.get("storage", {}).get("base_dir", "./pxd_data")
    prompts_dir = config.config.get("prompts", {}).get("dir", "./prompts")
    email = config.config.get("pmc", {}).get("email")
    ncbi_api_key = config.config.get("pmc", {}).get("api_key")
    
    logger.info(f"Using config from {config_path}")
    logger.info(f"  LLM model: {llm_model}")
    logger.info(f"  Base directory: {base_dir}")
    logger.info(f"  Prompts directory: {prompts_dir}")
    
    # Initialize enhancer
    enhancer = PXDMetadataEnhancer(
        base_dir=base_dir,
        prompts_dir=prompts_dir,
        llm_model=llm_model,
        email=email,
        ncbi_api_key=ncbi_api_key,
    )
    logger.info("PXDMetadataEnhancer initialized")
    
    # Process each PXD with condensate_detection prompt only
    results = []
    failed = []
    
    for idx, pxd in enumerate(pxds_to_test, 1):
        logger.info(f"\n[{idx}/{len(pxds_to_test)}] Processing {pxd}")
        
        try:
            # Run LLM-only stage on this PXD with condensate_detection prompt
            metadata = enhancer.process_pxd(
                pxd=pxd,
                force_refresh=False,
                prompt_keys=["condensate_detection"],
                no_download=True,  # Skip raw processing
                skip_sdrf=True,
                skip_xi=True,
            )
            
            # Extract the condensate_detection response
            if metadata and "llm_responses" in metadata and "condensate_detection" in metadata["llm_responses"]:
                response = metadata["llm_responses"]["condensate_detection"]
                
                # Parse JSON response
                try:
                    if isinstance(response, str):
                        response_json = json.loads(response)
                    else:
                        response_json = response
                    
                    result = {
                        "accession": pxd,
                        "condensate_detected": response_json.get("condensate_detected", "unknown"),
                        "confidence": response_json.get("confidence", "unknown"),
                        "evidence_quote": response_json.get("evidence_quote", ""),
                        "evidence_location": response_json.get("evidence_location", ""),
                        "notes": response_json.get("notes", ""),
                    }
                    
                    # Pretty print result
                    logger.info(f"  Result: {result['condensate_detected']} ({result['confidence']})")
                    results.append(result)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response for {pxd}: {e}")
                    failed.append((pxd, str(e)))
            else:
                logger.warning(f"No condensate_detection response found for {pxd}")
                failed.append((pxd, "No response"))
        
        except Exception as e:
            logger.error(f"Error processing {pxd}: {e}")
            failed.append((pxd, str(e)))
    
    # Summary table
    logger.info(f"\n\n{'='*80}")
    logger.info("PROCESSING COMPLETE")
    logger.info('='*80)
    logger.info(f"Processed: {len(results)}")
    logger.info(f"Failed: {len(failed)}")
    
    if failed:
        logger.warning("Failed PXDs:")
        for pxd, error in failed:
            logger.warning(f"  {pxd}: {error}")
    
    if results:
        summary_df = pd.DataFrame(results)
        logger.info("\nResults breakdown:")
        logger.info(summary_df['condensate_detected'].value_counts().to_string())
        logger.info("\nConfidence breakdown:")
        logger.info(summary_df['condensate_confidence'].value_counts().to_string())
        
        # Save to temporary file for review
        output_file = Path("test_condensate_results.csv")
        summary_df.to_csv(output_file, index=False)
        logger.info(f"\nResults saved to {output_file}")
    else:
        logger.warning("No results to summarize")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run condensate_detection prompt (LLM-only, no raw downloads)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process first 5 PXDs (default)
  python scripts/test_condensate_detection.py
  
  # Process first 100 PXDs
  python scripts/test_condensate_detection.py --sample-size 100
  
  # Process all 1045 PXDs
  python scripts/test_condensate_detection.py --sample-size all
  
  # Resume from where you left off
  python scripts/test_condensate_detection.py --sample-size all --resume
        """
    )
    parser.add_argument(
        "--sample-size",
        type=str,
        default="5",
        help="Number of PXDs to process, or 'all' (default: 5)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/config_condensate_detection.yaml",
        help="Config file path (default: configs/config_condensate_detection.yaml)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip PXDs already processed (for resuming interrupted runs)"
    )
    
    args = parser.parse_args()
    
    # Parse sample_size
    if args.sample_size.lower() == "all":
        sample_size = None
    else:
        try:
            sample_size = int(args.sample_size)
        except ValueError:
            logger.error(f"Invalid sample-size: {args.sample_size}. Use an integer or 'all'.")
            sys.exit(1)
    
    test_condensate_detection(sample_size=sample_size, config_path=args.config, resume=args.resume)
