#!/usr/bin/env python3
"""Filter PXDs into a curated subset using SDRF + LLM extraction artifacts.

Criteria:
1) Proteome-wide experimental context in lysate/in-cell/whole-cell settings.
2) Any reported cross-linker in SDRF.
3) Model-organism taxon ID present (defaults include 9606, 4932, etc.).
4) Submission scale above cutoff (default: >10 raw files).

The script outputs a filtered version of the master CSV containing only PXDs
that satisfy all criteria.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


DEFAULT_MODEL_TAXIDS = {
    9606,   # Homo sapiens
    10090,  # Mus musculus
    10116,  # Rattus norvegicus
    4932,   # Saccharomyces cerevisiae
    559292, # Saccharomyces cerevisiae S288C
    7227,   # Drosophila melanogaster
    6239,   # Caenorhabditis elegans
    7955,   # Danio rerio
    3702,   # Arabidopsis thaliana
}

NAME_TO_TAXID = {
    "homo sapiens": 9606,
    "human": 9606,
    "hek": 9606,
    "hek293": 9606,
    "hek293t": 9606,
    "mus musculus": 10090,
    "mouse": 10090,
    "rattus norvegicus": 10116,
    "rat": 10116,
    "saccharomyces cerevisiae": 4932,
    "yeast": 4932,
    "drosophila melanogaster": 7227,
    "fruit fly": 7227,
    "caenorhabditis elegans": 6239,
    "c. elegans": 6239,
    "danio rerio": 7955,
    "zebrafish": 7955,
    "arabidopsis thaliana": 3702,
    "escherichia coli": 562,
    "e. coli": 562,
}


def _repo_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter curated PXDs from pxd_data and subset the master CSV."
    )
    parser.add_argument(
        "results_dir",
        help="Path to pxd_data results directory (contains PXD*/).",
    )
    parser.add_argument(
        "--master-csv",
        default=str(_repo_dir() / "assets" / "crosslinking_datasets_subset.csv"),
        help="Master CSV to subset (default: assets/crosslinking_datasets_subset.csv).",
    )
    parser.add_argument(
        "--output-csv",
        default=str(_repo_dir() / "assets" / "crosslinking_datasets_curated_subset.csv"),
        help="Output CSV path for curated subset.",
    )
    parser.add_argument(
        "--min-raw-files",
        type=int,
        default=10,
        help="Minimum raw file threshold (strictly greater than this value).",
    )
    parser.add_argument(
        "--model-taxids",
        default=",".join(str(t) for t in sorted(DEFAULT_MODEL_TAXIDS)),
        help="Comma-separated model organism taxids (e.g., 9606,4932,10090).",
    )
    parser.add_argument(
        "--report-tsv",
        default="",
        help="Optional path to write per-PXD criteria report TSV.",
    )
    return parser.parse_args()


def _parse_model_taxids(raw: str) -> Set[int]:
    values: Set[int] = set()
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            values.add(int(token))
        except ValueError:
            raise ValueError(f"Invalid taxid in --model-taxids: {token}") from None
    if not values:
        raise ValueError("No valid model taxids provided.")
    return values


def _read_tsv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _extract_taxids_from_text(text: str) -> Set[int]:
    taxids: Set[int] = set()
    for m in re.finditer(r"NCBITaxon:(\d+)", text, flags=re.IGNORECASE):
        taxids.add(int(m.group(1)))
    low = text.lower()
    for name, tid in NAME_TO_TAXID.items():
        if name in low:
            taxids.add(tid)
    return taxids


def _extract_taxids_from_master_field(taxids_field: str) -> Set[int]:
    out: Set[int] = set()
    if not taxids_field:
        return out
    for m in re.finditer(r"\d+", taxids_field):
        out.add(int(m.group(0)))
    return out


def _extract_taxids_from_sdrf(rows: Sequence[Dict[str, str]]) -> Set[int]:
    taxids: Set[int] = set()
    for row in rows:
        for value in row.values():
            if not value:
                continue
            taxids.update(_extract_taxids_from_text(value))
    return taxids


def _collect_sdrf_text(rows: Sequence[Dict[str, str]]) -> str:
    chunks: List[str] = []
    for row in rows:
        for value in row.values():
            if value:
                chunks.append(str(value))
    return "\n".join(chunks).lower()


def _raw_file_count_from_sdrf(rows: Sequence[Dict[str, str]]) -> int:
    if not rows:
        return 0
    return len(rows)


def _criteria_material_type_whole_cell_lysate(rows: Sequence[Dict[str, str]]) -> bool:
    """Return True if any SDRF row has characteristics[material type] == whole cell lysate."""
    for row in rows:
        for key, value in row.items():
            if key.strip().lower() == "characteristics[material type]":
                if str(value or "").strip().lower() == "whole cell lysate":
                    return True
    return False


def _criteria_proteome_context(sdrf_text: str, llm_text: str) -> bool:
    text = f"{sdrf_text}\n{llm_text}"
    context_tokens = (
        "in-cell",
        "in cell",
        "in-cellulo",
        "whole-cell",
        "whole cell",
        "cell lysate",
        "whole-cell lysate",
        "whole cell lysate",
        "lysate",
    )
    proteome_tokens = (
        "proteome-wide",
        "proteome wide",
        "whole proteome",
        "global proteome",
        "large-scale proteome",
        "proteome-level",
        "proteomic profiling by mass spectrometry",
    )
    has_context = any(tok in text for tok in context_tokens)
    has_proteome_signal = any(tok in text for tok in proteome_tokens)
    return has_context and has_proteome_signal


def _looks_like_reported_crosslinker(value: str) -> bool:
    v = value.strip().lower()
    if not v:
        return False
    if v in {"not available", "na", "n/a", "none", "null"}:
        return False
    return True


def _criteria_crosslinker_reported_in_sdrf(rows: Sequence[Dict[str, str]]) -> bool:
    for row in rows:
        for key, value in row.items():
            if key.strip().lower() == "comment[cross-linker]":
                if _looks_like_reported_crosslinker(str(value or "")):
                    return True
    return False


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text()
    except OSError:
        return ""


def _load_master_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Sequence[Dict[str, str]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _iter_pxd_dirs(results_dir: Path) -> Iterable[Path]:
    for child in sorted(results_dir.iterdir()):
        if child.is_dir() and re.fullmatch(r"PXD\d+", child.name):
            yield child


def _evaluate_pxd(
    pxd_dir: Path,
    model_taxids: Set[int],
    min_raw_files: int,
    master_taxids: Set[int],
) -> Dict[str, object]:
    pxd = pxd_dir.name
    sdrf_path = pxd_dir / "sdrf" / f"{pxd}.sdrf.tsv"
    llm_path = pxd_dir / "llm" / "responses.json"

    if not sdrf_path.exists():
        return {
            "pxd": pxd,
            "has_sdrf": False,
            "raw_count": 0,
            "proteome_context": False,
            "has_crosslinker": False,
            "model_organism": False,
            "taxids": set(),
            "passes": False,
        }

    try:
        sdrf_rows = _read_tsv(sdrf_path)
    except Exception:
        return {
            "pxd": pxd,
            "has_sdrf": False,
            "raw_count": 0,
            "proteome_context": False,
            "has_crosslinker": False,
            "model_organism": False,
            "taxids": set(),
            "passes": False,
        }

    raw_count = _raw_file_count_from_sdrf(sdrf_rows)
    llm_text = _safe_read_text(llm_path).lower()
    sdrf_text = _collect_sdrf_text(sdrf_rows)
    taxids = _extract_taxids_from_sdrf(sdrf_rows) | master_taxids

    # Primary signal: characteristics[material type] == "whole cell lysate" (set by
    # updated LLM prompt).  Fall back to free-text heuristic for older cached SDRFs.
    proteome_context = (
        _criteria_material_type_whole_cell_lysate(sdrf_rows)
        or _criteria_proteome_context(sdrf_text, llm_text)
    )
    has_crosslinker = _criteria_crosslinker_reported_in_sdrf(sdrf_rows)
    model_organism = len(taxids & model_taxids) > 0
    scale_ok = raw_count > min_raw_files

    material_type_match = _criteria_material_type_whole_cell_lysate(sdrf_rows)
    passes = proteome_context and has_crosslinker and model_organism and scale_ok

    return {
        "pxd": pxd,
        "has_sdrf": True,
        "raw_count": raw_count,
        "proteome_context": proteome_context,
        "material_type_match": material_type_match,
        "has_crosslinker": has_crosslinker,
        "model_organism": model_organism,
        "scale_ok": scale_ok,
        "taxids": taxids,
        "passes": passes,
    }


def _write_report_tsv(path: Path, evaluations: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "pxd",
                "has_sdrf",
                "raw_count",
                "proteome_context",
                "material_type_match",
                "has_crosslinker",
                "model_organism",
                "scale_ok",
                "taxids",
                "passes",
            ]
        )
        for e in evaluations:
            writer.writerow(
                [
                    e.get("pxd", ""),
                    e.get("has_sdrf", False),
                    e.get("raw_count", 0),
                    e.get("proteome_context", False),
                    e.get("material_type_match", False),
                    e.get("has_crosslinker", False),
                    e.get("model_organism", False),
                    e.get("scale_ok", False),
                    ";".join(str(x) for x in sorted(e.get("taxids", set()))),
                    e.get("passes", False),
                ]
            )


def main() -> int:
    args = _parse_args()

    results_dir = Path(args.results_dir)
    master_csv = Path(args.master_csv)
    output_csv = Path(args.output_csv)

    if not results_dir.exists() or not results_dir.is_dir():
        print(f"Results directory does not exist: {results_dir}", file=sys.stderr)
        return 1
    if not master_csv.exists():
        print(f"Master CSV does not exist: {master_csv}", file=sys.stderr)
        return 1

    try:
        model_taxids = _parse_model_taxids(args.model_taxids)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    master_rows = _load_master_rows(master_csv)
    master_taxids_map: Dict[str, Set[int]] = {
        row.get("accession", ""): _extract_taxids_from_master_field(row.get("taxids", ""))
        for row in master_rows
    }

    evaluations = [
        _evaluate_pxd(
            pxd_dir,
            model_taxids=model_taxids,
            min_raw_files=args.min_raw_files,
            master_taxids=master_taxids_map.get(pxd_dir.name, set()),
        )
        for pxd_dir in _iter_pxd_dirs(results_dir)
    ]

    curated_pxds = {e["pxd"] for e in evaluations if e.get("passes", False)}
    filtered_rows = [row for row in master_rows if row.get("accession", "") in curated_pxds]

    if not master_rows:
        print(f"Master CSV has no rows: {master_csv}", file=sys.stderr)
        return 1

    _write_csv(output_csv, filtered_rows, fieldnames=list(master_rows[0].keys()))

    if args.report_tsv:
        _write_report_tsv(Path(args.report_tsv), evaluations)

    print(f"Total PXDs evaluated: {len(evaluations)}")
    print(f"Curated PXDs passing all criteria: {len(curated_pxds)}")
    print(f"Master CSV input rows: {len(master_rows)}")
    print(f"Filtered CSV output rows: {len(filtered_rows)}")
    print(f"Output written: {output_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
