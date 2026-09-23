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

When PRIDE supplies exactly one `.fa`, `.fas`, or `.fasta` file for a project,
xHAMLET downloads and caches that sequence database for ReLink. Projects with
no supplied FASTA use the reviewed UniProt proteome for the detected taxid.

When file clustering resolves different crosslinkers for a project, xHAMLET
runs ReLink separately for each organism-and-crosslinker group. Each group
uses a filtered SDRF, chemistry-specific Xi config, and separate results
directory; files with unresolved cluster chemistry retain the dataset-level
ReLink configuration.

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
- `--assessor-files-per-cluster N`: representative files per cluster for spectral assessment
- `--relink-profile <name>`: Nextflow profile for ReLink
- `--relink-resume`: pass `-resume` to Nextflow
- `--relink-work-dir <dir>`: Nextflow work dir override
- `--relink-queue-size N`: Nextflow queue size
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
- `file_clustering.txt`
- `ms_acquisition.txt`
- `organism_sample.txt`
- `sample_attributes.txt`
- `sample_preparation.txt`
- `xlms_conditions.txt`
- `xlms_reagents.txt`

### Which prompts are called

- Stage 2.5 file clustering always calls `file_clustering.txt` directly.
- Stage 5 LLM extraction calls the selected prompt list (from `--prompts`, `prompts.enabled`, or all files).

Note: If Stage 5 includes `file_clustering.txt`, it will be queried there too in addition to Stage 2.5.

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
	--static-snap
```

This writes `xhamlet-results.sqlite3` locally and generates
`web/results-explorer/data/catalog.json`. See
[documents/RESULT_CATALOG_AND_EXPLORER.md](documents/RESULT_CATALOG_AND_EXPLORER.md)
for PostgreSQL and publishing options.

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

## References

[1] Graziadei, A. and Rappsilber, J. Structure 30, 37-54 (2022).
[2] Sinz, A. Angew. Chem. Int. Ed. 57, 6390-6396 (2018).
[3] Leitner, A. et al. Trends Biochem. Sci. 41, 20-32 (2016).
[4] Eagen, K. P. Trends Biochem. Sci. 43, 469-478 (2018).
[5] Matzinger, M. and Mechtler, K. J. Proteome Res. 20, 78-93 (2021).

Write-access test.
