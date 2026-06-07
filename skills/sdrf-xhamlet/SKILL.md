---
name: sdrf:xhamlet
description: >
  Full end-to-end annotation workflow for crosslinking mass spectrometry (XL-MS) datasets.
  Use when the user provides a PXD accession for a crosslinking experiment, or asks to
  annotate, validate, or generate Xi search configs for XL-MS data.
  Combines PRIDE metadata, publication extraction, crosslinker lookup (via crosslinking-xl MCP),
  SDRF generation with the crosslinking template, and Xi config generation.
user-invocable: true
argument-hint: "PXD###### [--pxd-file <path>] [--no-download] [--keep-raw] [--xi-config-only] [--skip-spectral] [--limit N]"
---

# xHAMLET — XL-MS Annotation Workflow

You are performing a complete annotation of a crosslinking proteomics dataset.
Follow ALL stages in order. Do not skip steps. Do not guess ontology terms.

**Required MCP servers**: PRIDE, OLS, PubMed, crosslinking-xl (local)
**Required tools**: `parse_sdrf` (validation), `techsdrf` (optional, raw file metadata)

---

## Stage 0: Pre-flight Checks

Before starting, verify tool and flag availability:

```bash
parse_sdrf --version                               # SDRF validation (required)
which thermorawfileparser                          # Thermo .raw metadata extractor (required)
which aria2c || which wget                         # Download tool
python -c "import sdrf_pipelines"                  # validation library
test -f scripts/mzML_assessor.py && echo "OK"      # spectral assessor (required)
python -c "from metadata_handler import MetadataHandler" 2>/dev/null \
  || python -c "import sys; sys.path.insert(0,'scripts'); from metadata_handler import MetadataHandler" \
  && echo "metadata_handler: OK"                   # MetadataHandler (required)
```

**Argument flags:**
| Flag | Meaning |
|------|---------|
| `--pxd-file <path>` | TSV file containing a column of PXD accessions to process in batch (see below) |
| `--no-download` | Skip Stages 2–4 (no file download, conversion, or spectral assessment) |
| `--keep-raw` | After Stage 3 processing, retain downloaded raw files (default: delete immediately after processing) |
| `--xi-config-only` | Skip SDRF generation; produce Xi configs only |
| `--skip-spectral` | Skip mzML conversion and mzML_assessor (use thermorawfileparser JSON only — faster but no spectral QC) |
| `--limit N` | Process only the first N raw files (default: **all** files — no limit) |

### PXD list resolution

If `--pxd-file <path>` is given, read the TSV to build a list of accessions:

```python
import csv, re

def load_pxd_file(path: str) -> list[str]:
    """Read PXD accessions from a TSV file.
    Finds the first column whose header matches (case-insensitive):
      'pxd', 'accession', 'project_accession', or 'dataset'
    Skips blank values. Returns a deduplicated, ordered list.
    """
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        # Locate the PXD column
        pxd_col = None
        for col in (reader.fieldnames or []):
            if col.strip().lower() in ("pxd", "accession", "project_accession", "dataset"):
                pxd_col = col
                break
        if pxd_col is None:
            raise ValueError(
                f"No PXD column found in {path}. "
                "Expected a column named: pxd, accession, project_accession, or dataset."
            )
        seen, result = set(), []
        for row in reader:
            val = row[pxd_col].strip()
            if val and re.match(r'^PXD\d+$', val, re.IGNORECASE) and val.upper() not in seen:
                seen.add(val.upper())
                result.append(val.upper())
    return result
```

**Resolving the final PXD list** (union of positional argument + file):

```python
pxd_list = []

# Positional argument (may be absent when --pxd-file is used alone)
if positional_pxd:
    pxd_list.append(positional_pxd.upper())

# File argument
if pxd_file_path:
    file_pxds = load_pxd_file(pxd_file_path)
    for p in file_pxds:
        if p not in pxd_list:
            pxd_list.append(p)

if not pxd_list:
    raise ValueError("No PXD accessions provided. Pass a PXD######  or --pxd-file <path>.")
```

After resolving, present the batch plan to the user before processing:

```
Batch mode: {len(pxd_list)} dataset(s) to process
  {pxd_list[0]}
  {pxd_list[1]}
  ...
Flags applied to each: {active_flags}
```

Then run **Stages 1–10 in full for each PXD in order**, treating each as an independent run.
All per-run flags (`--no-download`, `--keep-raw`, `--skip-spectral`, `--limit N`, etc.) apply equally
to every dataset. Output for each PXD is isolated under `pxd_data/{PXD}/` as normal.

---

If `parse_sdrf` is unavailable:
- Warn the user: "Programmatic validation will be skipped."
- Suggest: `/sdrf:setup` or `pip install sdrf-pipelines[ontology]`
- Continue — manual validation is still valuable.

Check that the **crosslinking-xl MCP** is available:
- Call `list_crosslinkers()` — if it returns results, the MCP is live.
- If unavailable: warn user; proceed with manual crosslinker lookup via OLS.

Also update the spec submodule before selecting templates:
```bash
git submodule update --remote --recursive
```

---

## Stage 1: Metadata Gathering

> All metadata fetched in this stage is saved as JSON files under `pxd_data/{PXD}/`
> for reproducibility and debugging. Failures are logged to `pxd_data/{PXD}/stage1.log`
> but never halt the workflow — downstream stages use whatever was successfully saved.

### 1.1 PRIDE project metadata

```
Tool: get_project_details(project_accession="PXD######")
Extract: title, organism, instruments, modifications, publications (PMID/DOI),
         file count, file types, description, submitter notes
```

Save the raw API response to disk:
```bash
# Save PRIDE project metadata (full MCP response)
mkdir -p pxd_data/{PXD}
# Write the JSON returned by get_project_details() to:
#   pxd_data/{PXD}/pride_metadata.json
# If the call fails, write to stage1.log:
#   PRIDE_METADATA: FAILED — {error message}
```

`pride_metadata.json` structure to extract:
```json
{
  "accession": "PXD######",
  "title": "...",
  "organisms": [{"accession": "NCBITaxon:9606", "name": "Homo sapiens"}],
  "instruments": [{"accession": "MS:1002732", "name": "Orbitrap Fusion Lumos"}],
  "modifications": ["Oxidation", "Carbamidomethyl"],
  "publicationList": [{"pubmedId": "12345678", "doi": "10.xxx/yyy"}],
  "submissionDate": "...",
  "labPIs": [...]
}
```

### 1.2 File list

```
Tool: get_project_files(project_accession="PXD######")
Extract: raw file names (for comment[data file]), file types (.raw, .d, .wiff),
         file count, sizes if available
```

Save the raw file list to disk:
```bash
# Write tab-separated file list to /tmp/{PXD}_files.txt  (name \t bytes \t ftp_url)
# Also save a copy to pxd_data/{PXD}/file_list.tsv for the project record
```

### 1.3 Publication

```
a. Extract PMID or DOI from PRIDE publications field
b. If PMID → get_article_metadata(pmids=["PMID"])
c. Convert to PMCID → convert_article_ids(ids=["PMID"], id_type="pmid")
d. If PMCID → get_full_text_article(pmc_ids=["PMCID"])
   Focus on: Abstract, Materials & Methods (crosslinker name, concentration,
   quencher, enzyme, instrument, fractionation, enrichment)
e. If no PMID → search_europepmc(query="PXD######")
f. If DOI only → convert_article_ids(ids=["DOI"], id_type="doi")
```

Save all publication data to disk:
```bash
# Write combined publication JSON to:
#   pxd_data/{PXD}/publication.json
#
# Structure:
# {
#   "pmid": "12345678",
#   "pmcid": "PMC1234567",
#   "doi": "10.xxx/yyy",
#   "title": "...",
#   "abstract": "...",
#   "full_text_available": true,
#   "full_text": "...Methods section text...",
#   "fetch_log": ["get_article_metadata: OK", "get_full_text_article: OK"]
# }
#
# If publication lookup fails entirely, write:
# {"pmid": null, "pmcid": null, "doi": null, "full_text_available": false,
#  "fetch_log": ["FAILED — no PMID in PRIDE metadata", "search_europepmc: no results"]}
#
# Log outcome to pxd_data/{PXD}/stage1.log:
#   PUBLICATION: OK  (PMID=12345678, PMCID=PMC1234567, full_text=yes)
#   PUBLICATION: PARTIAL  (PMID=12345678, no open-access full text)
#   PUBLICATION: FAILED  — {reason}
```

> **It is acceptable for `publication.json` to have partial or no content** — many datasets
> reference papers that are not open-access. The workflow proceeds using PRIDE metadata
> and thermorawfileparser/mzML_assessor outputs for SDRF construction. Log the reason
> for any failure so the annotator can follow up manually.

### 1.4 Structured extraction from the paper

Extract these fields from the Methods section (with confidence + evidence quote):

| SDRF Column | What to Extract |
|---|---|
| `comment[cross-linker]` | Crosslinker name (DSSO, BS3, DSBU, etc.), concentration, target residues |
| `comment[quenching reagent]` | Quencher name (Tris, ABC, ammonium bicarbonate, glycine) |
| `comment[dissociation method]` | HCD, CID, ETD, EThcD, stepped HCD |
| `comment[collision energy]` | NCE value(s) e.g. "27 NCE", "25,27,30 NCE" |
| `comment[cleavage agent details]` | Enzyme (Trypsin, LysC), missed cleavages |
| `comment[instrument]` | Full instrument name (Q Exactive HF, Orbitrap Astral, etc.) |
| `comment[label]` | LFQ, TMT-6, iTRAQ-4, SILAC, or "label free sample" |
| `comment[fraction identifier]` | Number of fractions, method (SCX, HPRP, SEC, none) |
| `comment[crosslink enrichment method]` | SEC, size-exclusion, IMAC, none |
| `characteristics[organism]` | Species |
| `characteristics[organism part]` | Tissue/cell type |
| `characteristics[disease]` | Disease or "normal" |
| `characteristics[biological replicate]` | Number of replicates, how labelled |
| `characteristics[crosslink type]` | inter-protein, intra-protein, mixed |
| `characteristics[enrichment process]` | enrichment of cross-linked peptides |

---

## Stage 2: File List

> **Skip Stages 2–4** entirely if `--no-download` was passed.

### 2.1 Get file list from PRIDE

```
Tool: get_project_files(project_accession="PXD######")
Extract: filenames, FTP URLs, file sizes, file types (.raw, .d, .wiff2)
Filter:  raw instrument files only (exclude .mzML, .mzid, .fasta, result files)
```

If the PRIDE API file list is empty or returns an error, fall back to the FTP index:
```
https://ftp.pride.ebi.ac.uk/pride/data/archive/{YYYY}/{MM}/{PXD}/
```

Save the canonical file list:
```bash
# /tmp/{PXD}_files.txt          ← working copy (name \t bytes \t ftp_url)
# pxd_data/{PXD}/file_list.tsv  ← permanent project record (same format)
```

### 2.2 Present plan to user

> **Default: ALL raw files are processed.** The SDRF will have one row per raw file.
> Pass `--limit N` to process only the first N files (useful for testing).

Report the file inventory and what will happen:

```
Found <N> raw files for {PXD} (total: ~<X> GB)
Files (showing first 5 of <N>):
  - {filename1}.raw  ({size1} MB)
  - {filename2}.raw  ({size2} MB)
  ...

Processing plan: ALL <N> files (serial) via scripts/xhamlet_stage3a.sh
  [--limit <M> passed → will process <M> of <N>]
  Script runs two phases automatically:
    Phase 1 (per file): download .raw → thermorawfileparser metadata → mzML → delete .raw
    Phase 2 (once):     mzML_assessor on all .mzML → study_metadata.json → delete .mzML
  Peak disk use: all mzML files simultaneously (~3–5× one raw file)
  [Pass --skip-spectral to omit mzML conversion/assessment entirely; recommended if disk < N×2 GB]

Intermediate files saved under pxd_data/{PXD}/:
  pride_metadata.json        ← PRIDE API response
  publication.json           ← PubMed/PMC article + full text
  file_list.tsv              ← canonical raw file list
  assessment/*-metadata.json ← thermorawfileparser (one per raw file)
  assessment/study_metadata.json ← mzML_assessor aggregate
  stage1.log                 ← Stage 1 fetch outcomes
```

For Thermo .raw files: thermorawfileparser metadata + mzML conversion run per-file (Phase 1);
mzML_assessor runs ONCE on all mzML files after Phase 1 completes (Phase 2).

If the dataset uses Bruker .d or SCIEX .wiff files: warn the user that non-Thermo formats
are not yet supported — skip to Stage 5.

### 2.3 Detect file format and available converter

| Raw format | Vendor | Tool | Status |
|------------|--------|------|--------|
| `.raw` | Thermo Fisher | `thermorawfileparser` | ✅ Supported |
| `.d` | Bruker | msconvert (ProteoWizard) | ❌ Not yet implemented |
| `.wiff` / `.wiff2` | SCIEX | msconvert (ProteoWizard) | ❌ Not yet implemented |

```bash
thermorawfileparser --version 2>/dev/null && echo "thermorawfileparser: OK"
```

---

## Stage 3: Per-file Processing Loop

> Files are processed **serially**, one at a time. Peak disk usage = size of one raw file.
> No raw or mzML files are retained after this stage (unless `--keep-raw` was passed).

### 3A: Thermo `.raw` — default path

**Use the existing script** — do NOT write new code:

```bash
# Standard run (all files, full mzML spectral assessment):
bash scripts/xhamlet_stage3a.sh {PXD}

# Common variants:
bash scripts/xhamlet_stage3a.sh {PXD} --limit 1           # test with 1 file first
bash scripts/xhamlet_stage3a.sh {PXD} --skip-spectral     # metadata-only (no mzML; faster, low disk)
bash scripts/xhamlet_stage3a.sh {PXD} --skip-existing     # resume after interruption
bash scripts/xhamlet_stage3a.sh {PXD} --keep-raw          # retain .raw files after processing
```

**Disk space check before running** — Phase 2 of the script keeps all mzML files
simultaneously until `mzML_assessor` completes:

```
Expected peak disk use ≈ N_files × avg_mzML_size_GB
  - Each Thermo .raw for XL-MS ≈ 0.5–3 GB as mzML
  - For >30 files: check available disk with `df -h .` before proceeding
  - If disk < expected peak: use --skip-spectral
    (thermorawfileparser instrument metadata is still extracted per-file)
```

The script implements a two-phase workflow:
- **Phase 1 (per file)**: download `.raw` → thermorawfileparser metadata JSON → thermorawfileparser mzML → delete `.raw`
- **Phase 2 (once)**: `mzML_assessor --inpath work/ --outpath assessment/` on all mzML → `study_metadata.json` → delete all mzML

On completion: `pxd_data/{PXD}/work/` will be empty;  
`pxd_data/{PXD}/assessment/` contains `{file}-metadata.json` × N + `study_metadata.json` (1).

> **Never create a new script** to work around disk pressure or to add per-file mzML deletion.
> Use `--skip-spectral` if disk is tight. The existing script is the correct tool.

### 3B: Bruker/SCIEX — mzML conversion path

> **NOT YET IMPLEMENTED** — Bruker .d and SCIEX .wiff support requires ProteoWizard (msconvert),
> which is not currently installed. Deferred to a future iteration.
>
> If the dataset contains .d or .wiff files, warn the user and skip to Stage 5.

### 3.3 Track progress

After each file completes, log the result:

```
Phase 1:
[1/96] {file}.raw → thermorawfileparser ✓ + mzML ✓  (downloaded 420 MB)
[2/96] {file}.raw → thermorawfileparser ✓ + mzML ✓  (downloaded 380 MB)
...
[5/96] {file}.raw → FAILED: converter error — skipping
...
[96/96] done

Phase 2: mzML assessor (95 files)
  → study_metadata.json written
  ✓ All mzML files assessed and deleted
```

Stop early if ≥3 consecutive failures (likely a converter/format problem).

---

## Stage 4: Spectral Assessment

> **Skip this stage** if `--no-download` or `--skip-spectral` was passed, or if Stage 3 was skipped.

The purpose is to **confirm or correct** technical metadata extracted from the paper:
- DDA vs DIA acquisition mode
- Fragmentation method (HCD / ETD / EThcD / stepped HCD)
- Label type (LFQ / TMT / SILAC)
- Instrument model (cross-check with PRIDE metadata)

Two sources of assessment data are merged (both produced in Stage 3A by default):
1. **`{file}-metadata.json`** — thermorawfileparser per-file output: instrument model, method filename, scan counts
2. **`study_metadata.json`** — mzML_assessor aggregate output: acquisition type, fragmentation type, labeling scores

### 4.1 Parse thermorawfileparser JSON (per-file)

Output files are named `{file}-metadata.json` in `pxd_data/{PXD}/assessment/`.

Verified JSON structure (thermorawfileparser v2.0.0.0):

```json
{
  "FileProperties": [
    {"accession": "NCIT:C47922", "name": "Pathname",              "value": "/path/to/file.raw"},
    {"accession": "NCIT:C25714", "name": "Version",               "value": "66"},
    {"accession": "NCIT:C69199", "name": "Content Creation Date", "value": "10/07/2021 01:48:59"}
  ],
  "InstrumentProperties": [
    {"accession": "MS:1000494", "name": "Thermo Scientific instrument model", "value": "Orbitrap Fusion Lumos"},
    {"accession": "MS:1000496", "name": "instrument attribute",              "value": "Orbitrap Fusion Lumos"},
    {"accession": "MS:1000529", "name": "instrument serial number",          "value": "EXRFSN20471"},
    {"accession": "NCIT:C111093","name": "Software Version",                 "value": "3.4.3072.18"}
  ],
  "MsData": [
    {"accession": "PRIDE:0000481", "name": "Number of MS1 spectra", "value": "24996"},
    {"accession": "PRIDE:0000482", "name": "Number of MS2 spectra", "value": "691"},
    {"accession": "PRIDE:0000472", "name": "MS min charge",         "value": "4"},
    {"accession": "PRIDE:0000473", "name": "MS max charge",         "value": "6"},
    {"accession": "PRIDE:0000474", "name": "MS min RT",             "value": "0.001..."},
    {"accession": "PRIDE:0000475", "name": "MS max RT",             "value": "177.0..."},
    {"accession": "PRIDE:0000476", "name": "MS min MZ",             "value": "388.43..."},
    {"accession": "PRIDE:0000477", "name": "MS max MZ",             "value": "1124.48..."}
  ],
  "ScanSettings": [
    {"accession": "PRIDE:0000478", "name": "Number of scans",      "value": "25687"},
    {"accession": "MS:1000422",    "name": "beam-type collision-induced dissociation", "value": "HCD"},
    {"accession": "PRIDE:0000484", "name": "Retention time range", "value": "0.001:177.01"},
    {"accession": "PRIDE:0000485", "name": "Mz range",             "value": "130:2000"}
  ],
  "SampleData": [
    {"accession": "AFR:0002045", "name": "device acquisition method",
     "value": "C:\\Xcalibur\\methods\\...\\DSSO_trig180minXL_StepHCD152127_MS2_FAIMS_50_60_75.meth"}
  ]
}
```

Extract these fields using Python:

```python
import json, glob, collections

def parse_meta(meta):
    """Extract SDRF-relevant fields from thermorawfileparser metadata JSON."""
    result = {}

    # Instrument model (from InstrumentProperties)
    for item in meta.get("InstrumentProperties", []):
        if item["accession"] == "MS:1000494":
            result["instrument_model"] = item["value"]      # e.g. "Orbitrap Fusion Lumos"
            result["instrument_accession"] = "MS:1000494"

    # Fragmentation method (from ScanSettings)
    for item in meta.get("ScanSettings", []):
        if item["name"] in ("beam-type collision-induced dissociation",
                             "electron transfer dissociation",
                             "supplemental beam-type collision-induced dissociation"):
            result.setdefault("activations", []).append(item["name"])

    # MS1/MS2 counts (from MsData)
    for item in meta.get("MsData", []):
        if item["accession"] == "PRIDE:0000481":
            result["ms1_count"] = int(item["value"])
        elif item["accession"] == "PRIDE:0000482":
            result["ms2_count"] = int(item["value"])

    # Acquisition method file name — may encode stepped HCD, FAIMS CVs, etc.
    for item in meta.get("SampleData", []):
        if item["accession"] == "AFR:0002045":
            result["method_file"] = item["value"]

    return result

# Aggregate across all files
all_results = []
for meta_file in sorted(glob.glob("pxd_data/{PXD}/assessment/*-metadata.json")):
    with open(meta_file) as f:
        meta = json.load(f)
    all_results.append(parse_meta(meta))

# Summarise
instruments  = collections.Counter(r.get("instrument_model") for r in all_results)
activations  = collections.Counter(a for r in all_results for a in r.get("activations", []))
total_ms2    = sum(r.get("ms2_count", 0) for r in all_results)
method_files = set(r.get("method_file", "") for r in all_results)

print("Instruments:",  dict(instruments))
print("Activations:",  dict(activations))
print("Total MS2:",    total_ms2)
print("Method files:", method_files)    # inspect for StepHCD, FAIMS, etc.
```

**Important**: `ScanSettings` reports the dominant fragmentation type. If the method file name
contains `StepHCD` / `SteppedHCD`, the true dissociation method is **stepped HCD** (MS:1002134),
even though the JSON only says `HCD`.

| JSON field | SDRF column | Notes |
|------------|-------------|-------|
| `InstrumentProperties[MS:1000494].value` | `comment[instrument]` | Use accession `MS:1000494` |
| `ScanSettings[MS:1000422]` present | `comment[dissociation method]` = HCD (`MS:1000422`) | Check method file for stepped HCD |
| `SampleData[AFR:0002045].value` contains `StepHCD` | `comment[dissociation method]` = stepped HCD (`MS:1002134`) | Method file is more specific |
| `SampleData[AFR:0002045].value` contains `FAIMS_50_60_75` | `comment[fractionation method]` = FAIMS | CVs 50, 60, 75 V |

### 4.2 Parse mzML_assessor JSON (study_metadata.json)

After Stage 3A completes, `pxd_data/{PXD}/assessment/study_metadata.json` exists.
Parse it to extract study-level spectral parameters:

```python
import json

data = json.load(open("pxd_data/{PXD}/assessment/study_metadata.json"))

# Study-level aggregated results
search_criteria = data["search_criteria"]
knowledge       = data["knowledge"]

acquisition_type         = search_criteria.get("acquisition_type")         # "DDA" | "DIA"
fragmentation_type       = search_criteria.get("fragmentation_type")       # "HR_HCD" | "HR_IT_CID" | ...
high_accuracy_precursors = search_criteria.get("high_accuracy_precursors") # "true" | "false"
labeling                 = search_criteria.get("labeling")                 # "none" | "TMT6" | "TMTpro" | ...
instrument_model         = knowledge.get("instrument_model")               # e.g. "Orbitrap Fusion Lumos"

# Per-file details (first file as representative)
files = data["files"]
first_file = next(iter(files.values()))
spectra_stats    = first_file.get("spectra_stats", {})
instrument_info  = first_file.get("instrument_model", {})
labeling_scores  = first_file.get("summary", {}).get("labeling", {}).get("scores", {})

print(f"Acquisition:   {acquisition_type}")
print(f"Fragmentation: {fragmentation_type}")
print(f"Labeling:      {labeling}  (scores: {labeling_scores})")
print(f"Instrument:    {instrument_model}")
print(f"MS2 spectra:   {spectra_stats.get('n_ms2_spectra')}")
```

**Fragmentation type mapping** from mzML_assessor tags to SDRF terms:

| mzML_assessor `fragmentation_type` | SDRF `comment[dissociation method]` | Accession |
|---|---|---|
| `HR_HCD` | `NT=beam-type collision-induced dissociation;AC=MS:1000422` | MS:1000422 |
| `HR_EThcD` | `NT=supplemental beam-type collision-induced dissociation;AC=MS:1002678` | MS:1002678 |
| `HR_IT_ETD` | `NT=electron transfer dissociation;AC=MS:1000598` | MS:1000598 |
| `HR_IT_CID` | `NT=trap-type collision-induced dissociation;AC=MS:1002472` | MS:1002472 |

> **Note on stepped HCD**: mzML_assessor reports `HR_HCD` even for stepped HCD experiments,
> because stepped HCD is a scan-level parameter not distinguishable from plain HCD in mzML.
> Always cross-check the thermorawfileparser method filename (Step 4.1) — if it contains
> `StepHCD` or `SteppedHCD`, override with `NT=stepped HCD;AC=PRIDE:0000590`.

**Labeling detection** — mzML_assessor scores TMT/iTRAQ reporter ions:
- `"none"` → label-free: `NT=label free sample;AC=MS:1002038`
- `"TMT6"` → `NT=TMT6;AC=PRIDE:0000114`
- `"TMTpro"` → `NT=TMTpro;AC=PRIDE:0000636`
- `"iTRAQ4"` → `NT=iTRAQ4plex;AC=PRIDE:0000114`

### 4.3 Merge all four sources and reconcile

After Stage 3A completes, four JSON sources are available for SDRF construction.
Merge them in priority order (higher = more authoritative):

```
Source priority (highest to lowest):
  1. assessment/{file}-metadata.json    thermorawfileparser — instrument model, method file, scan counts
  2. assessment/study_metadata.json     mzML_assessor      — acquisition type, fragmentation, labeling
  3. pride_metadata.json                PRIDE API          — organism, instruments list, modifications
  4. publication.json                   PubMed/PMC         — crosslinker, enzyme, NCE, tissue, disease
```

Produce a consolidated assessment summary:

```
Spectral assessment summary ({N} files processed):
  Instrument:          {model}        [thermorawfileparser InstrumentProperties | pride_metadata instruments]
  Acquisition:         DDA / DIA      [mzML_assessor search_criteria.acquisition_type]
  Fragmentation:       HR_HCD / ...   [mzML_assessor; cross-check method filename for StepHCD]
  Labeling:            none / TMT6    [mzML_assessor; confirm vs paper]
  MS2 scans (total):   {count}        [sum from thermorawfileparser MsData across all files]
  Method file:         {filename}     [thermorawfileparser SampleData]
  FAIMS CVs:           {cvs}          [parsed from method filename if present]
  StepHCD NCE:         {values}       [parsed from method filename if present]
  Crosslinker (paper): {name}         [publication.json Methods section]
  Organism (PRIDE):    {organism}     [pride_metadata.json organisms[0].name]
  Tissue (paper):      {tissue}       [publication.json]
```

If `study_metadata.json` is missing (--skip-spectral was used): fill acquisition/fragmentation/labeling
from `publication.json` or `pride_metadata.json` instead, and note the lower confidence.

### 4.4 Reconcile with paper-extracted metadata

- If assessment **agrees** with paper: use paper values (higher specificity, e.g. "stepped HCD")
- If assessment **disagrees**: flag discrepancy; prefer raw file evidence for instrument/fragmentation fields; prefer paper for biology fields (organism, disease)
- If instrument name from raw differs from PRIDE metadata: use raw file value (most precise)
- Update `comment[collision energy]` from raw scan values if paper was vague

---

## Stage 5: Crosslinker Resolution

### 5.1 Identify the crosslinker (crosslinking-xl MCP)
```
Tool: identify_crosslinker(name="<name from paper>")
```
- Use `name` exactly as written in the paper first (e.g., "DSSO", "BS³", "disuccinimidyl sulfoxide")
- If not found: try common abbreviations, check `list_crosslinkers()` for the closest match
- Extract: `xlmod_accession`, `sdrf_comment_cross_linker`, `xi_class`, `mass`, `cleavable`

If XLMOD accession is null or the crosslinker is not in the database:
1. Search OLS: `searchClasses(query="<crosslinker name>", ontologyId="xlmod")`
2. If found in OLS: use that accession; note it may be missing from the local database
3. If not in XLMOD at all: use `NT=<name>` (no AC field) and log a WARNING

### 5.2 Resolve the quencher (crosslinking-xl MCP)
```
Tool: resolve_quencher(crosslinker_name="<xl name>", quencher_name="<quencher from paper>")
```
- Use the free-text quencher from the paper (e.g., "20 mM Tris-HCl pH 8.0")
- Extract: `quencher_canonical`, `xi_symbol`, `mono_link_mass`, `xi_modification_string`

If quencher not found or not in paper:
- Set `comment[quenching reagent]` = `"not available"`
- Log WARNING: "Quencher not specified; mono-link mass unknown"
- Use only Oxidation (M) as variable mod in Xi configs

### 5.3 Multiple crosslinkers
If the paper used more than one crosslinker (e.g., DSSO + BS3):
- Create a `comment[cross-linker]` column for each crosslinker
- Or create separate SDRF sub-tables per crosslinker condition
- Generate separate Xi configs for each crosslinker

---

## Stage 6: Template Selection

Using the SDRF template decision tree:

**Always required for XL-MS:**
1. `ms-proteomics` — base proteomics template
2. `crosslinking` — adds XL-MS-specific columns

**Organism-based (pick one):**
- Homo sapiens → `+ human`
- Mouse/rat/zebrafish → `+ vertebrates`
- Insect/worm → `+ invertebrates`
- Plant → `+ plants`

**Experiment-based (add if applicable):**
- DIA acquisition → `+ dia-acquisition`
- Cell line study → `+ cell-lines`
- Clinical patient cohort → `+ clinical-metadata`
- Cancer metadata → `+ oncology-metadata`
- In vivo crosslinking (photo-amino acids) → note: still use `crosslinking`

Read the crosslinking template:
```bash
spec/sdrf-proteomics/sdrf-templates/crosslinking/{version}/crosslinking.yaml
```
Use `spec/sdrf-proteomics/sdrf-templates/templates.yaml` to get the current version.

Present template selection to the user for confirmation.

---

## Stage 7: SDRF Construction

### 7.0 Input JSON sources

All four intermediate JSON files feed SDRF construction:

| JSON file | Provides |
|---|---|
| `pxd_data/{PXD}/pride_metadata.json` | Organism, instrument list, modification hints, submitter notes |
| `pxd_data/{PXD}/publication.json` | Crosslinker, enzyme, NCE, tissue, disease, replicate design |
| `pxd_data/{PXD}/assessment/{file}-metadata.json` | Per-file instrument model, method file, scan counts, RT/mz range |
| `pxd_data/{PXD}/assessment/study_metadata.json` | Study-level DDA/DIA, fragmentation type, labeling detection |

If any source is missing or partial, use the remaining sources and note reduced confidence
in a `# comment` block above the SDRF header row.

### 7.1 Column set
Build columns from `spec/sdrf-proteomics/TERMS.tsv` for all selected templates.

**Required crosslinking template columns:**
- `comment[cross-linker]` — full format: `NT=<name>;AC=<XLMOD:accession>;CL=yes|no;TA=<residues>[;MH=<stub1>;ML=<stub2>]`
  - For MS-cleavable XLs include stub masses: e.g., `NT=DSSO;AC=XLMOD:02126;CL=yes;TA=K,S,T,Y,nterm;MH=54.01;ML=85.98`
  - `get_sdrf_crosslinker()` from crosslinking-xl MCP generates this automatically
- `comment[dissociation method]` — use `NT=HCD;AC=MS:1000422` for HCD/stepped-HCD experiments

**Recommended crosslinking columns:**
- `characteristics[enrichment process]` — `enrichment of cross-linked peptides`
- `comment[collision energy]` — e.g., `27 NCE`
- `comment[quenching reagent]` — canonical quencher name or `not available`
- `comment[crosslink enrichment method]` — SEC | IMAC | `not applicable`
- `comment[chemical cross-linking coupled with ms]` — `yes`

**Optional crosslinking columns (include if evidence found):**
- `characteristics[crosslink distance]` — e.g., `26.4 Å` (from DSSO spacer arm)
- `characteristics[crosslink type]` — `inter-protein` | `intra-protein` | `mixed`
- `comment[crosslinker concentration]` — e.g., `0.5 mM`
- `characteristics[crosslinking reaction time]` — e.g., `30 min`
- `characteristics[crosslinking temperature]` — e.g., `4°C`
- `comment[crosslinker to protein ratio]` — e.g., `25:1`

**Inherited ms-proteomics required columns:**
- `source name`, `assay name`, `technology type`
- `characteristics[organism]`, `characteristics[organism part]`, `characteristics[disease]`
- `comment[data file]`, `comment[instrument]`, `comment[label]`
- `comment[modification parameters]` — one column per modification
- `comment[fraction identifier]`, `comment[technical replicate]`
- `comment[cleavage agent details]`
- `comment[sdrf template]` — one column per template

### 7.2 OLS ontology validation

For each ontology-controlled column, verify the term via OLS before writing:

| Column | Ontology | Tool |
|---|---|---|
| `characteristics[organism]` | NCBITaxon | `searchClasses(query="Homo sapiens", ontologyId="ncbitaxon")` |
| `characteristics[organism part]` | UBERON | `searchClasses(query="liver", ontologyId="uberon")` |
| `characteristics[disease]` | MONDO | `searchClasses(query="breast cancer", ontologyId="mondo")` |
| `characteristics[cell type]` | CL | `searchClasses(query="HEK293", ontologyId="cl")` |
| `comment[instrument]` | MS | `searchClasses(query="Q Exactive HF", ontologyId="ms")` |
| `comment[cross-linker]` | XLMOD | Already resolved via crosslinking-xl MCP |
| `comment[label]` | MS or PRIDE | `searchClasses(query="label free sample", ontologyId="ms")` |
| `comment[dissociation method]` | MS | `searchClasses(query="HCD", ontologyId="ms")` |
| `comment[modification parameters]` | UNIMOD | `searchClasses(query="Oxidation", ontologyId="unimod")` |
| `comment[cleavage agent details]` | MS | `searchClasses(query="Trypsin", ontologyId="ms")` |

**Modification format:**  
`NT=Oxidation;AC=UNIMOD:21;TA=M;MT=Variable`  
`NT=Carbamidomethyl;AC=UNIMOD:4;TA=C;MT=Fixed`

### 7.3 One row per MS run

- Each raw file = one row in the SDRF
- Assign `source name` = sample identifier (e.g., S1, S2, or from paper)
- Assign `assay name` = run identifier (e.g., Run1, or raw file base name without extension)
- `technology type` = `"proteomic profiling by mass spectrometry"`
- `comment[data file]` = exact filename as listed in PRIDE

### 7.4 Fraction handling
- If fractionated: `comment[fraction identifier]` = 1, 2, 3, ... per fraction
- If not fractionated: `comment[fraction identifier]` = `1`

### 7.5 SDRF template metadata (last columns)
```
comment[sdrf template] = "NT=ms-proteomics;VV=<version>"
comment[sdrf template] = "NT=crosslinking;VV=<version>"     ← second column, same name
comment[sdrf template] = "NT=human;VV=<version>"            ← etc.
```
Multiple `comment[sdrf template]` columns are CORRECT — one per template.

---

## Stage 8: Validation

```bash
parse_sdrf validate-sdrf --sdrf_file <pxd>.sdrf.tsv --template crosslinking
```

### Fix common crosslinking errors
| Error | Fix |
|---|---|
| `XLMOD accession not valid` | Re-verify via OLS `searchClasses(ontologyId="xlmod")` |
| `cross-linker format invalid` | Use `NT=name;AC=XLMOD:XXXXX` — no spaces, semicolons as separators |
| `dissociation method not found` | Check MS ontology: HCD = MS:1000422, ETD = MS:1000598, EThcD = MS:1002631 |
| `modification parameters format` | Must be `NT=X;AC=UNIMOD:N;TA=X;MT=Fixed|Variable` |
| `enrichment process value` | Must be exact: `"enrichment of cross-linked peptides"` |

Iterate until 0 errors. Warnings are acceptable if they are expected (e.g., novel crosslinker).

---

## Stage 9: Xi Config Generation

Generate Xi search engine configuration files using the crosslinking-xl MCP.

### 9.1 Generate XL config
```
Tool: generate_xi_config(
    crosslinker_name="<xl name>",
    quencher_name="<quencher or null>",
    enzyme="<enzyme>",
    mode="xl"
)
```

### 9.2 Generate linear config
```
Tool: generate_xi_config(
    crosslinker_name="Linear",
    quencher_name=null,
    enzyme="<enzyme>",
    mode="linear"
)
```

### 9.3 Save configs
Write the config text to files:
- `<PXD>/xi_configs/xi_crosslinking.conf`
- `<PXD>/xi_configs/xi_linear.conf`

Remind the user:
- Configs use default tolerances: 10 ppm precursor, 20 ppm fragment
- These should be adjusted based on instrument type (e.g., Orbitrap Astral → tighter)
- Add FASTA database path manually: `sequenceDB:<path/to/db.fasta>`

---

## Stage 10: Summary

Report to the user:

```
✓ SDRF generated: <PXD>.sdrf.tsv
  - <N> rows (MS runs)
  - Templates: ms-proteomics, crosslinking, <organism>
  - Crosslinker: <name> (XLMOD:<accession>)
  - Quencher: <canonical name> (mono-link mass: <mass> Da)
  - Validation: PASSED (N errors, M warnings)

✓ Raw file processing: <N> files processed, <M> failed  [if Stages 2–4 ran]
  - Method: metadata-only (thermorawfileparser -f 4 -m 0)  OR  mzML conversion path
  - Peak disk use: ~<largest single file size> GB
  - All raw files deleted after processing  [unless --keep-raw]
  - Assessment JSON: pxd_data/<PXD>/assessment/

✓ Spectral QC:     acquisition=<DDA/DIA>, fragmentation=<>, instrument=<>  [if Stage 4 ran]

✓ Xi configs generated:
  - xi_crosslinking.conf
  - xi_linear.conf
  - Crosslinker: <Xi format line>
  - Mono-link mod: <Xi mod line>

⚠ Warnings (if any):
  - [list any unresolved fields, manual action needed]

Next steps:
  1. Add FASTA database path to Xi configs: sequenceDB:<path>
  2. Review any WARNING fields in the SDRF
  3. Use /sdrf:improve to score annotation quality
  4. Use /sdrf:contribute to submit via PR when ready
```

---

## Edge Cases

### Multiple crosslinkers in one study
- Check if paper used multiple crosslinkers (e.g., DSSO + BS3)
- Option A: One SDRF with multiple `comment[cross-linker]` columns (one per crosslinker per row)
- Option B: Separate SDRF sub-tables if crosslinker varies per sample
- Generate separate Xi configs per crosslinker
- Ask user which approach to use if ambiguous

### Quencher not stated in paper
1. Search PMC full text for "quench", "Tris", "ammonium bicarbonate", "ABC"
2. If still not found: use `not available` for `comment[quenching reagent]`
3. Log WARNING; add only Oxidation (M) as variable mod to Xi configs

### Crosslinker not in XLMOD
1. Verify via OLS: `searchClasses(query="<name>", ontologyId="xlmod")`
2. If truly absent: use `NT=<name>` (no AC field)
3. Log WARNING: "XLMOD accession unavailable; review manually"

### Photo-crosslinkers (SDA, photo-leucine, photo-methionine)
- Still use `crosslinking` template
- `comment[cross-linker]` = `NT=SDA;AC=XLMOD:02134` etc.
- For metabolically incorporated photo-amino acids: note in `comment[notes]` if column exists
- Xi class: SDA = AsymetricSingleAminoAcidRestrictedCrossLinker

### MS-cleavable crosslinkers (DSSO, DSBU, DSAU, BS2G)
- Must include `STUBS` in Xi config line
- DSSO stubs: `A,54.0105647,S,103.9932001,T,85.9826354`
- DSBU stubs: `Bu,85.052763875,BuUr,111.032028435`
- `generate_xi_config` handles this automatically from crosslinker_definitions.json

> **Verified XLMOD accessions (OLS-confirmed)**
> - DSSO = `XLMOD:02126` (Disuccinimidyl sulfoxide, CID-cleavable C-S bond)
> - DSBU = `XLMOD:02184`
> - BS3/BS²G = `XLMOD:02001` (homobifunctional NHS ester)
> - EDC = `XLMOD:02010` (zero-length carbodiimide)
> - SDA = `XLMOD:02134` (photo-reactive NHS ester)
>
> ⚠️ **Known spec example bug**: `spec/examples/PXD042173/PXD042173.sdrf.tsv` uses
> `XLMOD:02010` for DSSO — this is wrong. XLMOD:02010 = EDC, not DSSO.
> The correct accession for DSSO is `XLMOD:02126`.

### Zero-length crosslinkers (EDC, CDI, DMTMM)
- `comment[cross-linker]` still follows `NT=EDC;AC=XLMOD:02010`
- `characteristics[crosslink type]` = `"zero-length"`
- EDC is asymmetric: SDRF note "carboxyl to amine" if space allows

### Enrichment
- If crosslinks were enriched (SEC, IMAC, size-exclusion):
  `characteristics[enrichment process]` = `"enrichment of cross-linked peptides"`
  `comment[crosslink enrichment method]` = the method (e.g., `size-exclusion chromatography`)
- If no enrichment: omit `comment[crosslink enrichment method]` or set to `"not applicable"`

---

## Key Rules (never violate)

1. **Never guess XLMOD accessions** — always use crosslinking-xl MCP or OLS
2. **Never use "N/A" or "NA"** — use `"not available"` or `"not applicable"` (reserved words)
3. **`comment[cross-linker]` format**: `NT=<name>;AC=<XLMOD:id>;CL=yes|no;TA=<residues>`
4. **Multiple `comment[modification parameters]`** columns = CORRECT (one per mod)
5. **Multiple `comment[sdrf template]`** columns = CORRECT (one per template)
6. **UNIMOD for PTMs**, **XLMOD for crosslinkers** — never swap
7. **Validate before presenting** any SDRF to the user
