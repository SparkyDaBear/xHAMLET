#!/usr/bin/env python3
"""Fetch hu.MAP 3.0 and Complex Portal complexes and load them into the xHAMLET catalog.

These are the reference co-complex PPIs used to validate crosslink-supported protein pairs.
Each source is downloaded (once, with a recorded SHA-256 and provenance file) into
``reference_data/<source>/<release>/``, parsed into complexes and members, expanded to
unordered UniProt pairs, and written to four catalog tables: ``reference_source``,
``reference_complex``, ``reference_complex_member`` and ``reference_ppi``.

Scope (deliberate):
  * Complex Portal: human, curated only (9606.tsv). The ``9606_predicted.tsv`` file is
    hu.MAP imported into Complex Portal and would double-count hu.MAP 3.0.
  * hu.MAP 3.0: the complexes file with all confidence tiers (1 = best ... 6). Pair
    confidence is the best tier among the complexes containing the pair.
  * Pairs mean co-complex membership, not direct contact, and self pairs are not stored.
  * The two sources are not independent: hu.MAP 3.0 was trained and tested on Complex
    Portal, so agreement between them is not two confirmations.

Examples:
    python scripts/sync_reference_ppis.py
    python scripts/sync_reference_ppis.py --database-path databases/test.sqlite3 --no-fetch
    python scripts/sync_reference_ppis.py --force
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import re
import sys
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ppi_index import base_accession, ensure_schema as ppi_ensure_schema, refresh_ppi_index, summary_text  # noqa: E402
from sync_result_database import DEFAULT_LOCAL_DATABASE, DatabaseSynchronizer, open_database  # noqa: E402

DEFAULT_REFERENCE_DIR = Path("reference_data")
REQUEST_TIMEOUT = 300

SOURCES: dict[str, dict[str, str]] = {
    "complex_portal": {
        "url": "https://ftp.ebi.ac.uk/pub/databases/intact/complex/current/complextab/9606.tsv",
        "filename": "9606.tsv",
        "license": "CC0 (EMBL-EBI Complex Portal)",
        "citation": "Meldal BHM et al. Nucleic Acids Res 50:D578 (2022), doi:10.1093/nar/gkab991",
    },
    "humap3": {
        "url": "https://humap3.proteincomplexes.org/static/downloads/humap3/"
        "hu.MAP3.0_complexes_wConfidenceScores_total15326_wGenenames_20240922.csv",
        "filename": "hu.MAP3.0_complexes_wConfidenceScores_total15326_wGenenames_20240922.csv",
        "license": "CC-BY-4.0 (Hugging Face card); site states CC0 (+BY). Attribution required",
        "citation": "Fischer SN et al. bioRxiv (2024), doi:10.1101/2024.10.11.617930",
    },
}


def parse_complex_portal(path: Path) -> list[dict[str, Any]]:
    """Parse a Complex Portal ComplexTAB file; non-UniProt participants are counted and dropped."""
    complexes = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        next(reader)
        for row in reader:
            if len(row) < 6:
                continue
            members: dict[str, int | None] = {}
            dropped = 0
            for token in row[4].split("|"):
                participant, _, stoichiometry = token.partition("(")
                accession = base_accession(participant)
                if accession is None:
                    dropped += 1
                    continue
                count = int(stoichiometry.rstrip(")") or 0) or None
                previous = members.get(accession)
                members[accession] = count if previous is None else (previous + (count or 0))
            complexes.append({
                "complex_id": row[0], "name": row[1], "taxid": row[3], "tier": None,
                "evidence": row[5].split("(")[0], "members": members, "dropped": dropped,
            })
    return complexes


def parse_humap3(path: Path) -> list[dict[str, Any]]:
    complexes = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            accessions = {a for a in row["Uniprot_ACCs"].split() if base_accession(a)}
            complexes.append({
                "complex_id": row["HuMAP3_ID"], "name": row.get("genenames") or None, "taxid": "9606",
                "tier": int(row["ComplexConfidence"]), "evidence": None,
                "members": {base_accession(a): None for a in accessions},
                "dropped": len(row["Uniprot_ACCs"].split()) - len(accessions),
            })
    return complexes


def derive_pairs(complexes: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    """Unordered co-complex pairs (lower accession first); self pairs are not stored."""
    pairs: dict[tuple[str, str], dict[str, Any]] = {}
    for item in complexes:
        for pair in itertools.combinations(sorted(item["members"]), 2):
            entry = pairs.setdefault(pair, {"complex_ids": [], "best_tier": None, "evidence": set()})
            entry["complex_ids"].append(item["complex_id"])
            if item["tier"] is not None:
                entry["best_tier"] = item["tier"] if entry["best_tier"] is None else min(entry["best_tier"], item["tier"])
            if item["evidence"]:
                entry["evidence"].add(item["evidence"])
    return pairs


PARSERS = {"complex_portal": parse_complex_portal, "humap3": parse_humap3}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remote_release(name: str, source: dict[str, str]) -> str:
    """Release label: hu.MAP's date is in the file name; Complex Portal uses the file's Last-Modified date."""
    match = re.search(r"_(\d{8})\.", source["filename"])
    if match:
        return match.group(1)
    response = requests.head(source["url"], timeout=REQUEST_TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    return parsedate_to_datetime(response.headers["Last-Modified"]).strftime("%Y%m%d")


def fetch_source(name: str, source: dict[str, str], reference_dir: Path) -> Path:
    release = remote_release(name, source)
    release_dir = reference_dir / name / release
    target = release_dir / source["filename"]
    if target.is_file() and target.stat().st_size > 0:
        return target
    release_dir.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    print(f"Downloading {source['url']}", flush=True)
    try:
        with requests.get(source["url"], stream=True, timeout=REQUEST_TIMEOUT) as response:
            response.raise_for_status()
            with temporary.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    handle.write(chunk)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    provenance = {
        "source": name, "release": release, "url": source["url"], "sha256": sha256_file(target),
        "bytes": target.stat().st_size, "fetched_at": datetime.now(UTC).isoformat(),
        "license": source["license"], "citation": source["citation"],
    }
    (release_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return target


def local_source(name: str, source: dict[str, str], reference_dir: Path) -> Path:
    candidates = sorted((reference_dir / name).glob(f"*/{source['filename']}"))
    if not candidates:
        raise SystemExit(f"No local copy of {name} under {reference_dir}; run without --no-fetch.")
    return candidates[-1]


def ensure_schema(connection: Any) -> None:
    """Create the base result catalog (if absent), then the reference and PPI-index tables."""
    DatabaseSynchronizer(connection, Path(__file__).resolve().parents[1]).create_schema()
    ppi_ensure_schema(connection)


def load_source(connection: Any, name: str, path: Path, force: bool) -> str:
    source = SOURCES[name]
    release = path.parent.name
    digest = sha256_file(path)
    provenance_path = path.parent / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.is_file() else {}
    with connection.cursor() as cursor:
        cursor.execute("SELECT reference_source_id, sha256 FROM reference_source WHERE name = %s AND release = %s", (name, release))
        existing = cursor.fetchone()
    if existing and existing[1] == digest and not force:
        return f"{name} {release}: unchanged"

    complexes = PARSERS[name](path)
    pairs = derive_pairs(complexes)
    with connection.cursor() as cursor:
        if existing:
            cursor.execute("DELETE FROM reference_source WHERE reference_source_id = %s", (existing[0],))
        cursor.execute(
            "INSERT INTO reference_source (name, release, url, sha256, license, citation, fetched_at, complex_count, pair_count) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (name, release, provenance.get("url", source["url"]), digest, source["license"], source["citation"],
             provenance.get("fetched_at"), len(complexes), len(pairs)),
        )
        cursor.execute("SELECT reference_source_id FROM reference_source WHERE name = %s AND release = %s", (name, release))
        source_id = cursor.fetchone()[0]
        for item in complexes:
            cursor.execute(
                "INSERT INTO reference_complex (reference_source_id, complex_id, name, taxid, confidence_tier, evidence_code, "
                "member_count, dropped_participants) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (source_id, item["complex_id"], item["name"], item["taxid"], item["tier"], item["evidence"],
                 len(item["members"]), item["dropped"]),
            )
            cursor.execute(
                "SELECT reference_complex_id FROM reference_complex WHERE reference_source_id = %s AND complex_id = %s",
                (source_id, item["complex_id"]),
            )
            complex_key = cursor.fetchone()[0]
            for accession, stoichiometry in item["members"].items():
                cursor.execute(
                    "INSERT INTO reference_complex_member (reference_complex_id, accession, stoichiometry) VALUES (%s, %s, %s)",
                    (complex_key, accession, stoichiometry),
                )
        for (accession_a, accession_b), entry in pairs.items():
            cursor.execute(
                "INSERT INTO reference_ppi (reference_source_id, accession_a, accession_b, complex_count, complex_ids, "
                "best_tier, evidence_codes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (source_id, accession_a, accession_b, len(entry["complex_ids"]), json.dumps(entry["complex_ids"]),
                 entry["best_tier"], ";".join(sorted(entry["evidence"])) or None),
            )
    return f"{name} {release}: loaded {len(complexes)} complexes, {len(pairs)} pairs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reference-dir", type=Path, default=DEFAULT_REFERENCE_DIR, help="Download cache (default: reference_data)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--database-url", help="PostgreSQL connection URL")
    group.add_argument("--database-path", type=Path, help=f"SQLite catalog (default: {DEFAULT_LOCAL_DATABASE})")
    parser.add_argument("--source", choices=sorted(SOURCES), nargs="+", default=sorted(SOURCES), help="Sources to load")
    parser.add_argument("--no-fetch", action="store_true", help="Use files already under --reference-dir")
    parser.add_argument("--force", action="store_true", help="Reload even if the source file is unchanged")
    args = parser.parse_args()
    if args.database_url is None and args.database_path is None:
        args.database_path = DEFAULT_LOCAL_DATABASE
    return args


def main() -> int:
    args = parse_args()
    paths = {
        name: (local_source if args.no_fetch else fetch_source)(name, SOURCES[name], args.reference_dir)
        for name in args.source
    }
    with open_database(args) as connection:
        ensure_schema(connection)
        for name, path in paths.items():
            print(load_source(connection, name, path, args.force))
            connection.commit()
        print(summary_text(refresh_ppi_index(connection)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
