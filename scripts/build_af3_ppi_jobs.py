#!/usr/bin/env python3
"""Single-entry AlphaFold 3 PPI wrapper: query, JSON, and Slurm submission generation.

Reads the xHAMLET result catalog (see scripts/sync_result_database.py) for passing,
non-decoy inter-protein crosslink_match rows, resolves each protein pair to full-length
sequences from the per-PXD ReLink search FASTA (<pxd_dir>/relink/fasta/*.fa*), and writes
for every unique pair: one two-chain AF3 job JSON, one ready-to-submit Slurm script
(GPU data-pipeline + inference, no array indexing needed), plus a manifest TSV and a
`submit_all.sh` helper that sbatches every generated job.

Unlike the upstream colleague-provided run.sh helper, this script does not split
multi-record FASTAs into independent single-chain jobs — each pair becomes one real
two-chain complex prediction.

Examples:
    python scripts/build_af3_ppi_jobs.py --database-path xhamlet-results.sqlite3 \
        --data-dir store --out-dir af3_ppi_jobs
    python scripts/build_af3_ppi_jobs.py --pxd PXD031997 --min-supporting 2
    python scripts/build_af3_ppi_jobs.py --data-dir store --out-dir af3_ppi_jobs --submit
    python scripts/build_af3_ppi_jobs.py --data-dir store --out-dir af3_ppi_jobs/cohort \\
        --commands-file af3_ppi_jobs/cohort/commands.txt --matches-file af3_ppi_jobs/cohort/matches.tsv
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ACCESSION_HEADER_RE = re.compile(r"^(?:sp|tr)\|([^|]+)\|")
DEFAULT_DATABASE = Path("xhamlet-results.sqlite3")
DEFAULT_OUT_DIR = Path("af3_ppi_jobs")


@dataclass
class PairEvidence:
    protein_a: str
    protein_b: str
    supporting_crosslinks: int = 0
    max_xi_score: float | None = None
    match_examples: list[str] = field(default_factory=list)
    ambiguous: bool = False
    # Unique crosslinks (peptide pair + residue positions), oriented to protein_a / protein_b.
    crosslinks: dict[tuple[str, str, str, str], dict] = field(default_factory=dict)


def positions_for(accession: str, positions: list[str]) -> str:
    """Return the 'start-end' residue ranges that belong to one accession."""
    prefix = f"{accession}:"
    return ";".join(sorted(p[len(prefix):] for p in positions if p.startswith(prefix)))


def record_crosslink(evidence: PairEvidence, row: sqlite3.Row, alpha_proteins: list[str], beta_proteins: list[str]) -> None:
    """Add one passing match to the pair's unique-crosslink table, oriented A/B."""
    alpha_positions = json.loads(row["alpha_positions"] or "[]")
    beta_positions = json.loads(row["beta_positions"] or "[]")
    if evidence.protein_a in alpha_proteins and evidence.protein_b in beta_proteins:
        peptide_a, peptide_b = row["alpha_sequence"], row["beta_sequence"]
        positions_a = positions_for(evidence.protein_a, alpha_positions)
        positions_b = positions_for(evidence.protein_b, beta_positions)
    else:
        peptide_a, peptide_b = row["beta_sequence"], row["alpha_sequence"]
        positions_a = positions_for(evidence.protein_a, beta_positions)
        positions_b = positions_for(evidence.protein_b, alpha_positions)
    key = (peptide_a or "", peptide_b or "", positions_a, positions_b)
    entry = evidence.crosslinks.setdefault(
        key, {"peptide_a": key[0], "peptide_b": key[1], "positions_a": positions_a, "positions_b": positions_b,
              "n_psms": 0, "max_xi_score": None}
    )
    entry["n_psms"] += 1
    if row["xi_score"] is not None:
        entry["max_xi_score"] = max(entry["max_xi_score"] or row["xi_score"], row["xi_score"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database-path", type=Path, default=DEFAULT_DATABASE, help="xHAMLET SQLite result catalog")
    parser.add_argument("--data-dir", type=Path, required=True, help="Root directory containing PXD*/relink/fasta/*.fa*")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for AF3 job JSONs")
    parser.add_argument("--pxd", nargs="+", metavar="PXD_OR_MASK", help="Restrict to matching PXD accessions")
    parser.add_argument(
        "--min-supporting",
        type=int,
        default=1,
        help="Minimum number of distinct passing crosslinks required to accept a pair (default: 1)",
    )
    parser.add_argument(
        "--include-self-links",
        action="store_true",
        help="Also emit homodimer jobs for crosslinks mapping both sides to the same accession",
    )
    parser.add_argument(
        "--expand-ambiguous",
        action="store_true",
        help=(
            "Enumerate candidate pairs for crosslinks whose alpha/beta protein assignment is ambiguous "
            "(peptide shared across multiple accessions, e.g. homologous constructs/isoforms). Each "
            "generated pair is flagged 'ambiguous' in the manifest since the true partner is unresolved."
        ),
    )
    parser.add_argument(
        "--max-ambiguous-group-size",
        type=int,
        default=3,
        help="Skip expansion when either side's candidate accession list exceeds this size (default: 3)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report planned jobs without writing files")
    parser.add_argument(
        "--complex-portal-only", action="store_true",
        help="Use catalog-indexed pairs overlapping Complex Portal, preserving all ambiguous candidate mappings",
    )
    parser.add_argument(
        "--pair-file", type=Path,
        help=(
            "Use catalog-indexed pairs listed in this TSV (header with accession_a and accession_b columns, "
            "e.g. from scripts/sample_negative_ppis.py), preserving ambiguous candidate mappings like "
            "--complex-portal-only"
        ),
    )
    parser.add_argument(
        "--prediction-dir", type=Path, nargs="+", default=[DEFAULT_OUT_DIR],
        help="Existing AF3 job roots to check for completed models via manifests (default: af3_ppi_jobs)",
    )
    parser.add_argument(
        "--sequence-fasta", type=Path, nargs="+", default=[],
        help="Prefer exact-accession sequences from these FASTAs, falling back to each PXD's search FASTAs",
    )
    parser.add_argument(
        "--total-residues-below",
        type=int,
        help=(
            "Only generate commands for pairs whose combined residue count is strictly below N "
            "(e.g. 1200). Larger pairs stay in the manifest and matches file with status 'too_large'."
        ),
    )
    parser.add_argument(
        "--dedupe-pairs",
        action="store_true",
        help=(
            "Predict each unique protein pair (matched on accession IDs only) once across ALL PXDs: jobs live under "
            "<out-dir>/pairs/ with PXD-independent names, every PXD observation points at the shared job, "
            "and pairs that already have a prediction are not queued again."
        ),
    )
    parser.add_argument(
        "--commands-file",
        type=Path,
        help="Write one 'sbatch <script>' command per line (nothing is submitted). Pair with --matches-file to filter.",
    )
    parser.add_argument(
        "--matches-file",
        type=Path,
        help=(
            "Write a TSV of the ReLink crosslinks behind every command (peptides, accessions, protein lengths, "
            "system size, xi score); the 'command_line' column is the line number in --commands-file"
        ),
    )
    parser.add_argument("--partition", default="standard", help="Slurm GPU partition (default: standard)")
    parser.add_argument("--gres", default="gpu:a100:1", help="Slurm --gres value (default: gpu:a100:1)")
    parser.add_argument(
        "--constraint",
        default="a100",
        help=(
            "Slurm --constraint value (default: a100). Restricts scheduling to nodes advertising the "
            "plain 'a100' feature, excluding MIG-partitioned nodes (features a100_1g/2g/3g) whose GRES "
            "can otherwise satisfy a generic --gres=gpu:a100:1 request with a fractional-memory slice. "
            "Pass '' to disable."
        ),
    )
    parser.add_argument("--cpus-per-task", type=int, default=16, help="Slurm --cpus-per-task (default: 16)")
    parser.add_argument("--mem", default="64G", help="Slurm --mem (default: 64G)")
    parser.add_argument("--time", default="12:00:00", help="Slurm --time (default: 12:00:00)")
    parser.add_argument("--account", default="ncems_cr_default", help="Optional Slurm --account")
    parser.add_argument(
        "--submit", action="store_true", help="Immediately sbatch each generated job (default: generate only)"
    )
    return parser.parse_args()


def load_pair_evidence(
    database_path: Path,
    pxd_patterns: list[str] | None,
    include_self_links: bool,
    expand_ambiguous: bool,
    max_ambiguous_group_size: int,
    complex_portal_only: bool = False,
    pair_filter: set[tuple[str, str]] | None = None,
) -> dict[str, dict[tuple[str, str], PairEvidence]]:
    if not database_path.is_file():
        raise FileNotFoundError(f"Result catalog not found: {database_path}. Run scripts/sync_result_database.py first.")
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    query = """
        SELECT p.accession AS pxd, cm.alpha_proteins, cm.beta_proteins, cm.xi_score, cm.crosslink_match_id,
               cm.alpha_sequence, cm.beta_sequence, cm.alpha_positions, cm.beta_positions
        FROM crosslink_match cm
        JOIN mzid_document md USING (mzid_document_id)
        JOIN search_run sr USING (search_run_id)
        JOIN pipeline_run pr USING (pipeline_run_id)
        JOIN project p USING (project_id)
        WHERE cm.pass_threshold = 1
        """
    indexed = complex_portal_only or pair_filter is not None
    if indexed:
        query = """
        SELECT project.accession AS pxd,
               json_array(cmp.accession_a) AS alpha_proteins,
               json_array(cmp.accession_b) AS beta_proteins,
               cmp.peptide_a AS alpha_sequence, cmp.peptide_b AS beta_sequence,
               json_array(cmp.accession_a || ':' || cmp.positions_a) AS alpha_positions,
               json_array(cmp.accession_b || ':' || cmp.positions_b) AS beta_positions,
               cm.xi_score, cm.crosslink_match_id, cmp.is_ambiguous
        FROM crosslink_match_ppi cmp
        JOIN ppi USING (accession_a, accession_b)
        JOIN crosslink_match cm USING (crosslink_match_id)
        JOIN mzid_document USING (mzid_document_id)
        JOIN search_run USING (search_run_id)
        JOIN pipeline_run USING (pipeline_run_id)
        JOIN project USING (project_id)
        WHERE cm.pass_threshold = 1
        """
        if complex_portal_only:
            query += " AND ppi.complex_portal_complex_count > 0"
    rows = connection.execute(query).fetchall()
    connection.close()

    by_pxd: dict[str, dict[tuple[str, str], PairEvidence]] = {}
    for row in rows:
        pxd = row["pxd"]
        if pxd_patterns and not any(fnmatch.fnmatchcase(pxd.upper(), pattern.upper()) for pattern in pxd_patterns):
            continue
        alpha_proteins = json.loads(row["alpha_proteins"] or "[]")
        beta_proteins = json.loads(row["beta_proteins"] or "[]")
        if pair_filter is not None and tuple(sorted((alpha_proteins[0], beta_proteins[0]))) not in pair_filter:
            continue
        is_ambiguous = (
            bool(row["is_ambiguous"]) if indexed
            else len(alpha_proteins) != 1 or len(beta_proteins) != 1
        )
        if is_ambiguous:
            if not expand_ambiguous:
                continue
            if len(alpha_proteins) > max_ambiguous_group_size or len(beta_proteins) > max_ambiguous_group_size:
                continue
        candidate_pairs = {tuple(sorted((a, b))) for a in alpha_proteins for b in beta_proteins}
        for protein_a, protein_b in candidate_pairs:
            if protein_a == protein_b and not include_self_links:
                continue
            pair_map = by_pxd.setdefault(pxd, {})
            evidence = pair_map.setdefault((protein_a, protein_b), PairEvidence(protein_a, protein_b))
            evidence.supporting_crosslinks += 1
            evidence.ambiguous = evidence.ambiguous or is_ambiguous
            if row["xi_score"] is not None:
                evidence.max_xi_score = max(evidence.max_xi_score or row["xi_score"], row["xi_score"])
            if len(evidence.match_examples) < 3:
                evidence.match_examples.append(str(row["crosslink_match_id"]))
            record_crosslink(evidence, row, alpha_proteins, beta_proteins)
    return by_pxd


FASTA_SUFFIXES = {".fa", ".fas", ".fasta", ".faa"}


def find_search_fastas(pxd_dir: Path) -> list[Path]:
    """All FASTAs ReLink may have searched (taxid FASTA, PRIDE-supplied files, their combination)."""
    fasta_dir = pxd_dir / "relink" / "fasta"
    if not fasta_dir.is_dir():
        return []
    return sorted(path for path in fasta_dir.iterdir() if path.suffix.lower() in FASTA_SUFFIXES)


def load_search_sequences(fastas: list[Path]) -> dict[str, str]:
    sequences: dict[str, str] = {}
    for fasta_path in fastas:
        for accession, sequence in load_fasta_sequences(fasta_path).items():
            sequences.setdefault(accession, sequence)
    return sequences


def load_fasta_sequences(fasta_path: Path) -> dict[str, str]:
    sequences: dict[str, str] = {}
    header_accession: str | None = None
    header_token: str | None = None
    chunks: list[str] = []

    def flush() -> None:
        if header_accession is None:
            return
        sequence = "".join(chunks).upper()
        if sequence:
            sequences[header_accession] = sequence
            if header_token and header_token != header_accession:
                sequences.setdefault(header_token, sequence)

    for line in fasta_path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if line.startswith(">"):
            flush()
            header = line[1:].strip()
            match = ACCESSION_HEADER_RE.match(header)
            header_accession = match.group(1) if match else header.split()[0]
            header_token = header.split()[0]
            chunks = []
        else:
            chunks.append(line.strip())
    flush()
    return sequences


def sanitize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def build_job_json(job_name: str, sequence_a: str, sequence_b: str) -> str:
    payload = {
        "name": job_name,
        "sequences": [
            {"protein": {"id": "A", "sequence": sequence_a}},
            {"protein": {"id": "B", "sequence": sequence_b}},
        ],
        "modelSeeds": [1],
        "dialect": "alphafold3",
        "version": 1,
    }
    return json.dumps(payload, indent=2)


SLURM_TEMPLATE = """#!/usr/bin/env bash
#SBATCH --job-name=af3_{job_name}
#SBATCH --partition={partition}
{account_line}#SBATCH --gres={gres}
{constraint_line}#SBATCH --cpus-per-task={cpus_per_task}
#SBATCH --mem={mem}
#SBATCH --time={time}
#SBATCH --output={job_name}_%j.out

# Auto-generated by scripts/build_af3_ppi_jobs.py - one JSON, one job.
set -euo pipefail
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

ALPHAFOLD3_BASE="/storage/icds/RISE/sw8/alphafold3"
ALPHAFOLD3_DB="${{ALPHAFOLD3_BASE}}/alphafold3/databases"
ALPHAFOLD3_WEIGHTS="${{ALPHAFOLD3_BASE}}/alphafold3_weights"
ALPHAFOLD3_CONTAINER="${{ALPHAFOLD3_BASE}}/singularity/alphafold3_x86.sif"

if command -v apptainer >/dev/null 2>&1; then
  RUNNER="apptainer"
elif command -v singularity >/dev/null 2>&1; then
  RUNNER="singularity"
else
  echo "ERROR: Neither apptainer nor singularity found in PATH." >&2
  exit 1
fi

JOB_JSON="{json_path}"
OUTDIR="{out_dir}"
mkdir -p "${{OUTDIR}}"

RUN_INPUT_DIR="$(mktemp -d)"
INFER_INPUT_DIR="$(mktemp -d)"
trap 'rm -rf "${{RUN_INPUT_DIR}}" "${{INFER_INPUT_DIR}}"' EXIT
cp "${{JOB_JSON}}" "${{RUN_INPUT_DIR}}/"

echo "Running {job_name}: ${{JOB_JSON}}"

# Phase 1: data pipeline (CPU-heavy: MSA/template search)
"${{RUNNER}}" run \\
  --bind "${{RUN_INPUT_DIR}}:/root/af_input" \\
  --bind "${{OUTDIR}}:/root/af_output" \\
  --bind "${{ALPHAFOLD3_WEIGHTS}}:/root/models" \\
  --bind "${{ALPHAFOLD3_DB}}:/root/public_databases" \\
  "${{ALPHAFOLD3_CONTAINER}}" \\
  --input_dir=/root/af_input \\
  --model_dir=/root/models \\
  --db_dir=/root/public_databases \\
  --output_dir=/root/af_output \\
  --run_data_pipeline=true \\
  --run_inference=false

# AF3 lowercases the job name for its own output subdirectory; feed inference
# the *_data.json (with precomputed MSA) it wrote there, not the bare input.
SANITIZED_NAME="$(echo "{job_name}" | tr '[:upper:]' '[:lower:]')"
DATA_JSON="${{OUTDIR}}/${{SANITIZED_NAME}}/${{SANITIZED_NAME}}_data.json"
[[ -f "${{DATA_JSON}}" ]] || {{ echo "ERROR: expected data JSON not found: ${{DATA_JSON}}" >&2; exit 1; }}

# Phase 2 (--force_output_dir=true) overwrites DATA_JSON in place, so archive
# phase 1's output first. This preserves evidence of what the data pipeline
# actually produced if inference fails early, and lets us validate it below.
PHASE1_ARCHIVE="${{OUTDIR}}/${{SANITIZED_NAME}}/${{SANITIZED_NAME}}_data.phase1.json"
cp "${{DATA_JSON}}" "${{PHASE1_ARCHIVE}}"

# Fail fast if phase 1 did not populate an unpaired MSA for every protein
# chain, rather than burning a GPU allocation only to hit AF3's "missing
# unpaired MSA" validation error during inference.
command -v python3 >/dev/null 2>&1 || {{ echo "ERROR: python3 not found in PATH for MSA validation." >&2; exit 1; }}
python3 - "${{PHASE1_ARCHIVE}}" <<'PYEOF'
import json, sys

path = sys.argv[1]
with open(path) as f:
    data = json.load(f)

missing = [
    seq["protein"].get("id", "?")
    for seq in data.get("sequences", [])
    if "protein" in seq and not seq["protein"].get("unpairedMsa")
]
if missing:
    print("ERROR: phase 1 data JSON is missing unpairedMsa for chain(s): %s (%s)" % (missing, path), file=sys.stderr)
    sys.exit(1)
PYEOF

cp "${{DATA_JSON}}" "${{INFER_INPUT_DIR}}/"

# Phase 2: inference (GPU)
"${{RUNNER}}" run --nv \\
  --bind "${{INFER_INPUT_DIR}}:/root/af_input" \\
  --bind "${{OUTDIR}}:/root/af_output" \\
  --bind "${{ALPHAFOLD3_WEIGHTS}}:/root/models" \\
  --bind "${{ALPHAFOLD3_DB}}:/root/public_databases" \\
  "${{ALPHAFOLD3_CONTAINER}}" \\
  --input_dir=/root/af_input \\
  --model_dir=/root/models \\
  --db_dir=/root/public_databases \\
  --output_dir=/root/af_output \\
  --run_data_pipeline=false \\
  --run_inference=true \\
  --force_output_dir=true

echo "Done: {job_name} -> ${{OUTDIR}}/"
"""


def build_slurm_script(job_name: str, json_path: Path, out_dir: Path, args: argparse.Namespace) -> str:
    account_line = f"#SBATCH --account={args.account}\n" if args.account else ""
    constraint_line = f"#SBATCH --constraint={args.constraint}\n" if args.constraint else ""
    return SLURM_TEMPLATE.format(
        job_name=job_name,
        partition=args.partition,
        account_line=account_line,
        gres=args.gres,
        constraint_line=constraint_line,
        cpus_per_task=args.cpus_per_task,
        mem=args.mem,
        time=args.time,
        json_path=json_path.resolve(),
        out_dir=out_dir.resolve(),
    )


MATCH_COLUMNS = [
    "pxd", "job_name", "status", "command_line", "uniprot_a", "uniprot_b", "peptide_a", "peptide_b",
    "positions_a", "positions_b", "protein_length_a", "protein_length_b", "total_residues",
    "max_xi_score", "n_psms", "ambiguous",
]
MANIFEST_HEADER = (
    "pxd\tprotein_a\tprotein_b\tsupporting_crosslinks\tmax_xi_score\tambiguous\tjob_name\tjson_path\tslurm_path\t"
    "status\ttotal_residues"
)


def find_existing_prediction_pairs(data_dir: Path) -> set[frozenset[str]]:
    """Accession pairs already promoted under <data_dir>/<PXD>/af3_predictions/*/pair.json."""
    pairs: set[frozenset[str]] = set()
    for pair_path in data_dir.glob("*/af3_predictions/*/pair.json"):
        pair = json.loads(pair_path.read_text(encoding="utf-8"))
        if pair.get("protein_a") and pair.get("protein_b") and (pair_path.parent / "model.cif").is_file():
            pairs.add(frozenset((pair["protein_a"], pair["protein_b"])))
    return pairs


def find_unpromoted_prediction_pairs(roots: list[Path]) -> set[frozenset[str]]:
    """Identify completed jobs from their manifests, including older per-PXD layouts."""
    pairs: set[frozenset[str]] = set()
    for root in roots:
        if not root.exists():
            print(f"Prediction root does not exist, skipping: {root}", file=sys.stderr)
            continue
        for manifest in root.rglob("manifest.tsv"):
            with manifest.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle, delimiter="\t"):
                    if not row.get("json_path"):
                        continue
                    json_path = Path(row["json_path"])
                    if not json_path.is_absolute() and not json_path.exists():
                        json_path = manifest.parent / json_path
                    job_name = row["job_name"]
                    if prediction_exists(json_path.parent / job_name, job_name):
                        pairs.add(frozenset((row["protein_a"], row["protein_b"])))
    return pairs


def prediction_exists(job_out_dir: Path, job_name: str) -> bool:
    # AF3 lowercases the job name for its own output subdirectory.
    name = job_name.lower()
    return (job_out_dir / name / f"{name}_model.cif").is_file()


def read_pair_file(path: Path) -> set[tuple[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or not {"accession_a", "accession_b"} <= set(reader.fieldnames):
            raise SystemExit(f"{path}: expected a TSV header with accession_a and accession_b columns")
        return {tuple(sorted((row["accession_a"], row["accession_b"]))) for row in reader}


def main() -> int:
    args = parse_args()
    by_pxd = load_pair_evidence(
        args.database_path,
        args.pxd,
        args.include_self_links,
        args.expand_ambiguous,
        args.max_ambiguous_group_size,
        args.complex_portal_only,
        read_pair_file(args.pair_file) if args.pair_file else None,
    )
    if not by_pxd:
        print("No passing inter-protein crosslink pairs matched the given filters.", file=sys.stderr)
        return 1

    manifest_rows: list[str] = [MANIFEST_HEADER]
    slurm_paths: list[Path] = []
    match_rows: list[list[str]] = []
    jobs: dict[tuple, dict] = {}
    status_counts: dict[str, int] = {}
    already_predicted = find_existing_prediction_pairs(args.data_dir) if args.dedupe_pairs else set()
    already_predicted.update(find_unpromoted_prediction_pairs(args.prediction_dir))
    print(f"Found {len(already_predicted)} already-predicted protein pairs.")
    preferred_sequences = load_search_sequences(args.sequence_fasta)
    if args.sequence_fasta:
        print(f"Preferred sequence FASTAs: {', '.join(str(path) for path in args.sequence_fasta)}")

    for pxd, pairs in sorted(by_pxd.items()):
        pxd_dir = args.data_dir / pxd
        fasta_paths = find_search_fastas(pxd_dir)
        fasta_path = ", ".join(str(path) for path in fasta_paths)
        sequences = load_search_sequences(fasta_paths)
        sequences.update(preferred_sequences)
        if not sequences:
            print(f"Warning: no search FASTA found for {pxd} under {pxd_dir}/relink/fasta; skipping its pairs", file=sys.stderr)

        for (protein_a, protein_b), evidence in sorted(pairs.items()):
            if evidence.supporting_crosslinks < args.min_supporting:
                continue
            sequence_a = sequences.get(protein_a)
            sequence_b = sequences.get(protein_b)
            observed_name = f"{pxd}__{sanitize_name(protein_a)}__{sanitize_name(protein_b)}"
            crosslinks = sorted(evidence.crosslinks.values(), key=lambda c: -(c["max_xi_score"] or 0))

            if not sequence_a or not sequence_b:
                missing = protein_a if not sequence_a else protein_b
                print(f"Warning: sequence for accession '{missing}' not found in {fasta_path}; skipping {observed_name}", file=sys.stderr)
                job = {"job_name": observed_name, "status": "missing_sequence", "command_line": "", "json": "", "slurm": ""}
                status_counts[job["status"]] = status_counts.get(job["status"], 0) + 1
                lengths = (str(len(sequence_a)) if sequence_a else "", str(len(sequence_b)) if sequence_b else "", "")
            else:
                total_residues = len(sequence_a) + len(sequence_b)
                # The key is the accession pair only; sequences are never compared. The hash just
                # keeps names unique when sanitizing accessions would make two names collide.
                digest = hashlib.sha1(f"{protein_a}|{protein_b}".encode()).hexdigest()[:8]
                key = (None if args.dedupe_pairs else pxd, protein_a, protein_b, digest)
                job = jobs.get(key)
                if job is None:
                    if args.dedupe_pairs:
                        job_name = f"{sanitize_name(protein_a)}__{sanitize_name(protein_b)}__{digest}"
                        job_dir = args.out_dir / "pairs"
                    else:
                        job_name, job_dir = observed_name, args.out_dir / pxd
                    json_path = job_dir / f"{job_name}.json"
                    slurm_path = job_dir / f"{job_name}.slurm"
                    job_out_dir = job_dir / job_name
                    job = {"job_name": job_name, "command_line": "", "json": str(json_path), "slurm": str(slurm_path)}
                    if args.total_residues_below is not None and total_residues >= args.total_residues_below:
                        job["status"] = "too_large"
                    elif prediction_exists(job_out_dir, job_name) or frozenset((protein_a, protein_b)) in already_predicted:
                        job["status"] = "already_predicted"
                    else:
                        job["status"] = "ready"
                        if not args.dry_run:
                            json_path.parent.mkdir(parents=True, exist_ok=True)
                            json_path.write_text(build_job_json(job_name, sequence_a, sequence_b), encoding="utf-8")
                            slurm_path.write_text(build_slurm_script(job_name, json_path, job_out_dir, args), encoding="utf-8")
                        slurm_paths.append(slurm_path)
                        # 1-based line number of this job in the commands file.
                        job["command_line"] = str(len(slurm_paths))
                    if job["status"] != "ready":
                        job["json"] = job["slurm"] = ""
                    jobs[key] = job
                    status_counts[job["status"]] = status_counts.get(job["status"], 0) + 1
                lengths = (str(len(sequence_a)), str(len(sequence_b)), str(total_residues))

            for crosslink in crosslinks:
                match_rows.append([
                    pxd, job["job_name"], job["status"], job["command_line"], protein_a, protein_b,
                    crosslink["peptide_a"], crosslink["peptide_b"],
                    crosslink["positions_a"], crosslink["positions_b"], *lengths,
                    "" if crosslink["max_xi_score"] is None else f"{crosslink['max_xi_score']:.4f}",
                    str(crosslink["n_psms"]), str(evidence.ambiguous),
                ])
            manifest_rows.append(
                f"{pxd}\t{protein_a}\t{protein_b}\t{evidence.supporting_crosslinks}\t"
                f"{evidence.max_xi_score or ''}\t{evidence.ambiguous}\t{job['job_name']}\t{job['json']}\t{job['slurm']}\t"
                f"{job['status']}\t{lengths[2]}"
            )

    if not args.dry_run:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        submit_all_path = args.out_dir / "submit_all.sh"
        submit_all_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
        submit_all_lines += [f'sbatch "{p.resolve()}"' for p in slurm_paths]
        submit_all_path.write_text("\n".join(submit_all_lines) + "\n", encoding="utf-8")
        submit_all_path.chmod(0o755)
        print(f"Submit helper: {submit_all_path}")

        if args.commands_file:
            args.commands_file.parent.mkdir(parents=True, exist_ok=True)
            args.commands_file.write_text(
                "".join(f'sbatch "{p.resolve()}"\n' for p in slurm_paths), encoding="utf-8"
            )
            print(f"Commands file ({len(slurm_paths)} commands, not submitted): {args.commands_file}")
        if args.matches_file:
            args.matches_file.parent.mkdir(parents=True, exist_ok=True)
            with args.matches_file.open("w", encoding="utf-8") as handle:
                handle.write("\t".join(MATCH_COLUMNS) + "\n")
                for row in match_rows:
                    handle.write("\t".join(row) + "\n")
            print(f"Matches file ({len(match_rows)} crosslinks): {args.matches_file}")

        if args.submit:
            for slurm_path in slurm_paths:
                subprocess.run(["sbatch", str(slurm_path)], check=True)

        manifest_path = args.out_dir / "manifest.tsv"
        manifest_path.write_text("\n".join(manifest_rows) + "\n", encoding="utf-8")
        print(f"Manifest: {manifest_path}")

    summary = ", ".join(f"{count} {status}" for status, count in sorted(status_counts.items()))
    print(f"Unique jobs: {len(slurm_paths)} ready; all pair outcomes: {summary or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
