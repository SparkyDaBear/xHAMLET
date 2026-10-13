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
"""

from __future__ import annotations

import argparse
import fnmatch
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
) -> dict[str, dict[tuple[str, str], PairEvidence]]:
    if not database_path.is_file():
        raise FileNotFoundError(f"Result catalog not found: {database_path}. Run scripts/sync_result_database.py first.")
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        SELECT p.accession AS pxd, cm.alpha_proteins, cm.beta_proteins, cm.xi_score, cm.crosslink_match_id
        FROM crosslink_match cm
        JOIN mzid_document md USING (mzid_document_id)
        JOIN search_run sr USING (search_run_id)
        JOIN pipeline_run pr USING (pipeline_run_id)
        JOIN project p USING (project_id)
        WHERE cm.pass_threshold = 1
        """
    ).fetchall()
    connection.close()

    by_pxd: dict[str, dict[tuple[str, str], PairEvidence]] = {}
    for row in rows:
        pxd = row["pxd"]
        if pxd_patterns and not any(fnmatch.fnmatchcase(pxd.upper(), pattern.upper()) for pattern in pxd_patterns):
            continue
        alpha_proteins = json.loads(row["alpha_proteins"] or "[]")
        beta_proteins = json.loads(row["beta_proteins"] or "[]")
        is_ambiguous = len(alpha_proteins) != 1 or len(beta_proteins) != 1
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
    return by_pxd


def find_search_fasta(pxd_dir: Path) -> Path | None:
    fasta_dir = pxd_dir / "relink" / "fasta"
    if not fasta_dir.is_dir():
        return None
    candidates = sorted(fasta_dir.glob("*.fa")) + sorted(fasta_dir.glob("*.fasta")) + sorted(fasta_dir.glob("*.faa"))
    return candidates[0] if candidates else None


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

    for line in fasta_path.read_text(encoding="utf-8", errors="replace").splitlines():
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


def main() -> int:
    args = parse_args()
    by_pxd = load_pair_evidence(
        args.database_path,
        args.pxd,
        args.include_self_links,
        args.expand_ambiguous,
        args.max_ambiguous_group_size,
    )
    if not by_pxd:
        print("No passing inter-protein crosslink pairs matched the given filters.", file=sys.stderr)
        return 1

    manifest_rows: list[str] = [
        "pxd\tprotein_a\tprotein_b\tsupporting_crosslinks\tmax_xi_score\tambiguous\tjob_name\tjson_path\tslurm_path\tstatus"
    ]
    slurm_paths: list[Path] = []
    written = skipped = 0

    for pxd, pairs in sorted(by_pxd.items()):
        pxd_dir = args.data_dir / pxd
        fasta_path = find_search_fasta(pxd_dir)
        sequences = load_fasta_sequences(fasta_path) if fasta_path else {}
        if not sequences:
            print(f"Warning: no search FASTA found for {pxd} under {pxd_dir}/relink/fasta; skipping its pairs", file=sys.stderr)

        for (protein_a, protein_b), evidence in sorted(pairs.items()):
            if evidence.supporting_crosslinks < args.min_supporting:
                continue
            sequence_a = sequences.get(protein_a)
            sequence_b = sequences.get(protein_b)
            job_name = f"{pxd}__{sanitize_name(protein_a)}__{sanitize_name(protein_b)}"
            json_path = args.out_dir / pxd / f"{job_name}.json"
            slurm_path = args.out_dir / pxd / f"{job_name}.slurm"
            job_out_dir = args.out_dir / pxd / job_name

            if not sequence_a or not sequence_b:
                missing = protein_a if not sequence_a else protein_b
                print(f"Warning: sequence for accession '{missing}' not found in {fasta_path}; skipping {job_name}", file=sys.stderr)
                manifest_rows.append(
                    f"{pxd}\t{protein_a}\t{protein_b}\t{evidence.supporting_crosslinks}\t"
                    f"{evidence.max_xi_score or ''}\t{evidence.ambiguous}\t{job_name}\t\t\tmissing_sequence"
                )
                skipped += 1
                continue

            if not args.dry_run:
                json_path.parent.mkdir(parents=True, exist_ok=True)
                json_path.write_text(build_job_json(job_name, sequence_a, sequence_b), encoding="utf-8")
                slurm_path.write_text(build_slurm_script(job_name, json_path, job_out_dir, args), encoding="utf-8")
                slurm_paths.append(slurm_path)
            manifest_rows.append(
                f"{pxd}\t{protein_a}\t{protein_b}\t{evidence.supporting_crosslinks}\t"
                f"{evidence.max_xi_score or ''}\t{evidence.ambiguous}\t{job_name}\t{json_path}\t{slurm_path}\tready"
            )
            written += 1

    if not args.dry_run:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        submit_all_path = args.out_dir / "submit_all.sh"
        submit_all_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
        submit_all_lines += [f'sbatch "{p.resolve()}"' for p in slurm_paths]
        submit_all_path.write_text("\n".join(submit_all_lines) + "\n", encoding="utf-8")
        submit_all_path.chmod(0o755)
        print(f"Submit helper: {submit_all_path}")

        if args.submit:
            for slurm_path in slurm_paths:
                subprocess.run(["sbatch", str(slurm_path)], check=True)

        manifest_path = args.out_dir / "manifest.tsv"
        manifest_path.write_text("\n".join(manifest_rows) + "\n", encoding="utf-8")
        print(f"Manifest: {manifest_path}")

    print(f"Jobs ready: {written}, skipped (missing sequence or below threshold): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
