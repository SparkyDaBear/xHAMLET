import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from sync_reference_ppis import (  # noqa: E402
    base_accession, derive_pairs, ensure_schema, load_source, parse_complex_portal, parse_humap3,
)
from sync_result_database import SQLiteConnection  # noqa: E402

COMPLEXTAB_HEADER = "#Complex ac\tName\tAliases\tTaxonomy\tParticipants\tEvidence Code\n"


def write_complex_portal(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        COMPLEXTAB_HEADER
        + "CPX-1\tAB complex\t-\t9606\tP84022(1)|Q13485-2(2)|CPX-9(1)|CHEBI:15377(0)\tECO:0000353(evidence)\n"
        + "CPX-2\tChain complex\t-\t9606\tQ13485-PRO_0000012345(1)|P84022(1)|Q15796(0)\tECO:0005547(inference)\n",
        encoding="utf-8",
    )


def write_humap(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "HuMAP3_ID,ComplexConfidence,Uniprot_ACCs,genenames\n"
        "huMAP3_1.1,1,P84022 Q13485 645345,A B C\n"
        "huMAP3_2.1,4,P84022 Q13485 Q15796,A B C\n",
        encoding="utf-8",
    )


class ReferencePPITests(unittest.TestCase):
    def test_accessions_strip_isoforms_and_chains_and_reject_other_ids(self):
        self.assertEqual(base_accession("Q13485-2"), "Q13485")
        self.assertEqual(base_accession("Q13485-PRO_0000012345"), "Q13485")
        self.assertEqual(base_accession("A0A5B9"), "A0A5B9")
        for other in ("CPX-9", "CHEBI:15377", "URS000012AB34", "645345"):
            self.assertIsNone(base_accession(other))

    def test_complex_portal_members_dropped_participants_and_pairs(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "9606.tsv"
            write_complex_portal(path)
            complexes = parse_complex_portal(path)
        first, second = complexes
        self.assertEqual(first["members"], {"P84022": 1, "Q13485": 2})
        self.assertEqual(first["dropped"], 2)
        self.assertEqual(second["members"], {"Q13485": 1, "P84022": 1, "Q15796": None})
        pairs = derive_pairs(complexes)
        self.assertEqual(sorted(pairs), [("P84022", "Q13485"), ("P84022", "Q15796"), ("Q13485", "Q15796")])
        self.assertEqual(pairs[("P84022", "Q13485")]["complex_ids"], ["CPX-1", "CPX-2"])
        self.assertEqual(pairs[("P84022", "Q13485")]["evidence"], {"ECO:0000353", "ECO:0005547"})

    def test_humap_best_tier_is_minimum_and_junk_accession_is_dropped(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "humap.csv"
            write_humap(path)
            complexes = parse_humap3(path)
        self.assertEqual(complexes[0]["dropped"], 1)
        pairs = derive_pairs(complexes)
        self.assertEqual(pairs[("P84022", "Q13485")]["best_tier"], 1)
        self.assertEqual(pairs[("P84022", "Q15796")]["best_tier"], 4)
        self.assertNotIn("645345", {accession for pair in pairs for accession in pair})

    def test_load_is_idempotent_and_replaces_changed_sources(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            humap = root / "reference" / "humap3" / "20240922" / "humap.csv"
            write_humap(humap)
            with SQLiteConnection(root / "db.sqlite3") as connection:
                ensure_schema(connection)
                self.assertIn("loaded 2 complexes, 3 pairs", load_source(connection, "humap3", humap, False))
                connection.commit()
                self.assertIn("unchanged", load_source(connection, "humap3", humap, False))
                humap.write_text(humap.read_text() + "huMAP3_3.1,2,P84022 Q99999,D E\n")
                self.assertIn("loaded 3 complexes, 4 pairs", load_source(connection, "humap3", humap, False))
                connection.commit()
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM reference_source")
                self.assertEqual(cursor.fetchone()[0], 1)
                cursor.execute("SELECT COUNT(*) FROM reference_ppi")
                self.assertEqual(cursor.fetchone()[0], 4)
                cursor.execute("SELECT COUNT(*) FROM reference_complex_member")
                self.assertEqual(cursor.fetchone()[0], 7)


if __name__ == "__main__":
    unittest.main()
