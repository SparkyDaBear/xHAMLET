"""
Prompt templates for LLM-based metadata extraction
"""

import logging
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptTemplates:
    """Manager for LLM prompt templates"""
    
    def __init__(self, prompts_dir: str = "./prompts"):
        """
        Initialize prompt templates
        
        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.templates = self._load_all_prompts()
        logger.info(f"Loaded {len(self.templates)} prompt templates from {self.prompts_dir}")
    
    def _load_all_prompts(self) -> Dict[str, str]:
        """Load all prompt files from directory"""
        prompts = {}
        
        for prompt_file in self.prompts_dir.glob("*.txt"):
            key = prompt_file.stem
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompts[key] = f.read().strip()
                logger.info(f"Loaded prompt: {key}")
            except Exception as e:
                logger.error(f"Failed to load prompt {key}: {e}")
        
        return prompts
    
    def get_prompt(self, key: str) -> str:
        """
        Get a specific prompt by key
        
        Args:
            key: Prompt key (filename without .txt)
            
        Returns:
            Prompt text
            
        Raises:
            ValueError if prompt not found
        """
        if key not in self.templates:
            raise ValueError(f"Prompt '{key}' not found. Available: {list(self.templates.keys())}")
        return self.templates[key]
    
    def get_prompts(self, keys: list) -> Dict[str, str]:
        """
        Get multiple prompts
        
        Args:
            keys: List of prompt keys
            
        Returns:
            Dict of {key: prompt_text}
        """
        return {key: self.get_prompt(key) for key in keys}
    
    def list_prompts(self) -> list:
        """List all available prompts"""
        return list(self.templates.keys())
    
    def reload_prompts(self) -> None:
        """Reload prompts from disk"""
        self.templates = self._load_all_prompts()
        logger.info(f"Reloaded {len(self.templates)} prompt templates")
    
    # Default prompts (built-in fallbacks)
    DEFAULTS = {

    # ---------------------------
    # Characteristics[...] prompts
    # ---------------------------

    # ---------------------------
    "characteristics_crosslink_type": \
    """You are an expert SDRF-Proteomics annotator for XL-MS.
    Extract: characteristics[crosslink type]

    Identify the crosslinker chemistry class (derivable from the reagent) as one or more of:
    homo-bifunctional, hetero-bifunctional, zero-length, MS-cleavable.
    Only output classes supported by explicit manuscript statements; otherwise value=null.

    Return JSON keys: value, evidence_quote, evidence_location, confidence, notes""",

    # ---------------------------
    "characteristics_crosslink_distance": \
    """You are an expert SDRF-Proteomics annotator for XL-MS.
    Extract: characteristics[crosslink distance]

    Find the maximum Cα–Cα distance constraint used for structural interpretation (numeric + units, usually Å).
    If the paper only names the reagent but does not state a distance constraint, set value=null (do not infer).

    Return JSON keys: value, units, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "characteristics_crosslinking_reaction_time": \
    """You are an expert SDRF-Proteomics annotator for XL-MS.
    Extract: characteristics[crosslinking reaction time]

    Return the duration of the crosslinking reaction (numeric + units such as min or h).
    If multiple times were used, return a list with condition labels in notes.

    Return JSON keys: value, units, evidence_quote, evidence_location, confidence, notes""",

    # ---------------------------
    "characteristics_crosslinking_temperature": \
    """You are an expert SDRF-Proteomics annotator for XL-MS.
    Extract: characteristics[crosslinking temperature]

    Return the temperature at which crosslinking was performed (numeric + units, or 'room temperature' if stated).
    Normalize 'room temperature' to the literal string 'room temperature' (do not convert to °C unless specified).

    Return JSON keys: value, units, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "characteristics_organism": \
    """You are an expert SDRF-Proteomics annotator.
    Extract the value(s) for: characteristics[organism]

    Scientific name(s) exactly as stated of the species from which the proteomics samples were derived.

    Examples: Human, mouse, E. coli, Arabidopsis, etc.
    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "characteristics_organism_part": \
    """You are an expert SDRF-Proteomics annotator.
    Extract the value(s) for: characteristics[organism part]

    Examples: liver, brain, plasma, HeLa lysate (if mapped to part), etc.
    If not stated, null.

    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "characteristics_cell_type": \
    """You are an expert SDRF-Proteomics annotator.
    Extract the value(s) for: characteristics[cell type]

    Examples: HeLa, Jurkat, primary fibroblasts, etc.
    If not stated, null.

    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence""",


    # -----------------------
    # Comment[...] prompts
    # -----------------------

    # ---------------------------
    "comment_cross_linker": \
    """You are an expert SDRF-Proteomics annotator for XL-MS.
    Extract metadata for: comment[cross-linker] using the structured format:

    NT=<name>;AC=<XLMOD or ChEBI accession if explicitly provided>;CL=<yes/no>;TA=<targets>;
    MH=<heavy stub mass>;ML=<light stub mass>;SM=<spacer mass>

    Rules:
    - Populate ONLY what the manuscript explicitly states.
    - Validate crosslinker name against the ALLOWED list: DSSO, BS3, DSS, EDC, Formaldehyde, Glutaraldehyde, DMA, SDA, Benzoyl, Aryl azide, Isotope-labeled DSSO, Azide-alkyne, Psoralen.
    - If the named crosslinker is not in the allowed list but can be mapped to one (e.g., 'sulfoxide' → DSSO), provide best mapping in notes and set MAPPED=true.
    - If AC is not provided in the paper, set AC=null (do not look up).
    - If cleavable is stated (or MS-cleavable crosslinker is named AND explicitly called cleavable), set CL=yes; else if explicitly non-cleavable set CL=no; else null.
    - TA should list residue targets if stated (e.g., K, nterm, D/E, etc.) else null.
    - MH/ML only if explicitly stated.
    - SM only if explicitly stated.

    Return JSON with keys:
    NT, AC, CL, TA, MH, ML, SM, serialized, evidence_quote, evidence_location, confidence, mapped, notes""",

    # ---------------------------
    "comment_dissociation_method": \
    """You are an expert SDRF-Proteomics annotator.
    Extract the value(s) for: comment[dissociation method]

    Examples: HCD, CID, ETD, EThcD, UVPD, stepped HCD, MS2/MS3 strategies.
    If multiple methods are used, return a list.

    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "comment_collision_energy": \
    """You are an expert SDRF-Proteomics annotator.
    Extract the value(s) for: comment[collision energy]

    Capture collision energy settings and units if stated (e.g., NCE 30, eV, stepped ranges).

    Return JSON with keys:
    value, units, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "comment_crosslink_enrichment_method": \
    """You are an expert SDRF-Proteomics annotator for XL-MS.
    Extract the value(s) for: comment[crosslink enrichment method]

    Look specifically for enrichment methods targeting crosslinked species (e.g., SEC/SCX fractionation for crosslinks, affinity enrichment, specialized workflows).
    If not described, null.

    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "comment_crosslinker_concentration": \
    """You are an expert SDRF-Proteomics annotator for XL-MS.
    Extract the value(s) for: comment[crosslinker concentration]

    Capture concentration (e.g., mM, mg/mL) of the crosslinker reagent used in the reaction.

    Return JSON with keys:
    value, units, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "comment_crosslinker_to_protein_ratio": \
    """You are an expert SDRF-Proteomics annotator for XL-MS.
    Extract the value(s) for: comment[crosslinker to protein ratio]

    Look for mass ratio or molar ratio (e.g., 1:50 w/w, molar excess).
    If only protein concentration and crosslinker concentration are given without an explicit ratio, set null and note it.

    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence, notes""",

    # ---------------------------
    "comment_quenching_reagent": \
    """You are an expert SDRF-Proteomics annotator for XL-MS.
    Extract the value(s) for: comment[quenching reagent]

    Examples: Tris, ammonium bicarbonate, glycine, hydroxylamine, etc., and any concentration/time if stated.

    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "comment_label": \
    """You are an expert SDRF-Proteomics annotator.
    Extract the value(s) for: comment[label]

    Examples: label-free, SILAC, TMT, iTRAQ, isotopically labeled crosslinker variants, etc.
    If the study is unlabeled and says label-free, set that; if not stated, null.

    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "comment_instrument": \
    """You are an expert SDRF-Proteomics annotator.
    Extract the value(s) for: comment[instrument]

    Capture instrument make/model (e.g., Orbitrap Fusion Lumos, Q Exactive HF, timsTOF Pro).
    If multiple instruments are used, return a list.

    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "comment_cleavage_agent_details": \
    """You are an expert SDRF-Proteomics annotator.
    Extract the value(s) for: comment[cleavage agent details]

    This refers to cleavage agents used in sample prep (e.g., proteases like trypsin/LysC, chemical cleavage).
    Extract enzyme name(s), conditions if stated (overnight, 37C, etc.). If not present, null.

    Return JSON with keys:
    value, evidence_quote, evidence_location, confidence""",

    # ---------------------------
    "comment_modification_parameters": \
    """You are an expert SDRF-Proteomics annotator.
    Extract: comment[modification parameters]

    Goal: encode each search-time modification using the SDRF structured format:
    NT=<name>;AC=<UNIMOD:id>;TA=<target amino acid(s) or site>;MT=<Fixed|Variable>

    Rules:
    - Output one entry per modification.
    - AC must be 'UNIMOD:<id>' only if explicitly stated OR unambiguous (e.g., Carbamidomethyl on C, Oxidation on M). If not confidently mappable, set AC=null and keep NT as written.
    - TA should be residue letter(s) (e.g., C, M, STY) or site tokens ('Protein N-term', 'Peptide N-term', 'K', etc.) exactly as implied.
    - MT must be 'Fixed' or 'Variable' based on the manuscript search settings.
    - Do not infer masses. If masses are explicitly given, put them in notes.

    Return STRICT JSON with keys:
    entries (list of objects with: NT, AC, TA, MT, serialized),
    evidence_quote, evidence_location, confidence, notes""",

    }
    
    @classmethod
    def create_default_prompts(cls, output_dir: str = "./prompts") -> None:
        """
        Create default prompt files if they don't exist
        
        Args:
            output_dir: Directory to save prompts
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for name, content in cls.DEFAULTS.items():
            filepath = output_path / f"{name}.txt"
            if not filepath.exists():
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Created default prompt: {name}")
            else:
                logger.info(f"Prompt already exists: {name}")
