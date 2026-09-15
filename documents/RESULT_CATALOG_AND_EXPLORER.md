# xHAMLET Result Catalog and Explorer

The database catalog and the static result explorer both read an xHAMLET
`storage.base_dir`. They retain metadata, provenance, and result summaries;
they never ingest RAW, mzML, or FASTA binary content into PostgreSQL or the
GitHub Pages repository.

## Database Synchronization

`scripts/sync_result_database.py` is the single result-catalog command. By
default, it creates and incrementally synchronizes a local SQLite database at
`xhamlet-results.sqlite3`; `--database-url` selects PostgreSQL instead. Its
`--static-snap` option exports the compact database-backed JSON catalog used by
the website. It discovers PXD directories, stores a complete LLM response
document, records every non-binary output artifact, captures ReLink/mzIdentML
document provenance and key cross-link observations, and replaces a PXD's
catalog entry only as one transaction.

The local SQLite database uses Python's standard library and needs no database
server, credentials, R2 bucket, or additional package. Run this from the
repository root to create or update `xhamlet-results.sqlite3`:

```bash
python scripts/sync_result_database.py --config configs/config.yaml
```

Choose a different local database path when needed, for example to keep a
separate test catalog:

```bash
python scripts/sync_result_database.py \
  --config configs/config.yaml \
  --database-path databases/test-results.sqlite3
```

To use a shared PostgreSQL database instead, install the optional driver and
set a connection URL explicitly:

```bash
python -m pip install -r requirements.txt
python scripts/sync_result_database.py \
  --config configs/config.yaml \
  --database-url 'postgresql://USER:PASSWORD@HOST:5432/xhamlet'
```

Synchronize the selected database and write the GitHub Pages snapshot in one
command:

```bash
python scripts/sync_result_database.py \
  --config configs/config.yaml \
  --static-snap
```

Select PXD accessions or shell-style masks, exclude a mask, or replace a
catalog entry regardless of its source signature:

```bash
python scripts/sync_result_database.py \
  --config configs/config.yaml \
  --pxd PXD042173 'PXD05*' \
  --exclude-pxd PXD053010 \
  --force
```

Use `--dry-run` to inspect selected data without opening a database. Use
`--data-dir /path/to/output` to override `storage.base_dir` temporarily. Local
database files are ignored by Git; commit only the generated static snapshot
when publishing the website. SQLite retains JSON and text artifacts up to 16 MiB
per file by default. Larger files remain at their source path while their
relative path, type, size, modification time, checksum, and an omission marker
are stored. Set `--max-inline-artifact-bytes` to choose another limit; use `0`
to retain only artifact metadata in the local database.

### Captured Output Information

The implementation preserves the core schema information plus the output
surfaces needed to audit a PXD:

- PRIDE project JSON, publication JSON, complete LLM JSON, parsed LLM fields,
  enriched metadata, file assignments, SDRF, Xi configs, and assessment JSON;
- per-artifact relative path, category, size, mtime, and checksum; complete JSON
  content; and complete generated SDRF, TSV, CSV, and Xi config text;
- pipeline stage status, processing time, and the xHAMLET Git revision;
- ReLink run path, taxid directory, FASTA provenance reported by ReLink,
  crosslinker configuration lines, and mzIdentML documents; and
- mzIdentML checksum, XML version/namespace, declared search databases and
  software, spectrum-result count, spectrum-item count, passing-item count,
  parse-completion status, source RAW roster, and file-clustering assignments.

For each passing cross-link observation, the catalog stores the source RAW
filename when resolvable, spectrum and scan identifiers, alpha/beta peptide
sequences, protein accessions and positions, charge, xi score, and cross-link
group identifier. The static snapshot groups those observations by PXD, ReLink
run, and source RAW, leaving large mzIdentML XML files external.

The importer does not yet normalize every PSM, peptide modification, protein
evidence, and CV parameter described as future work in `DATABASE_SCHEMA.md`.
A complete scientific warehouse still needs that Phase 2 expansion for
arbitrary SQL analysis beyond the compact cross-link catalog.

## Static Explorer

The explorer lives in `web/results-explorer/`; it is plain HTML, CSS, and
JavaScript so it can be hosted on GitHub Pages. Its catalog is generated from
the PostgreSQL results database, after the selected PXD records are updated:

```bash
python scripts/sync_result_database.py --config configs/config.yaml --static-snap
```

For a focused local preview using the complete test fixtures:

```bash
python scripts/sync_result_database.py \
  --config configs/config.yaml \
  --data-dir test_data \
  --static-snap web/results-explorer/data/catalog.json
python -m http.server --directory web/results-explorer 8000
```

Open `http://localhost:8000`. The explorer provides PXD filtering, project and
pipeline status, selected LLM metadata, ReLink/mzIdentML counts and chemistry
configuration, plus a per-PXD artifact browser.

Recommended additional publishable artifacts are already included when they
exist: PRIDE project metadata, LLM responses and evidence, enhanced result
metadata, file-assignment maps, spectral summaries, SDRF files and validation
status, Xi configs, ReLink samplesheets, MultiQC reports, and mzIdentML files.
Avoid publishing raw files, mzML, FASTA, Nextflow work directories, keys, or
unredacted log files. Add `--include-work-files` only for a deliberately
restricted, authenticated artifact host.

## GitHub Pages and R2

GitHub Pages can host the static explorer and `data/catalog.json`. The included
`.github/workflows/deploy-results-explorer.yml` deploys
`web/results-explorer/` on pushes to `main`. Run the single synchronizer with
`--static-snap` in the environment that owns the catalog database, then commit
the generated `web/results-explorer/data/catalog.json` with the promoted
snapshot. Enable GitHub Pages with the **GitHub Actions** source in repository
settings. GitHub Actions deliberately does not need database access.

Cloudflare R2 can host the large source and result artifacts. Configure a public
custom domain or a Worker endpoint, then build the catalog with that public
root:

```bash
python scripts/sync_result_database.py \
  --config configs/config.yaml \
  --static-snap \
  --artifact-base-url https://results.example.org
```

The file browser will then link each artifact as
`https://results.example.org/<PXD>/<relative-path>`. R2 must contain the same
directory layout below each PXD. If artifacts are not public, put a Cloudflare
Worker in front of R2 to authenticate the request and return short-lived signed
URLs. Never place R2 access keys in the static catalog or browser JavaScript.

A browser hosted on GitHub Pages should **not** connect directly to PostgreSQL.
PostgreSQL credentials cannot be kept secret in client-side code, and exposing a
database socket publicly is unsafe. To read live database results, expose a
small read-only API through a Cloudflare Worker, validate request parameters,
use Hyperdrive or a private network connection to PostgreSQL, and enable CORS
only for the GitHub Pages origin. The static catalog remains the simplest and
most cacheable public view; a Worker API is appropriate when you need live SQL
filters or result drill-down beyond the exported catalog.