#!/usr/bin/env python3
"""Import one complete database-backed NCEMS XP run into the SQLite catalog.

Scores retain the immutable model and source mzIdentML hashes. Existing results
are never replaced; re-importing the same snapshot and source PXD is an error.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sqlite3
from pathlib import Path


DDL = """
CREATE TABLE IF NOT EXISTS xp_calculation (
    xp_calculation_id INTEGER PRIMARY KEY,
    snapshot_sha256 TEXT NOT NULL,
    source_pxd TEXT NOT NULL,
    result_path TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    UNIQUE(snapshot_sha256, source_pxd)
);
CREATE TABLE IF NOT EXISTS xp_model_result (
    xp_calculation_id INTEGER NOT NULL REFERENCES xp_calculation(xp_calculation_id),
    staged_job TEXT NOT NULL,
    model_pxd TEXT NOT NULL,
    model_job TEXT NOT NULL,
    model_sha256 TEXT NOT NULL,
    result_json TEXT NOT NULL,
    PRIMARY KEY(xp_calculation_id, staged_job)
);
CREATE TABLE IF NOT EXISTS xp_observation (
    xp_calculation_id INTEGER NOT NULL,
    staged_job TEXT NOT NULL,
    source_row_index INTEGER NOT NULL,
    source_mzid_sha256 TEXT NOT NULL,
    spectrum_native_id TEXT NOT NULL,
    crosslink_group_key TEXT NOT NULL,
    crosslink_match_id INTEGER NOT NULL,
    sasd_A REAL,
    xp_primary REAL,
    xp_exploratory REAL,
    reference_geometry_score REAL,
    score_status TEXT NOT NULL,
    result_json TEXT NOT NULL,
    PRIMARY KEY(xp_calculation_id, staged_job, source_row_index),
    FOREIGN KEY(xp_calculation_id, staged_job)
        REFERENCES xp_model_result(xp_calculation_id, staged_job)
);
CREATE INDEX IF NOT EXISTS xp_observation_match_idx ON xp_observation(crosslink_match_id);
CREATE TABLE IF NOT EXISTS xp_unmatched_observation (
    xp_calculation_id INTEGER NOT NULL REFERENCES xp_calculation(xp_calculation_id),
    source_row_index INTEGER NOT NULL,
    result_json TEXT NOT NULL,
    PRIMARY KEY(xp_calculation_id, source_row_index)
);
"""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"Invalid CSV header: {path}")
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError(f"Malformed CSV row: {path}")
        return rows


def number(value: str) -> float | None:
    if value == "":
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Non-finite XP value")
    return result


def import_run(database: Path, output: Path) -> int:
    output = output.resolve(strict=True)
    manifest_bytes = (output / "database_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    outcomes = json.loads((output / "outcomes.json").read_text())
    if len(outcomes) != 1 or outcomes[0]["exit_code"] != 0:
        raise ValueError("Expected one successfully completed source-project run")
    pxd = outcomes[0]["source_pxd"]
    run_dirs = list((output / "runs").glob(f"{pxd}_xp_v33_*"))
    if len(run_dirs) != 1:
        raise ValueError("Expected exactly one XP result directory")
    results = run_dirs[0] / "results"
    launch = json.loads((results / "launch_manifest.json").read_text())
    summary = json.loads((results / "run_summary.json").read_text())
    if launch.get("max_models") != 0 or launch.get("preflight_only") or not summary.get("full_catalog_processed"):
        raise ValueError("Refusing to import a smoke test or incomplete model selection")
    if summary.get("pxd") != pxd or not summary.get("input_accounting_ok"):
        raise ValueError("Result PXD or input accounting is invalid")
    if launch.get("software_sha256") != manifest["xp_package_sha256"]:
        raise ValueError("Result software differs from the frozen snapshot")
    selected = {m["staged_job"]: m for m in manifest["model_map"] if m["source_pxd"] == pxd}
    models = read_csv(results / "model_summary.csv")
    if len(models) != len(selected) or {m["job"] for m in models} != set(selected):
        raise ValueError("Model results do not cover the snapshot selection")
    if any(m["state"] in ("MODEL_FAILED", "ENGINE_FAILED") for m in models):
        raise ValueError("Model failures cannot be imported as complete")
    observations = read_csv(results / "xp_observations.csv")
    unmatched = read_csv(results / "unmatched_observations.csv")
    if (len(models) != summary.get("models_selected")
            or len(observations) != summary.get("model_observation_rows")
            or len(unmatched) != summary.get("unmatched_source_rows")):
        raise ValueError("XP result counts differ from the run summary")
    if any(m["pxd"] != pxd for m in models + observations + unmatched):
        raise ValueError("Mixed source projects in results")
    snapshot = hashlib.sha256(manifest_bytes).hexdigest()
    database = database.resolve(strict=True)
    with sqlite3.connect(database) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("BEGIN IMMEDIATE")
        for statement in DDL.split(";"):
            if statement.strip():
                db.execute(statement)
        for model in models:
            origin = selected[model["job"]]
            row = db.execute("""
                SELECT a.protein_a, a.protein_b FROM af3_prediction a
                JOIN pipeline_run r ON r.pipeline_run_id=a.pipeline_run_id
                JOIN project p ON p.project_id=r.project_id
                WHERE p.accession=? AND a.job_name=?
            """, (origin["model_pxd"], origin["job_name"])).fetchall()
            if len(row) != 1 or tuple(row[0]) != (model["protein_a"], model["protein_b"]):
                raise ValueError(f"Model no longer matches database: {model['job']}")
            if model["model_cif_sha256"] and model["model_cif_sha256"] != origin["model_sha256"]:
                raise ValueError(f"Model hash differs from snapshot: {model['job']}")
        for obs in observations + unmatched:
            raw = json.loads(obs["raw_observation_json"])
            if ("job" in obs and obs["job"] not in selected) or obs["scan_id"] != str(raw["crosslink_match_id"]):
                raise ValueError("Observation identity is inconsistent with snapshot")
            current = db.execute("""
                SELECT m.crosslink_match_id FROM crosslink_match m
                JOIN mzid_document d ON d.mzid_document_id=m.mzid_document_id
                JOIN search_run s ON s.search_run_id=d.search_run_id
                JOIN pipeline_run r ON r.pipeline_run_id=s.pipeline_run_id
                JOIN project p ON p.project_id=r.project_id
                WHERE p.accession=? AND d.source_sha256=? AND d.relative_path=?
                  AND m.spectrum_native_id=? AND m.crosslink_group_key=?
            """, (pxd, raw["source_mzid_sha256"], raw["source_mzid_path"],
                  raw["spectrum_native_id"], raw["crosslink_group_key"])).fetchall()
            if len(current) != 1 or current[0][0] != int(raw["crosslink_match_id"]):
                raise ValueError("Source match has changed since the XP snapshot")
        cursor = db.execute(
            "INSERT INTO xp_calculation(snapshot_sha256,source_pxd,result_path,summary_json,manifest_json) VALUES (?,?,?,?,?)",
            (snapshot, pxd, str(results), json.dumps(summary), manifest_bytes.decode("utf-8")),
        )
        calculation_id = cursor.lastrowid
        for model in models:
            origin = selected[model["job"]]
            db.execute("INSERT INTO xp_model_result VALUES (?,?,?,?,?,?)",
                       (calculation_id, model["job"], origin["model_pxd"], origin["job_name"],
                        origin["model_sha256"], json.dumps(model)))
        for obs in observations:
            raw = json.loads(obs["raw_observation_json"])
            db.execute("INSERT INTO xp_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                calculation_id, obs["job"], int(obs["source_row_index"]), raw["source_mzid_sha256"],
                raw["spectrum_native_id"], raw["crosslink_group_key"], int(raw["crosslink_match_id"]),
                number(obs["sasd_A"]), number(obs["xp_primary"]), number(obs["xp_exploratory"]),
                number(obs["reference_geometry_score"]), obs["score_status"], json.dumps(obs),
            ))
        for row in unmatched:
            db.execute("INSERT INTO xp_unmatched_observation VALUES (?,?,?)",
                       (calculation_id, int(row["source_row_index"]), json.dumps(row)))
        db.commit()
    print(f"Imported {pxd}: {len(models)} models, {len(observations)} observations, {len(unmatched)} unmatched")
    return calculation_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("xhamlet-results.sqlite3"))
    parser.add_argument("--output", type=Path, required=True, help="One source-PXD output directory")
    args = parser.parse_args()
    import_run(args.database, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
