#!/usr/bin/env python3
"""Publish compact, paged linear-search data for the static results explorer."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from export_search_results import LINEAR_COLUMNS, MAP_COLUMNS

PAGE_SIZE = 100
CHUNK_SIZE = 5000
COLUMNS = [
    "protein_accessions", "peptide", "modified_peptide", "peptide_starts",
    "xi_score", "charge", "search_group", "run", "scan", "scan_title", "scan_id",
]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_rows(path: Path, columns: list[str]):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or set(columns) - set(reader.fieldnames):
            raise ValueError(f"{path}: missing required CSV columns")
        for row in reader:
            if None in row or any(row.get(key) is None for key in columns):
                raise ValueError(f"{path}:{reader.line_num}: malformed CSV row")
            yield row


def save_chunk(output: Path, accession: str, number: int, rows: list[list[str]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(payload, compresslevel=6, mtime=0)
    digest = hashlib.sha256(compressed).hexdigest()
    relative = f"{accession}/{number:05d}-{digest}.json.gz"
    destination = output / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if file_hash(destination) != digest:
            raise ValueError(f"Existing chunk does not match its filename: {destination}")
    else:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            try:
                handle.write(compressed)
                handle.flush()
                os.replace(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)
    return relative


def export_project(accession: str, folder: Path, output: Path, chunk_size: int) -> dict:
    linear = folder / "linear.csv"
    mapping = folder / "scan_map.csv"
    before = {"linear_sha256": file_hash(linear), "scan_map_sha256": file_hash(mapping)}
    scans = {}
    seen = set()
    for row in csv_rows(mapping, MAP_COLUMNS):
        scan_id = row["scan_id"]
        if not scan_id or scan_id in seen:
            raise ValueError(f"{mapping}: missing or duplicate scan ID {scan_id!r}")
        seen.add(scan_id)
        if row["search_stage"] == "linear":
            scans[scan_id] = [row[key] for key in ("search_group", "run", "scan", "scan_title")]
    chunks = []
    pending = []
    count = 0
    for row in csv_rows(linear, LINEAR_COLUMNS):
        scan_id = row["scan_id"]
        if scan_id not in scans:
            raise ValueError(f"{linear}: scan {scan_id!r} has no linear provenance")
        if not row["protein_accessions"] or not row["peptide"]:
            raise ValueError(f"{linear}: scan {scan_id!r} has no protein or peptide")
        pending.append([row[key] for key in COLUMNS[:6]] + scans[scan_id] + [scan_id])
        count += 1
        if len(pending) == chunk_size:
            chunks.append(save_chunk(output, accession, len(chunks), pending))
            pending = []
    if pending:
        chunks.append(save_chunk(output, accession, len(chunks), pending))
    after = {"linear_sha256": file_hash(linear), "scan_map_sha256": file_hash(mapping)}
    if before != after:
        raise ValueError(f"{accession}: source CSV changed during export")
    return {"row_count": count, "chunks": chunks, **before}


def export(store: Path, catalog: Path, output: Path, chunk_size: int = CHUNK_SIZE) -> dict:
    if chunk_size < PAGE_SIZE or chunk_size % PAGE_SIZE:
        raise ValueError("Chunk size must be a positive multiple of the page size")
    store = store.resolve(strict=True)
    output = output.resolve()
    if output == store or store in output.parents or output in store.parents:
        raise ValueError("Output must be separate from the source store")
    snapshot = json.loads(catalog.read_text(encoding="utf-8"))
    accessions = {project["accession"] for project in snapshot["projects"]}
    sources = sorted(store.glob("PXD*/search_results/linear.csv"))
    if not sources:
        raise ValueError(f"No linear exports found in {store}")
    projects = {}
    output.mkdir(parents=True, exist_ok=True)
    for path in sources:
        accession = path.parent.parent.name
        if not re.fullmatch(r"PXD\d{6}", accession) or accession not in accessions:
            raise ValueError(f"Linear export is not represented in the catalog: {accession}")
        projects[accession] = export_project(accession, path.parent, output, chunk_size)
        print(f"{accession}: {projects[accession]['row_count']} rows", flush=True)
    index = {"version": 1, "page_size": PAGE_SIZE, "chunk_size": chunk_size,
             "columns": COLUMNS, "projects": projects}
    encoded = (json.dumps(index, indent=2) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(dir=output, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(encoded)
            handle.flush()
            os.replace(temporary, output / "index.json")
        finally:
            temporary.unlink(missing_ok=True)
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path("store"))
    parser.add_argument("--catalog", type=Path, default=Path("web/results-explorer/data/catalog.json"))
    parser.add_argument("--output", type=Path, default=Path("web/results-explorer/data/linear"))
    args = parser.parse_args()
    index = export(args.store, args.catalog, args.output)
    print(f"Published {len(index['projects'])} projects and "
          f"{sum(project['row_count'] for project in index['projects'].values())} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
