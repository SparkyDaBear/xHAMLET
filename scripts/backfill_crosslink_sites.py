#!/usr/bin/env python3
"""Backfill catalog link-site annotations from checksum-verified mzIdentML."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sync_result_database import DatabaseSynchronizer, SQLiteConnection, parse_mzid, sha256_file


def backfill(database: Path, store: Path, skip_changed: set[str] | None = None) -> dict[str, int]:
    store = store.resolve(strict=True)
    remaining = set(skip_changed or ())
    with SQLiteConnection(database.resolve(strict=True)) as connection:
        DatabaseSynchronizer(connection, Path(__file__).resolve().parents[1]).create_schema()
        db = connection.connection
        version = db.execute("PRAGMA data_version").fetchone()[0]
        documents = db.execute("""
            SELECT d.mzid_document_id, p.accession, d.relative_path, d.source_sha256, d.is_complete
            FROM mzid_document d JOIN search_run s ON s.search_run_id=d.search_run_id
            JOIN pipeline_run r ON r.pipeline_run_id=s.pipeline_run_id
            JOIN project p ON p.project_id=r.project_id
            WHERE EXISTS (SELECT 1 FROM crosslink_match m WHERE m.mzid_document_id=d.mzid_document_id)
            ORDER BY d.mzid_document_id
        """).fetchall()
        updates = []
        skipped_matches = 0
        for doc_id, pxd, relative, checksum, complete in documents:
            base = (store / pxd).resolve(strict=True)
            source = (base / relative).resolve(strict=True)
            if store not in base.parents or base not in source.parents or not complete:
                raise ValueError(f"Invalid or incomplete source: {source}")
            if sha256_file(source) != checksum:
                key = f"{pxd}/{relative}"
                if key not in remaining:
                    raise ValueError(f"Source checksum differs from catalog: {source}")
                remaining.remove(key)
                count = db.execute("SELECT COUNT(*) FROM crosslink_match WHERE mzid_document_id=?",
                                   (doc_id,)).fetchone()[0]
                skipped_matches += count
                print(f"WARNING: {count} matches have unavailable sites because source changed: {source}", flush=True)
                continue
            parsed = parse_mzid(source)
            if not parsed["is_complete"] or parsed["metadata"].get("parse_error") or sha256_file(source) != checksum:
                raise ValueError(f"Invalid or changed source: {source}")
            indexed = {}
            for item in parsed["crosslinks"]:
                key = item["spectrum_native_id"], item["crosslink_group_key"]
                if key in indexed:
                    raise ValueError(f"Duplicate match identity in {source}: {key}")
                indexed[key] = item
            rows = db.execute("""
                SELECT crosslink_match_id, spectrum_native_id, crosslink_group_key,
                       alpha_sequence, beta_sequence, alpha_proteins, beta_proteins,
                       alpha_positions, beta_positions
                FROM crosslink_match WHERE mzid_document_id=?
            """, (doc_id,)).fetchall()
            for match_id, spectrum, group, alpha, beta, aprot, bprot, apos, bpos in rows:
                key = spectrum, group
                item = indexed.get(key)
                if item is None or (item["alpha_sequence"], item["beta_sequence"]) != (alpha, beta):
                    raise ValueError(f"Catalog match missing or changed in {source}: {key}")
                for side, field, value in (("alpha", "proteins", aprot), ("beta", "proteins", bprot),
                                           ("alpha", "positions", apos), ("beta", "positions", bpos)):
                    if item[f"{side}_{field}"] != json.loads(value):
                        raise ValueError(f"Protein mapping mismatch in {source}: {key}")
                updates.append((json.dumps(item["alpha_link_sites"]),
                                json.dumps(item["beta_link_sites"]), match_id))
            print(f"Verified {pxd}/{relative}: {len(rows)} matches", flush=True)
        if remaining:
            raise ValueError(f"Specified sources were not changed: {sorted(remaining)}")
        db.execute("BEGIN IMMEDIATE")
        try:
            if db.execute("PRAGMA data_version").fetchone()[0] != version:
                raise ValueError("Catalog changed during verification; retry")
            total = db.execute("SELECT COUNT(*) FROM crosslink_match").fetchone()[0]
            if len(updates) + skipped_matches != total:
                raise ValueError("Not all catalog matches were accounted for")
            db.execute("UPDATE crosslink_match SET alpha_link_sites=NULL, beta_link_sites=NULL")
            db.executemany("UPDATE crosslink_match SET alpha_link_sites=?, beta_link_sites=? WHERE crosslink_match_id=?",
                           updates)
            db.commit()
        except BaseException:
            db.rollback()
            raise
    result = {"total": total, "verified": len(updates), "unavailable": skipped_matches}
    print(f"Backfilled link sites: {result}", flush=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--skip-changed-source", action="append", default=[], metavar="PXD/RELATIVE_PATH")
    args = parser.parse_args()
    backfill(args.database, args.store, set(args.skip_changed_source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
