# Store Layout

`store/` is the per-dataset result store. `storage.base_dir` in the pipeline
config points here, and every PRIDE accession gets one directory,
`store/<PXD>/`. Pipeline stages read cached files from this directory before
doing any network, LLM, or compute work, so a rerun resumes rather than starts
over (unless `--force-refresh` is given).

The store is **partially tracked in git**. Small metadata and curated results are
committed so collaborators can resume a PXD without re-querying PRIDE, PMC, or
the LLM. Large or fully regeneratable artifacts are ignored because many of them
exceed GitHub's 100 MB per-file hard limit (and 50 MB warning threshold).

## Directory overview

```
store/<PXD>/
├── pride/             tracked   PRIDE project metadata and file list
├── pmc/               tracked   Publication full text (PMC BioC)
├── ncbi/              tracked   NCBI lookup cache (often empty)
├── llm/               tracked   LLM extraction responses and RAW-file assignments
├── assessment/        tracked   Per-RAW instrument metadata and spectral summary
├── sdrf/              tracked   Generated SDRF
├── configs/           tracked   xiSEARCH crosslink/linear search configs
├── enhanced/          tracked   Final merged metadata for the PXD
├── af3_predictions/   tracked   Promoted AlphaFold3 models for supported PPIs
├── search_results/    tracked   Compact rank-1 linear and crosslink CSVs, plus spectrum map
├── work/              IGNORED   Downloaded vendor RAW files (up to GBs each)
└── relink/            IGNORED   ReLink FASTA and Nextflow search/FDR outputs
```

Ignore rules live in [`.gitignore`](../.gitignore): `**/work/`, `store/*/relink/`,
`**/relink/taxid_*/results/`, `*.raw`, and `*.mzML`.

## Tracked subdirectories

Cached JSON files written through `DataStore`
(`src/pxd_enhancer/data_store.py`) share a wrapper:
`{"metadata": {"pxd", "category", "saved_at", "filename"}, "data": ...}`.

| Path | Written by | Contents |
|---|---|---|
| `pride/project_details.json` | Stage 1, PRIDE client | PRIDE project record and file list |
| `pmc/full_text.json` | Stage 2, PMC client | Linked publication full text, when available |
| `ncbi/` | Stage 2, NCBI client | DOI→PMID lookup cache; usually empty, so usually absent from git |
| `llm/responses.json` | Stage 5, LLM client | Parsed answers for the extraction prompts |
| `llm/file_assignments.json`, `llm/file_assignment_map.json` | Stage 5 | Per-RAW-file organism, taxid, crosslinker, and cluster |
| `assessment/<raw>-metadata.json` | Stage 3, ThermoRawFileParser | Instrument and acquisition metadata per RAW file |
| `assessment/study_metadata.json`, `assessment/spectral_summary.json` | Stage 4, mzML assessor | Spectral QC summary across files |
| `sdrf/<PXD>.sdrf.tsv` | Stage 6, SDRF writer | Crosslinking SDRF used as ReLink input |
| `configs/xi_crosslinking[_<chem>].conf`, `configs/xi_linear[_<chem>].conf` | Stage 8, Xi config generator | xiSEARCH configs; one pair per crosslinker chemistry |
| `enhanced/metadata.json` | Stage 10 | Final merged view of all stages for the PXD |
| `af3_predictions/<job>/` | `scripts/promote_af3_predictions.py` | See below |

Temporary assessment mzML files are deleted after stage 4.

### `search_results/`

`scripts/export_search_results.py` runs after all current ReLink search groups
finish successfully. It can also backfill existing results:

```bash
python scripts/export_search_results.py --pxd PXD009641
python scripts/export_search_results.py --all --completed-pxd-file /tmp/exported_pxds.txt
python scripts/sync_result_database.py --pxd-file /tmp/exported_pxds.txt --force
```

The backfill reports and skips PXDs with incomplete result groups and exits
nonzero if any PXD fails. Only successfully exported PXDs are written to the
requested list. The automatic hook exports the current run's groups; the
standalone default checks every existing result group, including stale attempts.

Each file must be **strictly below 50,000,000 bytes**. The exporter validates
inputs and sizes in a temporary directory before replacing existing outputs;
oversized results are reported rather than truncated. A valid search with zero
accepted crosslinks produces a header-only crosslink CSV.

| File | Columns and filtering |
|---|---|
| `linear.csv` | `scan_id,charge,peptide,modified_peptide,protein_accessions,peptide_starts,xi_score`; only original xiSEARCH `MatchRank=1`, `decoy=0` rows, retaining ties. These are **not linear-FDR validated**. `modified_peptide` preserves xiSEARCH notation including flanking residues. |
| `crosslinks.csv` | `scan_id,charge,alpha_peptide,alpha_modifications,alpha_positions,alpha_link_sites,beta_peptide,beta_modifications,beta_positions,beta_link_sites,xi_score`; paired mzIdentML rank-1, FDR-passing matches without referenced decoy evidence. Includes intra-protein as well as inter-protein links. |
| `scan_map.csv` | `scan_id,search_group,search_stage,run,scan,scan_title`; maps PXD-local numeric IDs to source spectra and search groups (taxid/chemistry). Stages distinguish original linear spectra from recalibrated crosslink spectra. |

Protein ambiguity is preserved, not expanded into separate candidate-pair rows.
Linear accession/start lists retain xiSEARCH's original encoding and ordering.
Crosslink positions use `accession:start-end` entries separated by semicolons.
Link sites are 1-based positions within the peptide (terminal positions follow
mzIdentML conventions); protein sites require combining the peptide start with
the link position. Modifications are compact JSON arrays of mzIdentML attributes
(location, mass delta and residues when supplied), excluding donor/acceptor
crosslink markers. Those markers supply the separate link-site columns.

Spectrum IDs are deterministic for unchanged input ordering, but should only be
joined within the same PXD export. `scan` preserves the source's value: xiSEARCH's
`Scan` can differ from the native scan number recorded in `scan_title`. For
mzIdentML, `scan` is extracted from the native spectrum ID when available;
`scan_title` always retains the full native ID.

The catalog importer uses the same rank-1 crosslink filter, so future AF3 jobs
draw only from rank-1 passing evidence. Existing catalog entries need a forced
scoped refresh to apply the new rule; previously generated AF3 models are not
removed or rerun.

### `af3_predictions/<job>/`

One directory per AlphaFold3 prediction of a crosslink-supported protein pair
that was observed in this PXD. When a pair is supported by several PXDs, the
same prediction is copied into each one.

| File | Contents |
|---|---|
| `model.cif` | Top-ranked AF3 model (typically 0.1–2 MB) |
| `summary_confidences.json` | AF3 confidence summary (`iptm`, `ptm`, ranking score, ...) |
| `ranking_scores.csv` | Ranking score for every seed/sample |
| `pair.json` | Pair provenance: job name, proteins, supporting crosslinks, max xi score, ambiguity |

Job names come from `scripts/build_af3_ppi_jobs.py`: deduplicated jobs are named
`<accA>__<accB>__<hash8>`, while per-PXD jobs are named `<PXD>__<a>__<b>`. The
full AF3 working directories (MSA `*_data.json` archives of 60–200+ MB, every
seed/sample) stay in the ignored `af3_ppi_jobs/` tree. Only these four small
files are promoted into the store. `scripts/sync_result_database.py` imports
them as `af3_prediction` rows.

## Ignored subdirectories

### `work/`

Vendor RAW files downloaded from PRIDE (stage 3). They are retained for ReLink
and can be re-downloaded from PRIDE.

### `relink/`

```
relink/
├── fasta/taxid_<id>.fasta                 Search FASTA (project FASTA or UniProt proteome)
└── taxid_<id>/<chem>/results/             Nextflow --outdir for one taxid/crosslinker group
    ├── sdrf_parsing/                      ReLink design TSV and xi configs used
    ├── mzml/                              RAW→mzML conversions (hundreds of MB each)
    ├── linear_search/                     xiSEARCH linear CSV + peaks TSV
    ├── recalibrated/                      Mass-error tables, plots, recalibrated mzML
    ├── crosslinking_search/               xiSEARCH crosslink CSV + peaks CSV (~100+ MB)
    ├── fdr/results.mzid                   xiFDR mzIdentML; the catalog import source
    ├── multiqc/                           MultiQC report
    ├── pipeline_info/                     Nextflow trace, timeline, report, params, DAG
    └── .nextflow-run/                     Per-group Nextflow launch directory and history
```

`<chem>` (e.g. `bs3`, `dsso`) is omitted when no crosslinker name was resolved.
This tree is written by `src/pxd_enhancer/relink_runner.py` and the
`tools/relink` Nextflow workflow. Nextflow task work directories live under
`assets/slurm/<batch>/runs/<PXD>/work`, not in the store, and are cleaned
after a successful run. Everything here can be regenerated with `--relink`
once the RAW files are downloaded again.

## Derived data outside the store

| Path | Tracked | Notes |
|---|---|---|
| `xhamlet-results.sqlite3` | No (`*.sqlite3`) | Result catalog built from the store; see [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) |
| `web/results-explorer/data/catalog.json` | Yes | Static snapshot used by the explorer; see [RESULT_CATALOG_AND_EXPLORER.md](RESULT_CATALOG_AND_EXPLORER.md) |
| `af3_ppi_jobs/` | No | AF3 job inputs, SLURM scripts, and full outputs |
| `reference_data/uniprot_fasta/` | No | Cached UniProt proteomes used for searches and AF3 sequences |

## Adding new content to the store

Before committing a new file type under `store/`, check that it is small: no
file should approach 50 MB. Large artifacts belong under an ignored
subdirectory or in external storage. To list untracked, non-ignored files over
50 MB, run:

```bash
git ls-files -o --exclude-standard -z store | xargs -0 du -b | awk '$1 > 50e6'
```
