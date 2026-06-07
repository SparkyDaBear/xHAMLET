# xHAMLET – Architecture Overview

**Version**: 0.2.0  
**Last updated**: 2025-07-15

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                CLI Entry Point (main.py)                        │
│  --pxd / --pxd-file  --no-download  --skip-spectral            │
│  --clean-raw  --clean-mzml  --limit  --aria2c-connections      │
│  --skip-sdrf  --skip-xi  --force-refresh  --model  ...         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│        PXDMetadataEnhancer  (9-stage orchestrator)              │
│  process_pxd(pxd, …)                                           │
└──┬──────┬──────┬──────┬──────┬───────┬──────┬──────────────────┘
   │      │      │      │      │       │      │
   ▼      ▼      ▼      ▼      ▼       ▼      ▼
PRIDE   PMC   DataStore RawFile Assessor SDRF  XiConfig
Client Client          Processor Runner  Writer Generator
   │      │      │      │      │       │      │
   ▼      ▼      ▼      ▼      ▼       ▼      ▼
PRIDE  PMC/   JSON    aria2c/ Thermo/  TSV   .conf
REST   NCBI   cache   aria2c  assessor file  files
API    API
```

---

## 9-Stage Pipeline (per PXD)

```
Stage 1  PRIDE fetch
  ├─ fetch_project_details(pxd)
  ├─ extract_file_download_links(pxd)  → file_list (FTP URLs)
  └─ cache → pride/project_details.json

Stage 2  Publication fetch
  ├─ PRIDE → PMID → PMCID  (fallback: DOI → NCBI search)
  └─ cache → pmc/full_text.json

Stage 3  Raw file processing              [skipped with --no-download]
  ├─ RawFileProcessor.run(file_list)
  │   Phase 1 (per file):
  │   ├─ aria2c download (--aria2c-connections connections per file)
  │   ├─ thermorawfileparser -f 4  → assessment/{stem}-metadata.json
  │   ├─ thermorawfileparser -f 2  → work/{stem}.mzML   [unless --skip-spectral]
  │   └─ delete .raw                                    [if --clean-raw]
  │   Phase 2 (once, all files done):
  │   ├─ mzML_assessor.py --inpath work/ --outpath assessment/
  │   └─ delete .mzML                                   [if --clean-mzml]
  └─ cache → assessment/*-metadata.json, assessment/study_metadata.json

Stage 4  Spectral merge
  ├─ AssessorRunner.build_spectral_summary()
  │   Priority: thermorawfileparser > mzML_assessor > PRIDE > publication
  └─ cache → assessment/spectral_summary.json

Stage 5  LLM extraction
  ├─ 23 prompts × publication text (or PRIDE metadata if no publication)
  └─ cache → llm/responses.json

Stage 6  SDRF generation                  [skipped with --skip-sdrf]
  ├─ SDRFWriter.write() — one row per .raw file
  └─ output → sdrf/{pxd}.sdrf.tsv

Stage 7  SDRF validation
  └─ parse_sdrf validate-sdrf --template crosslinking
     (silently skipped if parse_sdrf not installed)

Stage 8  Xi config generation             [skipped with --skip-xi]
  ├─ XiConfigGenerator.generate_configs()
  └─ output → configs/{pxd}_crosslinking.conf, {pxd}_linear.conf

Stage 9  Final save
  └─ enhanced/metadata.json  (all stages + all collected data)
```

---

## CLI Flags Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--pxd PXD...` | — | One or more PXD accessions |
| `--pxd-file TSV` | — | TSV with `Accession` column |
| `--config YAML` | — | YAML config file |
| `--data-dir DIR` | `./pxd_data` | Base data directory |
| `--prompts-dir DIR` | `./prompts` | Prompt template directory |
| `--prompts KEY...` | all | Subset of prompts to run |
| `--model NAME` | `gpt-4-turbo` | LLM model |
| `--force-refresh` | false | Re-run even if cached |
| `--no-download` | false | Skip Stages 3–4 entirely |
| `--skip-spectral` | false | Skip mzML conversion + mzML_assessor (download + metadata JSON still run) |
| `--clean-raw` | false | Delete .raw after thermorawfileparser |
| `--clean-mzml` | false | Delete .mzML after mzML_assessor |
| `--limit N` | unlimited | Cap files processed per PXD |
| `--aria2c-connections N` | 16 | TCP connections per file |
| `--skip-sdrf` | false | Skip Stage 6 |
| `--skip-xi` | false | Skip Stage 8 |
| `--verbose` | false | DEBUG logging |
| `--create-prompts` | — | Create default prompts and exit |
| `--list-prompts` | — | List available prompts and exit |
| `--save-config FILE` | — | Save resolved config and exit |

---

## Storage Layout

```
pxd_data/
└── PXD000001/
    ├── pride/
    │   └── project_details.json          (PRIDE API response + file list)
    ├── pmc/
    │   └── full_text.json                (PMC BioC full text)
    ├── ncbi/                             (NCBI PubMed metadata, if used)
    ├── llm/
    │   └── responses.json                (23-prompt LLM output)
    ├── enhanced/
    │   └── metadata.json                 (final compiled output)
    ├── assessment/
    │   ├── {stem}-metadata.json          (thermorawfileparser, per file)
    │   ├── study_metadata.json           (mzML_assessor study summary)
    │   └── spectral_summary.json         (merged spectral metadata)
    ├── sdrf/
    │   └── PXD000001.sdrf.tsv            (SDRF-Proteomics crosslinking TSV)
    ├── configs/
    │   ├── PXD000001_crosslinking.conf   (Xi crosslinking config)
    │   └── PXD000001_linear.conf         (Xi linear search config)
    └── work/                             (transient: .raw and .mzML files)
        ├── sample01.raw                  (deleted if --clean-raw)
        └── sample01.mzML                (deleted if --clean-mzml)
```

---

## Class Relationships

```
PXDMetadataEnhancer
├── PrideClient            — PRIDE REST API v3
├── PMCClient              — PMC BioC API + PMID→PMCID converter
├── NCBIClient             — Entrez DOI→PMID fallback
├── DataStore              — JSON caching, directory management
├── LLMClient              — OpenAI API, response parsing
├── PromptTemplates        — 23-prompt template loader
├── XiConfigGenerator      — Xi search engine .conf generation
├── RawFileProcessor       — aria2c + thermorawfileparser + mzML_assessor
├── AssessorRunner         — Parse assessment JSONs, build spectral summary
├── OntologyMapper         — Map names → NT=...;AC=... SDRF terms
└── SDRFWriter             — Write SDRF-Proteomics crosslinking TSV
```

---

## Source Module Map

| Module | Path | Responsibility |
|--------|------|----------------|
| `main.py` | `src/main.py` | CLI, batch loop |
| `extractor.py` | `src/pxd_enhancer/extractor.py` | 9-stage orchestrator |
| `raw_processor.py` | `src/pxd_enhancer/raw_processor.py` | Download + thermorawfileparser + mzML_assessor |
| `assessor_runner.py` | `src/pxd_enhancer/assessor_runner.py` | Parse assessment JSONs, spectral summary |
| `ontology_mapper.py` | `src/pxd_enhancer/ontology_mapper.py` | Name → SDRF ontology term |
| `sdrf_writer.py` | `src/pxd_enhancer/sdrf_writer.py` | SDRF-Proteomics TSV writer |
| `pride_client.py` | `src/pxd_enhancer/pride_client.py` | PRIDE REST API |
| `pmc_client.py` | `src/pxd_enhancer/pmc_client.py` | PMC BioC API |
| `ncbi_client.py` | `src/pxd_enhancer/ncbi_client.py` | NCBI Entrez |
| `data_store.py` | `src/pxd_enhancer/data_store.py` | JSON file cache |
| `llm_client.py` | `src/pxd_enhancer/llm_client.py` | OpenAI API wrapper |
| `prompt_templates.py` | `src/pxd_enhancer/prompt_templates.py` | Prompt loader |
| `xi_config_generator.py` | `src/pxd_enhancer/xi_config_generator.py` | Xi .conf generator |
| `config.py` | `src/pxd_enhancer/config.py` | YAML config + defaults |
| `mzML_assessor.py` | `src/assessor/mzML_assessor.py` | mzML spectral assessor |
| `metadata_handler.py` | `src/assessor/metadata_handler.py` | Assessor metadata helper |

---

## External Tool Dependencies

| Tool | Version | Location | Purpose |
|------|---------|----------|---------|
| `thermorawfileparser` | 2.0.0.0 | `/home/ians/miniconda3/bin/` | `.raw` → metadata JSON + mzML |
| `aria2c` | 1.36.0 | `/usr/bin/aria2c` | Multi-connection FTP download |
| `parse_sdrf` | 0.1.4 | pip-installed | SDRF crosslinking template validation |

---

## Configuration Hierarchy

```
DEFAULT_CONFIG (config.py)
      │
      ▼
config.yaml  ──── overrides defaults
      │
      ▼
CLI arguments ─── override config file
      │
      ▼
Effective Configuration
```

Key configuration sections:

| Section | Key settings |
|---------|-------------|
| `download` | `aria2c_connections=16`, `clean_raw=false`, `clean_mzml=false` |
| `assessment` | `skip_spectral=false`, `assessor_script=src/assessor/mzML_assessor.py` |
| `sdrf` | `skip_sdrf=false`, `template=crosslinking` |
| `llm` | `model=gpt-4-turbo`, `temperature=0.3` |
| `storage` | `base_dir=./pxd_data` |

---

## SDRF Column Order (crosslinking template)

| Column | Source |
|--------|--------|
| `source name` | `{pxd}_{stem}` |
| `characteristics[organism]` | LLM → OntologyMapper |
| `characteristics[organism part]` | LLM |
| `characteristics[cell type]` | LLM |
| `characteristics[biological replicate]` | filename heuristic |
| `assay name` | `{pxd}_{stem}_assay` |
| `technology type` | `mass spectrometry` (fixed) |
| `comment[label]` | LLM → OntologyMapper |
| `comment[fraction identifier]` | filename regex |
| `comment[technical replicate]` | filename regex |
| `comment[instrument]` | spectral_summary > LLM > PRIDE |
| `comment[cleavage agent details]` | LLM → OntologyMapper |
| `comment[modification parameters]` | LLM (one column per mod; Carbamidomethyl always present) |
| `comment[collision energy]` | LLM |
| `comment[dissociation method]` | spectral_summary > LLM |
| `comment[cross-linker]` | LLM → `NT=...;AC=XLMOD:...;CL=...;TA=...` |
| `comment[crosslink enrichment method]` | LLM |
| `comment[crosslinker concentration]` | LLM |
| `comment[crosslinker to protein ratio]` | LLM |
| `comment[crosslinking reaction time]` | LLM |
| `comment[crosslinking temperature]` | LLM |
| `comment[data file]` | PRIDE file list (exact filename, not LLM) |
| `comment[sdrf template]` | `ms-proteomics/1.1`, `crosslinking/1.0`, taxonomy |

---

## Error Handling

- Per-file failures in Stage 3 are isolated; processing continues to next file
- 3 consecutive failures abort Phase 1 early with a clear error message
- `--no-download` + `--force-refresh` allows re-running LLM/SDRF/Xi stages on cached spectral data
- All stage status values: `success`, `failed`, `skipped`, `skipped_no_files`, `skipped_no_download`, `partial`, `success_cached`

---

## Caching Strategy

```
First run:           Fetch from APIs → save to disk
Subsequent runs:     Load from disk  (force_refresh=False)
Force refresh:       Fetch fresh     → overwrite disk cache

Stage 3 resume:      Skip files where assessment/{stem}-metadata.json already exists
```

---

## Batch Processing Examples

```bash
# Single PXD with full pipeline
python src/main.py --pxd PXD017620

# Test run: 2 files, clean up after, verbose
python src/main.py --pxd PXD042173 --limit 2 --clean-raw --clean-mzml --verbose

# Batch from TSV (1046 datasets)
python src/main.py \
  --pxd-file assets/crosslinking_datasets_list.tsv \
  --clean-raw --clean-mzml \
  --aria2c-connections 16

# LLM + SDRF only, no downloads
python src/main.py --pxd PXD042173 --no-download --force-refresh

# Re-run SDRF only on already-processed dataset
python src/main.py --pxd PXD042173 --no-download --skip-xi --force-refresh
```

---

*Created*: 2026-03-01  
*Updated*: 2025-07-15 — 9-stage pipeline, aria2c, thermorawfileparser, SDRF generation, OntologyMapper
