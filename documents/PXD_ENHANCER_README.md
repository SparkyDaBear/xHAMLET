# PXD Metadata Enhancer

A pythonic tool for enriching PRIDE (proteomics) project metadata with LLM-extracted information.

## Overview

This tool:
1. Fetches PRIDE project metadata (via PRIDE REST API)
2. Extracts publication information (DOI, PubMed IDs)
3. Fetches publication full text from PubMed Central (PMC)
4. Queries OpenAI LLM with customizable prompts to extract structured metadata
5. Caches all API responses for efficient reprocessing
6. Stores results in organized JSON format

## Architecture

### Module Structure

```
pxd_enhancer/
├── __init__.py              # Package initialization
├── pride_client.py          # PRIDE API interactions
├── pmc_client.py            # PMC API interactions
├── data_store.py            # Local file storage/retrieval
├── llm_client.py            # OpenAI LLM interactions
├── prompt_templates.py      # LLM prompt management
├── config.py                # Configuration management
└── extractor.py             # Main orchestrator class
```

### Class Overview

**PrideClient**: Fetches project metadata and file lists from PRIDE API
- `fetch_project_details(pxd)` - Get project metadata
- `fetch_project_files(pxd)` - Get file listing
- `extract_publication_info(project_details)` - Extract DOI and PubMed IDs

**PMCClient**: Fetches publication data from PubMed Central
- `pmid_to_pmcid(pmid)` - Convert PubMed ID to PMCID
- `fetch_full_text(pmcid)` - Get full text in BioC JSON format
- `extract_text_sections(bioc_json)` - Parse text sections (abstract, methods, etc.)
- `fetch_supplementary_files(pmcid)` - Get supplementary materials

**DataStore**: Manages local caching of all data
- `save_json(data, pxd, category, filename)` - Save with metadata
- `load_json(pxd, category, filename)` - Load from cache
- `file_exists(pxd, category, filename)` - Check if cached
- `compile_pxd_summary(pxd)` - Combine all data for a PXD

**LLMClient**: Interfaces with OpenAI API
- `query(prompt, text)` - Single prompt query
- `batch_query(prompts_dict, text)` - Multiple prompts
- `parse_json_response(response)` - Extract JSON from response
- `cache_response(...)` - Format response for storage

**PromptTemplates**: Manages LLM prompts
- `get_prompt(key)` - Get prompt by name
- `get_prompts(keys)` - Get multiple prompts
- `list_prompts()` - List available prompts
- `create_default_prompts()` - Initialize default prompt files

**PXDMetadataEnhancer**: Main orchestrator
- `process_pxd(pxd, force_refresh, prompt_keys)` - Full workflow
- `get_pxd_metadata(pxd)` - Retrieve processed metadata
- `list_processed_pxds()` - List all processed PXDs

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."
```

## Configuration

### Basic Usage (Default Config)

```bash
# Process a single PXD
python src/main.py --pxd PXD000001

# Process multiple PXDs
python src/main.py --pxd PXD000001 PXD000002 PXD000003

# Use specific prompts
python src/main.py --pxd PXD000001 --prompts organism disease

# Force refresh (ignore cache)
python src/main.py --pxd PXD000001 --force-refresh
```

### Configuration File

Create `config.yaml` (copy from `config.yaml.sample`):

```yaml
pride:
  base_url: "https://www.ebi.ac.uk/pride/ws/archive/v3"
  timeout: 30

pmc:
  email: "your.email@example.com"  # Recommended for PMC
  api_key: null

llm:
  model: "gpt-4-turbo"
  temperature: 0.3

storage:
  base_dir: "./pxd_data"
  cache_pride: true
  cache_pmc: true
  cache_llm: true

prompts:
  dir: "./prompts"
  enabled: [organism, disease, experimental_design, quantification, key_findings]
```

Use with CLI:
```bash
python src/main.py --pxd PXD000001 --config config.yaml
```

### Prompt Management

```bash
# Create default prompts
python src/main.py --create-prompts

# List available prompts
python src/main.py --list-prompts

# Save current config
python src/main.py --save-config myconfig.yaml
```

## Usage Examples

### Example 1: Basic Processing

```python
from pxd_enhancer import PXDMetadataEnhancer

enhancer = PXDMetadataEnhancer(
    base_dir="./pxd_data",
    prompts_dir="./prompts"
)

result = enhancer.process_pxd("PXD000001")
print(result)
```

### Example 2: Custom Prompts

```python
# Use only specific prompts
result = enhancer.process_pxd(
    "PXD000001",
    prompt_keys=["organism", "disease", "experimental_design"]
)
```

### Example 3: Batch Processing with Caching

```python
pxds = ["PXD000001", "PXD000002", "PXD000003"]

for pxd in pxds:
    try:
        result = enhancer.process_pxd(pxd)
        # Data is automatically cached
        print(f"✓ {pxd} processed")
    except Exception as e:
        print(f"✗ {pxd} failed: {e}")

# Later, retrieve cached data
metadata = enhancer.get_pxd_metadata("PXD000001")
```

### Example 4: Custom Configuration

```python
from pxd_enhancer.config import Config

config = Config("config.yaml")
config.config["llm"]["model"] = "gpt-4"
config.save_yaml("custom_config.yaml")

enhancer = PXDMetadataEnhancer(
    base_dir=config.get("storage.base_dir"),
    prompts_dir=config.get("prompts.dir"),
    llm_model=config.get("llm.model")
)
```

## Data Structure

Each PXD's data is organized as:

```
pxd_data/
└── PXD000001/
    ├── pride/
    │   └── project_details.json      # PRIDE API response
    ├── pmc/
    │   ├── full_text.json            # PMC full text (BioC format)
    │   └── sections.json             # Extracted text sections
    ├── llm/
    │   └── responses.json            # LLM query responses
    └── enhanced/
        ├── metadata.json             # Final compiled metadata
        └── summary.json              # Summary of all data
```

### Example Output Structure

```json
{
  "pxd": "PXD000001",
  "processed_at": "2026-03-01T12:34:56.789012",
  "stages": {
    "pride": "success",
    "pmc": "success",
    "llm": "success",
    "compilation": "success"
  },
  "pride_data": { /* PRIDE API response */ },
  "pmc_data": { /* PMC BioC JSON */ },
  "llm_responses": {
    "organism": {
      "response": "...",
      "parsed": { /* JSON if parseable */ },
      "queried_at": "2026-03-01T12:34:56",
      "model": "gpt-4-turbo"
    },
    /* ... other prompts ... */
  }
}
```

## Default Prompts

The tool comes with built-in prompts for:

1. **organism** - Extract organism names, taxonomy IDs, tissue types
2. **disease** - Extract disease/condition information
3. **experimental_design** - Summarize study design and variables
4. **quantification** - Identify quantification methods (LFQ, TMT, etc.)
5. **key_findings** - Extract primary findings and protein counts

Prompt files stored in `./prompts/` directory.

## Error Handling

The tool logs failures and continues processing other PXDs:

```
ERROR: pxd_enhancer.pride_client - Failed to fetch PXD000001: Connection timeout
ERROR: pxd_enhancer.extractor - Failed to process PXD000001: PRIDE data fetch failed
```

Use `--verbose` flag for detailed debugging:

```bash
python src/main.py --pxd PXD000001 --verbose
```

## Logging

Log file: `pxd_enhancer.log`

Configure in `config.yaml`:
```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

## Environment Variables

Required:
- `OPENAI_API_KEY` - Your OpenAI API key

Optional:
- `NCBI_EMAIL` - Email for PMC requests (recommended)
- `NCBI_API_KEY` - NCBI API key for higher rate limits

## Next Steps

Future enhancements:
1. Add support for other LLM providers (Anthropic, local models)
2. Implement parallel processing for batch PXDs
3. Add data validation and schema enforcement
4. Create web interface for browsing results
5. Integrate with downstream analysis pipelines

## Citation

If you use this tool in your research, please cite:
```
PXD Metadata Enhancer (2026)
XLMS-PPI Working Group
```
