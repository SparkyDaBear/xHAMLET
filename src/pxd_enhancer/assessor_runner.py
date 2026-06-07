"""
Assessor runner for XL-MS datasets.

Parses JSON outputs produced by thermorawfileparser and mzML_assessor,
then merges them with PRIDE and publication metadata to build a normalised
spectral summary.

Source priority (highest → lowest):
  thermorawfileparser > mzML_assessor > PRIDE API > publication text
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fragmentation method CV term mapping
# ---------------------------------------------------------------------------
FRAGMENTATION_MAP: Dict[str, str] = {
    "HR_HCD": "MS:1000422",       # HCD
    "HR_EThcD": "MS:1002678",     # EThcD
    "HR_IT_ETD": "MS:1000598",    # ETD
    "HR_IT_CID": "MS:1002472",    # CID (trap)
    "CID": "MS:1002472",
    "HCD": "MS:1000422",
    "ETD": "MS:1000598",
    "EThcD": "MS:1002678",
    "UVPD": "MS:1003247",
}

# Regex patterns for stepped HCD method filenames
_STEPPED_HCD_RE = re.compile(r"step(?:ped)?[\s_]?hcd", re.IGNORECASE)


class AssessorRunner:
    """
    Reads assessment/ directory outputs and builds a merged spectral summary.
    """

    def __init__(self, assessment_dir: Path) -> None:
        self.assessment_dir = Path(assessment_dir)

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def parse_per_file_metadata(self) -> List[Dict[str, Any]]:
        """
        Parse all *-metadata.json files produced by thermorawfileparser.

        Returns a list of dicts, one per file.
        """
        results = []
        for meta_path in sorted(self.assessment_dir.glob("*-metadata.json")):
            try:
                with open(meta_path) as fh:
                    data = json.load(fh)
                # Flatten the FileProperties / ScanSettings blocks
                entry = self._parse_rawfile_metadata(data, meta_path.name)
                results.append(entry)
            except Exception as exc:
                logger.warning("Could not parse %s: %s", meta_path.name, exc)
        logger.info("Parsed %d per-file metadata JSON(s)", len(results))
        return results

    def parse_study_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Parse study_metadata.json produced by mzML_assessor.

        Returns the parsed dict or None if the file is absent or unreadable.
        """
        study_path = self.assessment_dir / "study_metadata.json"
        if not study_path.exists():
            logger.warning("study_metadata.json not found in %s", self.assessment_dir)
            return None
        try:
            with open(study_path) as fh:
                data = json.load(fh)
            logger.info("Parsed study_metadata.json from mzML_assessor")
            return data
        except Exception as exc:
            logger.warning("Could not parse study_metadata.json: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Merge logic
    # ------------------------------------------------------------------

    def build_spectral_summary(
        self,
        pride_data: Optional[Dict[str, Any]] = None,
        publication_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build a normalised spectral_summary.json from all available sources.

        The priority chain (highest wins):
          thermorawfileparser > mzML_assessor > PRIDE > publication

        The summary is written to assessment/spectral_summary.json and
        also returned as a dict.
        """
        per_file = self.parse_per_file_metadata()
        study = self.parse_study_metadata()

        summary: Dict[str, Any] = {
            "source_files_parsed": len(per_file),
            "per_file": per_file,
        }

        # --- Instrument ---
        instrument = self._extract_instrument(per_file, study, pride_data)
        if instrument:
            summary["instrument"] = instrument

        # --- Fragmentation ---
        fragmentation = self._extract_fragmentation(per_file, study)
        if fragmentation:
            summary["fragmentation"] = fragmentation

        # --- Scan settings: mass range, resolution ---
        scan_settings = self._extract_scan_settings(per_file, study)
        summary.update(scan_settings)

        # --- FAIMS ---
        faims_cvs = self._extract_faims_cvs(per_file)
        if faims_cvs:
            summary["faims_compensation_voltages"] = faims_cvs

        # --- Detector / analyser ---
        analyser = self._extract_analyser(per_file, study)
        if analyser:
            summary["mass_analyser"] = analyser

        # Fallback: fill from PRIDE / publication for fields still absent
        if pride_data:
            self._fill_from_pride(summary, pride_data)
        if publication_data:
            self._fill_from_publication(summary, publication_data)

        # Write out
        out_path = self.assessment_dir / "spectral_summary.json"
        try:
            with open(out_path, "w") as fh:
                json.dump(summary, fh, indent=2)
            logger.info("spectral_summary.json written to %s", out_path)
        except Exception as exc:
            logger.warning("Could not write spectral_summary.json: %s", exc)

        return summary

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _parse_rawfile_metadata(
        self, data: Dict[str, Any], filename: str
    ) -> Dict[str, Any]:
        """Flatten a thermorawfileparser metadata JSON dict."""
        entry: Dict[str, Any] = {"filename": filename}

        # FileProperties block
        file_props = data.get("FileProperties", [])
        if isinstance(file_props, list):
            for prop in file_props:
                name = prop.get("Name", "")
                value = prop.get("Value", "")
                if name == "Instrument model":
                    entry["instrument_model"] = value
                elif name == "Instrument name":
                    entry["instrument_name"] = value
                elif name == "Instrument serial number":
                    entry["instrument_serial"] = value
                elif name == "Creation date":
                    entry["acquisition_date"] = value
                elif name == "Software version":
                    entry["software_version"] = value

        # ScanSettings block (list of scan windows)
        scan_settings = data.get("ScanSettings", [])
        if isinstance(scan_settings, list) and scan_settings:
            first_scan = scan_settings[0]
            entry["ms1_min_mz"] = first_scan.get("Min. mass", None)
            entry["ms1_max_mz"] = first_scan.get("Max. mass", None)
            entry["scan_count"] = first_scan.get("ScanCount", None)

        # Method filename (used for stepped HCD detection)
        method_filename = data.get("MethodFileName", "")
        if method_filename:
            entry["method_filename"] = method_filename
            if _STEPPED_HCD_RE.search(method_filename):
                entry["fragmentation_stepped_hcd"] = True

        return entry

    def _extract_instrument(
        self,
        per_file: List[Dict[str, Any]],
        study: Optional[Dict[str, Any]],
        pride_data: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """Return instrument model string from highest-priority source."""
        # thermorawfileparser — use first file that has one
        for entry in per_file:
            model = entry.get("instrument_model") or entry.get("instrument_name")
            if model:
                return model

        # mzML_assessor study summary
        if study:
            model = (
                study.get("instrument_model")
                or study.get("InstrumentModel")
                or study.get("instrument")
            )
            if model:
                return model

        # PRIDE
        if pride_data:
            instruments = pride_data.get("instruments", [])
            if instruments and isinstance(instruments[0], dict):
                return (
                    instruments[0].get("name")
                    or instruments[0].get("value")
                )

        return None

    def _extract_fragmentation(
        self,
        per_file: List[Dict[str, Any]],
        study: Optional[Dict[str, Any]],
    ) -> Optional[List[str]]:
        """Return list of fragmentation method names detected in this study."""
        methods: set = set()

        # Stepped HCD from method filename
        if any(e.get("fragmentation_stepped_hcd") for e in per_file):
            methods.add("Stepped HCD")

        # mzML_assessor fragmentation report
        if study:
            frag_list = study.get("fragmentation_methods", study.get("FragmentationMethods", []))
            if isinstance(frag_list, list):
                for method in frag_list:
                    if isinstance(method, str):
                        methods.add(method)

        return list(methods) if methods else None

    def _extract_scan_settings(
        self,
        per_file: List[Dict[str, Any]],
        study: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Return scan setting aggregates (ms1 m/z range, resolution hints)."""
        result: Dict[str, Any] = {}

        min_mzs = [e["ms1_min_mz"] for e in per_file if e.get("ms1_min_mz") is not None]
        max_mzs = [e["ms1_max_mz"] for e in per_file if e.get("ms1_max_mz") is not None]

        if min_mzs:
            result["ms1_mz_start"] = min(float(v) for v in min_mzs)
        if max_mzs:
            result["ms1_mz_end"] = max(float(v) for v in max_mzs)

        if study:
            for key in ("ms1_resolution", "ms2_resolution", "orbitrap_resolution"):
                val = study.get(key)
                if val is not None:
                    result[key] = val

        return result

    def _extract_faims_cvs(
        self, per_file: List[Dict[str, Any]]
    ) -> Optional[List[float]]:
        """Return sorted list of unique FAIMS compensation voltages, if present."""
        cvs: set = set()
        for entry in per_file:
            for cv in entry.get("faims_cvs", []):
                try:
                    cvs.add(float(cv))
                except (TypeError, ValueError):
                    pass
        return sorted(cvs) if cvs else None

    def _extract_analyser(
        self,
        per_file: List[Dict[str, Any]],
        study: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """Return mass analyser type string."""
        if study:
            analyser = study.get("mass_analyser") or study.get("MassAnalyser")
            if analyser:
                return analyser
        return None

    def _fill_from_pride(
        self, summary: Dict[str, Any], pride_data: Dict[str, Any]
    ) -> None:
        """Backfill missing summary fields from PRIDE project metadata."""
        if "instrument" not in summary:
            instruments = pride_data.get("instruments", [])
            if instruments and isinstance(instruments[0], dict):
                name = instruments[0].get("name") or instruments[0].get("value")
                if name:
                    summary["instrument"] = name

    def _fill_from_publication(
        self, summary: Dict[str, Any], publication_data: Dict[str, Any]
    ) -> None:
        """Backfill missing summary fields from publication metadata."""
        # Only fill instrument if still absent
        if "instrument" not in summary:
            data = publication_data.get("data", {})
            if isinstance(data, dict):
                instrument = data.get("instrument")
                if instrument:
                    summary["instrument"] = instrument
