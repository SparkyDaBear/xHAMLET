"""
SDRF-Proteomics TSV writer for XL-MS datasets.

Generates an SDRF TSV conforming to the crosslinking template:
  https://github.com/bigbio/proteomics-sample-metadata

One row is written per .raw file.  Column values are assembled in priority
order: spectral summary > LLM responses > PRIDE metadata > publication metadata.
"""

import csv
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ontology_mapper import OntologyMapper

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Filename heuristics
# ---------------------------------------------------------------------------
_FRACTION_RE = re.compile(
    r"[_\-](F|fr|frac|SCX|HPRP|SEC|SAX)[-_]?(\d{1,3})[_\-.]",
    re.IGNORECASE,
)
_TECH_REP_RE = re.compile(
    r"[_\-](rep|replicate|technical)[-_]?(\d{1,2})[_\-.]",
    re.IGNORECASE,
)

# SDRF template column values (NT=name;VV=vX.Y.Z format required by parse_sdrf)
_TEMPLATE_MS_PROTEOMICS = "NT=ms-proteomics;VV=v1.1.0"
_TEMPLATE_CROSSLINKING = "NT=crosslinking;VV=v1.0.0"

# Taxonomy-specific template per NCBITaxon accession
_TAXONOMY_TEMPLATE_MAP = {
    "NCBITaxon:9606": "NT=human;VV=v1.1.0",
    "NCBITaxon:10090": "NT=vertebrates;VV=v1.1.0",
    "NCBITaxon:10116": "NT=vertebrates;VV=v1.1.0",
    "NCBITaxon:9823": "NT=vertebrates;VV=v1.1.0",
    "NCBITaxon:9913": "NT=vertebrates;VV=v1.1.0",
    "NCBITaxon:7955": "NT=vertebrates;VV=v1.1.0",
    "NCBITaxon:8355": "NT=vertebrates;VV=v1.1.0",
    "NCBITaxon:7227": "NT=invertebrates;VV=v1.1.0",
    "NCBITaxon:6239": "NT=invertebrates;VV=v1.1.0",
    "NCBITaxon:3702": "NT=plants;VV=v1.1.0",
}

# Stepped collision energy pattern: "27 ± 6%" -> "stepped 27+-6%"
_STEPPED_CE_RE = re.compile(
    r'^(\d+(?:\.\d+)?)\s*[±+\-]{1,3}\s*(\d+(?:\.\d+)?)\s*%',
)

# Carbamidomethyl is always added as a fixed modification unless already present
_CARBAMIDOMETHYL = "NT=Carbamidomethyl;AC=UNIMOD:4;TA=C;MT=Fixed"

# Filename keyword patterns for organism assignment.
# Maps lowercase canonical species name fragment → list of filename keywords.
# Used to infer which organism each raw file belongs to.
_ORG_FILENAME_KEYWORDS: Dict[str, List[str]] = {
    "homo sapiens":                  ["human", "homo", "hsa", "hs"],
    "mus musculus":                  ["mouse", "murine", "mmu"],
    "saccharomyces cerevisiae":       ["yeast", "cerevisiae", "sacch", "sce"],
    "escherichia coli":              ["ecoli", "coli"],
    "bos taurus":                    ["bovine", "bov"],
    "rattus norvegicus":              ["rat", "rno", "rattus"],
    "drosophila melanogaster":        ["drosophila", "fly", "dmel"],
    "arabidopsis thaliana":          ["arabidopsis", "thaliana", "ath"],
    "caenorhabditis elegans":         ["elegans", "worm", "celegans"],
    "gallus gallus":                 ["chicken", "gallus", "gga"],
    "oryctolagus cuniculus":          ["rabbit"],
    "danio rerio":                   ["zebrafish", "danio"],
    "xenopus laevis":                ["xenopus"],
    "chlamydomonas reinhardtii":      ["chlamy", "reinhardtii"],
    "sus scrofa":                    ["pig", "porcine", "scrofa"],
}


class SDRFWriter:
    """Writes SDRF-Proteomics TSV files for crosslinking datasets."""

    def write(
        self,
        pxd: str,
        file_list: List[Dict[str, Any]],
        llm_responses: Optional[Dict[str, Any]],
        spectral_summary: Optional[Dict[str, Any]],
        pride_data: Optional[Dict[str, Any]],
        output_path: Path,
        file_assignments: Optional[Dict[str, Dict[str, Any]]] = None,
        assessed_files: Optional[List[str]] = None,
    ) -> Path:
        """
        Write the SDRF TSV file and return the output path.

        Args:
            pxd:                PRIDE project accession (e.g. 'PXD017620').
            file_list:          List of file dicts from PRIDE API (must have 'fileName').
            llm_responses:      Dict of prompt_key → {parsed: {...}} from extractor.
            spectral_summary:   Dict from AssessorRunner.build_spectral_summary().
            pride_data:         Dict from PrideClient.
            output_path:        Destination path for the TSV file.
            file_assignments:   Optional Dict[filename, {cluster_id, organism, taxid}] from file clustering.
            assessed_files:     Optional list of filenames that were actually assessed.

        Returns:
            The resolved output path.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        llm = llm_responses or {}
        spec = spectral_summary or {}
        pride = pride_data or {}
        file_assignments = file_assignments or {}
        assessed_files = assessed_files or []
        assessed_set = set(assessed_files)

        # ---- Resolve file list early (needed for per-file organism assignment) ----
        raw_files = [
            f for f in file_list
            if f.get("fileName", "").lower().endswith(".raw")
        ]
        if not raw_files:
            logger.warning("No .raw files in file_list — SDRF will be empty")

        # ---- Resolved values (dataset-level, shared across all rows) ----
        # Organisms: resolve full list, then assign per file
        # If file_assignments available, use per-file organism from clustering
        all_organisms = SDRFWriter._resolve_organisms_list(llm, pride)
        if file_assignments:
            per_file_org = self._assign_organisms_from_clustering(raw_files, file_assignments, all_organisms)
        else:
            per_file_org = SDRFWriter._assign_organisms_per_file(raw_files, all_organisms)
        
        max_org_count = max((len(v) for v in per_file_org.values()), default=1)
        if len(all_organisms) > 1:
            logger.info(
                "Multi-organism dataset: %d organisms, %d organism columns in SDRF",
                len(all_organisms), max_org_count,
            )

        organism_part_term = self._resolve_from_llm(llm, "characteristics[organism part]")
        cell_type_term = self._resolve_from_llm(llm, "characteristics[cell type]")
        label_term = self._resolve_label(llm, pride)
        instrument_term = self._resolve_instrument(llm, spec, pride)
        cleavage_term = self._resolve_cleavage(llm)
        dissociation_term = self._resolve_dissociation(llm, spec)
        crosslinker_term = self._resolve_crosslinker(llm)
        enrichment_term = self._resolve_from_llm(llm, "comment[crosslink enrichment method]")
        xl_concentration_term = self._resolve_with_units(llm, "comment[crosslinker concentration]")
        xl_ratio_term = self._resolve_from_llm(llm, "comment[crosslinker to protein ratio]")
        xl_time_term = self._resolve_with_units(llm, "characteristics[crosslinking reaction time]")
        xl_temp_term = self._resolve_with_units(llm, "characteristics[crosslinking temperature]")
        collision_energy_term = self._normalize_collision_energy(
            self._resolve_from_llm(llm, "comment[collision energy]")
        )

        modification_terms = self._resolve_modifications(llm)

        # SDRF template columns — use first organism for taxonomy template
        first_org = all_organisms[0] if all_organisms else None
        taxonomy_template = self._taxonomy_template(first_org)
        sdrf_templates = [
            _TEMPLATE_MS_PROTEOMICS,
            _TEMPLATE_CROSSLINKING,
        ]
        if taxonomy_template:
            sdrf_templates.append(taxonomy_template)

        # Map cluster -> assessed representative files for inheritance checks
        cluster_to_assessed: Dict[str, List[str]] = {}
        for filename in assessed_set:
            assignment = file_assignments.get(filename)
            if not assignment:
                continue
            cluster_id = assignment.get("cluster_id")
            if cluster_id:
                cluster_to_assessed.setdefault(cluster_id, []).append(filename)

        # ---- Build column headers ----
        mod_col_count = max(len(modification_terms), 1)
        tmpl_col_count = len(sdrf_templates)

        headers = ["source name"]
        for _ in range(max_org_count):
            headers.append("characteristics[organism]")
        headers += [
            "characteristics[organism part]",
            "characteristics[cell type]",
            "characteristics[biological replicate]",
            "assay name",
            "technology type",
            "comment[proteomics data acquisition method]",
            "comment[label]",
            "comment[fraction identifier]",
            "comment[technical replicate]",
            "comment[instrument]",
            "comment[cleavage agent details]",
        ]
        for i in range(mod_col_count):
            headers.append("comment[modification parameters]")
        headers += [
            "comment[collision energy]",
            "comment[dissociation method]",
            "comment[cross-linker]",
            "comment[crosslink enrichment method]",
            "comment[crosslinker concentration]",
            "comment[crosslinker to protein ratio]",
            "comment[crosslinking reaction time]",
            "comment[crosslinking temperature]",
            "comment[data file]",
        ]
        for _ in range(tmpl_col_count):
            headers.append("comment[sdrf template]")

        rows = []
        bio_rep_counter: Dict[str, int] = {}

        for idx, file_info in enumerate(raw_files, 1):
            filename = file_info.get("fileName", f"file_{idx}.raw")

            # Fraction number from filename
            frac_match = _FRACTION_RE.search(filename)
            fraction_id = frac_match.group(2) if frac_match else "1"

            # Technical replicate from filename
            rep_match = _TECH_REP_RE.search(filename)
            tech_rep = rep_match.group(2) if rep_match else "1"

            # Biological replicate — simple counter per fraction
            bio_key = fraction_id
            bio_rep_counter[bio_key] = bio_rep_counter.get(bio_key, 0) + 1
            bio_rep = str(bio_rep_counter[bio_key])

            source_name = f"{pxd}_{Path(filename).stem}"
            assay_name = f"{pxd}_{Path(filename).stem}_assay"

            # Per-file organism values (padded to max_org_count)
            file_orgs = per_file_org.get(filename, all_organisms)
            org_values = [o or "not available" for o in file_orgs]
            while len(org_values) < max_org_count:
                org_values.append("not available")
            org_values = org_values[:max_org_count]

            # Spectral field inheritance behavior:
            # - assessed file: use resolved spectral terms
            # - non-assessed file in a cluster with assessed representative: inherit resolved terms
            # - otherwise: not available
            cluster_id = (file_assignments.get(filename) or {}).get("cluster_id")
            has_representative = filename in assessed_set or (
                bool(cluster_id) and bool(cluster_to_assessed.get(cluster_id))
            )

            row_instrument = instrument_term if has_representative else None
            row_collision = collision_energy_term if has_representative else None
            row_dissociation = dissociation_term if has_representative else None

            row = (
                [source_name]
                + org_values
                + [
                    organism_part_term or "not available",
                    cell_type_term or "not available",
                    bio_rep,
                    assay_name,
                    "proteomic profiling by mass spectrometry",
                    "data-dependent acquisition",
                    label_term or "NT=label free sample;AC=MS:1002038",
                    fraction_id,
                    tech_rep,
                    row_instrument or "not available",
                    cleavage_term or "not available",
                ]
                + [modification_terms[i] if i < len(modification_terms) else "not available"
                   for i in range(mod_col_count)]
                + [
                    row_collision or "not available",
                    row_dissociation or "not available",
                    crosslinker_term or "not available",
                    enrichment_term or "not available",
                    xl_concentration_term or "not available",
                    xl_ratio_term or "not available",
                    xl_time_term or "not available",
                    xl_temp_term or "not available",
                    filename,
                ]
                + list(sdrf_templates)
            )

            rows.append(row)

        # ---- Write TSV ----
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            writer.writerows(rows)

        logger.info(
            "SDRF written: %s (%d rows, %d columns)",
            output_path, len(rows), len(headers),
        )
        return output_path

    # ------------------------------------------------------------------
    # Value resolver helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce_str(value: Any) -> Optional[str]:
        """Normalise a parsed LLM value to a plain string.

        The LLM occasionally returns a list (e.g. multi-organism studies).
        Take the first non-empty element in that case.
        """
        if isinstance(value, list):
            value = next((v for v in value if v), None)
        if value is None:
            return None
        s = str(value).strip()
        return s if s.lower() not in ("not available", "n/a", "none", "null", "") else None

    @staticmethod
    def _resolve_from_llm(
        llm: Dict[str, Any], key: str
    ) -> Optional[str]:
        """Extract 'value' from a parsed LLM response."""
        resp = llm.get(key, {})
        parsed = resp.get("parsed", {})
        if not isinstance(parsed, dict):
            return None
        value = parsed.get("value") or parsed.get("NT")
        return SDRFWriter._coerce_str(value)

    _UNIT_ABBREVIATIONS: Dict[str, str] = {
        "minutes": "min", "minute": "min",
        "hours": "h", "hour": "h",
        "seconds": "s", "second": "s",
        "celsius": "°C", "degrees celsius": "°C", "°c": "°C",
        "millimolar": "mM", "micromolar": "uM", "nanomolar": "nM",
    }
    _RANGE_RE = re.compile(r'^(\d+(?:\.\d+)?)\s*[-\u2013]\s*\d+(?:\.\d+)?$')

    @staticmethod
    def _resolve_with_units(llm: Dict[str, Any], key: str) -> Optional[str]:
        """
        Extract value+units from a parsed LLM response for number_with_unit columns.

        Handles:
        - Range values ("0.2-1") → uses first number ("0.2")
        - Unit name normalisation ("minutes" → "min", "Celsius" → "°C")
        - Special values ("room temperature") passed through as-is
        """
        resp = llm.get(key, {})
        parsed = resp.get("parsed", {})
        if not isinstance(parsed, dict):
            return None
        value = SDRFWriter._coerce_str(parsed.get("value") or parsed.get("NT"))
        if not value:
            return None
        # Special non-numeric values accepted by some validators
        if value.lower() in ("room temperature", "not available", "n/a", "not applicable"):
            return value
        # Normalize range to first number
        m = SDRFWriter._RANGE_RE.match(value)
        if m:
            value = m.group(1)
        # Append units if present
        units = SDRFWriter._coerce_str(parsed.get("units"))
        if units:
            units = SDRFWriter._UNIT_ABBREVIATIONS.get(units.lower(), units)
            return f"{value} {units}"
        return value

    @staticmethod
    def _resolve_organism(
        llm: Dict[str, Any], pride: Dict[str, Any]
    ) -> Optional[str]:
        """Resolve single organism (first entry). Kept for backwards compatibility."""
        terms = SDRFWriter._resolve_organisms_list(llm, pride)
        return terms[0] if terms else None

    @staticmethod
    def _resolve_organisms_list(
        llm: Dict[str, Any], pride: Dict[str, Any]
    ) -> List[str]:
        """
        Return ALL organisms for this dataset as a list of SDRF term strings.

        Each term is formatted as  NT=<name>;AC=<NCBITaxon:XXXX>  where available.
        The list preserves the order from LLM (preferred) or PRIDE fallback.
        """
        terms: List[str] = []

        # LLM
        resp = llm.get("characteristics[organism]", {})
        parsed = resp.get("parsed", {})
        if isinstance(parsed, dict):
            values = parsed.get("value") or parsed.get("NT")
            accessions = parsed.get("accession") or parsed.get("AC")

            if isinstance(values, list):
                if not isinstance(accessions, list):
                    accessions = [None] * len(values)
                for v, a in zip(values, accessions):
                    v_str = SDRFWriter._coerce_str(v)
                    ac = a if isinstance(a, str) else None
                    if v_str:
                        mapped = OntologyMapper.map_organism(v_str, ac)
                        if mapped:
                            terms.append(mapped)
            elif values:
                v_str = SDRFWriter._coerce_str(values)
                ac = accessions[0] if isinstance(accessions, list) and accessions else accessions
                if not isinstance(ac, str):
                    ac = None
                if v_str:
                    mapped = OntologyMapper.map_organism(v_str, ac)
                    if mapped:
                        terms.append(mapped)

        if not terms and pride:
            for org in pride.get("organisms", []):
                if isinstance(org, dict):
                    name = org.get("name") or org.get("value", "")
                    acc = org.get("accession")
                    if name:
                        mapped = OntologyMapper.map_organism(name, acc)
                        if mapped:
                            terms.append(mapped)

        return terms if terms else []

    @staticmethod
    def _filename_matches_organism(filename_stem: str, organism_term: str) -> bool:
        """
        Return True if *filename_stem* contains keywords associated with the
        organism described by *organism_term* (NT=...;AC=... format).
        """
        fname = filename_stem.lower()

        # Extract name and taxid from the SDRF term string
        name = ""
        taxid = ""
        for part in organism_term.split(";"):
            if part.startswith("NT="):
                name = part[3:].lower()
            elif part.startswith("AC=") and "NCBITaxon:" in part:
                taxid = part.split("NCBITaxon:")[-1]

        # Match by taxid number (e.g. file names sometimes embed "9606")
        if taxid and re.search(rf"(?:^|[_\-\.]){re.escape(taxid)}(?:[_\-\.\s]|$)", fname):
            return True

        # Match by keyword lookup table
        for canonical, keywords in _ORG_FILENAME_KEYWORDS.items():
            if canonical in name or name in canonical:
                for kw in keywords:
                    if re.search(rf"(?:^|[_\-\.\s]){re.escape(kw)}(?:[_\-\.\s]|$)", fname):
                        return True
                break

        return False

    @staticmethod
    def _assign_organisms_per_file(
        raw_files: List[Dict[str, Any]],
        organism_terms: List[str],
    ) -> Dict[str, List[str]]:
        """
        Assign organism term(s) to each raw file.

        Rules:
        1. For single-organism datasets, every file gets that one organism.
        2. For multi-organism datasets, attempt filename keyword matching.
        3. Any organism that matches no file is assigned to ALL files (ensures
           every taxid appears in at least one SDRF row).
        4. Any file with no match gets all organisms (mixed-sample assumption).
        """
        if not organism_terms:
            return {f.get("fileName", ""): [] for f in raw_files}

        if len(organism_terms) == 1:
            return {f.get("fileName", ""): [organism_terms[0]] for f in raw_files}

        # Multi-organism: try filename matching
        assignment: Dict[str, List[str]] = {f.get("fileName", ""): [] for f in raw_files}
        unmatched_indices: set = set(range(len(organism_terms)))

        for f in raw_files:
            fname = f.get("fileName", "")
            stem = Path(fname).stem
            for i, term in enumerate(organism_terms):
                if SDRFWriter._filename_matches_organism(stem, term):
                    assignment[fname].append(term)
                    unmatched_indices.discard(i)

        # Organisms that matched no file → add to every file so all taxids appear
        for i in unmatched_indices:
            term = organism_terms[i]
            for fname in assignment:
                if term not in assignment[fname]:
                    assignment[fname].append(term)
            logger.debug(
                "Organism '%s' matched no filename \u2014 assigned to all files", term
            )

        # Files with no match → assign all organisms (assume mixed sample)
        for fname, orgs in assignment.items():
            if not orgs:
                assignment[fname] = list(organism_terms)

        return assignment

    def _assign_organisms_from_clustering(
        self,
        raw_files: List[Dict[str, Any]],
        file_assignments: Dict[str, Dict[str, Any]],
        fallback_organisms: List[str],
    ) -> Dict[str, List[str]]:
        """
        Assign organism term(s) to each raw file using file_assignments from clustering.

        If file_assignments contains organism info, use it. Otherwise, fall back to 
        the fallback_organisms list (dataset-level).

        Args:
            raw_files: List of file dicts with 'fileName'
            file_assignments: Dict[filename, {cluster_id, organism, taxid, ...}]
            fallback_organisms: List of dataset-level organism terms

        Returns:
            Dict[filename, List[organism_terms]]
        """
        assignment: Dict[str, List[str]] = {}
        
        for f in raw_files:
            fname = f.get("fileName", "")
            if fname in file_assignments:
                # Use organism from file_assignments
                org_name = file_assignments[fname].get("organism", "")
                if org_name:
                    assignment[fname] = [org_name]
                else:
                    assignment[fname] = fallback_organisms if fallback_organisms else []
            else:
                # Fallback to dataset-level organism
                assignment[fname] = fallback_organisms if fallback_organisms else []
        
        return assignment

    @staticmethod
    def _resolve_label(
        llm: Dict[str, Any], pride: Dict[str, Any]
    ) -> Optional[str]:
        """Resolve comment[label]."""
        resp = llm.get("comment[label]", {})
        parsed = resp.get("parsed", {})
        if isinstance(parsed, dict):
            value = SDRFWriter._coerce_str(parsed.get("value") or parsed.get("NT"))
            if value:
                mapped = OntologyMapper.map_label(value)
                # Only accept if the mapper resolved a valid ontology AC
                if mapped and ";AC=" in mapped:
                    return mapped
                # Unknown term — fall through to PRIDE and default

        # Infer from PRIDE quantification methods
        if pride:
            quant = pride.get("quantificationMethods", [])
            if quant and isinstance(quant[0], dict):
                name = quant[0].get("name", "")
                if name:
                    return OntologyMapper.map_label(name)

        return "NT=label free sample;AC=MS:1002038"

    @staticmethod
    def _resolve_instrument(
        llm: Dict[str, Any],
        spec: Dict[str, Any],
        pride: Dict[str, Any],
    ) -> Optional[str]:
        """Resolve comment[instrument] from spectral summary or PRIDE."""
        # Spectral summary (thermorawfileparser) takes highest priority
        instrument = spec.get("instrument")
        if instrument:
            return OntologyMapper.map_instrument(instrument)

        # LLM comment[instrument]
        resp = llm.get("comment[instrument]", {})
        parsed = resp.get("parsed", {})
        if isinstance(parsed, dict):
            value = SDRFWriter._coerce_str(parsed.get("value") or parsed.get("NT"))
            ac = parsed.get("accession") or parsed.get("AC")
            if value:
                return OntologyMapper.map_instrument(value, ac)

        # PRIDE instruments list
        if pride:
            instruments = pride.get("instruments", [])
            if instruments and isinstance(instruments[0], dict):
                name = instruments[0].get("name") or instruments[0].get("value")
                acc = instruments[0].get("accession")
                if name:
                    return OntologyMapper.map_instrument(name, acc)

        return None

    @staticmethod
    def _resolve_cleavage(llm: Dict[str, Any]) -> Optional[str]:
        """Resolve comment[cleavage agent details]."""
        resp = llm.get("comment[cleavage agent details]", {})
        parsed = resp.get("parsed", {})
        if isinstance(parsed, dict):
            value = SDRFWriter._coerce_str(parsed.get("value") or parsed.get("NT"))
            if value:
                return OntologyMapper.map_cleavage_agent(value)
        return None

    @staticmethod
    def _resolve_dissociation(
        llm: Dict[str, Any], spec: Dict[str, Any]
    ) -> Optional[str]:
        """Resolve comment[dissociation method]."""
        # Spectral summary fragmentation takes priority
        frag_methods = spec.get("fragmentation", [])
        method_filename = None
        # Check if stepped HCD is in spectral summary
        if frag_methods and any(
            "stepped" in m.lower() or "step" in m.lower()
            for m in frag_methods
        ):
            method_filename = "SteppedHCD"

        if frag_methods:
            primary = frag_methods[0]
            return OntologyMapper.map_dissociation(primary, method_filename)

        resp = llm.get("comment[dissociation method]", {})
        parsed = resp.get("parsed", {})
        if isinstance(parsed, dict):
            value = SDRFWriter._coerce_str(parsed.get("value") or parsed.get("NT"))
            if value:
                return OntologyMapper.map_dissociation(value, method_filename)

        return None

    @staticmethod
    def _resolve_crosslinker(llm: Dict[str, Any]) -> Optional[str]:
        """
        Resolve comment[cross-linker] from the LLM parsed response.

        The LLM comment_cross_linker prompt returns keys:
        NT, AC, CL, TA, MH, ML, SM, serialized, …
        """
        resp = llm.get("comment[cross-linker]", {})
        parsed = resp.get("parsed", {})
        if not isinstance(parsed, dict):
            return None

        nt = parsed.get("NT") or parsed.get("value")
        if not nt or str(nt).lower() in ("not available", "n/a", "none", "null", ""):
            return None

        # Look up full SDRF term from crosslinker definitions (preferred)
        xl_defs = SDRFWriter._load_crosslinker_defs()
        key = str(nt).lower().strip()
        if key in xl_defs:
            sdrf_term = xl_defs[key].get("sdrf_comment_cross_linker", "")
            if sdrf_term and ";AC=" in sdrf_term:
                return sdrf_term

        # Build manually from LLM fields
        parts = [f"NT={nt}"]

        ac = parsed.get("AC") or parsed.get("accession")
        if ac and str(ac).lower() not in ("null", "none", "n/a", ""):
            parts.append(f"AC={ac}")
        elif key in xl_defs and xl_defs[key].get("xlmod_accession"):
            parts.append(f"AC={xl_defs[key]['xlmod_accession']}")

        cl = parsed.get("CL")
        if cl and str(cl).lower() in ("yes", "no"):
            parts.append(f"CL={str(cl).lower()}")

        ta = parsed.get("TA")
        if ta and str(ta).lower() not in ("null", "none", "n/a", ""):
            parts.append(f"TA={ta}")

        return ";".join(parts)

    @staticmethod
    def _resolve_modifications(llm: Dict[str, Any]) -> List[str]:
        """
        Build list of comment[modification parameters] values.

        Ensures Carbamidomethyl (UNIMOD:4, Fixed) is always present.
        """
        mods: List[str] = []

        resp = llm.get("comment[modification parameters]", {})
        parsed = resp.get("parsed", {})

        if isinstance(parsed, dict):
            # LLM may return a list of mods or a dict with a 'modifications' key
            mod_list = parsed.get("modifications") or parsed.get("value")
            if isinstance(mod_list, list):
                for mod in mod_list:
                    if isinstance(mod, dict):
                        term = OntologyMapper.map_modification(
                            mod.get("name") or mod.get("NT"),
                            mod.get("unimod") or mod.get("AC"),
                            mod.get("target") or mod.get("TA"),
                            mod.get("type") or mod.get("MT") or "Variable",
                        )
                        if term:
                            mods.append(term)
                    elif isinstance(mod, str) and mod:
                        mods.append(mod)
            elif isinstance(mod_list, str) and mod_list:
                mods.append(mod_list)

        # Ensure Carbamidomethyl (Fixed) is present
        has_cam = any(
            "unimod:4" in m.lower() or "carbamidomethyl" in m.lower()
            for m in mods
        )
        if not has_cam:
            mods.insert(0, _CARBAMIDOMETHYL)

        return mods

    # ------------------------------------------------------------------
    # Template helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _taxonomy_template(organism_term: Optional[str]) -> Optional[str]:
        """Return the appropriate taxonomy SDRF template string."""
        if not organism_term:
            return None
        for taxon_ac, template in _TAXONOMY_TEMPLATE_MAP.items():
            if taxon_ac in organism_term:
                return template
        return None

    @staticmethod
    def _load_crosslinker_defs() -> Dict[str, Any]:
        """Load crosslinker definitions keyed by name/alias (lowercase)."""
        defs_path = Path(__file__).parent.parent.parent / "assets" / "crosslinker_definitions.json"
        if not defs_path.exists():
            return {}
        try:
            with open(defs_path) as fh:
                data = json.load(fh)
            result: Dict[str, Any] = {}
            for xl in data.get("crosslinkers", []):
                for key in [xl.get("name", ""), xl.get("short_name", ""), xl.get("full_name", "")] + xl.get("aliases", []):
                    if key:
                        result[key.lower()] = xl
            return result
        except Exception:
            return {}

    @staticmethod
    def _normalize_collision_energy(value: Optional[str]) -> Optional[str]:
        """
        Normalize collision energy values to match parse_sdrf pattern.

        Converts:
          "27 ± 6%"  -> "stepped 27+-6%"
          "30 NCE"   -> "30 NCE"  (pass-through)
          "30% NCE"  -> "30% NCE" (pass-through)
        """
        if not value:
            return value
        m = _STEPPED_CE_RE.match(value.strip())
        if m:
            return f"stepped {m.group(1)}+-{m.group(2)}%"
        return value
