"""
Data storage and retrieval for cached API responses and processed data
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class DataStore:
    """Manages local storage of PRIDE, PMC, and LLM data"""
    
    def __init__(self, base_dir: str = "./pxd_data"):
        """
        Initialize data store
        
        Args:
            base_dir: Base directory for storing PXD data
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"DataStore initialized at {self.base_dir}")
    
    def get_pxd_dir(self, pxd: str) -> Path:
        """Get the directory for a specific PXD"""
        pxd_dir = self.base_dir / pxd
        pxd_dir.mkdir(parents=True, exist_ok=True)
        return pxd_dir
    
    def get_subdirs(self, pxd: str) -> Dict[str, Path]:
        """Get all subdirectories for a PXD"""
        pxd_dir = self.get_pxd_dir(pxd)
        subdirs = {
            "pride": pxd_dir / "pride",
            "pmc": pxd_dir / "pmc",
            "ncbi": pxd_dir / "ncbi",
            "llm": pxd_dir / "llm",
            "enhanced": pxd_dir / "enhanced",
            "assessment": pxd_dir / "assessment",  # thermorawfileparser + mzML_assessor JSON outputs
            "sdrf": pxd_dir / "sdrf",              # generated SDRF TSV files
        }
        for subdir in subdirs.values():
            subdir.mkdir(parents=True, exist_ok=True)
        return subdirs

    def get_work_dir(self, pxd: str) -> Path:
        """
        Return (and create) the transient work/ directory for raw/mzML files.
        This is NOT a JSON storage category — managed by RawFileProcessor.
        """
        work_dir = self.get_pxd_dir(pxd) / "work"
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir
    
    def save_json(self, data: Dict[str, Any], pxd: str, category: str, filename: str) -> Path:
        """
        Save JSON data with metadata
        
        Args:
            data: Data to save
            pxd: PRIDE project accession
            category: Category (pride, pmc, llm, enhanced)
            filename: Filename (without .json)
            
        Returns:
            Path to saved file
        """
        subdirs = self.get_subdirs(pxd)
        
        if category not in subdirs:
            raise ValueError(f"Invalid category: {category}. Must be one of {list(subdirs.keys())}")
        
        filepath = subdirs[category] / f"{filename}.json"
        
        # Add metadata
        payload = {
            "metadata": {
                "pxd": pxd,
                "category": category,
                "saved_at": datetime.now().isoformat(),
                "filename": filename
            },
            "data": data
        }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {category} data to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save JSON to {filepath}: {e}")
            raise
    
    def load_json(self, pxd: str, category: str, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load JSON data
        
        Args:
            pxd: PRIDE project accession
            category: Category (pride, pmc, llm, enhanced)
            filename: Filename (without .json)
            
        Returns:
            Data dict or None if file not found
        """
        subdirs = self.get_subdirs(pxd)
        filepath = subdirs[category] / f"{filename}.json"
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
            logger.info(f"Loaded {category} data from {filepath}")
            return payload.get("data")
        except Exception as e:
            logger.error(f"Failed to load JSON from {filepath}: {e}")
            return None
    
    def load_full_json(self, pxd: str, category: str, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load full JSON including metadata
        
        Args:
            pxd: PRIDE project accession
            category: Category (pride, pmc, llm, enhanced)
            filename: Filename (without .json)
            
        Returns:
            Full payload dict or None if file not found
        """
        subdirs = self.get_subdirs(pxd)
        filepath = subdirs[category] / f"{filename}.json"
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
            logger.info(f"Loaded full {category} data from {filepath}")
            return payload
        except Exception as e:
            logger.error(f"Failed to load JSON from {filepath}: {e}")
            return None
    
    def file_exists(self, pxd: str, category: str, filename: str) -> bool:
        """Check if a file exists"""
        subdirs = self.get_subdirs(pxd)
        filepath = subdirs[category] / f"{filename}.json"
        return filepath.exists()
    
    def list_pxds(self) -> list:
        """List all PXDs with stored data"""
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]
    
    def compile_pxd_summary(self, pxd: str) -> Dict[str, Any]:
        """
        Compile all data for a PXD into a single summary dict
        
        Args:
            pxd: PRIDE project accession
            
        Returns:
            Summary dict with pride, pmc, and llm sections
        """
        summary = {
            "pxd": pxd,
            "compiled_at": datetime.now().isoformat(),
            "pride": self.load_json(pxd, "pride", "project_details"),
            "pmc": self.load_json(pxd, "pmc", "full_text"),
            "llm_responses": self.load_json(pxd, "llm", "responses")
        }
        return summary
    
    def save_pxd_summary(self, pxd: str) -> Path:
        """
        Save compiled summary for a PXD
        
        Args:
            pxd: PRIDE project accession
            
        Returns:
            Path to saved summary file
        """
        summary = self.compile_pxd_summary(pxd)
        subdirs = self.get_subdirs(pxd)
        summary_path = subdirs["enhanced"] / "summary.json"
        
        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved summary to {summary_path}")
            return summary_path
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
            raise
