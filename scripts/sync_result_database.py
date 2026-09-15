#!/usr/bin/env python3
"""Create and incrementally synchronize the xHAMLET result catalog.

The command discovers PXD directories from ``storage.base_dir`` in the supplied
configuration. Source files stay on disk or object storage; the default local
SQLite database stores their checksums, locations, metadata, and queryable
result summaries. PostgreSQL remains available with ``--database-url``.

Examples:
    python scripts/sync_result_database.py --config configs/config.yaml
    python scripts/sync_result_database.py --database-path xhamlet-results.sqlite3
    export XHAMLET_DATABASE_URL='postgresql://user:password@localhost/xhamlet'
    python scripts/sync_result_database.py --database-url "$XHAMLET_DATABASE_URL" --static-snap
    python scripts/sync_result_database.py --pxd PXD042173 'PXD05*' --force
    python scripts/sync_result_database.py --exclude-pxd 'PXD00*' --dry-run
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

import yaml


PXD_PATTERN = re.compile(r"^PXD\d+$", re.IGNORECASE)
SCHEMA_VERSION = 1
EXCLUDED_ARTIFACT_SUFFIXES = {".raw", ".mzml", ".fasta", ".fas", ".fa"}
TEXT_ARTIFACT_SUFFIXES = {".conf", ".csv", ".sdrf", ".tsv"}
DEFAULT_STATIC_SNAPSHOT = Path("web/results-explorer/data/catalog.json")
DEFAULT_LOCAL_DATABASE = Path("xhamlet-results.sqlite3")
DEFAULT_LOCAL_INLINE_ARTIFACT_LIMIT = 16 * 1024 * 1024
STATIC_METADATA_FIELDS = (
    "characteristics[organism]",
    "comment[cross-linker]",
    "comment[quantification method]",
    "comment[instrument]",
    "characteristics[disease]",
)


DDL = """
CREATE TABLE IF NOT EXISTS catalog_schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    accession TEXT NOT NULL UNIQUE CHECK (accession ~ '^PXD[0-9]+$'),
    title TEXT,
    xhamlet_commit TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pipeline_run (
    pipeline_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES project(project_id) ON DELETE CASCADE,
    source_signature CHAR(64) NOT NULL,
    source_root TEXT NOT NULL,
    processed_at TIMESTAMPTZ,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    accepted BOOLEAN NOT NULL DEFAULT FALSE,
    stage_status JSONB NOT NULL DEFAULT '{}'::jsonb,
    enhanced_metadata JSONB,
    UNIQUE (project_id, source_signature)
);

CREATE TABLE IF NOT EXISTS llm_output (
    llm_output_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pipeline_run_id BIGINT NOT NULL UNIQUE REFERENCES pipeline_run(pipeline_run_id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ,
    source_json JSONB NOT NULL,
    source_sha256 CHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_response (
    llm_response_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    llm_output_id BIGINT NOT NULL REFERENCES llm_output(llm_output_id) ON DELETE CASCADE,
    field_key TEXT NOT NULL,
    prompt_group TEXT,
    model TEXT,
    raw_response_text TEXT,
    parsed_json JSONB,
    value_json JSONB,
    accession_json JSONB,
    confidence TEXT,
    evidence_quote TEXT,
    evidence_location TEXT,
    UNIQUE (llm_output_id, field_key)
);

CREATE TABLE IF NOT EXISTS output_artifact (
    artifact_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pipeline_run_id BIGINT NOT NULL REFERENCES pipeline_run(pipeline_run_id) ON DELETE CASCADE,
    relative_path TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    byte_size BIGINT NOT NULL,
    modified_at TIMESTAMPTZ NOT NULL,
    sha256 CHAR(64),
    content_json JSONB,
    content_text TEXT,
    UNIQUE (pipeline_run_id, relative_path)
);

ALTER TABLE output_artifact ADD COLUMN IF NOT EXISTS content_text TEXT;

CREATE TABLE IF NOT EXISTS source_file (
    source_file_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pipeline_run_id BIGINT NOT NULL REFERENCES pipeline_run(pipeline_run_id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    assignment_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (pipeline_run_id, filename)
);

CREATE TABLE IF NOT EXISTS search_run (
    search_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pipeline_run_id BIGINT NOT NULL REFERENCES pipeline_run(pipeline_run_id) ON DELETE CASCADE,
    run_path TEXT NOT NULL,
    taxid TEXT,
    crosslinker_config JSONB NOT NULL DEFAULT '[]'::jsonb,
    fasta_path TEXT,
    status TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (pipeline_run_id, run_path)
);

CREATE TABLE IF NOT EXISTS mzid_document (
    mzid_document_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    search_run_id BIGINT NOT NULL REFERENCES search_run(search_run_id) ON DELETE CASCADE,
    relative_path TEXT NOT NULL,
    source_sha256 CHAR(64) NOT NULL,
    xml_id TEXT,
    version TEXT,
    namespace_uri TEXT,
    creation_time TIMESTAMPTZ,
    document_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    spectrum_result_count BIGINT NOT NULL,
    spectrum_item_count BIGINT NOT NULL,
    passing_item_count BIGINT NOT NULL,
    is_complete BOOLEAN NOT NULL,
    UNIQUE (search_run_id, relative_path)
);

CREATE INDEX IF NOT EXISTS pipeline_run_project_idx ON pipeline_run(project_id, imported_at DESC);
CREATE INDEX IF NOT EXISTS artifact_run_type_idx ON output_artifact(pipeline_run_id, artifact_type);
CREATE INDEX IF NOT EXISTS source_file_run_idx ON source_file(pipeline_run_id, filename);
CREATE INDEX IF NOT EXISTS search_run_project_taxid_idx ON search_run(pipeline_run_id, taxid);
CREATE INDEX IF NOT EXISTS mzid_search_run_idx ON mzid_document(search_run_id);

CREATE TABLE IF NOT EXISTS crosslink_match (
    crosslink_match_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mzid_document_id BIGINT NOT NULL REFERENCES mzid_document(mzid_document_id) ON DELETE CASCADE,
    source_file TEXT,
    spectrum_native_id TEXT NOT NULL,
    scan_number BIGINT,
    crosslink_group_key TEXT NOT NULL,
    alpha_sequence TEXT,
    beta_sequence TEXT,
    alpha_proteins JSONB NOT NULL DEFAULT '[]'::jsonb,
    beta_proteins JSONB NOT NULL DEFAULT '[]'::jsonb,
    alpha_positions JSONB NOT NULL DEFAULT '[]'::jsonb,
    beta_positions JSONB NOT NULL DEFAULT '[]'::jsonb,
    charge_state INTEGER,
    xi_score DOUBLE PRECISION,
    pass_threshold BOOLEAN NOT NULL,
    UNIQUE (mzid_document_id, spectrum_native_id, crosslink_group_key)
);

CREATE INDEX IF NOT EXISTS crosslink_match_document_source_idx ON crosslink_match(mzid_document_id, source_file);
CREATE INDEX IF NOT EXISTS crosslink_match_passing_idx ON crosslink_match(mzid_document_id, pass_threshold);
"""


SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS catalog_schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    accession TEXT NOT NULL UNIQUE,
    title TEXT,
    xhamlet_commit TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_run (
    pipeline_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES project(project_id) ON DELETE CASCADE,
    source_signature TEXT NOT NULL,
    source_root TEXT NOT NULL,
    processed_at TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accepted INTEGER NOT NULL DEFAULT 0,
    stage_status TEXT NOT NULL DEFAULT '{}',
    enhanced_metadata TEXT,
    UNIQUE (project_id, source_signature)
);

CREATE TABLE IF NOT EXISTS llm_output (
    llm_output_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL UNIQUE REFERENCES pipeline_run(pipeline_run_id) ON DELETE CASCADE,
    saved_at TEXT,
    source_json TEXT NOT NULL,
    source_sha256 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_response (
    llm_response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    llm_output_id INTEGER NOT NULL REFERENCES llm_output(llm_output_id) ON DELETE CASCADE,
    field_key TEXT NOT NULL,
    prompt_group TEXT,
    model TEXT,
    raw_response_text TEXT,
    parsed_json TEXT,
    value_json TEXT,
    accession_json TEXT,
    confidence TEXT,
    evidence_quote TEXT,
    evidence_location TEXT,
    UNIQUE (llm_output_id, field_key)
);

CREATE TABLE IF NOT EXISTS output_artifact (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_run(pipeline_run_id) ON DELETE CASCADE,
    relative_path TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    modified_at TEXT NOT NULL,
    sha256 TEXT,
    content_json TEXT,
    content_text TEXT,
    UNIQUE (pipeline_run_id, relative_path)
);

CREATE TABLE IF NOT EXISTS source_file (
    source_file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_run(pipeline_run_id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    assignment_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (pipeline_run_id, filename)
);

CREATE TABLE IF NOT EXISTS search_run (
    search_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_run(pipeline_run_id) ON DELETE CASCADE,
    run_path TEXT NOT NULL,
    taxid TEXT,
    crosslinker_config TEXT NOT NULL DEFAULT '[]',
    fasta_path TEXT,
    status TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (pipeline_run_id, run_path)
);

CREATE TABLE IF NOT EXISTS mzid_document (
    mzid_document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_run_id INTEGER NOT NULL REFERENCES search_run(search_run_id) ON DELETE CASCADE,
    relative_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    xml_id TEXT,
    version TEXT,
    namespace_uri TEXT,
    creation_time TEXT,
    document_metadata TEXT NOT NULL DEFAULT '{}',
    spectrum_result_count INTEGER NOT NULL,
    spectrum_item_count INTEGER NOT NULL,
    passing_item_count INTEGER NOT NULL,
    is_complete INTEGER NOT NULL,
    UNIQUE (search_run_id, relative_path)
);

CREATE TABLE IF NOT EXISTS crosslink_match (
    crosslink_match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mzid_document_id INTEGER NOT NULL REFERENCES mzid_document(mzid_document_id) ON DELETE CASCADE,
    source_file TEXT,
    spectrum_native_id TEXT NOT NULL,
    scan_number INTEGER,
    crosslink_group_key TEXT NOT NULL,
    alpha_sequence TEXT,
    beta_sequence TEXT,
    alpha_proteins TEXT NOT NULL DEFAULT '[]',
    beta_proteins TEXT NOT NULL DEFAULT '[]',
    alpha_positions TEXT NOT NULL DEFAULT '[]',
    beta_positions TEXT NOT NULL DEFAULT '[]',
    charge_state INTEGER,
    xi_score REAL,
    pass_threshold INTEGER NOT NULL,
    UNIQUE (mzid_document_id, spectrum_native_id, crosslink_group_key)
);

CREATE INDEX IF NOT EXISTS pipeline_run_project_idx ON pipeline_run(project_id, imported_at DESC);
CREATE INDEX IF NOT EXISTS artifact_run_type_idx ON output_artifact(pipeline_run_id, artifact_type);
CREATE INDEX IF NOT EXISTS source_file_run_idx ON source_file(pipeline_run_id, filename);
CREATE INDEX IF NOT EXISTS search_run_project_taxid_idx ON search_run(pipeline_run_id, taxid);
CREATE INDEX IF NOT EXISTS mzid_search_run_idx ON mzid_document(search_run_id);
CREATE INDEX IF NOT EXISTS crosslink_match_document_source_idx ON crosslink_match(mzid_document_id, source_file);
CREATE INDEX IF NOT EXISTS crosslink_match_passing_idx ON crosslink_match(mzid_document_id, pass_threshold);
"""


class SQLiteCursor:
    """Provide the small PostgreSQL cursor surface used by the importer."""

    def __init__(self, cursor: sqlite3.Cursor) -> None:
        self.cursor = cursor

    def __enter__(self) -> SQLiteCursor:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.cursor.close()

    def execute(self, query: str, parameters: tuple[Any, ...] | list[Any] = ()) -> SQLiteCursor:
        sqlite_query = query.replace("%s", "?").replace("::jsonb", "").replace("now()", "CURRENT_TIMESTAMP")
        sqlite_parameters = tuple(
            value.isoformat() if isinstance(value, datetime) else value for value in parameters
        )
        self.cursor.execute(sqlite_query, sqlite_parameters)
        return self

    def fetchone(self) -> Any:
        return self.cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return self.cursor.fetchall()


class SQLiteConnection:
    """Transaction-compatible adapter for a local SQLite catalog file."""

    is_sqlite = True

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA foreign_keys = ON")

    def __enter__(self) -> SQLiteConnection:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.connection.close()

    def cursor(self) -> SQLiteCursor:
        return SQLiteCursor(self.connection.cursor())

    def commit(self) -> None:
        self.connection.commit()

    def execute_script(self, script: str) -> None:
        self.connection.executescript(script)

    @contextmanager
    def transaction(self) -> Iterable[None]:
        try:
            yield
        except BaseException:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/config.yaml", help="xHAMLET YAML configuration")
    parser.add_argument("--data-dir", help="Override storage.base_dir from the configuration")
    database_group = parser.add_mutually_exclusive_group()
    database_group.add_argument(
        "--database-url",
        help="PostgreSQL connection URL (default: XHAMLET_DATABASE_URL when set)",
    )
    database_group.add_argument(
        "--database-path",
        type=Path,
        help="Local SQLite catalog path (default: xhamlet-results.sqlite3 when no PostgreSQL URL is set)",
    )
    parser.add_argument(
        "--pxd",
        nargs="+",
        metavar="PXD_OR_MASK",
        help="PXD accessions or shell-style masks to include; default: all PXD directories",
    )
    parser.add_argument(
        "--exclude-pxd",
        nargs="+",
        default=[],
        metavar="PXD_OR_MASK",
        help="PXD accessions or shell-style masks to exclude",
    )
    parser.add_argument("--force", action="store_true", help="Replace the current catalog entry even if unchanged")
    parser.add_argument("--dry-run", action="store_true", help="Report planned imports without connecting to PostgreSQL")
    parser.add_argument(
        "--static-snap",
        "--static_snap",
        nargs="?",
        type=Path,
        const=DEFAULT_STATIC_SNAPSHOT,
        metavar="PATH",
        help="After synchronizing, export a compact database-backed JSON snapshot for the results explorer",
    )
    parser.add_argument(
        "--artifact-base-url",
        default="",
        help="Optional public R2 artifact root used for file-explorer links in the static snapshot",
    )
    parser.add_argument(
        "--max-inline-artifact-bytes",
        type=int,
        help=(
            "Maximum JSON or text artifact size retained inside the local SQLite database "
            f"(default: {DEFAULT_LOCAL_INLINE_ARTIFACT_LIMIT} bytes; 0 disables inline retention)"
        ),
    )
    args = parser.parse_args()
    if args.database_url is None and args.database_path is None:
        args.database_url = os.getenv("XHAMLET_DATABASE_URL")
        if args.database_url is None:
            args.database_path = DEFAULT_LOCAL_DATABASE
    return args


def read_config(config_path: Path) -> dict[str, Any]:
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def unwrap_payload(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"], payload.get("metadata", {})
    return payload if isinstance(payload, dict) else {}, {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def iso_to_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def artifact_type(relative_path: Path) -> str:
    parts = relative_path.parts
    if not parts:
        return "other"
    if parts[0] in {"pride", "pmc", "llm", "enhanced", "assessment", "sdrf", "configs", "relink"}:
        return parts[0]
    return "other"


def catalog_files(pxd_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in pxd_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() in EXCLUDED_ARTIFACT_SUFFIXES:
            continue
        files.append(path)
    return sorted(files)


def source_signature(pxd_dir: Path, files: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(pxd_dir).as_posix()
        stat = path.stat()
        digest.update(f"{relative}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode())
    return digest.hexdigest()


def select_pxds(base_dir: Path, include: list[str] | None, exclude: list[str]) -> list[Path]:
    candidates = sorted(path for path in base_dir.iterdir() if path.is_dir() and PXD_PATTERN.fullmatch(path.name))

    def matches(name: str, patterns: list[str]) -> bool:
        return any(fnmatch.fnmatchcase(name.upper(), pattern.upper()) for pattern in patterns)

    selected = [path for path in candidates if (not include or matches(path.name, include)) and not matches(path.name, exclude)]
    if include:
        matched = {path.name.upper() for path in selected}
        missing = [pattern for pattern in include if not any(fnmatch.fnmatchcase(name, pattern.upper()) for name in matched)]
        if missing:
            print(f"Warning: no PXD directories matched: {', '.join(missing)}", file=sys.stderr)
    return selected


def scan_number(spectrum_id: str) -> int | None:
    match = re.search(r"(?:^|\s)scan=(\d+)", spectrum_id)
    return int(match.group(1)) if match else None


def item_score(item: ET.Element) -> float | None:
    for parameter in item.findall("{*}cvParam"):
        if parameter.get("name", "").lower() == "xi:score":
            try:
                return float(parameter.get("value", ""))
            except ValueError:
                return None
    return None


def item_group_key(item: ET.Element) -> str | None:
    for parameter in item.findall("{*}cvParam"):
        if parameter.get("name") == "cross-link spectrum identification item":
            return parameter.get("value")
    return None


def peptide_side(peptide_id: str) -> str:
    if peptide_id.endswith("_p0"):
        return "alpha"
    if peptide_id.endswith("_p1"):
        return "beta"
    return "single"


def parse_mzid(path: Path) -> dict[str, Any]:
    """Stream mzIdentML metadata plus compact, passing cross-link observations."""
    summary: dict[str, Any] = {
        "xml_id": None,
        "version": None,
        "namespace_uri": None,
        "creation_time": None,
        "metadata": {"search_databases": [], "software": []},
        "spectrum_result_count": 0,
        "spectrum_item_count": 0,
        "passing_item_count": 0,
        "is_complete": False,
        "crosslinks": [],
    }
    proteins: dict[str, str] = {}
    peptides: dict[str, str] = {}
    evidence: dict[str, list[dict[str, str]]] = {}
    spectra_data: dict[str, str] = {}
    pending_matches: list[dict[str, Any]] = []
    try:
        for _, element in ET.iterparse(path, events=("end",)):
            tag = element.tag.rsplit("}", 1)[-1]
            if tag == "MzIdentML":
                summary["xml_id"] = element.get("id")
                summary["version"] = element.get("version")
                if element.tag.startswith("{"):
                    summary["namespace_uri"] = element.tag[1:].split("}", 1)[0]
                summary["creation_time"] = iso_to_datetime(element.get("creationDate"))
                summary["is_complete"] = True
            elif tag == "SearchDatabase":
                summary["metadata"]["search_databases"].append(
                    {key: value for key, value in element.attrib.items() if key in {"id", "location", "name", "version"}}
                )
            elif tag == "AnalysisSoftware":
                summary["metadata"]["software"].append(
                    {key: value for key, value in element.attrib.items() if key in {"id", "name", "version"}}
                )
            elif tag == "DBSequence":
                proteins[element.get("id", "")] = element.get("accession", "")
            elif tag == "Peptide":
                peptides[element.get("id", "")] = element.findtext("{*}PeptideSequence", default="")
            elif tag == "PeptideEvidence":
                peptide_id = element.get("peptide_ref", "")
                evidence.setdefault(peptide_id, []).append(
                    {
                        "protein_id": element.get("dBSequence_ref", ""),
                        "start": element.get("start", ""),
                        "end": element.get("end", ""),
                        "is_decoy": element.get("isDecoy", "false"),
                    }
                )
            elif tag == "SpectraData":
                spectra_data[element.get("id", "")] = element.get("location", "")
            elif tag == "SpectrumIdentificationResult":
                summary["spectrum_result_count"] += 1
                grouped_items: dict[str, list[ET.Element]] = {}
                for item in element.findall("{*}SpectrumIdentificationItem"):
                    summary["spectrum_item_count"] += 1
                    is_passing = item.get("passThreshold", "false").lower() == "true"
                    if is_passing:
                        summary["passing_item_count"] += 1
                    group_key = item_group_key(item)
                    if is_passing and group_key:
                        grouped_items.setdefault(group_key, []).append(item)
                for group_key, items in grouped_items.items():
                    sides = {peptide_side(item.get("peptide_ref", "")): item for item in items}
                    if "alpha" not in sides or "beta" not in sides:
                        continue
                    match: dict[str, Any] = {
                        "source_ref": element.get("spectraData_ref", ""),
                        "spectrum_native_id": element.get("spectrumID", ""),
                        "scan_number": scan_number(element.get("spectrumID", "")),
                        "crosslink_group_key": group_key,
                    }
                    for side in ("alpha", "beta"):
                        item = sides[side]
                        peptide_id = item.get("peptide_ref", "")
                        mappings = evidence.get(peptide_id, [])
                        match[f"{side}_sequence"] = peptides.get(peptide_id)
                        match[f"{side}_proteins"] = sorted(
                            {proteins.get(mapping["protein_id"], mapping["protein_id"]) for mapping in mappings if mapping["is_decoy"] != "true"}
                        )
                        match[f"{side}_positions"] = sorted(
                            {
                                f"{proteins.get(mapping['protein_id'], mapping['protein_id'])}:{mapping['start']}-{mapping['end']}"
                                for mapping in mappings if mapping["is_decoy"] != "true"
                            }
                        )
                    match["charge_state"] = int(sides["alpha"].get("chargeState", "0")) or None
                    match["xi_score"] = item_score(sides["alpha"])
                    pending_matches.append(match)
                element.clear()
                continue
            if tag in {"MzIdentML", "SearchDatabase", "AnalysisSoftware", "DBSequence", "Peptide", "PeptideEvidence", "SpectraData"}:
                element.clear()
    except ET.ParseError as error:
        summary["metadata"]["parse_error"] = str(error)
    for match in pending_matches:
        match["source_spectrum"] = spectra_data.get(match.pop("source_ref"), "")
    summary["crosslinks"] = pending_matches
    return summary


def find_taxid(path: Path) -> str | None:
    for parent in (path, *path.parents):
        match = re.fullmatch(r"taxid_(\d+)", parent.name)
        if match:
            return match.group(1)
    return None


def config_lines(run_dir: Path) -> list[str]:
    candidates = sorted(run_dir.rglob("*crosslink*.conf"))
    lines: list[str] = []
    for config_path in candidates:
        try:
            for line in config_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("crosslinker:") or "unknown crosslinker" in line.lower():
                    lines.append(line.strip())
        except OSError:
            continue
    return lines


def find_fasta(run_dir: Path) -> str | None:
    for report in sorted(run_dir.rglob("*.html")):
        try:
            match = re.search(r"fasta</dt><dd><samp>([^<]+)", report.read_text(encoding="utf-8", errors="ignore"))
            if match:
                return match.group(1)
        except OSError:
            continue
    return None


def collect_search_runs(pxd_dir: Path) -> list[dict[str, Any]]:
    relink_dir = pxd_dir / "relink"
    if not relink_dir.is_dir():
        return []
    runs: dict[Path, dict[str, Any]] = {}
    for mzid_path in relink_dir.rglob("*.mzid"):
        results_dir = next((parent for parent in (mzid_path.parent, *mzid_path.parents) if parent.name == "results"), None)
        run_dir = results_dir.parent if results_dir else mzid_path.parent
        runs.setdefault(
            run_dir,
            {
                "path": run_dir.relative_to(pxd_dir).as_posix(),
                "taxid": find_taxid(run_dir),
                "crosslinker_config": config_lines(run_dir),
                "fasta_path": find_fasta(run_dir),
                "status": "complete",
                "mzids": [],
            },
        )["mzids"].append(mzid_path)
    return [runs[path] for path in sorted(runs)]

def project_raw_names(pxd_dir: Path) -> list[str]:
    """Return known RAW filenames for resolving ReLink mzML spectrum paths."""
    names: set[str] = set()
    enhanced, _ = unwrap_payload(pxd_dir / "enhanced" / "metadata.json")
    assignments = enhanced.get("file_assignments", {})
    if isinstance(assignments, dict):
        names.update(name for name in assignments if name.lower().endswith(".raw"))
    pride, _ = unwrap_payload(pxd_dir / "pride" / "project_details.json")
    files = pride.get("files", {}).get("files", []) if isinstance(pride.get("files"), dict) else []
    if isinstance(files, list):
        names.update(
            str(file_info.get("fileName"))
            for file_info in files
            if isinstance(file_info, dict) and str(file_info.get("fileName", "")).lower().endswith(".raw")
        )
    return sorted(names)


def project_file_assignments(pxd_dir: Path) -> dict[str, dict[str, Any]]:
    """Collect every known RAW filename and its LLM clustering assignment."""
    enhanced, _ = unwrap_payload(pxd_dir / "enhanced" / "metadata.json")
    raw_assignments = enhanced.get("file_assignments", {})
    assignments = {
        filename: assignment
        for filename, assignment in raw_assignments.items()
        if filename.lower().endswith(".raw") and isinstance(assignment, dict)
    } if isinstance(raw_assignments, dict) else {}
    for filename in project_raw_names(pxd_dir):
        assignments.setdefault(filename, {})
    return assignments


def resolve_raw_filename(source_spectrum: str, raw_names: list[str]) -> str | None:
    """Map a ReLink mzML location back to a manifest or assigned RAW filename."""
    source = Path(source_spectrum).name.lower()
    matches = [name for name in raw_names if Path(name).stem.lower() in source]
    return matches[0] if len(matches) == 1 else None


def json_value(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def timestamp_text(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else value


def open_database(args: argparse.Namespace) -> Any:
    if args.database_path is not None:
        return SQLiteConnection(args.database_path.expanduser().resolve())
    try:
        import psycopg
    except ImportError as error:
        raise SystemExit("Install PostgreSQL support with: python -m pip install 'psycopg[binary]>=3.2'") from error
    return psycopg.connect(args.database_url)


class DatabaseSynchronizer:
    def __init__(self, connection: Any, repo_root: Path, max_inline_artifact_bytes: int | None = None) -> None:
        self.connection = connection
        self.repo_root = repo_root
        self.max_inline_artifact_bytes = max_inline_artifact_bytes

    def create_schema(self) -> None:
        if getattr(self.connection, "is_sqlite", False):
            self.connection.execute_script(SQLITE_DDL)
        with self.connection.cursor() as cursor:
            if not getattr(self.connection, "is_sqlite", False):
                cursor.execute(DDL)
            cursor.execute(
                "INSERT INTO catalog_schema_version (version) VALUES (%s) ON CONFLICT (version) DO NOTHING",
                (SCHEMA_VERSION,),
            )
        self.connection.commit()

    def is_current(self, accession: str, signature: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM pipeline_run run
                JOIN project project USING (project_id)
                WHERE project.accession = %s AND run.source_signature = %s
                """,
                (accession, signature),
            )
            return cursor.fetchone() is not None

    def sync_pxd(self, pxd_dir: Path, signature: str, files: list[Path]) -> str:
        accession = pxd_dir.name.upper()
        enhanced_path = pxd_dir / "enhanced" / "metadata.json"
        pride_path = pxd_dir / "pride" / "project_details.json"
        llm_path = pxd_dir / "llm" / "responses.json"
        enhanced, enhanced_meta = unwrap_payload(enhanced_path) if enhanced_path.exists() else ({}, {})
        pride, _ = unwrap_payload(pride_path) if pride_path.exists() else ({}, {})
        llm, llm_meta = unwrap_payload(llm_path) if llm_path.exists() else ({}, {})
        stages = enhanced.get("stages", {}) if isinstance(enhanced, dict) else {}
        accepted = stages.get("compilation") == "success"

        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO project (accession, title, xhamlet_commit, updated_at)
                    VALUES (%s, %s, %s, now())
                    ON CONFLICT (accession) DO UPDATE SET
                        title = EXCLUDED.title,
                        xhamlet_commit = EXCLUDED.xhamlet_commit,
                        updated_at = now()
                    RETURNING project_id
                    """,
                    (accession, pride.get("title"), git_commit(self.repo_root)),
                )
                project_id = cursor.fetchone()[0]
                cursor.execute("DELETE FROM pipeline_run WHERE project_id = %s", (project_id,))
                cursor.execute(
                    """
                    INSERT INTO pipeline_run
                    (project_id, source_signature, source_root, processed_at, accepted, stage_status, enhanced_metadata)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    RETURNING pipeline_run_id
                    """,
                    (
                        project_id,
                        signature,
                        str(pxd_dir),
                        iso_to_datetime(enhanced.get("processed_at") or enhanced_meta.get("saved_at")),
                        accepted,
                        json.dumps(stages),
                        json.dumps(enhanced),
                    ),
                )
                pipeline_run_id = cursor.fetchone()[0]
                self._insert_artifacts(cursor, pipeline_run_id, pxd_dir, files)
                self._insert_source_files(cursor, pipeline_run_id, pxd_dir)
                self._insert_llm(cursor, pipeline_run_id, llm, llm_meta, llm_path)
                self._insert_search_runs(cursor, pipeline_run_id, pxd_dir)
        return "accepted" if accepted else "cataloged-incomplete"

    def _insert_artifacts(self, cursor: Any, pipeline_run_id: int, pxd_dir: Path, files: list[Path]) -> None:
        for path in files:
            relative = path.relative_to(pxd_dir)
            stat = path.stat()
            content_json: dict[str, Any] | None = None
            content_text: str | None = None
            is_oversized = (
                self.max_inline_artifact_bytes is not None
                and stat.st_size > self.max_inline_artifact_bytes
            )
            if is_oversized:
                content_json = {
                    "content_omitted": f"artifact exceeds local inline limit of {self.max_inline_artifact_bytes} bytes"
                }
            elif path.suffix.lower() == ".json":
                try:
                    content_json, _ = unwrap_payload(path)
                except (OSError, json.JSONDecodeError):
                    content_json = {"parse_error": "invalid JSON"}
            elif path.suffix.lower() in TEXT_ARTIFACT_SUFFIXES:
                try:
                    content_text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    content_text = None
            cursor.execute(
                """
                INSERT INTO output_artifact
                (pipeline_run_id, relative_path, artifact_type, byte_size, modified_at, sha256, content_json, content_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    pipeline_run_id,
                    relative.as_posix(),
                    artifact_type(relative),
                    stat.st_size,
                    datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                    sha256_file(path),
                    json.dumps(content_json) if content_json is not None else None,
                    content_text,
                ),
            )

    def _insert_source_files(self, cursor: Any, pipeline_run_id: int, pxd_dir: Path) -> None:
        for filename, assignment in project_file_assignments(pxd_dir).items():
            cursor.execute(
                """
                INSERT INTO source_file (pipeline_run_id, filename, assignment_json)
                VALUES (%s, %s, %s::jsonb)
                """,
                (pipeline_run_id, filename, json.dumps(assignment)),
            )

    def _insert_llm(self, cursor: Any, pipeline_run_id: int, llm: dict[str, Any], metadata: dict[str, Any], path: Path) -> None:
        if not llm or not path.exists():
            return
        cursor.execute(
            """
            INSERT INTO llm_output (pipeline_run_id, saved_at, source_json, source_sha256)
            VALUES (%s, %s, %s::jsonb, %s) RETURNING llm_output_id
            """,
            (pipeline_run_id, iso_to_datetime(metadata.get("saved_at")), json.dumps(llm), sha256_file(path)),
        )
        llm_output_id = cursor.fetchone()[0]
        for field_key, response in llm.items():
            if not isinstance(response, dict):
                continue
            parsed = response.get("parsed") if isinstance(response.get("parsed"), dict) else {}
            cursor.execute(
                """
                INSERT INTO llm_response
                (llm_output_id, field_key, prompt_group, model, raw_response_text, parsed_json,
                 value_json, accession_json, confidence, evidence_quote, evidence_location)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)
                """,
                (
                    llm_output_id,
                    field_key,
                    response.get("prompt_group"),
                    response.get("model"),
                    response.get("response"),
                    json.dumps(parsed),
                    json.dumps(parsed.get("value")),
                    json.dumps(parsed.get("accession")),
                    parsed.get("confidence"),
                    parsed.get("evidence_quote"),
                    parsed.get("evidence_location"),
                ),
            )

    def _insert_search_runs(self, cursor: Any, pipeline_run_id: int, pxd_dir: Path) -> None:
        for run in collect_search_runs(pxd_dir):
            cursor.execute(
                """
                INSERT INTO search_run
                (pipeline_run_id, run_path, taxid, crosslinker_config, fasta_path, status, metadata_json)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s::jsonb) RETURNING search_run_id
                """,
                (
                    pipeline_run_id,
                    run["path"],
                    run["taxid"],
                    json.dumps(run["crosslinker_config"]),
                    run["fasta_path"],
                    run["status"],
                    json.dumps({"mzid_count": len(run["mzids"])}),
                ),
            )
            search_run_id = cursor.fetchone()[0]
            for mzid_path in run["mzids"]:
                summary = parse_mzid(mzid_path)
                cursor.execute(
                    """
                    INSERT INTO mzid_document
                    (search_run_id, relative_path, source_sha256, xml_id, version, namespace_uri,
                     creation_time, document_metadata, spectrum_result_count, spectrum_item_count,
                     passing_item_count, is_complete)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                    RETURNING mzid_document_id
                    """,
                    (
                        search_run_id,
                        mzid_path.relative_to(pxd_dir).as_posix(),
                        sha256_file(mzid_path),
                        summary["xml_id"], summary["version"], summary["namespace_uri"], summary["creation_time"],
                        json.dumps(summary["metadata"]), summary["spectrum_result_count"],
                        summary["spectrum_item_count"], summary["passing_item_count"], summary["is_complete"],
                    ),
                )
                mzid_document_id = cursor.fetchone()[0]
                self._insert_crosslinks(cursor, mzid_document_id, summary["crosslinks"], project_raw_names(pxd_dir))

    def _insert_crosslinks(
        self,
        cursor: Any,
        mzid_document_id: int,
        matches: list[dict[str, Any]],
        raw_names: list[str],
    ) -> None:
        for match in matches:
            cursor.execute(
                """
                INSERT INTO crosslink_match
                (mzid_document_id, source_file, spectrum_native_id, scan_number, crosslink_group_key,
                 alpha_sequence, beta_sequence, alpha_proteins, beta_proteins, alpha_positions,
                 beta_positions, charge_state, xi_score, pass_threshold)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, true)
                """,
                (
                    mzid_document_id,
                    resolve_raw_filename(match.get("source_spectrum", ""), raw_names),
                    match["spectrum_native_id"],
                    match["scan_number"],
                    match["crosslink_group_key"],
                    match.get("alpha_sequence"),
                    match.get("beta_sequence"),
                    json.dumps(match.get("alpha_proteins", [])),
                    json.dumps(match.get("beta_proteins", [])),
                    json.dumps(match.get("alpha_positions", [])),
                    json.dumps(match.get("beta_positions", [])),
                    match.get("charge_state"),
                    match.get("xi_score"),
                ),
            )


def database_catalog(
    connection: Any,
    artifact_base_url: str,
    accessions: list[str] | None = None,
) -> dict[str, Any]:
    """Build the compact static explorer catalog from the accepted database rows."""
    artifact_base_url = artifact_base_url.rstrip("/")
    with connection.cursor() as cursor:
        if accessions is not None and not accessions:
            pipeline_rows: list[Any] = []
        else:
            selection = ""
            parameters: list[Any] = []
            if accessions is not None:
                selection = f" AND project.accession IN ({', '.join('%s' for _ in accessions)})"
                parameters.extend(accessions)
            cursor.execute(
                f"""
                SELECT project.project_id, project.accession, project.title, pipeline_run.pipeline_run_id,
                       pipeline_run.processed_at, pipeline_run.stage_status
                FROM project
                JOIN pipeline_run USING (project_id)
                WHERE pipeline_run.accepted{selection}
                ORDER BY project.accession
                """,
                parameters,
            )
            pipeline_rows = cursor.fetchall()
    projects = []
    for project_id, accession, title, pipeline_run_id, processed_at, stages in pipeline_rows:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT content_json FROM output_artifact
                WHERE pipeline_run_id = %s AND relative_path = 'pride/project_details.json'
                """,
                (pipeline_run_id,),
            )
            pride_row = cursor.fetchone()
            cursor.execute(
                """
                SELECT content_json FROM output_artifact
                WHERE pipeline_run_id = %s AND relative_path = 'assessment/spectral_summary.json'
                """,
                (pipeline_run_id,),
            )
            spectral_row = cursor.fetchone()
            cursor.execute(
                                f"""
                SELECT field_key, value_json, accession_json, confidence
                FROM llm_response response
                JOIN llm_output output USING (llm_output_id)
                                WHERE output.pipeline_run_id = %s
                                    AND field_key IN ({', '.join('%s' for _ in STATIC_METADATA_FIELDS)})
                ORDER BY field_key
                """,
                                (pipeline_run_id, *STATIC_METADATA_FIELDS),
            )
            metadata_fields = [
                {"key": key, "value": json_value(value), "accession": json_value(term), "confidence": confidence}
                for key, value, term, confidence in cursor.fetchall()
            ]
            cursor.execute(
                """
                SELECT relative_path, artifact_type, byte_size, modified_at
                FROM output_artifact WHERE pipeline_run_id = %s ORDER BY relative_path
                """,
                (pipeline_run_id,),
            )
            artifacts = [
                {
                    "path": path,
                    "category": category,
                    "size": size,
                    "modified_at": timestamp_text(modified_at),
                    **({"url": f"{artifact_base_url}/{accession}/{path}"} if artifact_base_url else {}),
                }
                for path, category, size, modified_at in cursor.fetchall()
            ]
            cursor.execute(
                """
                SELECT filename, assignment_json
                FROM source_file WHERE pipeline_run_id = %s ORDER BY filename
                """,
                (pipeline_run_id,),
            )
            raw_files = [
                {"filename": filename, "assignment": json_value(assignment) or {}}
                for filename, assignment in cursor.fetchall()
            ]
            cursor.execute(
                """
                SELECT search_run_id, run_path, taxid, fasta_path, crosslinker_config
                FROM search_run WHERE pipeline_run_id = %s ORDER BY run_path
                """,
                (pipeline_run_id,),
            )
            runs = []
            for search_run_id, run_path, taxid, fasta_path, crosslinkers in cursor.fetchall():
                cursor.execute(
                    """
                    SELECT mzid_document_id, relative_path, spectrum_result_count, spectrum_item_count,
                           passing_item_count, is_complete
                    FROM mzid_document WHERE search_run_id = %s ORDER BY relative_path
                    """,
                    (search_run_id,),
                )
                documents = [
                    {
                        "id": document_id,
                        "path": path,
                        "spectra": spectra,
                        "items": items,
                        "passing_items": passing,
                        "complete": bool(complete),
                    }
                    for document_id, path, spectra, items, passing, complete in cursor.fetchall()
                ]
                cursor.execute(
                    """
                    SELECT coalesce(match.source_file, '[unresolved RAW]'), match.alpha_sequence, match.beta_sequence,
                           match.alpha_proteins, match.beta_proteins, match.alpha_positions, match.beta_positions,
                           count(*), max(match.xi_score)
                    FROM crosslink_match match
                    JOIN mzid_document document USING (mzid_document_id)
                    WHERE document.search_run_id = %s AND match.pass_threshold
                    GROUP BY match.source_file, match.alpha_sequence, match.beta_sequence, match.alpha_proteins,
                             match.beta_proteins, match.alpha_positions, match.beta_positions
                    ORDER BY count(*) DESC, max(match.xi_score) DESC
                    """,
                    (search_run_id,),
                )
                crosslinks = [
                    {
                        "source_file": source_file,
                        "alpha_sequence": alpha_sequence,
                        "beta_sequence": beta_sequence,
                        "alpha_proteins": json_value(alpha_proteins),
                        "beta_proteins": json_value(beta_proteins),
                        "alpha_positions": json_value(alpha_positions),
                        "beta_positions": json_value(beta_positions),
                        "observations": observations,
                        "best_xi_score": best_score,
                    }
                    for source_file, alpha_sequence, beta_sequence, alpha_proteins, beta_proteins,
                    alpha_positions, beta_positions, observations, best_score in cursor.fetchall()
                ]
                runs.append(
                    {
                        "path": run_path,
                        "taxid": taxid,
                        "fasta": fasta_path,
                        "crosslinkers": json_value(crosslinkers) or [],
                        "mzid_documents": documents,
                        "crosslinks": crosslinks,
                    }
                )
        pride = json_value(pride_row[0]) if pride_row else {}
        projects.append(
            {
                "accession": accession,
                "title": title or pride.get("title", accession),
                "description": pride.get("projectDescription", ""),
                "doi": pride.get("doi"),
                "organisms": pride.get("organisms", []),
                "processed_at": timestamp_text(processed_at),
                "stages": json_value(stages) or {},
                "file_assignment_count": len(raw_files),
                "raw_files": raw_files,
                "metadata_fields": metadata_fields,
                "spectral_summary": json_value(spectral_row[0]) if spectral_row else {},
                "relink_runs": runs,
                "artifacts": artifacts,
            }
        )
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source": f"{'SQLite' if getattr(connection, 'is_sqlite', False) else 'PostgreSQL'} xHAMLET result catalog",
        "artifact_base_url": artifact_base_url,
        "project_count": len(projects),
        "projects": projects,
    }


def write_static_snapshot(
    connection: Any,
    output: Path,
    artifact_base_url: str,
    accessions: list[str] | None,
) -> None:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    catalog = database_catalog(connection, artifact_base_url, accessions)
    output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Static snapshot: {output} ({catalog['project_count']} PXD(s))")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    config = read_config(config_path)
    configured_base = config.get("storage", {}).get("base_dir", "./pxd_data")
    base_dir = Path(args.data_dir or configured_base).expanduser().resolve()
    if not base_dir.is_dir():
        raise FileNotFoundError(f"storage.base_dir does not exist: {base_dir}")
    pxds = select_pxds(base_dir, args.pxd, args.exclude_pxd)
    plans = [(pxd_dir, catalog_files(pxd_dir)) for pxd_dir in pxds]

    if args.dry_run:
        print(f"Data directory: {base_dir}")
        for pxd_dir, files in plans:
            print(f"{pxd_dir.name}: {len(files)} catalogable artifacts")
        print(f"Dry run: {len(plans)} PXD(s) selected")
        if args.static_snap:
            print("Static snapshot requires a PostgreSQL database; --dry-run does not write one")
        return 0
    repo_root = Path(__file__).resolve().parents[1]
    imported = skipped = 0
    with open_database(args) as connection:
        local_inline_limit = None
        if getattr(connection, "is_sqlite", False):
            local_inline_limit = (
                args.max_inline_artifact_bytes
                if args.max_inline_artifact_bytes is not None
                else DEFAULT_LOCAL_INLINE_ARTIFACT_LIMIT
            )
        synchronizer = DatabaseSynchronizer(connection, repo_root, local_inline_limit)
        synchronizer.create_schema()
        for pxd_dir, files in plans:
            signature = source_signature(pxd_dir, files)
            if not args.force and synchronizer.is_current(pxd_dir.name.upper(), signature):
                print(f"{pxd_dir.name}: unchanged, skipped")
                skipped += 1
                continue
            status = synchronizer.sync_pxd(pxd_dir, signature, files)
            print(f"{pxd_dir.name}: {status}")
            imported += 1
        if args.static_snap:
            selected_accessions = (
                [pxd_dir.name.upper() for pxd_dir, _ in plans]
                if args.pxd or args.exclude_pxd
                else None
            )
            write_static_snapshot(connection, args.static_snap, args.artifact_base_url, selected_accessions)
    print(f"Completed: {imported} imported, {skipped} unchanged, {len(plans)} selected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())