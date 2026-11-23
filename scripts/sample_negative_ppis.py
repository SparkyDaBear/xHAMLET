#!/usr/bin/env python3
"""Sample a size-matched negative-control set of ReLink PPIs for AlphaFold 3.

Negatives are catalog PPIs supported by at least one passing ReLink crosslink
that appear in neither Complex Portal nor hu.MAP 3.0 (``ppi`` table built by
scripts/ppi_index.py). Each negative is matched to one reference (positive)
pair on combined residue count, so ipTM comparisons between the two sets are
not confounded by system size. Sequence lengths come from the same sources
build_af3_ppi_jobs.py uses: --sequence-fasta first, then the per-PXD search
FASTAs. Pairs without both sequences are excluded from the pool.

The output TSV feeds build_af3_ppi_jobs.py --pair-file.

Example:
    python scripts/sample_negative_ppis.py \\
        --reference-manifest af3_ppi_jobs/complex_portal100/manifest.tsv \\
        --sequence-fasta reference_data/uniprot_fasta/taxid_9606_reviewed.fasta --require-sequence-fasta \\
        --pxd-file af3_ppi_jobs/negative100/human_only_pxds.txt \\
        --seed 7684858753 --out af3_ppi_jobs/negative100/negative_pairs.tsv
"""

from __future__ import annotations

import argparse
import csv
import random
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_af3_ppi_jobs import DEFAULT_DATABASE, find_search_fastas, load_search_sequences  # noqa: E402
from sync_result_database import read_pxds  # noqa: E402

OUTPUT_COLUMNS = [
    "accession_a", "accession_b", "length_a", "length_b", "total_residues",
    "matched_reference_job", "matched_reference_total_residues",
    "relink_match_count", "relink_unambiguous_match_count", "relink_project_count",
    "relink_best_xi_score", "pxds",
]
TOLERANCES = (0.05, 0.10, 0.20, 0.40)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database-path", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--data-dir", type=Path, default=Path("store"))
    parser.add_argument(
        "--reference-manifest", type=Path, required=True,
        help="manifest.tsv of the positive AF3 batch; one size target per unique job_name",
    )
    parser.add_argument("--sequence-fasta", type=Path, nargs="*", default=[])
    parser.add_argument(
        "--require-sequence-fasta", action="store_true",
        help=(
            "Only sample pairs whose accessions both appear in --sequence-fasta (e.g. the reviewed human "
            "proteome), keeping the negative set in the same species as human-only references"
        ),
    )
    parser.add_argument(
        "--unambiguous-only", action="store_true",
        help="Only sample pairs with at least one unambiguous supporting crosslink",
    )
    parser.add_argument(
        "--pxd-file", type=Path,
        help="Only count crosslink evidence from PXDs listed in this file (e.g. species-verified datasets)",
    )
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def reference_targets(manifest: Path) -> list[tuple[str, int]]:
    targets: dict[str, int] = {}
    with manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("total_residues"):
                targets.setdefault(row["job_name"], int(row["total_residues"]))
    return sorted(targets.items())


def load_candidates(database_path: Path, unambiguous_only: bool) -> tuple[list[sqlite3.Row], dict[tuple[str, str], list[str]]]:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    where = "relink_match_count > 0 AND complex_portal_complex_count = 0 AND humap3_complex_count = 0"
    if unambiguous_only:
        where += " AND relink_unambiguous_match_count > 0"
    pairs = connection.execute(f"SELECT * FROM ppi WHERE {where} ORDER BY accession_a, accession_b").fetchall()
    pxds: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in connection.execute(
        """
        SELECT DISTINCT cmp.accession_a, cmp.accession_b, project.accession AS pxd
        FROM crosslink_match_ppi cmp
        JOIN crosslink_match cm USING (crosslink_match_id)
        JOIN mzid_document USING (mzid_document_id)
        JOIN search_run USING (search_run_id)
        JOIN pipeline_run USING (pipeline_run_id)
        JOIN project USING (project_id)
        WHERE cm.pass_threshold = 1
        """
    ):
        pxds[(row["accession_a"], row["accession_b"])].add(row["pxd"])
    connection.close()
    return pairs, {pair: sorted(values) for pair, values in pxds.items()}


def resolve_lengths(pairs, pxds_by_pair, data_dir: Path, preferred: dict[str, str]) -> dict[tuple[str, str], tuple[int, int]]:
    """Mirror build_af3_ppi_jobs: the first PXD (sorted) emits the job, preferred sequences win."""
    fasta_cache: dict[str, dict[str, str]] = {}
    lengths: dict[tuple[str, str], tuple[int, int]] = {}
    for row in pairs:
        pair = (row["accession_a"], row["accession_b"])
        for pxd in pxds_by_pair.get(pair, []):
            if pxd not in fasta_cache:
                fasta_cache[pxd] = load_search_sequences(find_search_fastas(data_dir / pxd))
            sequences = fasta_cache[pxd]
            seq_a = preferred.get(pair[0]) or sequences.get(pair[0])
            seq_b = preferred.get(pair[1]) or sequences.get(pair[1])
            if seq_a and seq_b:
                lengths[pair] = (len(seq_a), len(seq_b))
                break
    return lengths


def size_matched_sample(targets, pool: dict[tuple[str, str], int], rng: random.Random):
    available = dict(pool)
    order = list(targets)
    rng.shuffle(order)
    picks = []
    for job_name, target in order:
        candidates = []
        for tolerance in TOLERANCES:
            candidates = sorted(p for p, total in available.items() if abs(total - target) <= tolerance * target)
            if candidates:
                break
        if not candidates:
            best = min(abs(total - target) for total in available.values())
            candidates = sorted(p for p, total in available.items() if abs(total - target) == best)
        pair = rng.choice(candidates)
        picks.append((pair, job_name, target))
        del available[pair]
    return picks


def main() -> int:
    args = parse_args()
    targets = reference_targets(args.reference_manifest)
    pairs, pxds_by_pair = load_candidates(args.database_path, args.unambiguous_only)
    if args.pxd_file:
        allowed = set(read_pxds([], args.pxd_file))
        pxds_by_pair = {
            pair: kept for pair, values in pxds_by_pair.items() if (kept := [p for p in values if p in allowed])
        }
        pairs = [row for row in pairs if (row["accession_a"], row["accession_b"]) in pxds_by_pair]
        print(f"Restricted evidence to {len(allowed)} PXDs from {args.pxd_file}")
    preferred = load_search_sequences(args.sequence_fasta)
    if args.require_sequence_fasta:
        if not preferred:
            raise SystemExit("--require-sequence-fasta needs at least one --sequence-fasta")
        pairs = [row for row in pairs if row["accession_a"] in preferred and row["accession_b"] in preferred]
    lengths = resolve_lengths(pairs, pxds_by_pair, args.data_dir, preferred)
    print(f"Reference targets: {len(targets)}; negative candidates: {len(pairs)}; with sequences: {len(lengths)}")
    if len(lengths) < len(targets):
        raise SystemExit("Not enough negative candidates with sequences to match every reference pair")

    picks = size_matched_sample(targets, {pair: a + b for pair, (a, b) in lengths.items()}, random.Random(args.seed))
    rows_by_pair = {(row["accession_a"], row["accession_b"]): row for row in pairs}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(OUTPUT_COLUMNS)
        for pair, job_name, target in sorted(picks):
            row = rows_by_pair[pair]
            length_a, length_b = lengths[pair]
            writer.writerow([
                *pair, length_a, length_b, length_a + length_b, job_name, target,
                row["relink_match_count"], row["relink_unambiguous_match_count"], row["relink_project_count"],
                row["relink_best_xi_score"], ";".join(pxds_by_pair.get(pair, [])),
            ])
    print(f"Wrote {len(picks)} size-matched negative pairs: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
