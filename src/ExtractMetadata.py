#!/usr/bin/env python3
"""
Development test script for the xHAMLET pipeline.
For batch processing use main.py instead.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pxd_enhancer import PXDMetadataEnhancer
from pxd_enhancer.prompt_templates import PromptTemplates

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    ## Credentials from environment variables (never hardcode)
    email       = os.environ.get("NCBI_EMAIL", "")
    ncbi_api_key = os.environ.get("NCBI_API_KEY", "")

    if not email:
        logger.warning("NCBI_EMAIL not set. DOI-based PMID lookup will be unavailable.")

    ## PXD list — edit here or switch to the TSV loader in main.py
    pxds = ["PXD017620"]

    # Initialise prompts once
    PromptTemplates.create_default_prompts("./prompts")
    logger.info("Prompts initialised")

    # Initialise enhancer once outside the loop
    enhancer = PXDMetadataEnhancer(
        base_dir="./pxd_data",
        prompts_dir="./prompts",
        email=email,
        ncbi_api_key=ncbi_api_key,
    )
    logger.info("PXDMetadataEnhancer initialised")

    failed = []
    for pxd in pxds:
        logger.info("Processing %s", pxd)
        try:
            result = enhancer.process_pxd(pxd, force_refresh=True)

            logger.info("Stages: %s", result.get("stages", {}))
            logger.info("Output: pxd_data/%s/enhanced/metadata.json", pxd)
            logger.info("✓ %s processed successfully", pxd)

        except Exception as e:
            logger.error("✗ Failed to process %s: %s", pxd, e, exc_info=True)
            failed.append(pxd)

    if failed:
        logger.warning("Failed PXDs (%d): %s", len(failed), ", ".join(failed))

    


if __name__ == "__main__":
    sys.exit(main())
