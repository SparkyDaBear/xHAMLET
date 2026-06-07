"""
Ontology term mapper for SDRF-Proteomics (crosslinking template).

Provides static lookup tables for mapping raw strings from PRIDE, LLM, and
spectral metadata to fully qualified PSI/OBO ontology terms in the form:
  NT=<human_readable_name>;AC=<accession>

All look-ups are case-insensitive on the input string.  Each public method
returns the canonical SDRF value string or None if the input cannot be mapped.
"""

import re
from typing import Optional
from . import ols_client

# ---------------------------------------------------------------------------
# Instrument ontology map  (MS ontology)
# Keys: lowercase normalised instrument names / PRIDE accession prefixes
# ---------------------------------------------------------------------------
_INSTRUMENT_MAP = {
    # Orbitrap Astral
    "orbitrap astral": ("Orbitrap Astral", "MS:1003356"),
    # Orbitrap Exploris series
    "orbitrap exploris 480": ("Orbitrap Exploris 480", "MS:1003028"),
    "orbitrap exploris 240": ("Orbitrap Exploris 240", "MS:1003029"),
    "orbitrap exploris 120": ("Orbitrap Exploris 120", "MS:1003030"),
    # Orbitrap Eclipse
    "orbitrap eclipse": ("Orbitrap Eclipse", "MS:1003349"),
    # Orbitrap Fusion series
    "orbitrap fusion lumos": ("Orbitrap Fusion Lumos", "MS:1002732"),
    "orbitrap fusion": ("Orbitrap Fusion", "MS:1002416"),
    # Q Exactive series
    "q exactive hf-x": ("Q Exactive HF-X", "MS:1002877"),
    "q exactive hf": ("Q Exactive HF", "MS:1002523"),
    "q exactive plus": ("Q Exactive Plus", "MS:1002634"),
    "q exactive": ("Q Exactive", "MS:1001911"),
    # Orbitrap Velos
    "orbitrap velos": ("Orbitrap Velos", "MS:1001742"),
    "lto orbitrap velos": ("LTQ Orbitrap Velos", "MS:1001742"),
    "ltq orbitrap velos": ("LTQ Orbitrap Velos", "MS:1001742"),
    # LTQ Orbitrap
    "ltq orbitrap xl": ("LTQ Orbitrap XL", "MS:1000556"),
    "ltq orbitrap": ("LTQ Orbitrap", "MS:1000449"),
    "ltq": ("LTQ", "MS:1000447"),
    # timsTOF
    "timstof": ("timsTOF", "MS:1003005"),
    "timstof pro": ("timsTOF Pro", "MS:1003230"),
    "timstof scp": ("timsTOF SCP", "MS:1003378"),
    # TripleTOF / SCIEX
    "tripletof 6600": ("TripleTOF 6600", "MS:1002583"),
    "tripletof 5600": ("TripleTOF 5600", "MS:1001982"),
    # Synapt / Waters
    "synapt g2-si": ("Synapt G2-Si", "MS:1002726"),
    "synapt g2": ("Synapt G2", "MS:1002280"),
}

# ---------------------------------------------------------------------------
# Dissociation method map  (MS ontology)
# ---------------------------------------------------------------------------
_DISSOCIATION_MAP = {
    "hcd": ("HCD", "MS:1000422"),
    "higher-energy collision dissociation": ("HCD", "MS:1000422"),
    "stepped hcd": ("HCD", "MS:1000422"),    # Stepped HCD is still HCD in SDRF
    "cid": ("CID", "MS:1002472"),
    "collision-induced dissociation": ("CID", "MS:1002472"),
    "etd": ("ETD", "MS:1000598"),
    "electron transfer dissociation": ("ETD", "MS:1000598"),
    "ethcd": ("EThcD", "MS:1002678"),
    "etd+hcd": ("EThcD", "MS:1002678"),
    "etchd": ("EThcD", "MS:1002678"),
    "uvpd": ("UVPD", "MS:1003247"),
    "ultraviolet photodissociation": ("UVPD", "MS:1003247"),
    "ecd": ("ECD", "MS:1000250"),
    "electron capture dissociation": ("ECD", "MS:1000250"),
}

# ---------------------------------------------------------------------------
# Organism map  (NCBI Taxonomy ontology via NCBITaxon / OLS NEWT)
# ---------------------------------------------------------------------------
_ORGANISM_MAP = {
    "homo sapiens": ("Homo sapiens", "NCBITaxon:9606"),
    "human": ("Homo sapiens", "NCBITaxon:9606"),
    "mus musculus": ("Mus musculus", "NCBITaxon:10090"),
    "mouse": ("Mus musculus", "NCBITaxon:10090"),
    "rattus norvegicus": ("Rattus norvegicus", "NCBITaxon:10116"),
    "rat": ("Rattus norvegicus", "NCBITaxon:10116"),
    "saccharomyces cerevisiae": ("Saccharomyces cerevisiae", "NCBITaxon:4932"),
    "yeast": ("Saccharomyces cerevisiae", "NCBITaxon:4932"),
    "escherichia coli": ("Escherichia coli", "NCBITaxon:562"),
    "e. coli": ("Escherichia coli", "NCBITaxon:562"),
    "drosophila melanogaster": ("Drosophila melanogaster", "NCBITaxon:7227"),
    "danio rerio": ("Danio rerio", "NCBITaxon:7955"),
    "xenopus laevis": ("Xenopus laevis", "NCBITaxon:8355"),
    "caenorhabditis elegans": ("Caenorhabditis elegans", "NCBITaxon:6239"),
    "arabidopsis thaliana": ("Arabidopsis thaliana", "NCBITaxon:3702"),
    "sus scrofa": ("Sus scrofa", "NCBITaxon:9823"),
    "bos taurus": ("Bos taurus", "NCBITaxon:9913"),
}

# NEWT: prefix → NCBITaxon: prefix normalisation
_NEWT_RE = re.compile(r"^NEWT:(\d+)$")

# ---------------------------------------------------------------------------
# Label map  (PRIDE / MS ontology)
# ---------------------------------------------------------------------------
_LABEL_MAP = {
    "label free": ("label free sample", "MS:1002038"),
    "label-free": ("label free sample", "MS:1002038"),
    "unlabeled": ("label free sample", "MS:1002038"),
    "silac": ("SILAC", "MS:1002038"),   # TODO: add proper SILAC AC
    "itraq4": ("iTRAQ4plex", "PRIDE:0000114"),
    "itraq8": ("iTRAQ8plex", "PRIDE:0000115"),
    "tmt6": ("TMT6plex", "PRIDE:0000116"),
    "tmt10": ("TMT10plex", "PRIDE:0000117"),
    "tmt11": ("TMT11plex", "PRIDE:0000119"),
    "tmt16": ("TMTpro 16plex", "PRIDE:0000120"),
    "tmtpro": ("TMTpro 16plex", "PRIDE:0000120"),
}

# ---------------------------------------------------------------------------
# Cleavage agent map  (MS ontology)
# ---------------------------------------------------------------------------
_CLEAVAGE_AGENT_MAP = {
    "trypsin": ("Trypsin", "MS:1001251"),
    "trypsin/p": ("Trypsin/P", "MS:1001313"),
    "lysc": ("Lys-C", "MS:1001309"),
    "lys-c": ("Lys-C", "MS:1001309"),
    "lysc/p": ("Lys-C/P", "MS:1001309"),
    "asp-n": ("Asp-N", "MS:1001303"),
    "aspn": ("Asp-N", "MS:1001303"),
    "glu-c": ("Glu-C", "MS:1001917"),
    "gluc": ("Glu-C", "MS:1001917"),
    "chymotrypsin": ("Chymotrypsin", "MS:1001306"),
    "lys-n": ("Lys-N", "MS:1003093"),
    "arg-c": ("Arg-C", "MS:1001303"),
    "argc": ("Arg-C", "MS:1001303"),
    "elastase": ("Elastase", "MS:1001304"),
    "no cleavage": ("No cleavage", "MS:1001955"),
    "unspecific cleavage": ("Unspecific cleavage", "MS:1001956"),
}


class OntologyMapper:
    """
    Static ontology lookup helper.  All methods return a formatted SDRF value
    string (NT=...;AC=...) or None if no match is found.
    """

    # ------------------------------------------------------------------
    # Instrument
    # ------------------------------------------------------------------

    @staticmethod
    def map_instrument(
        name: Optional[str],
        pride_accession: Optional[str] = None,
    ) -> Optional[str]:
        """
        Map an instrument name to an SDRF ontology term.

        If *pride_accession* already starts with 'MS:' it is used directly.
        """
        # Use PRIDE accession when it is already an MS: term
        if pride_accession and pride_accession.startswith("MS:"):
            nt = name or pride_accession
            return f"NT={nt};AC={pride_accession}"

        if not name:
            return None

        key = name.lower().strip()
        # Try exact map
        if key in _INSTRUMENT_MAP:
            nt, ac = _INSTRUMENT_MAP[key]
            return f"NT={nt};AC={ac}"

        # Partial match — longest key that is a substring of the input name
        match = None
        match_len = 0
        for map_key, (nt, ac) in _INSTRUMENT_MAP.items():
            if map_key in key and len(map_key) > match_len:
                match = (nt, ac)
                match_len = len(map_key)
        if match:
            return f"NT={match[0]};AC={match[1]}"

        # OLS4 fallback
        hit = ols_client.lookup(name, ["ms"])
        if hit:
            return f"NT={hit[0]};AC={hit[1]}"

        # Return as-is without an accession — still useful in SDRF
        return f"NT={name}"

    # ------------------------------------------------------------------
    # Dissociation method
    # ------------------------------------------------------------------

    @staticmethod
    def map_dissociation(
        name: Optional[str],
        method_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Map a dissociation method name to an SDRF ontology term.

        If *method_filename* contains 'SteppedHCD' or 'StepHCD' the method
        is still reported as HCD (Stepped HCD is a variant, not a separate CV
        term).
        """
        # Stepped HCD override from instrument method filename
        if method_filename and re.search(r"step(?:ped)?[\s_]?hcd", method_filename, re.I):
            return "NT=HCD;AC=MS:1000422"

        if not name:
            return None

        key = name.lower().strip()
        if key in _DISSOCIATION_MAP:
            nt, ac = _DISSOCIATION_MAP[key]
            return f"NT={nt};AC={ac}"

        # Partial match
        for map_key, (nt, ac) in _DISSOCIATION_MAP.items():
            if map_key in key:
                return f"NT={nt};AC={ac}"

        # OLS4 fallback
        hit = ols_client.lookup(name, ["ms"])
        if hit:
            return f"NT={hit[0]};AC={hit[1]}"

        return f"NT={name}"

    # ------------------------------------------------------------------
    # Organism
    # ------------------------------------------------------------------

    @staticmethod
    def map_organism(
        name: Optional[str],
        pride_accession: Optional[str] = None,
    ) -> Optional[str]:
        """
        Map an organism name to an SDRF ontology term.

        NEWT: prefixed accessions are converted to NCBITaxon: automatically.
        """
        # Normalise NEWT: → NCBITaxon:
        if pride_accession:
            m = _NEWT_RE.match(pride_accession)
            if m:
                pride_accession = f"NCBITaxon:{m.group(1)}"
            if pride_accession.startswith("NCBITaxon:"):
                nt = name or pride_accession
                return f"NT={nt};AC={pride_accession}"

        if not name:
            return None

        key = name.lower().strip()
        if key in _ORGANISM_MAP:
            nt, ac = _ORGANISM_MAP[key]
            return f"NT={nt};AC={ac}"

        # Partial/containment match
        for map_key, (nt, ac) in _ORGANISM_MAP.items():
            if map_key in key:
                return f"NT={nt};AC={ac}"

        # OLS4 fallback — search ncbitaxon for unknown species
        hit = ols_client.lookup(name, ["ncbitaxon"])
        if hit:
            return f"NT={hit[0]};AC={hit[1]}"

        return f"NT={name}"

    # ------------------------------------------------------------------
    # Label
    # ------------------------------------------------------------------

    @staticmethod
    def map_label(name: Optional[str]) -> Optional[str]:
        """Map a sample label description to an SDRF ontology term."""
        if not name:
            return "NT=label free sample;AC=MS:1002038"

        key = name.lower().strip()
        if key in _LABEL_MAP:
            nt, ac = _LABEL_MAP[key]
            return f"NT={nt};AC={ac}"

        for map_key, (nt, ac) in _LABEL_MAP.items():
            if map_key in key:
                return f"NT={nt};AC={ac}"

        return f"NT={name}"

    # ------------------------------------------------------------------
    # Cleavage agent
    # ------------------------------------------------------------------

    @staticmethod
    def map_cleavage_agent(name: Optional[str]) -> Optional[str]:
        """Map a protease name to an SDRF ontology term."""
        if not name:
            return None

        key = name.lower().strip()
        if key in _CLEAVAGE_AGENT_MAP:
            nt, ac = _CLEAVAGE_AGENT_MAP[key]
            return f"NT={nt};AC={ac}"

        for map_key, (nt, ac) in _CLEAVAGE_AGENT_MAP.items():
            if map_key in key:
                return f"NT={nt};AC={ac}"

        # OLS4 fallback
        hit = ols_client.lookup(name, ["ms"])
        if hit:
            return f"NT={hit[0]};AC={hit[1]}"

        return f"NT={name}"

    # ------------------------------------------------------------------
    # Modification parameters
    # ------------------------------------------------------------------

    @staticmethod
    def map_modification(
        name: Optional[str],
        unimod_ac: Optional[str] = None,
        target: Optional[str] = None,
        mod_type: str = "Variable",
    ) -> Optional[str]:
        """
        Build an SDRF comment[modification parameters] value.

        Args:
            name:       Human-readable modification name (e.g. 'Oxidation').
            unimod_ac:  UNIMOD accession number or full 'UNIMOD:N' string.
            target:     Amino acid one-letter code (e.g. 'M').
            mod_type:   'Fixed' or 'Variable'.

        Returns:
            Formatted string such as 'NT=Oxidation;AC=UNIMOD:21;TA=M;MT=Variable'
        """
        if not name:
            return None

        parts = [f"NT={name}"]

        if unimod_ac:
            ac_str = (
                unimod_ac
                if str(unimod_ac).startswith("UNIMOD:")
                else f"UNIMOD:{unimod_ac}"
            )
            parts.append(f"AC={ac_str}")

        if target:
            parts.append(f"TA={target}")

        parts.append(f"MT={mod_type}")

        return ";".join(parts)
