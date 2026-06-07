"""
Configuration module for PXDMetadataEnhancer
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Config:
    """Configuration management"""
    
    DEFAULT_CONFIG = {
        "pride": {
            "base_url": "https://www.ebi.ac.uk/pride/ws/archive/v3",
            "timeout": 30
        },
        "pmc": {
            "email": None,
            "api_key": None
        },
        "ncbi": {
            "email": None,
            "api_key": None,
            "timeout": 10
        },
        "llm": {
            "model": "gpt-4-turbo",
            "temperature": 0.3,
            "max_retries": 3
        },
        "storage": {
            "base_dir": "./pxd_data",
            "cache_pride": True,
            "cache_pmc": True,
            "cache_llm": True
        },
        "prompts": {
            "dir": "./prompts",
            "enabled": ["organism", "disease", "experimental_design", "quantification", "key_findings"]
        },
        "download": {
            "aria2c_connections": 16,   # TCP connections per file (--max-connection-per-server)
            "clean_raw": False,         # Delete .raw after thermorawfileparser
            "clean_mzml": False         # Delete .mzML after mzML_assessor
        },
        "assessment": {
            "skip_spectral": False,                          # Skip mzML conversion + mzML_assessor
            "assessor_script": "src/assessor/mzML_assessor.py"  # Path to mzML_assessor script
        },
        "sdrf": {
            "skip_sdrf": False,           # Skip SDRF generation stage
            "template": "crosslinking"    # SDRF template type for parse_sdrf validation
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Load configuration
        
        Args:
            config_path: Path to config YAML file (optional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path and Path(config_path).exists():
            self.load_yaml(config_path)
            logger.info(f"Loaded config from {config_path}")
    
    def load_yaml(self, path: str) -> None:
        """Load configuration from YAML file"""
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        
        # Deep merge user config over defaults
        self._deep_merge(self.config, user_config)
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge override dict into base dict"""
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save_yaml(self, path: str) -> None:
        """Save current configuration to YAML file"""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved config to {path}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation path
        
        Args:
            key_path: Path like "pride.timeout"
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split(".")
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def to_dict(self) -> Dict:
        """Get configuration as dictionary"""
        return self.config.copy()
