# Intelligent Metadata Compilation for Crosslinking Mass Spectrometry Data
https://github.com/NCEMS/XLMS-PPI-working-group  

## Project Abstract

Crosslinking mass spectrometry (XL-MS) is a powerful structural proteomics method that provides high-resolution structural information about complex mixtures of proteins in their native physiological context.[1],[2],[3] The method works by chemically crosslinking two reactive amino acid residues that are close to one another in 3-D space, thereby freezing this spatial information into a covalent bond, and then retrieving this information by sequencing crosslinked peptides following enzymatic digest of the constituent proteins (like Hi-C,[4] but for proteins).

This project seeks to standardize, combine, and integrate existing publicly available crosslinking datasets from PRIDE to make these data more reusable and useful for integrative and hybrid modeling. We will also create a meta-dataset to catalogue protein-protein interactions (PPIs) in human and other model organisms. Because XL-MS encodes information about both protein identity and interacting residues, these findings can be cross-validated to structural predictions of protein complexes using AlphaFold3, thereby providing stronger evidence for their existence compared to other databases that predict protein complexes without structural evidence. We will integrate these findings into the EBI Complex Portal to make it accessible to the life science community.

## Key Features

### 1. Automated Metadata Extraction from PRIDE
- Fetches project metadata directly from PRIDE
- Extracts sample characteristics, proteomics protocols, and instrument information
- Parses publication metadata from associated publications (via PubMed/PMC)

### 2. LLM-Enhanced Metadata Processing
- Uses GPT-4o-mini to extract and standardize structured metadata from publications
- Intelligent parsing of crosslinker information, digestion enzymes, modifications
- Validation of extracted data against known parameters (15+ crosslinkers)

### 3. Xi Search Engine Configuration Generation ⭐ NEW
- **Automatically generates Xi search engine configuration files for each project**
- Creates paired configurations: one for crosslinking analysis, one for linear peptide analysis
- Intelligent parameter extraction based on:
  - **Crosslinker identification and mapping** to Xi format (DSSO, BS³, DSS, EDC, Formaldehyde, etc.)
  - **Digestion enzyme detection** (Trypsin, Lys-C, Pepsin, Chymotrypsin, Glu-C, Asp-N)
  - **Mono-quench modification support** (Tris, Ammonium bicarbonate, Glycine)
  - **Modification mapping** (crosslinker-specific modifications, oxidation, etc.)
- Configuration features:
  - Mass tolerance settings (10 ppm precursor, 20 ppm fragment)
  - Automatic digestion parameter inference
  - **Quencher-aware mono-link masses** (e.g., BS3+Tris → bs3_tris modifications)
  - Crosslinker-specific variable modifications
  - Proper handling of linear vs. crosslinked search differences (TOPMATCHESONLY parameter)

#### Mono-Quench Modifications (New Feature)
The system now automatically generates mono-link (dead-end) modifications for crosslinker-quencher combinations:
- **Tris**: Supported for DSSO, BS³, DSS, DSBU crosslinkers
  - Example: `modification:variable::SYMBOLEXT:dsso_tris;MODIFIED:K;DELTAMASS:279.077658`
- **Ammonium bicarbonate (ABC)**: Supported for DSSO, BS³, DSS, DSBU
  - Different mass shifts than Tris (e.g., DSSO+ABC = 263.062 Da vs DSSO+Tris = 279.078 Da)
- **Glycine**: Supported for Formaldehyde crosslinking
- Quencher lookup table: [assets/quencher_definitions.json](assets/quencher_definitions.json)
- If quencher is not found or not in lookup table, configs still generate with default oxidation only (safe fallback with warning)

### 4. Comprehensive Data Organization
- Structured directory layout for each PXD project:
  - `pride/` - Raw PRIDE metadata
  - `pmc/` - Publication metadata from PMC
  - `llm/` - LLM-generated extractions
  - `enhanced/` - Final compiled metadata
  - `configs/` - Generated Xi configuration files

## Contacts and Important Links

*Working Group Leadership*
- Lead: Stephen D. Fried, Johns Hopkins University, sdfried@jhu.edu
- Co-Lead: Yasset Perez-Riverol, EMBL-EBI, yperez@ebi.ac.uk
- Co-Lead: Henning Hermjakob, EMBL-EBI, hhe@ebi.ac.uk

*NCEMS Staff*
- Staff Scientist: Ian Sitarik, Penn State University, ims86@psu.edu
- Project Coordinator: Maowei Dong, Penn State University, mod5361@psu.edu

*Communication links*
- [Zoom Meeting](https://psu.zoom.us/j/2163369137?pwd=K0l5Mmo2ZGpFSitwTVVBOUljaE1Fdz09)
- [Slack Channel](https://friedlab.slack.com/archives/C09L906UPUH)

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt

# Set up environment variables (or edit config.yaml)
export OPENAI_API_KEY="your-openai-key"
export NCBI_API_KEY="your-ncbi-key"  # Optional but recommended
```

### Command-Line Usage (Via main.py)

The pipeline can be run from the command line to process one or multiple PXD projects:

#### Process a Single PXD
```bash
python src/main.py --pxd PXD017620
```

#### Process Multiple PXDs
```bash
python src/main.py --pxd PXD017620 PXD042173
```

#### With Custom Configuration
```bash
python src/main.py --pxd PXD017620 --config config.yaml --verbose
```

#### Force Refresh (Reprocess even if data exists)
```bash
python src/main.py --pxd PXD017620 --force-refresh
```

### Example: Complete Workflow

Processing PXD017620 (BS3 crosslinker with Tris quencher):
```bash
python src/main.py --pxd PXD017620 --verbose
```

Output structure:
```
pxd_data/PXD017620/
├── pride/project_details.json              # PRIDE metadata
├── pmc/full_text.json                      # Publication full text
├── llm/responses.json                      # LLM-extracted features
│   └── data:
│       ├── comment_cross_linker: "BS3"
│       ├── comment_quenching_reagent: "Tris, 50 mm"
│       └── (20+ other extracted fields)
├── enhanced/metadata.json                  # Combined metadata
└── configs/
    ├── xi_crosslinking.conf               # Generated config for XL search
    └── xi_linear.conf                     # Generated config for linear search
```

### Generated Config Example (PXD017620: BS3 + Tris)

**Input from LLM responses:**
- Crosslinker: BS3
- Quencher: Tris, 50 mm
- Digestion enzymes: Trypsin, Lys-C

**Output: xi_crosslinking.conf**
```properties
####################
##Tolerances
tolerance:precursor:10ppm
tolerance:fragment:20ppm

#################
## Cross Linker + associated modifications
crosslinker:SymetricSingleAminoAcidRestrictedCrossLinker:Name:BS3;MASS:172.0211;LINKEDAMINOACIDS:K(0),nterm(0)

##========================
##--Fixed Modifications
modification:fixed::SYMBOLEXT:cm;MODIFIED:C;DELTAMASS:57.021464

##========================
##--Variable Modifications
modification:variable::SYMBOLEXT:ox;MODIFIED:M;DELTAMASS:15.99491463
modification:variable::SYMBOLEXT:bs3_tris;MODIFIED:K;DELTAMASS:259.142
modification:variable::SYMBOLEXT:bs3_tris;MODIFIED:nterm;DELTAMASS:259.142

###################
## Digest
digestion:PostAAConstrainedDigestion:DIGESTED:K,R;ConstrainingAminoAcids:P;NAME=Trypsin
digestion:PostAAConstrainedDigestion:DIGESTED:K;ConstrainingAminoAcids:P;NAME=Lys-C
...
```
Notice the mono-quench modifications: `bs3_tris` entries for K and nterm with mass 259.142 Da.

### Another Example (PXD042173: DSSO + Tris-HCl)

Processing PXD042173:
```bash
python src/main.py --pxd PXD042173
```

**Input from LLM responses:**
- Crosslinker: DSSO
- Quencher: Tris-HCl, 20 mM (pH 8.0)
- Digestion enzymes: Lys-C, Trypsin

**Output: xi_crosslinking.conf (Variable Modifications section)**
```properties
modification:variable::SYMBOLEXT:ox;MODIFIED:M;DELTAMASS:15.99491463
modification:variable::SYMBOLEXT:dsso_tris;MODIFIED:K;DELTAMASS:279.077658
modification:variable::SYMBOLEXT:dsso_tris;MODIFIED:nterm;DELTAMASS:279.077658
modification:variable::SYMBOLEXT:dsso_tris;MODIFIED:S;DELTAMASS:279.077658
modification:variable::SYMBOLEXT:dsso_tris;MODIFIED:T;DELTAMASS:279.077658
modification:variable::SYMBOLEXT:dsso_tris;MODIFIED:Y;DELTAMASS:279.077658
```
Notice: DSSO (MS-cleavable) has different amino acid targets (K, nterm, S, T, Y) compared to BS3 (K, nterm only), and different mono-link mass (279.078 vs 259.142 Da).

### Programmatic Usage (Python API)

```python
from pxd_enhancer import PXDMetadataEnhancer

# Initialize the enhancer
enhancer = PXDMetadataEnhancer(
    base_dir="./pxd_data",
    prompts_dir="./prompts"
)

# Process a single PXD
result = enhancer.process_pxd("PXD042173")

# The result contains:
# - pride_data: Metadata from PRIDE
# - publication_metadata: Publication info
# - llm_responses: Extracted structured metadata
# - xi_config_paths: Paths to generated Xi config files
# - stages: Dict of per-stage statuses
```

Access generated configs:
```python
print("Xi crosslinking config generated at:", result["xi_config_paths"]["crosslinking"])
print("Xi linear config generated at:", result["xi_config_paths"]["linear"])
print("Xi stage status:", result["stages"]["xi_configs"])
```

### Using the Legacy Example Script

```bash
python src/ExtractMetadata.py
```

This script processes `PXD042173` and generates:
- Enhanced metadata JSON at `pxd_data/PXD042173/enhanced/metadata.json`
- Xi configuration files at `pxd_data/PXD042173/configs/`:
  - `xi_crosslinking.conf` - Configuration for crosslinked peptide analysis
  - `xi_linear.conf` - Configuration for linear peptide analysis (no crosslinkers)

## Architecture

The current pipeline is implemented in `src/pxd_enhancer/extractor.py` as a 9-stage workflow with an intermediate Stage 2.5:

| Stage | Name | What it does | Main outputs |
|------:|------|---------------|--------------|
| 1 | PRIDE fetch | Fetch PRIDE project metadata and file links | `pride/project_details.json` |
| 2 | Publication fetch | Resolve PMID/PMCID (with DOI fallback) and retrieve publication text | `pmc/full_text.json` |
| 2.5 | File clustering | Cluster `.raw` files by biological condition using LLM | `llm/file_assignments.json`, `llm/file_assignment_map.json` |
| 3 | Raw file processing | Download raw files, run thermorawfileparser, optionally convert to mzML | `assessment/*-metadata.json`, `work/*.mzML` |
| 4 | Spectral merge | Merge thermorawfileparser + mzML_assessor + PRIDE/publication fallbacks | `assessment/spectral_summary.json` |
| 5 | LLM extraction | Run grouped prompts to extract structured metadata terms | `llm/responses.json` |
| 6 | SDRF generation | Build SDRF TSV (one row per raw file) | `sdrf/{PXD}.sdrf.tsv` |
| 7 | SDRF validation | Validate SDRF with `parse_sdrf` crosslinking template | Validation status + warnings in result metadata |
| 8 | Xi config generation | Generate Xi configs for crosslinking and linear searches | `configs/{PXD}_crosslinking.conf`, `configs/{PXD}_linear.conf` |
| 9 | Final compilation/save | Compile all stage data into final record | `enhanced/metadata.json` |

Flow summary:

```
Stage 1 -> Stage 2 -> Stage 2.5 -> Stage 3 -> Stage 4 -> Stage 5 -> Stage 6 -> Stage 7 -> Stage 8 -> Stage 9
```

Skip controls used during execution:
- `--no-download` skips Stage 3 (and effectively bypasses fresh Stage 4 generation)
- `--skip-sdrf` skips Stage 6
- `--skip-xi` skips Stage 8
- `--sdrf-only` runs SDRF generation/validation from cached data

For detailed architecture information, see [documents/ARCHITECTURE.md](documents/ARCHITECTURE.md).

## Supported Crosslinkers & Quenchers

### Crosslinkers (14+ entries in crosslinker_definitions.json)

**Implemented:**
- Symmetric: DSSO, BS³, DSS, EDC, MBS, DMA, Formaldehyde, Glutaraldehyde
- Photo-crosslinkers: Photo-DMAB, AzP, AzPC
- Linear: For peptide sequence analysis without crosslinks

Each crosslinker definition includes:
- Full name and short name
- Xi format class
- Monoisotopic mass
- Linked amino acids
- Cleavage stubs (if applicable)
- Aliases for flexible name matching

### Quenchers (3 types in quencher_definitions.json)

| Quencher | Crosslinkers | Mono-Link Masses |
|----------|--------------|------------------|
| **Tris** | DSSO, BS³, DSS, DSBU | DSSO: 279.08, BS³: 259.14, DSS: 241.12, DSBU: 292.12 |
| **Ammonium bicarbonate (ABC)** | DSSO, BS³, DSS, DSBU | DSSO: 263.06, BS³: 243.13, DSS: 225.11, DSBU: 276.11 |
| **Glycine** | Formaldehyde | FA: 75.03 |

**Adding New Quencher-Crosslinker Combinations:**
Edit `assets/quencher_definitions.json` and add entries:
```json
{
  "name": "Ammonium acetate",
  "aliases": ["ammonium acetate", "NH4OAc"],
  "crosslinker_modifications": {
    "DSSO": {
      "symbol": "dsso_aac",
      "mass": 278.123,
      "amino_acids": {...}
    }
  }
}
```

## Output Format

### Enhanced Metadata (JSON)
Located at `pxd_data/{PXD_ACCESSION}/enhanced/metadata.json`

Contains:
- PRIDE project metadata
- Publication information
- LLM-extracted structured data:
  - Crosslinker specifications (name, targets, cleavability)
  - Digestion enzyme parameters with names and conditions
  - Sample modifications
  - Instrument configurations
- Processing stage status and timestamps

### Xi Configuration Files
Located at `pxd_data/{PXD_ACCESSION}/configs/`

Two configuration files per PXD project:
- **xi_crosslinking.conf**: Optimized for crosslinked peptide detection
  - Includes crosslinker-specific modifications
  - **Quencher-aware mono-link modifications** (if quencher detected)
  - Sets `TOPMATCHESONLY:true` for efficiency
  - Example DSSO+Tris entries:
    - `modification:variable::SYMBOLEXT:dsso_tris;MODIFIED:K;DELTAMASS:279.077658`
    - `modification:variable::SYMBOLEXT:dsso_tris;MODIFIED:S;DELTAMASS:279.077658`
  
- **xi_linear.conf**: For linear peptide detection
  - Only includes oxidation modifications (no crosslinkers or mono-links)
  - Sets `TOPMATCHESONLY:false`
  - Uses LinearCrosslinker definition

Both configs include:
- Precursor tolerance: 10 ppm
- Fragment tolerance: 20 ppm
- Missed cleavages: 3
- Minimum peptide length: 6
- Automatically detected digestion enzymes (Trypsin, Lys-C, Pepsin, etc.)
- Safe fallback: If quencher is unknown, configs still generate with defaults and warning logged

## Tasks Progress (Updated March 30, 2026)

✅ **Completed:**
1. Access to GitHub repo with selected crosslinking projects
2. PRIDE metadata extraction pipeline (Stage 1)
3. Publication metadata extraction from PMC/PubMed (Stage 2)
4. LLM-based metadata extraction with validation (Stage 5)
5. Xi configuration file generation (Stage 8) - **Fully Complete**
6. Mono-quench modification support with quencher lookup table - **Complete**
7. Integration of configs and quencher data into main pipeline - **Complete**
8. Crosslinker definitions registry with 14+ entries - **Complete**
9. Quencher definitions registry with 3+ types and 15+ combinations - **Complete**
10. Testing and validation with PXD017620 (BS3+Tris) and PXD042173 (DSSO+Tris-HCl) - **Complete**
11. Comprehensive error handling and defensive type checking - **Complete**
12. CLI interface with main.py supporting single/batch processing - **Complete**
13. Repository infrastructure improvements (.gitignore, documentation) - **Complete**

🔄 **In Progress:**
1. Batch processing of multiple PXDs from `crosslinking_datasets_list.tsv`
2. Configuration validation with actual Xi search runs
3. Handling edge cases (missing metadata, alternative enzyme names)
4. Performance optimization for large-scale runs

📋 **Planned:**
1. Scale to 100+ PXD projects
2. Configuration optimization based on actual search results
3. Integration with EBI Complex Portal
4. Publication of standardized PPI dataset
5. AlphaFold3 validation of cross-linked residue pairs

## Recent Updates

### Phase 3B: Mono-Quench Modification Support (✅ Completed March 16, 2026)
- Implemented quencher detection from LLM responses (`comment_quenching_reagent`)
- Created quencher definitions registry: `assets/quencher_definitions.json`
- Added quencher-specific mono-link mass lookup tables
- Supports 3 quencher types: Tris, Ammonium bicarbonate, Glycine
- Supports 15+ crosslinker-quencher combinations with distinct mass values
- Updated `_get_variable_modifications_for_crosslinker()` to accept quencher parameter
- Intelligent quencher name parsing (handles lists, nested structures, special characters)
- Safe fallback: Missing quenchers generate configs without monolink mods + warning
- Tested with PXD017620 (BS3+Tris) and PXD042173 (DSSO+Tris-HCl)

**Example output:**
- BS3+Tris: `modification:variable::SYMBOLEXT:bs3_tris;MODIFIED:K;DELTAMASS:259.142`
- DSSO+Tris: `modification:variable::SYMBOLEXT:dsso_tris;MODIFIED:K;DELTAMASS:279.077658`

### Phase 3A: Xi Configuration Generation (✅ Completed March 2, 2026)
- Implemented automatic generation of Xi config files from metadata
- Created crosslinker definitions registry with 14+ entries
- Integrated config generation as Stage 8 of the pipeline
- Fixed data structure handling for LLM responses
- Comprehensive digestion enzyme parsing (handles list of dicts, strings, mixed types)
- Defensive type checking throughout for robustness

**Implementation Details:**
- Automated crosslinker name resolution with alias support
- Variable modification mapping based on crosslinker type
- Digestion enzyme detection from `comment_cleavage_agent_details`
- Proper handling of DSSO-specific modifications
- Automatic fallback to default parameters (Trypsin + Lys-C) when data is incomplete
- Safe data unwrapping from LLM response cache structures

## File Structure

```
XLMS-PPI-working-group/
├── README.md                               (This file)
├── requirements.txt                        (Python dependencies)
├── config.yaml.sample                      (Example configuration)
├── assets/
│   ├── crosslinker_definitions.json        (Crosslinker registry with 14+ entries)
│   ├── quencher_definitions.json           (Quencher registry with mono-link masses)
│   ├── crosslinking_datasets_list.tsv      (List of PRIDE projects)
│   └── example_xi_configs/                 (Example Xi config files)
├── documents/
│   ├── ARCHITECTURE.md                     (System design)
│   ├── BUILD_SUMMARY.md                    (Development notes)
│   └── README.md                           (Original project notes)
├── prompts/                                (LLM prompt templates)
│   ├── comment_cross_linker.txt
│   ├── comment_cleavage_agent_details.txt
│   ├── comment_quenching_reagent.txt
│   └── (18+ other LLM prompts)
├── pxd_data/                               (Data directory)
│   └── PXD*/
│       ├── pride/                          (PRIDE metadata)
│       ├── pmc/                            (Publication metadata)
│       ├── llm/                            (LLM responses)
│       ├── enhanced/                       (Compiled metadata)
│       └── configs/                        (Generated Xi configs)
├── src/
│   ├── main.py                             (CLI entry point)
│   ├── ExtractMetadata.py                  (Example usage script)
│   └── pxd_enhancer/
│       ├── __init__.py
│       ├── config.py                       (Configuration management)
│       ├── extractor.py                    (Main orchestrator)
│       ├── xi_config_generator.py          (Config generation with quencher support)
│       ├── prompt_templates.py             (LLM prompts)
│       ├── llm_client.py                   (OpenAI API wrapper)
│       ├── pride_client.py                 (PRIDE API client)
│       ├── pmc_client.py                   (PMC/PubMed API client)
│       ├── ncbi_client.py                  (NCBI E-utilities client)
│       └── data_store.py                   (File I/O)
└── logs/                                   (Processing logs)
```

## Technical Details

### Dependencies
- Python 3.8+
- OpenAI API (for GPT-4o-mini)
- PRIDE API
- PubMed/PMC APIs
- Standard libraries: requests, json, pathlib

See [requirements.txt](requirements.txt) for complete dependency list.

### Data Sources
- **PRIDE**: https://www.ebi.ac.uk/pride/
- **PubMed Central**: https://www.ncbi.nlm.nih.gov/pmc/
- **NCBI E-utilities**: For PMID/PMCID lookups

### API Keys Required
- **OpenAI API Key**: For GPT-4o-mini access
- **NCBI API Key**: Optional but recommended for reliable PMID lookups

## Configuration

Edit `config.yaml.sample` and rename to `config.yaml` to customize:
```yaml
base_dir: ./pxd_data
prompts_dir: ./prompts
email: your.email@example.com
ncbi_api_key: your_api_key_here
openai_api_key: your_openai_key_here
```

## Troubleshooting

### No configs generated
- Check that LLM responses include `comment_cross_linker` and `comment_cleavage_agent_details`
- Verify Xi config generator has crosslinker definitions loaded
- Check logs for parsing errors in LLM response structure

### Missing quencher in mono-quench modifications
- Check the LLM response for `comment_quenching_reagent` value
- Quencher names are case-insensitive but must match aliases in `assets/quencher_definitions.json`
- Common names: "tris", "tris-hcl", "ammonium bicarbonate", "abc", "glycine"
- If quencher is unknown, configs still generate with default oxidation only + warning logged
- To add support: Update `quencher_definitions.json` with crosslinker-specific masses

### Missing crosslinker
- Add definition to [assets/crosslinker_definitions.json](assets/crosslinker_definitions.json)
- Update [prompts/comment_cross_linker.txt](prompts/comment_cross_linker.txt) with new crosslinker alias
- If crosslinker has cleavable stubs (like DSSO), add to "stubs" field
- Add to quencher_definitions.json if it pairs with common quenchers

### Incorrect digestion enzymes in config
- Check `comment_cleavage_agent_details` in LLM responses for enzyme names
- Supported enzyme mappings: Trypsin, Lys-C, Pepsin, Chymotrypsin, Glu-C, Asp-N
- If custom enzyme used, add mapping to `_parse_digestion_from_llm()` method in `xi_config_generator.py`
- Default fallback: Trypsin + Lys-C when parsing fails

### Enzyme not detected
- Add enzyme name to `_parse_digestion_from_llm()` method
- Ensure LLM response includes enzyme name in expected field
- Check enzyme name capitalization in response parsing

## Contributing

To add support for new crosslinkers:
1. Update `assets/crosslinker_definitions.json` with mass and amino acid targets
2. Add aliases to prompt templates for LLM recognition
3. Add variable modifications if needed in generator code
4. Test with a sample PXD project

## References

[1]: Graziadei, A. & Rappsilber, J. Leveraging crosslinking mass spectrometry in structural and cell biology. *Structure* **30**, 37–54 (2022).

[2]: Sinz, A. Cross-Linking/Mass Spectrometry for Studying Protein Structures and Protein–Protein Interactions: Where Are We Now and Where Should We Go from Here? *Angew. Chem. Int. Ed.* **57**, 6390–6396 (2018).

[3]: Leitner, A., Faini, M., Stengel, F. & Aebersold, R. Crosslinking and Mass Spectrometry: An Integrated Technology to Understand the Structure and Function of Molecular Machines. *Trends Biochem. Sci.* **41**, 20–32 (2016).

[4]: Eagen, K. P. Principles of Chromosome Architecture Revealed by Hi-C. *Trends Biochem. Sci.* **43**, 469–478 (2018).

[5]: Matzinger, M. & Mechtler, K. Cleavable Cross-Linkers and Mass Spectrometry for the Ultimate Task of Profiling Protein–Protein Interaction Networks in Vivo. *J. Proteome Res.* **20**, 78–93 (2021).

---

**Last Updated:** March 2, 2026  
**Version:** 1.1 (Xi Config Generation v1 Complete)
