# xHAMLET: Crosslinking Mass Spectrometry Metadata Pipeline

https://github.com/NCEMS/XLMS-PPI-working-group

xHAMLET processes PRIDE XL-MS studies and produces:
- Structured metadata enriched with LLM extraction
- SDRF files for crosslinking studies
- XiSearch configuration files
- Optional ReLink runs

## What The Pipeline Does

For each PXD accession, xHAMLET runs a staged workflow:

1. PRIDE metadata fetch
2. Publication fetch (PMID/PMCID, DOI fallback)
3. Raw processing (download, thermorawfileparser, optional mzML conversion)
4. Spectral merge (thermoraw + mzML_assessor + fallback data)
5. LLM metadata extraction
6. SDRF generation
7. SDRF validation
8. Xi config generation
9. Optional ReLink
10. Final metadata save

Detailed architecture: [documents/ARCHITECTURE.md](documents/ARCHITECTURE.md)

## Quick Start

### 1) Environment setup (Conda recommended)

```bash
# Installs Miniconda in ~/miniconda3 automatically when conda is unavailable.
bash src/setup.sh

# Create and activate the environment, then rerun setup to install dependencies.
source ~/miniconda3/etc/profile.d/conda.sh
conda create -n xhamlet python=3.11 -y
conda activate xhamlet
bash src/setup.sh
```

`src/setup.sh` installs Miniconda in `~/miniconda3` when `conda` is unavailable. With an active conda environment, it installs the `aria2c` downloader, ThermoRawFileParser, Java, a ReLink-compatible Nextflow 25.04 release, all Python dependencies, synchronizes the pinned ReLink submodule, and initializes `configs/config.yaml` from `config.yaml.sample` if it does not exist. Set `MINICONDA_PREFIX` to use another installation directory.

Alternative (venv):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set credentials:

```bash
export OPENAI_API_KEY="your-openai-key"
export NCBI_API_KEY="your-ncbi-key"   # optional
```

### 2) Verify config file in configs/

```bash
mkdir -p configs
cp config.yaml.sample configs/config.yaml
```

If you used `bash src/setup.sh`, this file is already created. Edit `configs/config.yaml` for model, paths, and defaults.

### 3) Run one PXD

```bash
python src/main.py --pxd PXD042173 --config configs/config.yaml --verbose
```

### 4) Batch run from TSV

```bash
python src/main.py --pxd-file assets/crosslinking_datasets_list.tsv --config configs/config.yaml
```

### 5) One Slurm job per PXD (ROAR)

The CPU-only template `assets/templates/xHAMLETfull.slurm` runs the full Python
pipeline, including ReLink with Singularity, in a single allocation per PXD.
It replaces the copied HAMLET Nextflow/GPU templates; xHAMLET does not need a GPU.
Defaults are `basic`, account `ncems_cr_default`, 16 CPUs, 64 GB, and seven days.
Edit the template's scheduler directives for a different allocation.

Export `OPENROUTER_API_KEY` or `OPENAI_API_KEY` before submission; Slurm inherits
the environment. No credentials are written into job scripts. The template uses
the existing ROAR conda installation and xhamlet environment; override
`CONDA_BASE` and `XHAMLET_ENV` in the submission environment if needed.

For the 50-dataset pilot, select the smallest positive RAW-file counts (ties
broken by accession), excluding the student's 13 datasets:

```bash
python src/job_scripts/gen_slurm_per_pxd.py \
  assets/templates/xHAMLETfull.slurm \
  assets/crosslinking_datasets_confident_subset.csv \
  -o assets/slurm/pilot50 \
  --count 50 --sort-by-raw-count \
  --exclude PXD003737 PXD006246 PXD014738 PXD010963 PXD022119 \
    PXD048965 PXD052923 PXD055356 PXD017020 PXD021648 PXD063968 \
    PXD022861 PXD025220
```

Add `--submit --batch 5 --dwell 2` to generate and submit. The generator accepts
an `accession`, `PXD`, or `PXDs` CSV column, or a headerless first-column PXD list.
Without selection flags it uses all accessions in CSV order. It rejects invalid
and duplicate accessions, insufficient eligible datasets, and changed scripts
in an existing output directory.
For reduced PRIDE download pressure, add `--max-concurrent 5`: this keeps one
Slurm job per PXD but links jobs into five independent `afterany` dependency
chains. A failed job does not prevent later jobs in its chain from starting.
The template requests 128 GB (xiSEARCH's heap is derived from it: 80% of 85%
of the allocation), passes `--force-taxid 9606`, and PRIDE FASTAs are BOM/CRLF-normalized.

Each batch directory contains:
- `PXD*.slurm`: one job script per dataset
- `selected_pxds.csv`: selected source metadata, in submission order
- `submitted_jobs.csv`: successful PXD/job-ID/script mappings, flushed after
  every submission; rerunning skips recorded PXDs and stops on submission errors
- `runs/PXD*/slurm_<jobid>.log`, `pipeline.log`, and `work/`

The submission manifest records scheduler acceptance, not pipeline success.
Use a fresh output directory for an intentional retry of failed or cancelled jobs;
the previous directory remains an audit trail and is not resubmitted automatically.

Results continue to use `store/PXD*/` (layout and git-tracking policy:
[documents/STORE_LAYOUT.md](documents/STORE_LAYOUT.md)). Existing caches are reused rather than
force-refreshed, and temporary assessment mzML files are cleaned. RAW files are
retained for ReLink. Log directories are created **before** `sbatch` so Slurm
can open them immediately.

After successful ReLink searches, `search_results/` contains compact
`linear.csv`, `crosslinks.csv`, and `scan_map.csv` files, each strictly below
50 MB. Linear exports contain rank-1 targets (not FDR-validated); crosslink
exports and the AF3 catalog use rank-1, FDR-passing non-decoy matches.
Backfill with `python scripts/export_search_results.py --all
--completed-pxd-file /tmp/exported_pxds.txt`, then refresh only successful PXDs
with `python scripts/sync_result_database.py --pxd-file /tmp/exported_pxds.txt
--force`. See the store-layout document for column definitions and failure handling.

ReLink uses a separate `.nextflow-run` launch directory per output group, avoiding
shared Nextflow history/cache locks between PXDs. Under Slurm,
`assets/relink_slurm_resources.config` caps local ReLink tasks to the allocation's
CPUs and 85% of its memory, with one task at a time; it does not submit nested jobs.
The template also gives every PXD its own Nextflow work directory.
xiSEARCH's Java heap is capped at 80% of its task memory, leaving additional
headroom for native allocations. ReLink mass-error calculation streams the
peaks TSV, projecting only required columns and filtering before collecting
the error values; it does not load the full peak-annotation table into RAM.
The mzML correction also streams one spectrum at a time, preserving MS1 peaks,
precursor metadata, chromatograms, and experimental settings.
Each ReLink invocation writes live console output to
`results/.nextflow-run/<run_name>.stdout.log`, rather than buffering it in the
parent Python process until completion. This preserves available diagnostics
when a job terminates abruptly.
Nextflow container images also use a private per-PXD cache, seeded with links to
existing shared images, to avoid concurrent image-promotion races. PRIDE FTP RAW
links use the equivalent HTTPS endpoint, with one RAW worker and two connections
per file in this template. Transfers retry transient failures up to three process
attempts, with 10/20-second backoff and a 20-minute timeout per attempt. aria2
also uses a bounded internal retry count; HTTP 429/5xx responses and transient
connection errors trigger the outer backoff.
Interrupted `.aria2` downloads are resumed rather than treated as
complete RAW files, and ReLink runs restore missing RAWs even when assessment
metadata is already cached. ReLink refuses to launch when any selected RAW is
missing, empty, or still has an `.aria2` marker, rather than searching a partial
dataset. `--limit` restricts this check to the selected RAW prefix.

Singularity ReLink runs automatically reuse the installed image at
`tools/relink/work/singularity/ghcr.io-bigbio-relink-1.0.0.img` when readable.
The xiSEARCH, recalibration, xiFDR, and format-correction processes reference that
file directly, so private per-PXD caches do not cause another GHCR pull.
Set `XHAMLET_RELINK_IMAGE` to an absolute path to use another local `.sif`/`.img`;
an explicitly configured missing or unreadable file fails configuration.
Without an override or the installed image, the existing registry behavior is
retained. SDRF parsing and RAW conversion use their own separate container images.
Scout processes retain their separate ReLink 1.1.0 image requirement.

## User Interface: Main CLI Commands

Single accession:

```bash
python src/main.py --pxd PXD042173 --config configs/config.yaml
```

Multiple accessions:

```bash
python src/main.py --pxd PXD017620 PXD042173 --config configs/config.yaml
```

Use cached data (skip fresh Stage 3-4 work):

```bash
python src/main.py --pxd PXD042173 --config configs/config.yaml --no-download
```

SDRF-only regeneration from cache:

```bash
python src/main.py --pxd PXD042173 --config configs/config.yaml --sdrf-only
```

Run ReLink:

```bash
python src/main.py --pxd PXD042173 --config configs/config.yaml --relink --relink-profile js2-m3-xl --relink-resume
```

Use a profile matching the installed container runtime: `docker`, `singularity`, or `apptainer`. The `js2-m3-medium` and `js2-m3-xl` profiles run ReLink through Docker with JS2 resource limits.

### ReLink Resource Defaults

xHAMLET injects a 32-CPU and 64-GB xiSEARCH cap for native Conda ReLink runs.
These limits are based on successful one-RAW PXD042173 validation runs and
avoid the excessive JVM garbage-collection pressure observed with larger
resource requests.

The `js2-m3-medium` profile caps xiSEARCH, mass recalibration, and xiFDR at
8 CPUs and 24 GB, matching the resources exposed by the xHAMLET JS2 m3.medium
instance.

The `js2-m3-xl` profile gives xiSEARCH a 96-GB Docker memory limit and an
80-GB Java heap at up to 32 CPUs, retaining container headroom for JVM native
memory. Mass recalibration is capped at 96 GB and xiFDR at 64 GB.
Use `--relink-resume` to reuse completed ReLink tasks from the last matching
workflow invocation.

When a recognized quenching reagent is present in extracted metadata, Xi
crosslink configs retain its crosslinker-specific mono-quench variable
modification on lysine in addition to oxidation. Restricting mono-quench
sites to lysine prevents unsupported low-specificity site assignments and
controls the modified peptide search space. The config generator omits these
modifications when no recognized quencher is available.

When PRIDE supplies `.fa`, `.fas`, or `.fasta` files for a project, xHAMLET
downloads and caches every supplied database for ReLink. Multiple files are
concatenated in filename order into one `combined_pride_<digest>.fasta` search
database, preserving all headers and sequences (including duplicate entries).
A newline separates files even when an input lacks a final newline. Every
source must pass the FASTA-header check; failed or invalid inputs stop the
search rather than silently omitting a database. A single supplied FASTA is
used directly. Projects with no supplied FASTA use the reviewed UniProt
proteome for the detected taxid.

UniProt FASTAs are downloaded once into a cache shared by all runs
(`reference_data/uniprot_fasta/taxid_<id>_reviewed.fasta` plus a `.json` with the query, size, sequence
count and SHA-256; override with `XHAMLET_UNIPROT_FASTA_CACHE`). Each PXD's
`relink/fasta/taxid_<id>.fasta` is a hard link (or copy) to the cached file, so every PXD directory stays
self-contained. Concurrent jobs take a file lock so only one downloads, and a download that breaks
mid-stream is restarted. The cache never expires on its own: to refresh a taxid after a UniProt release,
delete its two cache files and the next run downloads it again. The cache was seeded from identical
copies already in the store.

For multi-organism and/or multi-crosslinker projects, xHAMLET runs ReLink
separately for each organism-and-crosslinker combination. Each group runs the
full RAW-file set with a chemistry-specific Xi config and a separate results
directory, since XiSearch should never mix two different crosslinker
chemistries into a single search. A PRIDE-supplied combined database is reused
for every group; without supplied FASTAs, each group uses its taxid-specific
UniProt database.

## Stage Selection Controls

| Flag | Effect |
|---|---|
| `--no-download` | Skip Stage 3 and fresh Stage 4 generation |
| `--skip-spectral` | In Stage 3, skip mzML conversion + mzML_assessor |
| `--skip-sdrf` | Skip Stage 6 |
| `--skip-xi` | Skip Stage 8 |
| `--relink` | Enable Stage 9 |
| `--sdrf-only` | Run Stage 6-7 only from cache |
| `--force-refresh` | Recompute/refetch data rather than using cache |

## Main Arguments

- `--pxd PXD...`: one or more accessions
- `--pxd-file <tsv>`: load accession list from TSV (`Accession` column)
- `--config <yaml>`: load config file
- `--data-dir <dir>`: base output directory
- `--prompts-dir <dir>`: prompt directory
- `--prompts <keys...>`: explicit prompt subset for Stage 5
- `--model <name>`: LLM model override
- `--limit N`: cap RAW files per PXD
- `--nproc N|auto`: parallel workers for raw processing
- `--relink-profile <name>`: Nextflow profile for ReLink
- `--relink-resume`: pass `-resume` to Nextflow
- `--relink-work-dir <dir>`: Nextflow work dir override
- `--relink-queue-size N`: Nextflow queue size
- `--force-taxid TAXID`: run ReLink for this single NCBITaxon ID (e.g. `9606`)
  instead of the SDRF organisms; only matters for the UniProt FASTA fallback when
  PRIDE supplies no FASTA. Default: SDRF organisms (legacy behavior)
- `--verbose`: debug logging
- `--log-file <file>`: custom log path

## Config Semantics

Current config loader path is explicit. Pass config with `--config`.

Example:

```bash
python src/main.py --pxd PXD042173 --config configs/config.yaml
```

Important keys in `configs/config.yaml`:
- `llm.model`, `llm.temperature`
- `storage.base_dir`
- `prompts.dir`
- `prompts.enabled`

### What prompts.enabled means

`prompts.enabled` is the default Stage 5 prompt list used when:
- you do not pass `--prompts` on CLI.

Selection precedence:
1. CLI `--prompts` (highest)
2. Config `prompts.enabled`
3. All `.txt` files in the prompts directory (fallback)

## Prompts Used In LLM Metadata Extraction

Prompt files currently present in [prompts](prompts):

- `disease_treatment.txt`
- `factor_values.txt`
- `ms_acquisition.txt`
- `organism_sample.txt`
- `sample_attributes.txt`
- `sample_preparation.txt`
- `xlms_conditions.txt`
- `xlms_reagents.txt`

### Which prompts are called

- Stage 5 LLM extraction calls the selected prompt list (from `--prompts`, `prompts.enabled`, or all files).

## Output Layout

Per accession under `pxd_data/<PXD>/`:

- `pride/project_details.json`
- `pmc/full_text.json`
- `llm/responses.json`
- `assessment/*-metadata.json` (thermorawfileparser per-file metadata)
- `assessment/study_metadata.json` (mzML_assessor study-level output)
- `assessment/spectral_summary.json` (Stage 4 merged spectral metadata)
- `sdrf/<PXD>.sdrf.tsv`
- `configs/<PXD>_crosslinking.conf`
- `configs/<PXD>_linear.conf`
- `enhanced/metadata.json`
- `relink/taxid_<taxid>/results/` (if ReLink enabled)

## Result Catalog

Create or update the local SQLite result catalog and generate the static
results-explorer snapshot:

```bash
python scripts/sync_result_database.py \
	--config configs/config.yaml \
	--all \
	--static-snap
```

This writes `xhamlet-results.sqlite3` locally and generates
`web/results-explorer/data/catalog.json`. See
[documents/RESULT_CATALOG_AND_EXPLORER.md](documents/RESULT_CATALOG_AND_EXPLORER.md)
for PostgreSQL and publishing options.

## Crosslinker Reagent Coverage

A full reanalysis of all 1,045 PXDs in `assets/crosslinking_datasets_list.tsv`
found the following crosslinker-extraction/mapping breakdown (see
[documents/CROSSLINKER_EXTRACTION_FAILURE_ANALYSIS.md](documents/CROSSLINKER_EXTRACTION_FAILURE_ANALYSIS.md)
for the full per-PXD table and manual spot-check investigation):

| Status | PXDs | Notes |
|---|---:|---|
| **Usable now** — mapped to a verified DB entry with a real, mass-bearing Xi config | **474** | Ready for XiSearch/ReLink today; see `assets/crosslinking_datasets_true_subset.csv` below. |
| Mapped, but config has no mass (xi_class `NonCovalentBound`) | 61 | Reagent resolved (FA/Formaldehyde, Benzoyl, Click, photo-Met, photo-Leu), but the generated config omits the `MASS` field, so XiSearch cannot computationally detect crosslinks for these yet. |
| Mapped to a DB entry still awaiting human chemistry verification (`NeedsVerification`) | 77 | Needs a chemist to confirm monoisotopic mass/chemistry before use (see `scripts/normalize_crosslinker_database.py`). |
| No valid crosslinker reagent identified | 433 | Mostly proximity-labeling (TurboID/BioID/APEX), native UV photo-crosslinking, natural/enzymatic crosslinks, or a non-XL-MS study altogether — see the analysis doc for the full breakdown. |
| **Total** | **1,045** | |

**[assets/crosslinking_datasets_true_subset.csv](assets/crosslinking_datasets_true_subset.csv)**
is the curated subset of 474 PXDs confirmed to have a fully usable,
mass-bearing crosslinker configuration — the recommended starting point for
any downstream ReLink/search work.

## AlphaFold3 PPI Structure Prediction

For crosslink-supported protein-protein interactions found in the result
catalog, xHAMLET can generate and submit AlphaFold3 (AF3) two-chain complex
predictions with a single wrapper script,
[scripts/build_af3_ppi_jobs.py](scripts/build_af3_ppi_jobs.py). This is
separate from the upstream colleague-provided AF3 `run.sh` helper
(`/storage/group/RISE/toShare/AF3/run.sh`), which only builds single-chain
jobs by splitting each FASTA record independently and cannot predict
complexes.

### 1) Build the result catalog

```bash
python scripts/sync_result_database.py --pxd-file done_pxds.txt --data-dir store --database-path xhamlet-results.sqlite3
```

Select completed PXDs with `--pxd-file` (whitespace/comma-separated accessions,
with `#` comments) or `--pxd PXD031997 PXD041519`. Full-store synchronization
requires explicit `--all`; omitting a selection is an error. Progress is printed
immediately, including the selected count and PPI-index refresh.

### Quick start: one command for a list of completed PXDs

```bash
python scripts/prepare_af3_ppi_jobs.py --pxd-file done_pxds.txt
# or: python scripts/prepare_af3_ppi_jobs.py PXD031997 PXD041519
```

[scripts/prepare_af3_ppi_jobs.py](scripts/prepare_af3_ppi_jobs.py) checks that
each PXD has ReLink results, syncs just those PXDs into the result catalog,
and runs the builder below with the cohort defaults (each UniProt pair
predicted once across all PXDs, combined residues below 1200, ambiguous pairs
expanded). It writes `af3_ppi_jobs/shared/commands.txt` (one `sbatch` per
line) and `af3_ppi_jobs/shared/matches.tsv`; nothing is submitted. Use `--tag
NAME` to keep per-batch file names, `--total-residues-below N` to change the
cutoff, `--dry-run` to preview, and `--skip-sync` to reuse the catalog as is.
Other options (`--account`, `--mem`, `--time`, ...) are forwarded to the
builder. The manual steps are described below.

### 2) Generate AF3 job JSONs + Slurm scripts for validated PPI pairs

```bash
python scripts/build_af3_ppi_jobs.py \
	--database-path xhamlet-results.sqlite3 \
	--data-dir store \
	--out-dir af3_ppi_jobs \
	--expand-ambiguous \
	--account ncems_cr_default
```

For each unique, crosslink-supported protein pair found in the catalog,
`scripts/build_af3_ppi_jobs.py`:

1. Resolves both accessions to full-length sequences from the matching PXD's
   ReLink search FASTAs (every `<pxd_dir>/relink/fasta/*.fa*` file, including
   PRIDE-supplied and combined FASTAs).
2. Writes a two-chain AF3 job JSON (`<job_name>.json`).
3. Writes a ready-to-submit Slurm script (`<job_name>.slurm`) that runs the
   AF3 data-pipeline phase (CPU) followed by GPU inference for that one job,
   using the containers, weights, and databases installed under
   `/storage/icds/RISE/sw8/alphafold3/`.
4. Appends a row to `manifest.tsv` and a `sbatch` line to `submit_all.sh`
   (made executable) for convenience.

Key flags:

- `--complex-portal-only`: generate only catalog-indexed pairs present in Complex
  Portal, using the index's base-accession normalization. Use `--expand-ambiguous`
  to retain all candidate overlaps, without the raw-mapping expansion size cap.
- `--prediction-dir DIR...`: check manifests and completed models in existing
  job roots (default: `af3_ppi_jobs`), even before promotion into the store.
  Use `--dedupe-pairs` to also check promoted predictions across PXDs.
- `--sequence-fasta FILE...`: prefer exact-accession sequences from these files,
  falling back to the per-PXD search FASTAs. For base-accession Complex Portal
  jobs, the cached `reference_data/uniprot_fasta/taxid_9606_reviewed.fasta`
  provides canonical human sequences rather than arbitrarily choosing an isoform.
- `--pxd <accession_or_mask...>`: restrict to matching PXDs
- `--min-supporting N`: minimum distinct supporting crosslinks required (default: 1)
- `--include-self-links`: also emit homodimer jobs
- `--expand-ambiguous`: enumerate candidate pairs when a crosslink's alpha/beta
  side maps to multiple accessions (e.g. homologous constructs/isoforms);
  such pairs are flagged `ambiguous=True` in the manifest since the true
  partner is unresolved
- `--partition`, `--gres`, `--cpus-per-task`, `--mem`, `--time`, `--account`:
  override the generated Slurm resource requests (defaults: `standard`
  partition, `gpu:a100:1`, 16 CPUs, 128G, 12:00:00)
- `--submit`: sbatch every generated job immediately instead of just writing
  the scripts
- `--dry-run`: report planned jobs without writing files
- `--total-residues-below N`: only queue pairs whose combined residue count is
  strictly below `N` (for example `1200`). Larger pairs stay in the manifest and
  matches file with status `too_large`, so nothing is dropped from the record.
- `--dedupe-pairs`: predict each unique UniProt accession pair once across all
  PXDs (matched on the accession IDs only, never on sequences or peptides). Jobs live under `<out-dir>/pairs/` with PXD-independent
  names (`<a>__<b>__<hash>`); every PXD observation in the matches file points
  at the shared job, and pairs that already have a prediction (a `model.cif` in
  the job directory or under `store/<PXD>/af3_predictions/`) get status
  `already_predicted` and no command.
- `--commands-file FILE`: also write one `sbatch "<script>"` command per line
  to `FILE`. Nothing is submitted; use it to pick which jobs to run.
- `--matches-file FILE`: companion TSV with one row per unique ReLink crosslink
  per PXD, keyed by `job_name` and `command_line` (the 1-based line in
  `--commands-file`, blank when the pair has no command). Columns: `pxd`,
  `job_name`, `status` (`ready`, `too_large`, `already_predicted`,
  `missing_sequence`), `command_line`,
  `uniprot_a`, `uniprot_b`, `peptide_a`, `peptide_b`, `positions_a`,
  `positions_b`, `protein_length_a`, `protein_length_b`, `total_residues`
  (system size = length A + length B), `max_xi_score`, `n_psms`, `ambiguous`.
  ReLink's mzIdentML carries no per-match p-value or q-value, so none is
  reported; passing matches are those inside xiFDR's configured link FDR
  (5% by default).

Accessions in `alpha_proteins`/`beta_proteins` come directly from the source
mzIdentML `DBSequence` accession attribute, not from FASTA parsing, so any
non-standard-looking accession (e.g. missing a UniProt prefix) reflects the
underlying search database rather than a parsing bug.

### 3) Submit AF3 jobs to Slurm

```bash
bash af3_ppi_jobs/submit_all.sh
```

Or submit an individual pair's job directly:

```bash
sbatch af3_ppi_jobs/<PXD>/<job_name>.slurm
```

### 4) Promote completed predictions into the store

The job wrapper leaves results in its job directory. Copy the best model,
confidence summary, rankings, and pair evidence into every associated PXD:

```bash
python scripts/promote_af3_predictions.py --manifest af3_ppi_jobs/complex_portal100/manifest.tsv
```

Shared jobs are resolved using the manifest's JSON paths (run from the repository
root). Failed jobs without a model are skipped; complete destinations are skipped
on subsequent runs. Large MSA archives and alternate samples remain in the job
directory. After promotion, sync only the affected PXDs into the catalog.

## Reference PPIs for Validation (hu.MAP 3.0 and Complex Portal)

Reference co-complex protein pairs are loaded into the result catalog for validating
crosslink-supported pairs:

```bash
python scripts/sync_reference_ppis.py            # fetch + load into xhamlet-results.sqlite3
python scripts/sync_reference_ppis.py --no-fetch # reuse files already in reference_data/
```

[scripts/sync_reference_ppis.py](scripts/sync_reference_ppis.py) downloads each source once
into `reference_data/<source>/<release>/` (with a `provenance.json` holding the URL,
SHA-256, license and citation), parses it, and writes `reference_source`,
`reference_complex`, `reference_complex_member`, and `reference_ppi` (one row per unordered
UniProt pair per source, lower accession first). Re-running is a no-op unless the file
changed or `--force` is given. SQLite is the default; `--database-url` selects PostgreSQL.

- **Complex Portal:** human, curated only (`9606.tsv`). `9606_predicted.tsv` is hu.MAP
  imported into Complex Portal, so it is not loaded.
- **hu.MAP 3.0:** the complexes file, all confidence tiers (1 = best, 6 = weakest); a pair's
  `best_tier` is the best tier among complexes containing it.
- Isoform and chain suffixes are removed (`Q13485-2` becomes `Q13485`); non-UniProt
  participants (sub-complexes, ChEBI, RNA) are dropped and counted in
  `reference_complex.dropped_participants`. Self pairs are not stored.
- Pairs mean **co-complex membership, not direct contact**, and the two sources are **not
  independent**: hu.MAP 3.0 was trained and tested on Complex Portal.
- Attribution is required (hu.MAP 3.0 is CC-BY).

### Looking up a PPI (ReLink + reference notations)

Every pair seen in ReLink **or** in a reference source gets one row in the `ppi` table
(unordered UniProt accessions, `accession_a < accession_b`), even if ReLink never saw it.
[scripts/ppi_index.py](scripts/ppi_index.py) rebuilds it, and it refreshes automatically
after `sync_reference_ppis.py` and `sync_result_database.py`:

```bash
sqlite3 -header -line xhamlet-results.sqlite3 "SELECT * FROM ppi WHERE accession_a='P84022' AND accession_b='Q13485'"
sqlite3 -header -column xhamlet-results.sqlite3 "SELECT * FROM ppi_reference_detail WHERE accession_a='P84022' AND accession_b='Q13485'"
sqlite3 -header -column xhamlet-results.sqlite3 "SELECT * FROM ppi_relink_detail    WHERE accession_a='P84022' AND accession_b='Q13485'"
```

- `ppi`: ReLink match / project counts and best xi score, plus Complex Portal and hu.MAP 3.0
  complex counts, evidence codes and best tier. ReLink-only and reference-only pairs both appear.
- `ppi_by_protein`: the same summary with one row per (`accession`, `partner`) in both
  orientations, so a protein is found with a single filter (see below).
- `ppi_relink_detail`: each ReLink observation (PXD, peptides and residue positions oriented to
  `accession_a`/`accession_b`, xi score, ambiguity flag).
- `ppi_reference_detail`: each reference complex containing the pair (source, release, complex
  ID and name, tier or evidence code).
- ReLink matches whose protein assignment is ambiguous are expanded to every candidate pair and
  flagged `is_ambiguous`; self pairs are excluded. Non-UniProt identifiers in a search database
  are kept as they are and will simply have no reference match.
- Reference sources cover **human** only, so ReLink pairs from other organisms (and from
  searches against a forced human database) will show no reference support.

**All records for one UniProt ID** (pairs store the lower accession in `accession_a`, so a
protein can be in either column; `ppi_by_protein` handles that):

```bash
# every partner, with ReLink and reference support
sqlite3 -header -column xhamlet-results.sqlite3 "SELECT * FROM ppi_by_protein WHERE accession='Q13485' ORDER BY relink_match_count DESC"
# every ReLink observation / every reference complex involving the protein
sqlite3 -header -column xhamlet-results.sqlite3 "SELECT * FROM ppi_relink_detail    WHERE accession_a='Q13485' OR accession_b='Q13485'"
sqlite3 -header -column xhamlet-results.sqlite3 "SELECT * FROM ppi_reference_detail WHERE accession_a='Q13485' OR accession_b='Q13485'"
```

## Troubleshooting

### Missing assessment/study_metadata.json

Check logs for mzML_assessor dependency/runtime failures.

Stage 3 assessor requires Python packages from requirements, including:
- `lxml`
- `pyteomics`
- `scipy`
- `matplotlib`

### No Xi configs

Check:
- `llm/responses.json` contents
- crosslinker parsing in `xlms_reagents` output
- errors from Stage 8 in logs

### ReLink skipped or failed

Common causes:
- SDRF missing or invalid
- Xi configs not generated
- no local RAW files in `work/`
- Nextflow profile/container/runtime issues

## Additional Docs

- Architecture: [documents/ARCHITECTURE.md](documents/ARCHITECTURE.md)
- Build notes: [documents/BUILD_SUMMARY.md](documents/BUILD_SUMMARY.md)
- Result catalog and static explorer: [documents/RESULT_CATALOG_AND_EXPLORER.md](documents/RESULT_CATALOG_AND_EXPLORER.md)
- Crosslinker extraction failure analysis: [documents/CROSSLINKER_EXTRACTION_FAILURE_ANALYSIS.md](documents/CROSSLINKER_EXTRACTION_FAILURE_ANALYSIS.md)

## References

[1] Graziadei, A. and Rappsilber, J. Structure 30, 37-54 (2022).
[2] Sinz, A. Angew. Chem. Int. Ed. 57, 6390-6396 (2018).
[3] Leitner, A. et al. Trends Biochem. Sci. 41, 20-32 (2016).
[4] Eagen, K. P. Trends Biochem. Sci. 43, 469-478 (2018).
[5] Matzinger, M. and Mechtler, K. J. Proteome Res. 20, 78-93 (2021).
