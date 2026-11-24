import json
import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from backfill_crosslink_sites import backfill
from import_xp_database import DDL as XP_DDL
from sync_result_database import DatabaseSynchronizer, SQLiteConnection, database_catalog, parse_mzid, sha256_file
from test_export_search_results import mzid


class CrosslinkSiteSnapshotTests(unittest.TestCase):
    def test_backfill_and_snapshot_keep_unlocalized_and_candidate_provenance(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            store = root / "store"
            source = store / "PXD000001/relink/results/fdr/results.mzid"
            source.parent.mkdir(parents=True)
            source.write_text(mzid().replace(
                'location="2"><cvParam accession="MS:1002509"',
                'location="-1"><cvParam accession="MS:1002509"'))
            checksum = sha256_file(source)
            database = root / "catalog.sqlite"
            with SQLiteConnection(database) as connection:
                sync = DatabaseSynchronizer(connection, root)
                sync.create_schema()
                db = connection.connection
                db.execute("INSERT INTO project (accession) VALUES ('PXD000001')")
                db.execute("INSERT INTO pipeline_run (project_id, source_signature, source_root, accepted) "
                           "VALUES (1, 's', 'r', 1)")
                db.execute("INSERT INTO search_run (pipeline_run_id, run_path, status) VALUES (1, 'relink/r', 'ok')")
                db.execute("""INSERT INTO mzid_document
                    (search_run_id,relative_path,source_sha256,spectrum_result_count,
                     spectrum_item_count,passing_item_count,is_complete)
                    VALUES (1,'relink/results/fdr/results.mzid',?,1,2,2,1)""", (checksum,))
                with connection.cursor() as cursor:
                    sync._insert_crosslinks(cursor, 1, parse_mzid(source)["crosslinks"], [])
                db.executescript(XP_DDL)
                db.execute("""INSERT INTO xp_calculation
                    (xp_calculation_id,snapshot_sha256,source_pxd,result_path,summary_json,manifest_json)
                    VALUES (1,'s','PXD000001','results','{}','{}')""")
                db.execute("INSERT INTO xp_model_result VALUES (1,'job','PXD000001','model','model-hash','{}')")
                for index, site, sha in ((1, "10", checksum), (2, "11", checksum), (3, "12", "stale")):
                    result = {"site_assignment": "HYPOTHETICAL", "protein_a": "P12345",
                              "protein_a_site": site, "protein_a_aa": "K", "protein_b": "Q12345",
                              "protein_b_site": "22", "protein_b_aa": "K"}
                    db.execute("INSERT INTO xp_observation VALUES (1,'job',?,?,?,?,?,12,NULL,0.04,NULL,'OK',?)",
                               (index, sha, "scan=7", "group", 1, json.dumps(result)))
                db.execute("UPDATE crosslink_match SET alpha_link_sites=NULL,beta_link_sites=NULL")
                db.commit()
            counts = backfill(database, store)
            self.assertEqual(counts, {"total": 1, "verified": 1, "unavailable": 0})
            with SQLiteConnection(database) as connection:
                catalog = database_catalog(connection, "")
                cross = catalog["projects"][0]["relink_runs"][0]["crosslinks"][0]
                self.assertEqual(cross["alpha_link_sites"], ["-1"])
                self.assertEqual(cross["beta_link_sites"], ["1"])
                self.assertEqual({row["protein_a_site"] for row in cross["candidate_scores"]}, {"10", "11"})
                self.assertTrue(all(row["model_job"] == "model" for row in cross["candidate_scores"]))

            source.write_text("changed")
            counts = backfill(database, store, {"PXD000001/relink/results/fdr/results.mzid"})
            self.assertEqual(counts["unavailable"], 1)
            with sqlite3.connect(database) as db:
                self.assertEqual(db.execute("SELECT alpha_link_sites,beta_link_sites FROM crosslink_match").fetchone(),
                                 (None, None))
                self.assertEqual(db.execute("SELECT COUNT(*) FROM crosslink_match").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
