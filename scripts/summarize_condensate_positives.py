#!/usr/bin/env python3
"""
Summarize PXDs with positive condensate detection results.
Reads responses.json files and reports all "yes" cases with full response details.
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_positive_condensate_studies(base_dir: str = "pxd_data_condensate") -> List[Tuple[str, dict]]:
    """
    Find all PXDs with qualifying_condensate_xlms_dataset.parsed.value == "yes"
    
    Args:
        base_dir: Base directory containing PXD subdirectories
        
    Returns:
        List of tuples: (pxd_name, full_response_dict)
    """
    base_path = Path(base_dir)
    positives = []
    
    if not base_path.exists():
        logger.error(f"Base directory not found: {base_path}")
        return positives
    
    # Find all PXD*/llm/responses.json files
    response_files = sorted(base_path.glob("PXD*/llm/responses.json"))
    logger.info(f"Found {len(response_files)} response files in {base_dir}")
    
    for response_file in response_files:
        pxd_name = response_file.parent.parent.name
        
        try:
            with open(response_file, 'r') as f:
                data = json.load(f)
            
            # Navigate to qualifying_condensate_xlms_dataset
            if "data" in data and "qualifying_condensate_xlms_dataset" in data["data"]:
                xlms_data = data["data"]["qualifying_condensate_xlms_dataset"]
                
                # Check if parsed.value == "yes"
                if xlms_data.get("parsed", {}).get("value") == "yes":
                    logger.info(f"✓ {pxd_name}: POSITIVE for condensate XL-MS")
                    positives.append((pxd_name, xlms_data))
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON in {response_file}: {e}")
        except Exception as e:
            logger.error(f"Error processing {response_file}: {e}")
    
    return positives


def print_positive_summary(positives: List[Tuple[str, dict]]):
    """
    Print detailed summary of positive condensate studies
    
    Args:
        positives: List of (pxd_name, response_dict) tuples
    """
    print(f"\n{'='*100}")
    print(f"CONDENSATE XL-MS POSITIVE STUDIES")
    print(f"{'='*100}")
    print(f"Total positives found: {len(positives)}\n")
    
    for idx, (pxd_name, xlms_data) in enumerate(positives, 1):
        print(f"\n{'-'*100}")
        print(f"[{idx}] {pxd_name}")
        print(f"{'-'*100}")
        
        # Extract model and response
        model = xlms_data.get("model", "unknown")
        response_str = xlms_data.get("response", "")
        
        print(f"Model: {model}")
        print(f"Confidence: {xlms_data.get('parsed', {}).get('value', 'N/A')}")
        
        # Try to parse the response as JSON to pretty-print it
        try:
            if isinstance(response_str, str):
                response_json = json.loads(response_str)
            else:
                response_json = response_str
            
            print(f"\nResponse (parsed JSON):")
            print(json.dumps(response_json, indent=2))
        except (json.JSONDecodeError, TypeError):
            print(f"\nResponse (raw):")
            print(response_str)
    
    print(f"\n{'='*100}")
    print(f"END OF REPORT")
    print(f"{'='*100}\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Summarize PXDs with positive condensate detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find and display all positive condensate studies
  python scripts/summarize_condensate_positives.py
  
  # Use alternative base directory
  python scripts/summarize_condensate_positives.py --base-dir pxd_data_condensate
        """
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="pxd_data_condensate",
        help="Base directory containing PXD subdirectories (default: pxd_data_condensate)"
    )
    
    args = parser.parse_args()
    
    # Find positive studies
    positives = find_positive_condensate_studies(base_dir=args.base_dir)
    
    # Print summary
    if positives:
        print_positive_summary(positives)
        return 0
    else:
        print(f"\nNo positive condensate XL-MS studies found in {args.base_dir}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
