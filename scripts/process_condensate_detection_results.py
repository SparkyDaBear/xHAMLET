#!/usr/bin/env python3
"""
Post-processing script for condensate_detection results
Parses cached LLM responses and generates output CSV
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_condensate_response(llm_data_dict) -> Optional[Dict]:
    """
    Parse LLM response for condensate_detection prompt
    
    Args:
        llm_data_dict: Dict from responses.json["data"] containing parsed field data
        
    Returns:
        Parsed dict with keys: condensate_detected, confidence, evidence_quote, evidence_location, notes
        or None if parsing failed
    """
    try:
        # Extract from nested structure
        condensate = llm_data_dict.get("condensate_detected", {})
        confidence = llm_data_dict.get("confidence", {})
        evidence_quote = llm_data_dict.get("evidence_quote", {})
        evidence_location = llm_data_dict.get("evidence_location", {})
        notes = llm_data_dict.get("notes", {})
        
        return {
            "condensate_detected": condensate.get("parsed", {}).get("value", "unknown"),
            "confidence": confidence.get("parsed", {}).get("value", "unknown"),
            "evidence_quote": evidence_quote.get("parsed", {}).get("value", ""),
            "evidence_location": evidence_location.get("parsed", {}).get("value", ""),
            "notes": notes.get("parsed", {}).get("value", ""),
        }
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to parse response: {e}")
        return None


def extract_results_from_cache(pxd_data_dir: str = "pxd_data") -> Dict[str, Dict]:
    """
    Extract condensate_detection results from cached LLM responses
    
    Args:
        pxd_data_dir: Base directory where PXD data is stored
        
    Returns:
        Dict mapping PXD accession to parsed result dict
    """
    pxd_path = Path(pxd_data_dir)
    results = {}
    
    # Iterate over all PXD directories
    for pxd_dir in sorted(pxd_path.glob("PXD*")):
        if not pxd_dir.is_dir():
            continue
        
        pxd_accession = pxd_dir.name
        llm_responses_file = pxd_dir / "llm" / "responses.json"
        
        if not llm_responses_file.exists():
            logger.debug(f"No LLM responses found for {pxd_accession}")
            continue
        
        try:
            with open(llm_responses_file, 'r', encoding='utf-8') as f:
                responses = json.load(f)
            
            # Check if condensate_detection response exists in the data section
            llm_data = responses.get("data", {})
            if llm_data and "condensate_detected" in llm_data:
                parsed = parse_condensate_response(llm_data)
                if parsed:
                    results[pxd_accession] = parsed
                    logger.info(f"Extracted results for {pxd_accession}: {parsed['condensate_detected']} ({parsed['confidence']})")
                else:
                    logger.warning(f"Failed to parse response for {pxd_accession}")
            else:
                logger.debug(f"No condensate_detection response in {pxd_accession}")
        
        except Exception as e:
            logger.error(f"Error processing {pxd_accession}: {e}")
    
    logger.info(f"Extracted results for {len(results)} PXDs")
    return results


def merge_with_original_csv(
    results: Dict[str, Dict],
    csv_path: str = "assets/crosslinking_datasets_subset.csv",
    output_path: str = "condensate_detection_results.csv"
) -> pd.DataFrame:
    """
    Merge extracted results with original CSV and generate output
    
    Args:
        results: Dict of extracted condensate detection results
        csv_path: Path to original CSV file
        output_path: Where to save output CSV
        
    Returns:
        DataFrame with merged results
    """
    # Load original CSV
    if not Path(csv_path).exists():
        logger.error(f"CSV not found: {csv_path}")
        return pd.DataFrame()
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} PXDs from {csv_path}")
    
    # Create result columns
    df['condensate_detected'] = df['accession'].map(
        lambda x: results.get(x, {}).get('condensate_detected', 'not_processed')
    )
    df['condensate_confidence'] = df['accession'].map(
        lambda x: results.get(x, {}).get('confidence', '')
    )
    df['condensate_evidence_quote'] = df['accession'].map(
        lambda x: results.get(x, {}).get('evidence_quote', '')
    )
    df['condensate_evidence_location'] = df['accession'].map(
        lambda x: results.get(x, {}).get('evidence_location', '')
    )
    df['condensate_notes'] = df['accession'].map(
        lambda x: results.get(x, {}).get('notes', '')
    )
    
    # Save output
    df.to_csv(output_path, index=False)
    logger.info(f"Saved merged results to {output_path}")
    
    # Print statistics
    processed = df[df['condensate_detected'] != 'not_processed']
    logger.info(f"\n{'='*80}")
    logger.info("RESULTS SUMMARY")
    logger.info('='*80)
    logger.info(f"Total PXDs in subset: {len(df)}")
    logger.info(f"Processed PXDs: {len(processed)}")
    logger.info(f"Not yet processed: {len(df) - len(processed)}")
    
    if len(processed) > 0:
        logger.info(f"\nBreakdown (processed only):")
        summary = processed['condensate_detected'].value_counts()
        for detection, count in summary.items():
            logger.info(f"  {detection}: {count}")
        
        logger.info(f"\nConfidence breakdown:")
        conf_summary = processed['condensate_confidence'].value_counts()
        for conf, count in conf_summary.items():
            if conf:  # Skip empty
                logger.info(f"  {conf}: {count}")
    
    return df


def main(
    pxd_data_dir: str = "pxd_data",
    csv_path: str = "assets/crosslinking_datasets_subset.csv",
    output_path: str = "condensate_detection_results.csv"
):
    """
    Main function: extract results and generate output CSV
    
    Args:
        pxd_data_dir: Base directory for PXD cached data
        csv_path: Path to original CSV
        output_path: Path for output CSV
    """
    logger.info("Starting post-processing of condensate_detection results")
    logger.info(f"PXD data directory: {pxd_data_dir}")
    logger.info(f"Input CSV: {csv_path}")
    logger.info(f"Output CSV: {output_path}")
    
    # Extract from cache
    results = extract_results_from_cache(pxd_data_dir)
    
    # Merge and save
    output_df = merge_with_original_csv(results, csv_path, output_path)
    
    logger.info(f"\n{'='*80}")
    logger.info("POST-PROCESSING COMPLETE")
    logger.info(f"Output saved to: {output_path}")
    
    # Print first few rows
    if len(output_df) > 0:
        logger.info("\nFirst 10 rows of output:")
        cols_to_show = ['accession', 'pubmed_id', 'organism', 'condensate_detected', 'condensate_confidence']
        logger.info("\n" + output_df[cols_to_show].head(10).to_string(index=False))


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Post-process condensate_detection results from cached LLM responses"
    )
    parser.add_argument(
        "--pxd-data-dir",
        type=str,
        default="pxd_data_condensate",
        help="Base directory for PXD data (default: pxd_data_condensate)"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="assets/crosslinking_datasets_subset.csv",
        help="Path to input CSV (default: assets/crosslinking_datasets_subset.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="condensate_detection_results.csv",
        help="Path for output CSV (default: condensate_detection_results.csv)"
    )
    
    args = parser.parse_args()
    main(pxd_data_dir=args.pxd_data_dir, csv_path=args.csv, output_path=args.output)
