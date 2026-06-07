# PXD Metadata Enhancer - Complete Structure Summary

**Date**: March 1, 2026  
**Status**: ✅ Architecture Complete & Ready for Testing

## What We Built

A production-ready Python tool for enriching PRIDE proteomics project metadata with LLM-extracted information. The tool follows a clean, modular architecture that makes it easy to import components into other scripts.

---

## 📁 Project Structure

```
XLMS-PPI-working-group/
├── src/
│   ├── pxd_enhancer/              # Main package
│   │   ├── __init__.py            # Package exports
│   │   ├── pride_client.py        # PRIDE API client
│   │   ├── pmc_client.py          # PMC/BioC client
│   │   ├── data_store.py          # File storage & caching
│   │   ├── llm_client.py          # OpenAI API client
│   │   ├── prompt_templates.py    # Prompt management
│   │   ├── config.py              # Configuration management
│   │   └── extractor.py           # Main orchestrator
│   ├── main.py                    # CLI entry point
│   └── example.py                 # Reference implementation (original)
├── prompts/                       # LLM prompt templates (created at runtime)
│   ├── organism.txt
│   ├── disease.txt
│   ├── experimental_design.txt
│   ├── quantification.txt
│   └── key_findings.txt
├── pxd_data/                      # Data storage (created at runtime)
│   └── PXD000001/
│       ├── pride/
│       ├── pmc/
│       ├── llm/
│       └── enhanced/
├── requirements.txt               # Python dependencies
├── config.yaml.sample             # Configuration template
├── PXD_ENHANCER_README.md         # Complete documentation
├── ARCHITECTURE.md                # System design & diagrams
├── BUILD_SUMMARY.md               # This file
└── examples.py                    # Example usage patterns
```

---

## 🏗️ Architecture Components

### Core Classes (in `src/pxd_enhancer/`)

#### 1. **PrideClient** (`pride_client.py`)
Handles all PRIDE API interactions with retry logic and exponential backoff.

```python
client = PrideClient(base_url, timeout)
project = client.fetch_project_details(pxd)
files = client.fetch_project_files(pxd)
doi, pubmed_ids = client.extract_publication_info(project)
```

**Features:**
- Automatic retry with exponential backoff
- Rate limit handling (429 responses)
- Pagination for file listings

#### 2. **PMCClient** (`pmc_client.py`)
Fetches publication data from PubMed Central in BioC JSON format.

```python
pmc = PMCClient(email, api_key)
pmcid = pmc.pmid_to_pmcid("12345678")
full_text = pmc.fetch_full_text(pmcid)
sections = pmc.extract_text_sections(full_text)
```

**Features:**
- PMID → PMCID conversion
- BioC JSON full text fetching
- Text section extraction (title, abstract, methods, results, discussion)
- Supplementary file handling

#### 3. **DataStore** (`data_store.py`)
Manages local file-based caching with organized directory structure.

```python
store = DataStore(base_dir="./pxd_data")
store.save_json(data, pxd="PXD000001", category="pride", filename="project_details")
retrieved = store.load_json(pxd, category, filename)
summary = store.compile_pxd_summary(pxd)
```

**Features:**
- Organized directory structure per PXD
- JSON with metadata (timestamps, filenames)
- File existence checking
- Summary compilation

#### 4. **LLMClient** (`llm_client.py`)
OpenAI API wrapper with response caching and JSON parsing.

```python
llm = LLMClient(api_key, model="gpt-4-turbo")
response = llm.query(prompt, text)
responses = llm.batch_query({"prompt1": "text1", "prompt2": "text2"}, data)
parsed = llm.parse_json_response(response)
```

**Features:**
- OpenAI API integration (uses environment variable)
- Configurable model and temperature
- Automatic JSON extraction from responses
- Response caching with metadata

#### 5. **PromptTemplates** (`prompt_templates.py`)
Manages LLM prompt templates with built-in defaults and file loading.

```python
prompts = PromptTemplates(prompts_dir="./prompts")
org_prompt = prompts.get_prompt("organism")
multiple = prompts.get_prompts(["organism", "disease"])
prompts.reload_prompts()
PromptTemplates.create_default_prompts()
```

**Built-in Prompts:**
- `organism` - Extract organism names, taxonomy IDs, tissue types
- `disease` - Extract disease/condition information
- `experimental_design` - Summarize study design
- `quantification` - Identify quantification methods
- `key_findings` - Extract primary findings

#### 6. **Config** (`config.py`)
YAML-based configuration management with CLI overrides.

```python
config = Config("config.yaml")
llm_model = config.get("llm.model")
config.config["llm"]["temperature"] = 0.1
config.save_yaml("new_config.yaml")
```

#### 7. **PXDMetadataEnhancer** (`extractor.py`) - Main Orchestrator
Coordinates all components in a 5-stage workflow.

```python
enhancer = PXDMetadataEnhancer(
    base_dir="./pxd_data",
    prompts_dir="./prompts",
    llm_model="gpt-4-turbo"
)

result = enhancer.process_pxd("PXD000001", force_refresh=False)
metadata = enhancer.get_pxd_metadata("PXD000001")
pxds = enhancer.list_processed_pxds()
```

**5-Stage Workflow:**
1. Fetch PRIDE project metadata
2. Fetch PMC publication data
3. Query LLM with multiple prompts
4. Compile and save results
5. Return enhanced metadata

---

## 🎯 Usage Patterns

### Pattern 1: CLI Usage (Easiest)

```bash
# Create default prompts
python src/main.py --create-prompts

# Process single PXD
python src/main.py --pxd PXD000001

# Process multiple PXDs with specific prompts
python src/main.py --pxd PXD000001 PXD000002 --prompts organism disease

# Force refresh (ignore cache)
python src/main.py --pxd PXD000001 --force-refresh

# Use custom config
python src/main.py --pxd PXD000001 --config my_config.yaml
```

### Pattern 2: Direct Python Usage (Most Flexible)

```python
from pxd_enhancer import PXDMetadataEnhancer

enhancer = PXDMetadataEnhancer()
result = enhancer.process_pxd("PXD000001")
```

### Pattern 3: Component Reuse (For Integration)

```python
from pxd_enhancer.pride_client import PrideClient
from pxd_enhancer.pmc_client import PMCClient
from pxd_enhancer.data_store import DataStore

# Use individual components in your own workflow
pride = PrideClient()
pmc = PMCClient()
store = DataStore()

# Custom processing logic
project = pride.fetch_project_details("PXD000001")
# ... do custom things ...
store.save_json(project, "PXD000001", "pride", "custom_analysis")
```

---

## 📋 Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `openai>=1.0.0` - OpenAI API client
- `requests>=2.28.0` - HTTP requests
- `pyyaml>=6.0` - Configuration parsing
- `pandas>=1.5.0` - Data manipulation
- `pathlib2>=2.3.0` - Path handling

### 2. Set Environment Variable

```bash
export OPENAI_API_KEY="sk-..."
```

### 3. Create Prompts (First Time)

```bash
python src/main.py --create-prompts
```

This creates `./prompts/` directory with default prompts.

### 4. Optional: Configure

Copy and modify `config.yaml.sample`:

```bash
cp config.yaml.sample config.yaml
# Edit config.yaml as needed
```

---

## 📊 Data Flow

```
PXD Input
    ↓
[1] PRIDE API → Cache (pride/project_details.json)
    ↓
    Extract: DOI, PubMed IDs
    ↓
[2] PMC API → Cache (pmc/full_text.json, pmc/sections.json)
    ↓
    Extract text sections
    ↓
[3] LLM Queries → Cache (llm/responses.json)
    ↓
    Query with: organism, disease, experimental_design, quantification, key_findings
    ↓
[4] Compile & Save → enhanced/metadata.json
    ↓
Output: Complete Enhanced Metadata
```

---

## 🧪 Testing & Examples

See `examples.py` for 5 runnable examples:

1. **Basic usage** - Process single PXD
2. **Custom prompts** - Use specific prompts only
3. **Batch processing** - Process multiple PXDs
4. **Retrieve cached data** - Load saved results
5. **Prompt management** - Create and list prompts

Run examples:
```bash
python examples.py
```

---

## 🔒 Error Handling

The tool is designed to **log and fail gracefully**:

- **Network errors**: Retry with exponential backoff (max 5 attempts)
- **API failures**: Log error, continue to next PXD
- **Missing data**: Skip that stage, continue processing (e.g., no PubMed ID → skip PMC)
- **LLM errors**: Log and save partial result

All errors logged to `pxd_enhancer.log` and stdout.

---

## 💾 Output Format

Final metadata JSON per PXD:

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
  "pride_data": { /* Full PRIDE API response */ },
  "pmc_data": { /* Full PMC BioC JSON */ },
  "llm_responses": {
    "organism": {
      "response": "Raw text from LLM",
      "parsed": { /* Extracted JSON if possible */ },
      "queried_at": "2026-03-01T12:34:56",
      "model": "gpt-4-turbo"
    },
    /* ... other prompts ... */
  }
}
```

Stored in: `pxd_data/PXD000001/enhanced/metadata.json`

---

## 🚀 Next Steps

### Immediate (Ready to Test)

1. **Install and test locally**
   ```bash
   pip install -r requirements.txt
   python src/main.py --create-prompts
   python examples.py
   ```

2. **Test with real PXD**
   ```bash
   python src/main.py --pxd PXD023343 --verbose
   ```

3. **Check output**
   ```bash
   cat pxd_data/PXD023343/enhanced/metadata.json | jq '.'
   ```

### Short-term (After Testing)

1. **Batch processing pipeline**
   - Process multiple PXDs with parallel workers
   - Add progress tracking
   - Generate summary reports

2. **Data validation**
   - Schema validation for outputs
   - Quality checks on LLM responses
   - Confidence scoring

3. **Web interface**
   - Simple Flask app to browse results
   - Search PXDs
   - View extracted metadata

### Medium-term (Integration)

1. **Multi-LLM support**
   - Anthropic Claude
   - Local models (Ollama)
   - Cost optimization

2. **Advanced analysis**
   - Cross-PXD metadata comparison
   - Organism-specific enrichment
   - Disease/condition clustering

3. **Dataset export**
   - CSV dumps of key findings
   - Integration with downstream analysis
   - Metadata standardization

---

## 📝 Key Design Decisions

1. **Class-based architecture**: Easy to import and reuse components
2. **Modular design**: Each responsibility in separate file
3. **Caching by default**: Avoid re-fetching, respect API rate limits
4. **Graceful degradation**: Continue even if some stages fail
5. **Configuration-driven**: Easy to customize behavior
6. **Comprehensive logging**: Understand what happened
7. **Single JSON output**: All data in one place per PXD
8. **Built-in prompts**: Works out-of-the-box, easy to customize

---

## 🔗 File Dependencies

```
main.py (CLI)
  └── Config
  └── PromptTemplates
  └── PXDMetadataEnhancer
      ├── PrideClient
      ├── PMCClient
      ├── DataStore
      ├── LLMClient
      └── PromptTemplates

Each component is independently importable and usable.
```

---

## ✅ Checklist for Getting Started

- [ ] Install Python 3.8+
- [ ] Run `pip install -r requirements.txt`
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Run `python src/main.py --create-prompts`
- [ ] Test with `python examples.py`
- [ ] Test with real PXD: `python src/main.py --pxd PXD000001`
- [ ] Check output in `pxd_data/PXD000001/enhanced/metadata.json`
- [ ] Read `PXD_ENHANCER_README.md` for full documentation
- [ ] Review `ARCHITECTURE.md` for system design
- [ ] Modify prompts in `prompts/` directory as needed

---

## 📚 Documentation Files

- **PXD_ENHANCER_README.md** - Complete user guide
- **ARCHITECTURE.md** - System design & diagrams
- **BUILD_SUMMARY.md** - This file (what we built)
- **examples.py** - Working code examples
- **config.yaml.sample** - Configuration template

---

## 🎓 How to Extend

### Add a Custom Prompt

1. Create `prompts/my_analysis.txt`
2. Write your prompt
3. Use it: `python src/main.py --pxd PXD000001 --prompts my_analysis`

### Add a New Data Source

1. Create `my_source_client.py` (see `pride_client.py` as example)
2. Add to PXDMetadataEnhancer
3. Update workflow in `process_pxd()`

### Support Different LLM

1. Subclass LLMClient
2. Implement `query()` method
3. Update Config for new model options

---

**Built with ❤️ by the XLMS-PPI Working Group**  
**Status**: ✅ Complete & Ready for Testing  
**Last Updated**: March 1, 2026
