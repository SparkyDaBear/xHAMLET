import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ppi_index import expand_match, normalize_accession, refresh_ppi_index  # noqa: E402
from sync_reference_ppis import derive_pairs, ensure_schema, load_source  # noqa: E402
from sync_result_database import SQLiteConnection  # noqa: E402


class ExpandMatchTests(unittest.TestCase):
    def test_isoforms_normalize_and_non_uniprot_ids_are_kept(self):
        self.assertEqual(normalize_accession("Q13485-2"), "Q13485")
        self.assertEqual(normalize_accession("PDK1_LKD"), "PDK1_LKD")

    def test_pair_is_oriented_to_sorted_accessions(self):
        row = (1, "AAAK", "BBBK", json.dumps(["Q2"]), json.dumps(["P1"]), json.dumps(["Q2:3-6"]), json.dumps(["P1:10-13"]))
        (pair,) = expand_match(row)
        self.assertEqual(pair, (1, "P1", "Q2", "BBBK", "AAAK", "10-13", "3-6", 0))

    def test_ambiguous_candidates_are_flagged_and_self_pairs_dropped(self):
        row = (2, "AAAK", "BBBK", json.dumps(["P84022", "P84022-2"]), json.dumps(["P84022", "Q13485"]), "[]", "[]")
        pairs = expand_match(row)
        self.assertEqual([(p[1], p[2], p[7]) for p in pairs], [("P84022", "Q13485", 1)])


class RefreshIndexTests(unittest.TestCase):
    def test_refresh_joins_relink_and_reference_and_keeps_reference_only_pairs(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            release = root / "humap3" / "20240922"
            release.mkdir(parents=True)
            humap = release / "humap.csv"
            humap.write_text(
                "HuMAP3_ID,ComplexConfidence,Uniprot_ACCs,genenames\n"
                "huMAP3_1.1,2,P84022 Q13485,A B\n"
                "huMAP3_2.1,5,Q13485 Q15796,B C\n"
            )
            with SQLiteConnection(root / "db.sqlite3") as connection:
                ensure_schema(connection)
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO project (accession) VALUES ('PXD000001')")
                    cursor.execute("INSERT INTO pipeline_run (project_id, source_signature, source_root) VALUES (1, 's', 'r')")
                    cursor.execute("INSERT INTO search_run (pipeline_run_id, run_path, taxid, status) VALUES (1, 'p', '9606', 'ok')")
                    cursor.execute(
                        "INSERT INTO mzid_document (search_run_id, relative_path, source_sha256, spectrum_result_count, "
                        "spectrum_item_count, passing_item_count, is_complete) VALUES (1, 'x', 'h', 1, 1, 1, 1)"
                    )
                    for index, (alpha, beta, score) in enumerate([("Q13485", "P84022", 4.0), ("P84022", "Q13485", 7.0), ("P1", "Q2", 3.0)]):
                        cursor.execute(
                            "INSERT INTO crosslink_match (mzid_document_id, spectrum_native_id, crosslink_group_key, alpha_sequence, "
                            "beta_sequence, alpha_proteins, beta_proteins, alpha_positions, beta_positions, xi_score, pass_threshold) "
                            "VALUES (1, %s, %s, 'AAAK', 'BBBK', %s, %s, '[]', '[]', %s, 1)",
                            (f"s{index}", f"g{index}", json.dumps([alpha]), json.dumps([beta]), score),
                        )
                    load_source(connection, "humap3", humap, False)
                counts = refresh_ppi_index(connection)
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT accession_a, accession_b, relink_match_count, relink_best_xi_score, humap3_complex_count, humap3_best_tier "
                    "FROM ppi ORDER BY accession_a, accession_b"
                )
                rows = cursor.fetchall()
                cursor.execute("SELECT complex_id, confidence_tier FROM ppi_reference_detail WHERE accession_a = 'P84022'")
                detail = cursor.fetchall()
                cursor.execute("SELECT pxd, xi_score FROM ppi_relink_detail WHERE accession_a = 'P84022' ORDER BY xi_score")
                relink = cursor.fetchall()
        self.assertEqual(counts["ppis"], 3)
        self.assertEqual(counts["relink_and_reference"], 1)
        self.assertIn(("P1", "Q2", 1, 3.0, 0, None), rows)
        self.assertIn(("P84022", "Q13485", 2, 7.0, 1, 2), rows)
        self.assertIn(("Q13485", "Q15796", 0, None, 1, 5), rows)
        self.assertEqual(detail, [("huMAP3_1.1", 2)])
        self.assertEqual(relink, [("PXD000001", 4.0), ("PXD000001", 7.0)])


if __name__ == "__main__":
    unittest.main()
