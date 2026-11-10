#!/usr/bin/env python3
"""Unified PPI index: one row per protein pair, with ReLink and reference-database evidence.

A "PPI" here is an unordered pair of distinct UniProt accessions (lower accession first).
This module owns the reference-PPI tables and the derived index that joins them to ReLink
crosslinks, so one indexed lookup returns everything known about a pair:

  reference_source / reference_complex / reference_complex_member / reference_ppi
      hu.MAP 3.0 and Complex Portal complexes and their co-complex pairs
      (loaded by scripts/sync_reference_ppis.py)
  crosslink_match_ppi
      each ReLink crosslink match expanded to its candidate protein pairs, with the peptides
      and residue positions oriented to accession_a / accession_b (derived from crosslink_match)
  ppi
      every pair seen in ReLink OR any reference source, with summary counts
  ppi_relink_detail / ppi_reference_detail
      views returning the individual ReLink observations / reference complexes for a pair

``refresh_ppi_index`` rebuilds the two derived tables from the catalog; it runs automatically
after ``sync_reference_ppis.py`` and ``sync_result_database.py``.

Examples:
    python scripts/ppi_index.py --database-path xhamlet-results.sqlite3
    sqlite3 -header -line xhamlet-results.sqlite3 "SELECT * FROM ppi WHERE accession_a='P84022' AND accession_b='Q13485'"
    sqlite3 -header -column xhamlet-results.sqlite3 "SELECT * FROM ppi_reference_detail WHERE accession_a='P84022' AND accession_b='Q13485'"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Base UniProt accession; Complex Portal may append an isoform ("-2") or chain ("-PRO_0000012345").
UNIPROT_RE = re.compile(
    r"^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-[A-Za-z0-9_]+)?$"
)


def base_accession(participant: str) -> str | None:
    match = UNIPROT_RE.match(participant)
    return match.group(1) if match else None


def normalize_accession(accession: str) -> str:
    """UniProt accessions lose isoform/chain suffixes; any other identifier is kept as is."""
    return base_accession(accession) or accession


def ddl(sqlite: bool) -> str:
    key = "INTEGER PRIMARY KEY AUTOINCREMENT" if sqlite else "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
    big = "INTEGER" if sqlite else "BIGINT"
    return f"""
CREATE TABLE IF NOT EXISTS reference_source (
    reference_source_id {key},
    name TEXT NOT NULL,
    release TEXT NOT NULL,
    url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    license TEXT,
    citation TEXT,
    fetched_at TEXT,
    complex_count INTEGER,
    pair_count INTEGER,
    UNIQUE (name, release)
);
CREATE TABLE IF NOT EXISTS reference_complex (
    reference_complex_id {key},
    reference_source_id {big} NOT NULL REFERENCES reference_source(reference_source_id) ON DELETE CASCADE,
    complex_id TEXT NOT NULL,
    name TEXT,
    taxid TEXT,
    confidence_tier INTEGER,
    evidence_code TEXT,
    member_count INTEGER NOT NULL,
    dropped_participants INTEGER NOT NULL DEFAULT 0,
    UNIQUE (reference_source_id, complex_id)
);
CREATE TABLE IF NOT EXISTS reference_complex_member (
    reference_complex_id {big} NOT NULL REFERENCES reference_complex(reference_complex_id) ON DELETE CASCADE,
    accession TEXT NOT NULL,
    stoichiometry INTEGER,
    PRIMARY KEY (reference_complex_id, accession)
);
CREATE INDEX IF NOT EXISTS reference_member_accession_idx ON reference_complex_member(accession);
CREATE TABLE IF NOT EXISTS reference_ppi (
    reference_source_id {big} NOT NULL REFERENCES reference_source(reference_source_id) ON DELETE CASCADE,
    accession_a TEXT NOT NULL,
    accession_b TEXT NOT NULL,
    complex_count INTEGER NOT NULL,
    complex_ids TEXT NOT NULL,
    best_tier INTEGER,
    evidence_codes TEXT,
    PRIMARY KEY (reference_source_id, accession_a, accession_b)
);
CREATE INDEX IF NOT EXISTS reference_ppi_pair_idx ON reference_ppi(accession_a, accession_b);
CREATE TABLE IF NOT EXISTS crosslink_match_ppi (
    crosslink_match_id {big} NOT NULL REFERENCES crosslink_match(crosslink_match_id) ON DELETE CASCADE,
    accession_a TEXT NOT NULL,
    accession_b TEXT NOT NULL,
    peptide_a TEXT,
    peptide_b TEXT,
    positions_a TEXT,
    positions_b TEXT,
    is_ambiguous INTEGER NOT NULL,
    PRIMARY KEY (crosslink_match_id, accession_a, accession_b)
);
CREATE INDEX IF NOT EXISTS crosslink_match_ppi_pair_idx ON crosslink_match_ppi(accession_a, accession_b);
CREATE TABLE IF NOT EXISTS ppi (
    ppi_id {key},
    accession_a TEXT NOT NULL,
    accession_b TEXT NOT NULL,
    relink_match_count INTEGER NOT NULL DEFAULT 0,
    relink_unambiguous_match_count INTEGER NOT NULL DEFAULT 0,
    relink_project_count INTEGER NOT NULL DEFAULT 0,
    relink_best_xi_score DOUBLE PRECISION,
    complex_portal_complex_count INTEGER NOT NULL DEFAULT 0,
    complex_portal_evidence_codes TEXT,
    humap3_complex_count INTEGER NOT NULL DEFAULT 0,
    humap3_best_tier INTEGER,
    UNIQUE (accession_a, accession_b)
);
CREATE INDEX IF NOT EXISTS ppi_accession_b_idx ON ppi(accession_b);
"""


VIEWS = {
    # One row per (protein, partner) in both orientations, so a protein is found with a single filter.
    "ppi_by_protein": """
SELECT accession_a AS accession, accession_b AS partner, ppi_id, relink_match_count, relink_unambiguous_match_count,
       relink_project_count, relink_best_xi_score, complex_portal_complex_count, complex_portal_evidence_codes,
       humap3_complex_count, humap3_best_tier
FROM ppi
UNION ALL
SELECT accession_b, accession_a, ppi_id, relink_match_count, relink_unambiguous_match_count,
       relink_project_count, relink_best_xi_score, complex_portal_complex_count, complex_portal_evidence_codes,
       humap3_complex_count, humap3_best_tier
FROM ppi
""",
    "ppi_relink_detail": """
SELECT cmp.accession_a, cmp.accession_b, project.accession AS pxd, run.taxid, cm.crosslink_match_id,
       cmp.peptide_a, cmp.peptide_b, cmp.positions_a, cmp.positions_b, cmp.is_ambiguous,
       cm.xi_score, cm.charge_state, cm.source_file, cm.scan_number
FROM crosslink_match_ppi cmp
JOIN crosslink_match cm ON cm.crosslink_match_id = cmp.crosslink_match_id
JOIN mzid_document doc ON doc.mzid_document_id = cm.mzid_document_id
JOIN search_run run ON run.search_run_id = doc.search_run_id
JOIN pipeline_run pipeline ON pipeline.pipeline_run_id = run.pipeline_run_id
JOIN project ON project.project_id = pipeline.project_id
""",
    "ppi_reference_detail": """
SELECT ppi.accession_a, ppi.accession_b, source.name AS source, source.release,
       complex.complex_id, complex.name AS complex_name, complex.confidence_tier,
       complex.evidence_code, complex.member_count
FROM ppi
JOIN reference_complex_member member_a ON member_a.accession = ppi.accession_a
JOIN reference_complex_member member_b
  ON member_b.reference_complex_id = member_a.reference_complex_id AND member_b.accession = ppi.accession_b
JOIN reference_complex complex ON complex.reference_complex_id = member_a.reference_complex_id
JOIN reference_source source ON source.reference_source_id = complex.reference_source_id
""",
}


def ensure_schema(connection: Any) -> None:
    """Create reference/PPI tables and views. The base result catalog must already exist."""
    sqlite = bool(getattr(connection, "is_sqlite", False))
    if sqlite:
        connection.execute_script(ddl(True))
    with connection.cursor() as cursor:
        if not sqlite:
            for statement in filter(None, (part.strip() for part in ddl(False).split(";"))):
                cursor.execute(statement)
        for name, query in VIEWS.items():
            if sqlite:
                cursor.execute(f"CREATE VIEW IF NOT EXISTS {name} AS {query}")
            else:
                cursor.execute(f"CREATE OR REPLACE VIEW {name} AS {query}")
    connection.commit()


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    return json.loads(value) if isinstance(value, str) else list(value)


def residue_ranges(raw_accession: str, positions: list[str]) -> str:
    prefix = f"{raw_accession}:"
    return ";".join(sorted(position[len(prefix):] for position in positions if position.startswith(prefix)))


def expand_match(row: tuple[Any, ...]) -> list[tuple[Any, ...]]:
    """One crosslink match to its distinct candidate pairs, oriented to the sorted accession pair."""
    match_id, alpha_sequence, beta_sequence, alpha_proteins, beta_proteins, alpha_positions, beta_positions = row
    alphas, betas = as_list(alpha_proteins), as_list(beta_proteins)
    alpha_positions, beta_positions = as_list(alpha_positions), as_list(beta_positions)
    ambiguous = int(len(alphas) != 1 or len(betas) != 1)
    pairs: dict[tuple[str, str], tuple[Any, ...]] = {}
    for alpha in alphas:
        for beta in betas:
            norm_alpha, norm_beta = normalize_accession(alpha), normalize_accession(beta)
            if norm_alpha == norm_beta:
                continue
            alpha_ranges, beta_ranges = residue_ranges(alpha, alpha_positions), residue_ranges(beta, beta_positions)
            if norm_alpha < norm_beta:
                key, orient = (norm_alpha, norm_beta), (alpha_sequence, beta_sequence, alpha_ranges, beta_ranges)
            else:
                key, orient = (norm_beta, norm_alpha), (beta_sequence, alpha_sequence, beta_ranges, alpha_ranges)
            pairs.setdefault(key, (match_id, key[0], key[1], *orient, ambiguous))
    return list(pairs.values())


REFRESH_PPI_SQL = """
INSERT INTO ppi (accession_a, accession_b, relink_match_count, relink_unambiguous_match_count,
                 relink_project_count, relink_best_xi_score, complex_portal_complex_count,
                 complex_portal_evidence_codes, humap3_complex_count, humap3_best_tier)
WITH latest AS (
    SELECT reference_source_id, name FROM reference_source source
    WHERE release = (SELECT MAX(release) FROM reference_source WHERE name = source.name)
),
pairs AS (
    SELECT accession_a, accession_b FROM crosslink_match_ppi
    UNION SELECT accession_a, accession_b FROM reference_ppi
),
relink AS (
    SELECT cmp.accession_a, cmp.accession_b, COUNT(*) AS matches,
           SUM(CASE WHEN cmp.is_ambiguous = 0 THEN 1 ELSE 0 END) AS unambiguous,
           COUNT(DISTINCT pipeline.project_id) AS projects, MAX(cm.xi_score) AS best_xi
    FROM crosslink_match_ppi cmp
    JOIN crosslink_match cm ON cm.crosslink_match_id = cmp.crosslink_match_id
    JOIN mzid_document doc ON doc.mzid_document_id = cm.mzid_document_id
    JOIN search_run run ON run.search_run_id = doc.search_run_id
    JOIN pipeline_run pipeline ON pipeline.pipeline_run_id = run.pipeline_run_id
    GROUP BY cmp.accession_a, cmp.accession_b
),
reference AS (
    SELECT ref.accession_a, ref.accession_b, latest.name, ref.complex_count, ref.best_tier, ref.evidence_codes
    FROM reference_ppi ref JOIN latest ON latest.reference_source_id = ref.reference_source_id
)
SELECT pairs.accession_a, pairs.accession_b,
       COALESCE(relink.matches, 0), COALESCE(relink.unambiguous, 0), COALESCE(relink.projects, 0), relink.best_xi,
       COALESCE(cp.complex_count, 0), cp.evidence_codes, COALESCE(hm.complex_count, 0), hm.best_tier
FROM pairs
LEFT JOIN relink ON relink.accession_a = pairs.accession_a AND relink.accession_b = pairs.accession_b
LEFT JOIN reference cp ON cp.accession_a = pairs.accession_a AND cp.accession_b = pairs.accession_b
     AND cp.name = 'complex_portal'
LEFT JOIN reference hm ON hm.accession_a = pairs.accession_a AND hm.accession_b = pairs.accession_b
     AND hm.name = 'humap3'
"""


def refresh_ppi_index(connection: Any) -> dict[str, int]:
    """Rebuild crosslink_match_ppi and ppi from the catalog in one transaction."""
    ensure_schema(connection)
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM ppi")
        cursor.execute("DELETE FROM crosslink_match_ppi")
        cursor.execute(
            "SELECT crosslink_match_id, alpha_sequence, beta_sequence, alpha_proteins, beta_proteins, "
            "alpha_positions, beta_positions FROM crosslink_match"
        )
        expanded = [pair for row in cursor.fetchall() for pair in expand_match(tuple(row))]
        for pair in expanded:
            cursor.execute(
                "INSERT INTO crosslink_match_ppi (crosslink_match_id, accession_a, accession_b, peptide_a, peptide_b, "
                "positions_a, positions_b, is_ambiguous) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                pair,
            )
        cursor.execute(REFRESH_PPI_SQL)
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN relink_match_count > 0 THEN 1 ELSE 0 END) FROM ppi")
        total, with_relink = cursor.fetchone()
        cursor.execute(
            "SELECT COUNT(*) FROM ppi WHERE relink_match_count > 0 AND "
            "(complex_portal_complex_count > 0 OR humap3_complex_count > 0)"
        )
        both = cursor.fetchone()[0]
    connection.commit()
    return {"ppis": total, "with_relink": with_relink or 0, "relink_and_reference": both, "relink_pairs": len(expanded)}


def main() -> int:
    from sync_result_database import DEFAULT_LOCAL_DATABASE, open_database

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--database-url", help="PostgreSQL connection URL")
    group.add_argument("--database-path", type=Path, help=f"SQLite catalog (default: {DEFAULT_LOCAL_DATABASE})")
    args = parser.parse_args()
    if args.database_url is None and args.database_path is None:
        args.database_path = DEFAULT_LOCAL_DATABASE
    with open_database(args) as connection:
        print(summary_text(refresh_ppi_index(connection)))
    return 0


def summary_text(counts: dict[str, int]) -> str:
    return (
        f"PPI index: {counts['ppis']} pairs ({counts['with_relink']} seen in ReLink, "
        f"{counts['relink_and_reference']} of those also in a reference source)"
    )


if __name__ == "__main__":
    raise SystemExit(main())
