"""
Xi Config File Generator
Generates Xi search engine configuration files for crosslinking and linear analyses
based on PRIDE metadata and LLM-extracted sample information.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class XiConfigGenerator:
    """Generate Xi configuration files from PXD metadata"""
    
    # Base template with common parameters across all configs
    BASE_TEMPLATE = """####################
##Tolerances
tolerance:precursor:10ppm
tolerance:fragment:20ppm

####################
## include linear matches
EVALUATELINEARS:true

{crosslinker_section}

##========================
##--Fixed Modifications
modification:fixed::SYMBOLEXT:cm;MODIFIED:C;DELTAMASS:57.021464

##========================
##--Variable Modifications
{variable_modifications}

###################
## Digest
{digestion_section}

#####################################################################################################
##Fragment match settings

####################
## Non-Lossy Fragments to consider
fragment:BIon
fragment:YIon
## peptide ion should always be enabled, as otherwise no standard cross-linked fragments will be matched - also needed for precoursor-fragment matches
fragment:PeptideIon

###################
## Losses
loss:AminoAcidRestrictedLoss:NAME:H20;aminoacids:S,T,D,E;MASS:18.01056027;cterm
loss:AminoAcidRestrictedLoss:NAME:NH3;aminoacids:R,K,N,Q;MASS:17.02654493;nterm
loss:AIonLoss

#####################
## Generally lossy fragmenst will have a smaller impact on subscores then non-lossy versions of a fragment.
## But some subscores (anything called conservative) considere a fragment observed even if n neutral losses for that fragment where observed but not the fragment itself 
## this defines how many loses are needed to make a fragment count as observed
ConservativeLosses:3

####################
## isotop annotation
IsotopPattern:Averagin

####################
# if this is set to true also fragment matches are reported that are of by 1 dalton
# default: true
MATCH_MISSING_MONOISOTOPIC:true

########################################
## consider also matches to a precursor mass that
## are up to n Dalton (actually n*1.00335 Da) lighter
## this would account for missing isotope peaks in the MS1
missing_isotope_peaks:2

####################
## how many peaks to consider for mgc-search
mgcpeaks:10

###################
### Candidate selection
topmgchits:150
## how many combinations of alpha and beta peptides will be considered for final scoreing
topmgxhits:10

##################
## how many misscleavages are considered
missedcleavages:1

####################
## define a minimum peptide length (default 2)
MINIMUM_PEPTIDE_LENGTH:6

#####################
## IO-settings
BufferInput:100
BufferOutput:100

#####################
## Only write out the top match per spectrum
## defaults: false
TOPMATCHESONLY:{topmatchesonly}

#####################
## maximum mass of a peptide to be considered for fragmentation
## Default: 1.7976931348623157e+308
## the value will be lowered to the maximum found precoursor mass in the peak-list
MAXPEPTIDEMASS:4000

#####################
## some limits for generating modified peptides
## default: 3 and 20
MAX_MODIFICATION_PER_PEPTIDE:3
MAX_MODIFIED_PEPTIDES_PER_PEPTIDE:20

################
## Fragment Tree
FRAGMENTTREE:FU
"""

    def __init__(self, crosslinker_defs_path: Optional[str] = None, quencher_defs_path: Optional[str] = None):
        """
        Initialize the Xi config generator
        
        Args:
            crosslinker_defs_path: Path to crosslinker definitions JSON file.
                                   If None, uses assets/crosslinker_definitions.json
            quencher_defs_path: Path to quencher definitions JSON file.
                               If None, uses assets/quencher_definitions.json
        """
        if crosslinker_defs_path is None:
            # Try to find the default location
            workspace_root = Path(__file__).parent.parent.parent
            crosslinker_defs_path = workspace_root / "assets" / "crosslinker_definitions.json"
        
        if quencher_defs_path is None:
            # Try to find the default location
            workspace_root = Path(__file__).parent.parent.parent
            quencher_defs_path = workspace_root / "assets" / "quencher_definitions.json"
        
        self.crosslinker_defs_path = Path(crosslinker_defs_path)
        self.quencher_defs_path = Path(quencher_defs_path)
        self.crosslinkers = self._load_crosslinker_definitions()
        self.quenchers = self._load_quencher_definitions()
        logger.info(f"Loaded {len(self.crosslinkers)} crosslinker definitions from {self.crosslinker_defs_path}")
        logger.info(f"Loaded {len(self.quenchers)} quencher definitions from {self.quencher_defs_path}")
    
    def _load_crosslinker_definitions(self) -> Dict[str, dict]:
        """Load crosslinker definitions from JSON file"""
        if not self.crosslinker_defs_path.exists():
            logger.warning(f"Crosslinker definitions file not found: {self.crosslinker_defs_path}")
            return {}
        
        try:
            with open(self.crosslinker_defs_path, "r") as f:
                data = json.load(f)
            
            # Create a lookup dict by name and aliases
            crosslinkers = {}
            for xl in data.get("crosslinkers", []):
                # Add by main name
                crosslinkers[xl["name"].lower()] = xl
                # Add by short name
                if "short_name" in xl:
                    crosslinkers[xl["short_name"].lower()] = xl
                # Add by aliases
                for alias in xl.get("aliases", []):
                    crosslinkers[alias.lower()] = xl
            
            return crosslinkers
        except Exception as e:
            logger.error(f"Failed to load crosslinker definitions: {e}")
            return {}
    
    def _load_quencher_definitions(self) -> Dict[str, dict]:
        """Load quencher definitions from JSON file"""
        if not self.quencher_defs_path.exists():
            logger.warning(f"Quencher definitions file not found: {self.quencher_defs_path}")
            return {}
        
        try:
            with open(self.quencher_defs_path, "r") as f:
                data = json.load(f)
            
            # Create a lookup dict by name and aliases
            quenchers = {}
            for qnch in data.get("quenchers", []):
                # Add by main name
                quenchers[qnch["name"].lower()] = qnch
                # Add by aliases
                for alias in qnch.get("aliases", []):
                    quenchers[alias.lower()] = qnch
            
            return quenchers
        except Exception as e:
            logger.error(f"Failed to load quencher definitions: {e}")
            return {}
    
    def get_crosslinker(self, name: str) -> Optional[dict]:
        """
        Get crosslinker definition by name (case-insensitive)
        Handles full names with abbreviations in parentheses, e.g., "Bis(sulfosuccinimidyl)suberate (BS3)"
        
        Args:
            name: Name or alias of the crosslinker
            
        Returns:
            Crosslinker definition dict or None
        """
        if not name:
            return None
        
        # Ensure we have a string (handle dict or other types gracefully)
        if not isinstance(name, str):
            logger.warning(f"Crosslinker name is not a string: {type(name)} - {name}")
            return None
        
        name_lower = name.lower()
        
        # First try direct lookup
        if name_lower in self.crosslinkers:
            return self.crosslinkers[name_lower]
        
        # If not found, try extracting abbreviation from parentheses 
        # e.g., "Bis(sulfosuccinimidyl)suberate (BS3)" -> extract "BS3"
        import re
        match = re.search(r'\(([A-Za-z0-9\-]+)\)$', name)
        if match:
            abbrev = match.group(1).lower()
            logger.debug(f"Extracted abbreviation '{abbrev}' from '{name}'")
            if abbrev in self.crosslinkers:
                return self.crosslinkers[abbrev]
        
        return None
    
    def _parse_crosslinker_from_llm(self, llm_response: dict) -> Optional[dict]:
        """
        Parse crosslinker info from LLM response (comment_cross_linker)
        
        Args:
            llm_response: Dictionary from llm_responses["comment_cross_linker"]
            
        Returns:
            Dict with 'name', 'targets', 'cleavable' keys or None
        """
        if not llm_response:
            return None
        
        # LLM should return parsed data with NT, TA, CL keys
        parsed = llm_response.get("parsed", {})
        if not parsed:
            # Fallback: try to extract from serialized string
            serialized = llm_response.get("serialized")
            if serialized:
                return self._parse_serialized_crosslinker(serialized)
            return None
        
        # Extract and validate crosslinker name
        xl_name = parsed.get("NT")
        if not xl_name or xl_name == "null":
            logger.warning("No valid crosslinker name in LLM response")
            return None
        
        return {
            "name": xl_name,
            "targets": parsed.get("TA"),
            "cleavable": parsed.get("CL") == "yes",
            "raw": parsed
        }
    
    def _parse_serialized_crosslinker(self, serialized: str) -> dict:
        """Parse NT=...;AC=...;CL=... format"""
        result = {}
        for part in serialized.split(";"):
            if "=" in part:
                key, value = part.split("=", 1)
                result[key.strip()] = value.strip()
        return result
    
    def _parse_quencher_from_llm(self, llm_response: dict) -> Optional[str]:
        """
        Extract quencher name from LLM response (comment_quenching_reagent)
        
        Args:
            llm_response: Dictionary from llm_responses["comment_quenching_reagent"]
            
        Returns:
            Quencher name (normalized) or None
        """
        if not llm_response:
            return None
        
        # Try to get from parsed data first
        parsed = llm_response.get("parsed", {})
        value = parsed.get("value") or llm_response.get("value")
        
        if not value:
            return None
        
        # Handle list of dicts (common format where multiple quenchers are listed)
        if isinstance(value, list):
            if len(value) > 0:
                # Get the first quencher
                first_item = value[0]
                if isinstance(first_item, dict):
                    # Try to get 'quenching_reagent' or 'reagent' key
                    value = first_item.get("quenching_reagent") or first_item.get("reagent") or str(first_item)
                else:
                    value = str(first_item)
        
        # If value is a dict with 'quenching_reagent', 'reagent' or 'value' key (nested)
        if isinstance(value, dict):
            if "quenching_reagent" in value:
                value = value["quenching_reagent"]
            elif "reagent" in value:
                value = value["reagent"]
            elif "value" in value:
                value = value["value"]
            else:
                value = str(value)
        
        if not isinstance(value, str):
            value = str(value)
        
        # Normalize: strip whitespace, convert en-dashes to regular dashes, lowercase
        value = value.strip().lower()
        value = value.replace("–", "-")  # en-dash to regular dash
        value = value.replace("—", "-")  # em-dash to regular dash
        
        # Extract just the quencher name from strings like "20 mm tris-hcl ph 8.0" or "20 mM Tris-HCl pH 8.0"
        # Remove concentrations (mM, mm, M, µM, etc.) and pH specifications
        quencher_name = value
        
        # Remove leading concentration: e.g., "20 mm " from "20 mm tris-hcl ph 8.0"
        import re
        quencher_name = re.sub(r'^[\d\.\s]*m[mµ]?\s*', '', quencher_name).strip()
        
        # Remove trailing pH info: e.g., " ph 8.0" -> ""
        quencher_name = re.sub(r'\s*ph[\s=]*[\d\.]+$', '', quencher_name).strip()
        quencher_name = re.sub(r'\s*pH[\s=]*[\d\.]+$', '', quencher_name).strip()
        
        # Split by common delimiters to get just the compound name
        # e.g., "tris-hcl, 20 mm" -> "tris-hcl"
        quencher_name = quencher_name.split(",")[0].strip()
        
        # Remove trailing "at ph X" pattern ONLY with word boundary (e.g., "tris at ph 8" -> "tris")
        # Must use word boundary \b to avoid matching "at" inside words like "bicarbonate"
        quencher_name = re.sub(r'\s+\bat\b\s+.*$', '', quencher_name).strip()
        
        if not quencher_name:
            return None
        
        logger.debug(f"Extracted quencher name: {quencher_name}")
        return quencher_name
    
    def _parse_digestion_from_llm(self, llm_response: dict) -> List[str]:
        """
        Parse digestion enzymes from LLM response (comment_cleavage_agent_details)
        
        Args:
            llm_response: Dictionary from llm_responses["comment_cleavage_agent_details"]
            
        Returns:
            List of digestion enzyme definitions (Xi format)
        """
        if not llm_response:
            return self._get_default_digestion()
        
        parsed = llm_response.get("parsed", {})
        value = parsed.get("value") or llm_response.get("value")
        
        if not value:
            return self._get_default_digestion()
        
        # Convert enzyme names to Xi digestion format
        enzymes = []
        
        # Handle single dict or list of dicts with 'enzyme_name' field
        if isinstance(value, list):
            # If list contains dicts with enzyme_name field
            if value and isinstance(value[0], dict):
                for enzyme_obj in value:
                    if isinstance(enzyme_obj, dict):
                        enzyme_name = enzyme_obj.get("enzyme_name", "").lower().strip()
                    else:
                        enzyme_name = str(enzyme_obj).lower().strip()
                    
                    if not enzyme_name:
                        continue
                    
                    # Map enzyme names to Xi format
                    if "tryp" in enzyme_name:
                        enzymes.append(
                            "digestion:PostAAConstrainedDigestion:DIGESTED:K,R;ConstrainingAminoAcids:P;NAME=Trypsin"
                        )
                    elif "lys" in enzyme_name or "lysc" in enzyme_name:
                        enzymes.append(
                            "digestion:PostAAConstrainedDigestion:DIGESTED:K;ConstrainingAminoAcids:P;NAME=Lys-C"
                        )
                    elif "peps" in enzyme_name:
                        enzymes.append(
                            "digestion:PostAAConstrainedDigestion:DIGESTED:F,L,W;ConstrainingAminoAcids:P;NAME=Pepsin"
                        )
                    elif "chym" in enzyme_name:
                        enzymes.append(
                            "digestion:PostAAConstrainedDigestion:DIGESTED:F,L,W,Y;ConstrainingAminoAcids:P;NAME=Chymotrypsin"
                        )
                    elif "glu" in enzyme_name:
                        enzymes.append(
                            "digestion:PostAAConstrainedDigestion:DIGESTED:D,E;ConstrainingAminoAcids:P;NAME=Glu-C"
                        )
                    elif "asp" in enzyme_name:
                        enzymes.append(
                            "digestion:PostAAConstrainedDigestion:DIGESTED:D;ConstrainingAminoAcids:P;NAME=Asp-N"
                        )
            else:
                # List of strings
                for enzyme_spec in value:
                    if not isinstance(enzyme_spec, str):
                        enzyme_spec = str(enzyme_spec)
                    enzyme_name = enzyme_spec.lower().strip()
                    
                    if "tryp" in enzyme_name:
                        enzymes.append(
                            "digestion:PostAAConstrainedDigestion:DIGESTED:K,R;ConstrainingAminoAcids:P;NAME=Trypsin"
                        )
                    elif "lys" in enzyme_name or "lysc" in enzyme_name:
                        enzymes.append(
                            "digestion:PostAAConstrainedDigestion:DIGESTED:K;ConstrainingAminoAcids:P;NAME=Lys-C"
                        )
        elif isinstance(value, str):
            # Single string
            enzyme_name = value.lower().strip()
            if "tryp" in enzyme_name:
                enzymes.append(
                    "digestion:PostAAConstrainedDigestion:DIGESTED:K,R;ConstrainingAminoAcids:P;NAME=Trypsin"
                )
            elif "lys" in enzyme_name or "lysc" in enzyme_name:
                enzymes.append(
                    "digestion:PostAAConstrainedDigestion:DIGESTED:K;ConstrainingAminoAcids:P;NAME=Lys-C"
                )
        
        # Return either found enzymes or default
        if enzymes:
            return enzymes
        return self._get_default_digestion()
    
    def _get_default_digestion(self) -> List[str]:
        """Return default digestion (Trypsin + Lys-C)"""
        return [
            "digestion:PostAAConstrainedDigestion:DIGESTED:K,R;ConstrainingAminoAcids:P;NAME=Trypsin",
            "digestion:PostAAConstrainedDigestion:DIGESTED:K;ConstrainingAminoAcids:P;NAME=Lys-C"
        ]
    
    def _get_variable_modifications_for_crosslinker(
        self, 
        crosslinker_name: str,
        quencher_name: Optional[str] = None
    ) -> List[str]:
        """
        Get variable modifications for a specific crosslinker with optional quencher
        
        Args:
            crosslinker_name: Name of the crosslinker
            quencher_name: Name of the quencher (optional)
            
        Returns:
            List of modification definitions
        """
        # Defensive check
        if not isinstance(crosslinker_name, str):
            logger.error(f"crosslinker_name is not a string: {type(crosslinker_name)} - {crosslinker_name}")
            return ["modification:variable::SYMBOLEXT:ox;MODIFIED:M;DELTAMASS:15.99491463"]
        
        # Default: always include oxidation
        mods = ["modification:variable::SYMBOLEXT:ox;MODIFIED:M;DELTAMASS:15.99491463"]
        
        # Try to add quencher-specific modifications if quencher is provided
        if quencher_name:
            quencher_def = self.quenchers.get(quencher_name.lower())
            if quencher_def:
                # Get crosslinker-specific mods for this quencher
                xl_short_name = crosslinker_name  # Try using the name directly first
                
                # Also try to resolve the full name
                xl_def = self.get_crosslinker(crosslinker_name)
                if xl_def and "short_name" in xl_def:
                    xl_short_name = xl_def["short_name"]
                
                # Look up if this quencher has modifications for this crosslinker
                xl_mods = quencher_def.get("crosslinker_modifications", {}).get(xl_short_name)
                
                if xl_mods:
                    # Add the mono-quench modifications
                    symbol = xl_mods.get("symbol", "")
                    mass = xl_mods.get("mass", 0)
                    amino_acids = xl_mods.get("amino_acids", {})
                    
                    for aa, probs in amino_acids.items():
                        # probs is an array like [0] or [0.2] - we add one modification per amino acid
                        mods.append(f"modification:variable::SYMBOLEXT:{symbol};MODIFIED:{aa};DELTAMASS:{mass}")
                    
                    logger.info(f"Added {len(amino_acids)} quencher-specific modifications for {crosslinker_name}+{quencher_name}")
                else:
                    logger.warning(f"Quencher '{quencher_name}' has no modifications defined for crosslinker '{crosslinker_name}'")
            else:
                logger.warning(f"Quencher '{quencher_name}' not found in definitions - skipping mono-quench modifications")
        else:
            logger.debug(f"No quencher provided for {crosslinker_name} - using default modifications")
        
        return mods
    
    def _build_crosslinker_section(self, crosslinkers: List[dict]) -> str:
        """
        Build the crosslinker section of the config
        
        Args:
            crosslinkers: List of crosslinker dicts from definitions
            
        Returns:
            Formatted crosslinker section
        """
        if not crosslinkers:
            # Default to linear
            return "#################\n## Cross Linker + associated modifications\ncrosslinker:LinearCrosslinker:NAME:linear"
        
        lines = ["#################", "## Cross Linker + associated modifications"]
        
        for xl in crosslinkers:
            xi_class = xl.get("xi_class", "LinearCrosslinker")
            
            if xi_class == "LinearCrosslinker":
                lines.append(f"crosslinker:LinearCrosslinker:NAME:linear")
            elif xi_class == "SymetricSingleAminoAcidRestrictedCrossLinker":
                name = xl.get("short_name", xl.get("name"))
                mass = xl.get("mass", 0)
                linked = xl.get("linked_aminoacids", "")
                stubs = xl.get("stubs")
                
                if stubs:
                    lines.append(
                        f"crosslinker:{xi_class}:Name:{name};MASS:{mass};LINKEDAMINOACIDS:{linked};STUBS:{stubs}"
                    )
                else:
                    lines.append(
                        f"crosslinker:{xi_class}:Name:{name};MASS:{mass};LINKEDAMINOACIDS:{linked}"
                    )
            elif xi_class == "NonCovalentBound":
                name = xl.get("short_name", xl.get("name"))
                lines.append(f"crosslinker:NonCovalentBound:Name:{name}")
        
        return "\n".join(lines)
    
    def generate_configs(
        self,
        pxd: str,
        llm_responses: dict,
        pride_data: Optional[dict] = None
    ) -> Tuple[str, str]:
        """
        Generate Xi config files for crosslinking and linear analyses
        
        Args:
            pxd: PXD accession
            llm_responses: Dictionary of LLM responses from metadata enrichment
            pride_data: Optional PRIDE metadata dict
            
        Returns:
            Tuple of (crosslinking_config, linear_config) as strings
        """
        logger.info(f"Generating Xi configs for {pxd}")
        
        # Extract crosslinker info from LLM
        crosslinker_response = llm_responses.get("comment[cross-linker]")
        if not crosslinker_response:
            logger.warning(f"No comment[cross-linker] response found for {pxd}")
            crosslinker_info = None
        else:
            crosslinker_info = self._parse_crosslinker_from_llm(crosslinker_response)
        
        # Extract quencher info from LLM
        quencher_response = llm_responses.get("comment[quenching reagent]")
        quencher_name = self._parse_quencher_from_llm(quencher_response)
        if quencher_name:
            logger.info(f"  Found quencher: {quencher_name}")
        else:
            logger.info(f"  No quencher found in LLM response")
        
        # Resolve crosslinker definitions
        crosslinkers_for_search = []
        crosslinker_names = []
        
        if crosslinker_info and crosslinker_info.get("name"):
            xl_name = crosslinker_info["name"]
            xl_def = self.get_crosslinker(xl_name)
            
            if xl_def:
                crosslinkers_for_search.append(xl_def)
                crosslinker_names.append(xl_def.get("short_name", xl_def["name"]))
                logger.info(f"  Found crosslinker: {xl_name}")
            else:
                logger.warning(f"  Unknown crosslinker: {xl_name} - using default (Linear)")
        else:
            logger.info(f"  No valid crosslinker name found - using default (Linear)")
        
        # Extract digestion info
        digestion_response = llm_responses.get("comment[cleavage agent details]", {})
        digestions = self._parse_digestion_from_llm(digestion_response)
        digestion_section = "\n".join(digestions)
        
        # For crosslinking config: use identified crosslinkers
        if crosslinkers_for_search:
            crosslinker_section_xl = self._build_crosslinker_section(crosslinkers_for_search)
            # Get variable mods for the identified crosslinker with quencher info
            var_mods_xl = self._get_variable_modifications_for_crosslinker(
                crosslinker_names[0] if crosslinker_names else "",
                quencher_name
            )
        else:
            # Fallback: use a generic crosslinker section for DSSO
            dsso_def = self.get_crosslinker("DSSO")
            crosslinker_section_xl = self._build_crosslinker_section([dsso_def] if dsso_def else [])
            var_mods_xl = self._get_variable_modifications_for_crosslinker("DSSO", quencher_name)
        
        # For linear config: never use crosslinkers
        crosslinker_section_linear = "#################\n## Cross Linker + associated modifications\ncrosslinker:LinearCrosslinker:NAME:linear"
        var_mods_linear = ["modification:variable::SYMBOLEXT:ox;MODIFIED:M;DELTAMASS:15.99491463"]
        
        # Generate configs
        config_xl = self.BASE_TEMPLATE.format(
            crosslinker_section=crosslinker_section_xl,
            variable_modifications="\n".join(var_mods_xl),
            digestion_section=digestion_section,
            topmatchesonly="true"
        )
        
        config_linear = self.BASE_TEMPLATE.format(
            crosslinker_section=crosslinker_section_linear,
            variable_modifications="\n".join(var_mods_linear),
            digestion_section=digestion_section,
            topmatchesonly="false"
        )
        
        logger.info(f"✓ Generated configs for {pxd}")
        
        return config_xl, config_linear
    
    def save_configs(
        self,
        pxd: str,
        config_xl: str,
        config_linear: str,
        output_dir: str
    ) -> Tuple[Path, Path]:
        """
        Save config files to disk
        
        Args:
            pxd: PXD accession
            config_xl: Crosslinking config content
            config_linear: Linear config content
            output_dir: Base output directory (e.g., ./pxd_data)
            
        Returns:
            Tuple of (crosslinking_path, linear_path)
        """
        pxd_config_dir = Path(output_dir) / pxd / "configs"
        pxd_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Save crosslinking config
        xl_path = pxd_config_dir / "xi_crosslinking.conf"
        with open(xl_path, "w") as f:
            f.write(config_xl)
        logger.info(f"Saved: {xl_path}")
        
        # Save linear config
        linear_path = pxd_config_dir / "xi_linear.conf"
        with open(linear_path, "w") as f:
            f.write(config_linear)
        logger.info(f"Saved: {linear_path}")
        
        return xl_path, linear_path
