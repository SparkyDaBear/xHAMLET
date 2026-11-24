import csv
import json
import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import import_xp_database as importer


def write_rows(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ImportXPDatabaseTests(unittest.TestCase):
    def test_import_preserves_cross_project_provenance_and_rejects_reimport(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / "catalog.sqlite"
            with sqlite3.connect(database) as db:
                db.executescript("""
                    CREATE TABLE project(project_id INTEGER, accession TEXT);
                    CREATE TABLE pipeline_run(pipeline_run_id INTEGER, project_id INTEGER);
                    CREATE TABLE af3_prediction(pipeline_run_id INTEGER, job_name TEXT, protein_a TEXT, protein_b TEXT);
                    CREATE TABLE search_run(search_run_id INTEGER, pipeline_run_id INTEGER);
                    CREATE TABLE mzid_document(mzid_document_id INTEGER, search_run_id INTEGER,
                        relative_path TEXT, source_sha256 TEXT);
                    CREATE TABLE crosslink_match(crosslink_match_id INTEGER, mzid_document_id INTEGER,
                        spectrum_native_id TEXT, crosslink_group_key TEXT);
                    INSERT INTO project VALUES (1,'PXD000001'), (2,'PXD000002');
                    INSERT INTO pipeline_run VALUES (1,1), (2,2);
                    INSERT INTO af3_prediction VALUES (1,'model','P12345','Q12345');
                    INSERT INTO search_run VALUES (3,2);
                    INSERT INTO mzid_document VALUES (4,3,'relink/result.mzid','source-hash');
                    INSERT INTO crosslink_match VALUES (5,4,'scan=7','group');
                """)
            output = root / "output"
            result = output / "runs/PXD000002_xp_v33_run/results"
            result.mkdir(parents=True)
            manifest = {"model_map": [{"source_pxd": "PXD000002", "model_pxd": "PXD000001",
                                       "job_name": "model", "staged_job": "model__db1",
                                       "model_sha256": "model-hash"}], "xp_package_sha256": {"score.py": "hash"}}
            (output / "database_manifest.json").write_text(json.dumps(manifest))
            (output / "outcomes.json").write_text('[{"source_pxd":"PXD000002","exit_code":0}]')
            (result / "launch_manifest.json").write_text(
                '{"max_models":0,"preflight_only":false,"software_sha256":{"score.py":"hash"}}')
            (result / "run_summary.json").write_text(
                '{"pxd":"PXD000002","full_catalog_processed":true,"input_accounting_ok":true,'
                '"models_selected":1,"model_observation_rows":2,"unmatched_source_rows":0}')
            write_rows(result / "model_summary.csv", [{
                "pxd": "PXD000002", "job": "model__db1", "protein_a": "P12345", "protein_b": "Q12345",
                "state": "COMPLETED", "model_cif_sha256": "model-hash",
            }])
            raw = {"crosslink_match_id": "5", "source_mzid_sha256": "source-hash",
                   "source_mzid_path": "relink/result.mzid", "spectrum_native_id": "scan=7",
                   "crosslink_group_key": "group"}
            observation = {
                "pxd": "PXD000002", "job": "model__db1", "scan_id": "5", "source_row_index": "1",
                "raw_observation_json": json.dumps(raw), "sasd_A": "12.5", "xp_primary": "",
                "xp_exploratory": "0.04", "reference_geometry_score": "0", "score_status": "EXPLORATORY",
            }
            write_rows(result / "xp_observations.csv", [observation, {**observation, "source_row_index": "2"}])
            (result / "unmatched_observations.csv").write_text("pxd,scan_id,source_row_index,raw_observation_json\n")
            importer.import_run(database, output)
            with sqlite3.connect(database) as db:
                model = db.execute("SELECT model_pxd,model_job FROM xp_model_result").fetchone()
                score = db.execute("SELECT crosslink_match_id,xp_primary,xp_exploratory,reference_geometry_score "
                                   "FROM xp_observation").fetchone()
                count = db.execute("SELECT COUNT(*) FROM xp_observation WHERE crosslink_match_id=5").fetchone()[0]
            self.assertEqual(model, ("PXD000001", "model"))
            self.assertEqual(score, (5, None, 0.04, 0))
            self.assertEqual(count, 2)
            with self.assertRaises(sqlite3.IntegrityError):
                importer.import_run(database, output)
            with sqlite3.connect(database) as db:
                self.assertEqual(db.execute("SELECT count(*) FROM xp_calculation").fetchone()[0], 1)

            (result / "launch_manifest.json").write_text('{"max_models":1,"preflight_only":false}')
            with self.assertRaisesRegex(ValueError, "smoke test"):
                importer.import_run(database, output)


if __name__ == "__main__":
    unittest.main()
