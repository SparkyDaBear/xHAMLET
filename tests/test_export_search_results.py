import csv
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from export_search_results import REQUIRED_LINEAR, export_pxd
from sync_result_database import parse_mzid


def mzid(rank="1", passing="true", decoy="false"):
    return f"""<MzIdentML id="test">
    <SequenceCollection>
    <DBSequence id="db" accession="P12345"/>
    <Peptide id="pair_p0"><PeptideSequence>AK</PeptideSequence>
      <Modification location="2"><cvParam accession="MS:1002509"/></Modification>
      <Modification location="1" monoisotopicMassDelta="42"/></Peptide>
    <Peptide id="pair_p1"><PeptideSequence>KA</PeptideSequence>
      <Modification location="1"><cvParam accession="MS:1002510"/></Modification></Peptide>
    <PeptideEvidence id="e0" peptide_ref="pair_p0" dBSequence_ref="db"
      start="10" end="11" isDecoy="{decoy}"/>
    <PeptideEvidence id="e1" peptide_ref="pair_p1" dBSequence_ref="db"
      start="20" end="21" isDecoy="false"/>
    </SequenceCollection>
    <SpectraData id="source" location="/input/raw.mzML"/>
    <SpectrumIdentificationResult spectraData_ref="source" spectrumID="scan=7">
    <SpectrumIdentificationItem peptide_ref="pair_p0" rank="{rank}" passThreshold="{passing}" chargeState="3">
      <PeptideEvidenceRef peptideEvidence_ref="e0"/>
      <cvParam name="cross-link spectrum identification item" value="group"/>
      <cvParam name="xi:score" value="12"/>
    </SpectrumIdentificationItem>
    <SpectrumIdentificationItem peptide_ref="pair_p1" rank="{rank}" passThreshold="{passing}" chargeState="3">
      <PeptideEvidenceRef peptideEvidence_ref="e1"/>
      <cvParam name="cross-link spectrum identification item" value="group"/>
    </SpectrumIdentificationItem>
    </SpectrumIdentificationResult></MzIdentML>"""


class ExportTests(unittest.TestCase):
    def prepare(self, root):
        pxd = root / "PXD000001"
        results = pxd / "relink/taxid_9606/dss/results"
        (results / "linear_search").mkdir(parents=True)
        (results / "fdr").mkdir()
        (results / "fdr/results.mzid").write_text(mzid())
        fields = sorted(REQUIRED_LINEAR)
        with (results / "linear_search/sample_linear.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            row = dict.fromkeys(fields, "")
            row.update(Run="raw.mzML", Scan="6", ScanTitle="scan=7", MatchRank="1",
                       decoy="0", BasePeptide1="AK", Peptide1="A.AK.G",
                       Protein1="P12345;Q12345", Start1="10;30",
                       PrecoursorCharge="3", **{"match score": "12"})
            writer.writerow(row)
            writer.writerow(dict(row, Protein1="Q12345"))
            writer.writerow(dict(row, MatchRank="2"))
            writer.writerow(dict(row, decoy="1"))
        return pxd, results

    def read(self, pxd, name):
        with (pxd / "search_results" / (name + ".csv")).open() as f:
            return list(csv.DictReader(f))

    def test_filters_mappings_sites_and_idempotency(self):
        with TemporaryDirectory() as temp:
            pxd, results = self.prepare(Path(temp))
            counts = export_pxd(pxd)
            self.assertEqual(counts, {"linear": 2, "crosslinks": 1, "scan_map": 2})
            linear = self.read(pxd, "linear")
            self.assertEqual(linear[0]["scan_id"], linear[1]["scan_id"])
            self.assertEqual(linear[0]["protein_accessions"], "P12345;Q12345")
            cross = self.read(pxd, "crosslinks")[0]
            self.assertEqual(cross["alpha_link_sites"], "2")
            self.assertEqual(cross["beta_link_sites"], "1")
            self.assertEqual(cross["alpha_positions"], "P12345:10-11")
            self.assertIn('"monoisotopicMassDelta":"42"', cross["alpha_modifications"])
            before = {p.name: p.read_bytes() for p in (pxd / "search_results").iterdir()}
            export_pxd(pxd)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (pxd / "search_results").iterdir()})

    def test_rank_fdr_and_decoy_filter_shared_with_catalog(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "results.mzid"
            for rank, passing, decoy, expected in [
                ("1", "true", "false", 1), ("2", "true", "false", 0),
                ("1", "false", "false", 0), ("1", "true", "true", 0),
            ]:
                path.write_text(mzid(rank, passing, decoy))
                self.assertEqual(len(parse_mzid(path)["crosslinks"]), expected)

    def test_failures_preserve_existing_outputs(self):
        with TemporaryDirectory() as temp:
            pxd, results = self.prepare(Path(temp))
            export_pxd(pxd)
            before = (pxd / "search_results/linear.csv").read_bytes()
            with self.assertRaisesRegex(ValueError, "limit"):
                export_pxd(pxd, limit=1)
            (results / "fdr/results.mzid").write_text("<MzIdentML>")
            with self.assertRaisesRegex(ValueError, "invalid"):
                export_pxd(pxd)
            self.assertEqual(before, (pxd / "search_results/linear.csv").read_bytes())

    def test_missing_and_empty_valid_results(self):
        with TemporaryDirectory() as temp:
            pxd, results = self.prepare(Path(temp))
            (results / "fdr/results.mzid").unlink()
            with self.assertRaisesRegex(ValueError, "missing"):
                export_pxd(pxd)
            (results / "fdr/results.mzid").write_text(mzid(passing="false"))
            self.assertEqual(export_pxd(pxd)["crosslinks"], 0)

    def test_scan_ids_do_not_collide_between_groups(self):
        import shutil

        with TemporaryDirectory() as temp:
            pxd, results = self.prepare(Path(temp))
            second = pxd / "relink/taxid_9606/bs3/results"
            shutil.copytree(results, second)
            export_pxd(pxd)
            mapping = self.read(pxd, "scan_map")
            self.assertEqual(len(mapping), 4)
            self.assertEqual(len({r["scan_id"] for r in mapping}), 4)
            self.assertEqual({r["search_group"] for r in mapping},
                             {"taxid_9606/bs3", "taxid_9606/dss"})

    def test_size_limit_includes_header_and_rejects_equality(self):
        with TemporaryDirectory() as temp:
            pxd, _ = self.prepare(Path(temp))
            export_pxd(pxd)
            largest = max(p.stat().st_size for p in (pxd / "search_results").iterdir())
            with self.assertRaisesRegex(ValueError, "limit"):
                export_pxd(pxd, limit=largest)
            export_pxd(pxd, limit=largest + 1)

    def test_malformed_csv_is_not_published(self):
        with TemporaryDirectory() as temp:
            pxd, results = self.prepare(Path(temp))
            path = results / "linear_search/sample_linear.csv"
            path.write_text("Run,Scan\nraw.mzML,1\n")
            with self.assertRaisesRegex(ValueError, "missing columns"):
                export_pxd(pxd)
            self.assertFalse((pxd / "search_results").exists())


if __name__ == "__main__":
    unittest.main()
