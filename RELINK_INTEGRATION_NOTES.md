# ReLink Integration — Development Notes

**Last updated**: 2026-06-29  
**Status**: 🔧 In progress — XiSearch crosslink search memory issue blocking completion

---

## What Works

| Stage | Status | Notes |
|-------|--------|-------|
| Singularity container pull | ✅ Fixed | `oras://` failed; fixed via `singularity_pull_docker_container=true` in `assets/nextflow_singularity_docker_pull.config` |
| FASTA download | ✅ Fixed | Now downloads SwissProt-only (`reviewed:true`) — 13 MB vs 107 MB (full TrEMBL) |
| Multi-organism detection | ✅ Working | Taxids extracted from LLM clustering response, SDRF, and file_assignment_map |
| Stale session cleanup | ✅ Fixed | `ReLinkRunner._clean_nextflow_state()` removes `.nextflow/` before each run |
| Silent retry loop | ✅ Fixed | `XISEARCH_CROSSLINK` and `XISEARCH_LINEAR` set to `maxRetries=0, errorStrategy=finish` |
| ThermoRawFileParser (mzML) | ✅ Working | Runs correctly with Singularity |
| XISEARCH_LINEAR | ✅ Working | Completes in ~8 min per file |
| MASS_RECALIBRATION | ✅ Working | Completes in ~20s |
| XISEARCH_CROSSLINK | ❌ Blocked | OOM during fragment tree construction — see below |
| CLI args (-work-dir, -qs) | ✅ Fixed | Now passed as proper Nextflow CLI args, not via NXF_OPTS (which crashed JVM) |

---

## Root Cause: XiSearch Crosslink OOM

### Symptom
`XISEARCH_CROSSLINK` runs with `java -Xmx64g` and builds an in-memory fragment tree from all digested peptides. The process hits severe GC pressure (~100% GC time) and stalls indefinitely between 60–70% of fragment tree construction.

### Why it happens
The peptide count is too large for the 64 GB heap:

| Config | Peptide count | Outcome |
|--------|--------------|---------|
| `missedcleavages:3`, full TrEMBL FASTA (107 MB) | ~94M | OOM immediately |
| `missedcleavages:2`, SwissProt FASTA (13 MB) | ~68.5M | Severe GC, eventual kill |
| `missedcleavages:1`, SwissProt FASTA (13 MB) | ~25.6M | GC pressure ~65%, still stalls |

### Why `missedcleavages:1` still fails
Even at 25.6M total peptides, the fragment tree construction uses significantly more RAM than the peptide list itself. GC pressure starts consistently around 65% fragmentation progress (~16.8M / 25.6M peptides).

The main driver of peptide space explosion is the **5 DSSO variable quench modifications**:
- `dsso_tris` variable mod applied to: K, nterm, S, T, Y
- Every peptide containing any of these residues is expanded into multiple variants
- Combined with Lys-C + Trypsin sequential digest, this creates a combinatorial explosion

### Fix needed (TODO)
Remove S, T, Y, and nterm as DSSO quench sites — keep only K (the primary crosslink site).  
Alternatively, make quench mods fixed instead of variable, since quenched peptides are already crosslinked and the mod is deterministic.

In `src/pxd_enhancer/xi_config_generator.py`, the `_get_variable_modifications_for_crosslinker()` method generates these mods from `crosslinker_definitions.json`. The quencher mods should be restricted to the primary crosslink residue (K for DSSO) rather than all crosslinkable sites.

---

## Architecture Changes Made

### `src/pxd_enhancer/relink_runner.py`
- `fetch_fasta_for_taxid()`: Added `AND reviewed:true` to UniProt query
- `run_nextflow()`: Auto-injects `-c assets/nextflow_singularity_docker_pull.config` for Singularity profile; cleans `.nextflow/` state before each run
- `_clean_nextflow_state()`: Removes stale `.nextflow/` dir and `.nextflow.log*` from `tools/relink/`

### `src/pxd_enhancer/extractor.py`
- `process_pxd()`: Added `relink_work_dir` and `relink_queue_size` parameters; passes as `extra_args` to `run_for_pxd()`

### `src/main.py`
- Added `--relink-work-dir` and `--relink-queue-size` CLI flags

### `src/pxd_enhancer/xi_config_generator.py`
- Template: `missedcleavages:3` → `missedcleavages:1`

### `assets/nextflow_singularity_docker_pull.config`
- Sets `ext.singularity_pull_docker_container = true` (fixes `oras://` container pull)
- Sets `maxRetries=0, errorStrategy=finish` for `XISEARCH_CROSSLINK` and `XISEARCH_LINEAR`

### `test_full_pipeline.py`
- Full pipeline test script (stages 1–9), replaces old `test_stage9_direct.py` and related scripts
- Streams pipeline output in real time with pass/fail detection
- Sets `NXF_SINGULARITY_CACHEDIR` env var to preserve container cache

---

## SDRF Issue (Separate Bug)

For PXD042173, the SDRF `characteristics[organism]` is set to `Escherichia coli` because E. coli was the growth organism, but the proteins of interest are human (taxid 9606). The ReLink FASTA correctly uses human proteins. The organism column issue is in the LLM extraction prompt and needs a future fix — the prompt should distinguish between the "growth/host organism" and the "study organism / proteins of interest".

---

## How to Resume After Kill

```bash
# Kill any running processes first, confirm clean:
ps aux | grep -E "nextflow|java|xisearch" | grep -v grep

# Delete Xi configs so they regenerate with missedcleavages:1
rm pxd_data/PXD042173/configs/xi_crosslinking.conf pxd_data/PXD042173/configs/xi_linear.conf

# Clean stale Nextflow session state (also done automatically by ReLinkRunner now)
rm -rf tools/relink/.nextflow tools/relink/.nextflow.log*

# Resume from cached LLM/SDRF/FASTA (skip download, skip spectral)
python3 test_full_pipeline.py --no-download --resume
```

---

## Next Steps

1. **Fix quench mods in Xi config generator** — restrict `dsso_tris` variable mod to K only (primary crosslink site), drop S/T/Y/nterm as quench targets
2. **Test with updated config** — should bring peptide count below ~5M, well within 64 GB heap
3. **Fix SDRF organism extraction** — update LLM prompt to correctly identify "proteins of interest" organism vs growth organism
4. **Second RAW file** — current test only processes 2 files; verify second file (F1_F2) also completes after first (C5_152127) succeeds
