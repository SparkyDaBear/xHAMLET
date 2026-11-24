"""Independent adversarial v3.3 checks.

All structures, rows, distances and accession numbers created here are SYNTHETIC.
The fake engine exercises intake, state separation and accounting only. It does
not validate Jwalk paths, experimental crosslinks, AF3 predictions or XP science.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SCORES = ("xp_primary", "xp_exploratory", "reference_geometry_score")


def number(value):
    try:
        result = float(value)
    except (ValueError, TypeError):
        return None
    return result if math.isfinite(result) else None


def row(**changes):
    result = {
        "pxd": "PXD999999", "job": "p00001__p00002__synthetic",
        "dataset": "SYNTHETIC INDEPENDENT TEST ONLY",
        "protein_a": "P00001", "protein_b": "P00002",
        "protein_a_aa": "K", "protein_b_aa": "K",
        "protein_a_site": "2", "protein_b_site": "2",
        "chain_a": "A", "pdb_site_a": "2",
        "chain_b": "B", "pdb_site_b": "2",
        "chemistry": "dss", "search_group": "taxid_9606/dss",
        "chemistry_evidence_status": "EXPERIMENT_REAGENT_CONFIRMED",
        "chemistry_evidence": "SYNTHETIC TEST DECLARATION ONLY; no experimental claim",
        "distance_metric": "JWALK_CA_SASD", "sasd_A": "18.62",
        "euclidean_A": "10", "status": "SCORED",
        "scan_id": "1", "xi_score": "20", "xp": "12345",
        "endpoint_a_kind": "SIDECHAIN", "endpoint_b_kind": "SIDECHAIN",
        "endpoint_a_modifications": "[]", "endpoint_b_modifications": "[]",
        "geometry_flag": "", "score_model": "SYNTHETIC_DISTANCE_ENGINE_ONLY",
        "supporting_spectra": "1", "evidence_rows": "1", "scan_ids": "1",
    }
    result.update(changes)
    return result


def raw_row(**changes):
    result = {
        "scan_id": "1", "charge": "3", "alpha_peptide": "AKKAA",
        "alpha_modifications": "[]", "alpha_positions": "P00001:1-5",
        "alpha_link_sites": "2", "beta_peptide": "GKKGG",
        "beta_modifications": "[]", "beta_positions": "P00002:1-5",
        "beta_link_sites": "2", "xi_score": "20",
    }
    result.update(changes)
    return result


def load_vendor():
    name = "independent_v33_vendor"
    spec = importlib.util.spec_from_file_location(name, ROOT / "vendor" / "batch_v01.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def csv_write(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(key for item in rows for key in item))
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def make_model_fixture(root):
    """A CA-only artificial structure adequate for mapper/fake-engine tests."""
    import numpy as np
    from Bio.PDB import MMCIFIO, StructureBuilder
    job = "p00001__p00002__synthetic"
    folder = root / "store" / "PXD999999" / "af3_predictions" / job
    folder.mkdir(parents=True)
    (folder / "pair.json").write_text(json.dumps({"protein_a": "P00001", "protein_b": "P00002"}))
    (folder / "summary_confidences.json").write_text(json.dumps({"iptm": 0.8, "synthetic": True}))
    builder = StructureBuilder.StructureBuilder()
    builder.init_structure("SYNTHETIC_ONLY")
    builder.init_model(0)
    serial = 0
    for chain, residues, y in (("A", ["ALA", "LYS", "LYS", "ALA", "ALA"], 0),
                               ("B", ["GLY", "LYS", "LYS", "GLY", "GLY"], 10)):
        builder.init_chain(chain)
        builder.init_seg(" ")
        for position, name in enumerate(residues, 1):
            serial += 1
            builder.init_residue(name, " ", position, " ")
            builder.init_atom("CA", np.array([3.0 * position, float(y), 0.0]),
                              20.0, 1.0, " ", " CA ", serial, element="C")
    output = MMCIFIO()
    output.set_structure(builder.get_structure())
    output.save(str(folder / "model.cif"))
    return job, folder


def run_synthetic_mapping(module, root, rows, group_by_scan=None):
    job, model_folder = make_model_fixture(root)
    group_by_scan = group_by_scan or {}
    scanmap = {r["scan_id"]: {"search_group": group_by_scan.get(r["scan_id"], "taxid_9606/dss"),
                                    "search_stage": "crosslink", "run": "SYNTHETIC", "scan": r["scan_id"]}
               for r in rows}
    output = root / "distance_run"
    output.mkdir()
    calls = []

    def fake_engine(command, **kwargs):
        calls.append(command)
        dest = Path(command[command.index("--outdir") + 1])
        dest.mkdir()
        with Path(command[command.index("--pairs") + 1]).open(newline="") as handle:
            requested = list(csv.DictReader(handle))
        engine_rows = []
        for request in requested:
            missing = request["residue1"] == "3"
            engine_rows.append({**request, "sasd_A": "" if missing else "18.62",
                                "euclidean_A": "" if missing else "10",
                                "xp": "" if missing else "9999",
                                "status": "NO_SASD_RETURNED" if missing else "SCORED",
                                "score_model": "SYNTHETIC_FAKE_ENGINE_NOT_JWALK"})
        csv_write(dest / "xp_pairs.csv", engine_rows)
        (dest / "summary.json").write_text(json.dumps({"synthetic": True, "jwalk_max_dist_A": 50.0}))
        return types.SimpleNamespace(returncode=0, stdout="SYNTHETIC MOCK ONLY", stderr="")

    prior = (model_folder / "model.cif").read_bytes()
    env = dict(os.environ)
    env.pop("NCEMS_REFERENCE_MANAGED", None)
    with patch.dict(os.environ, env, clear=True), patch.object(module, "subprocess", types.SimpleNamespace(run=fake_engine)):
        result = module.run_model(module.Entry("PXD999999", job, "SYNTHETIC ONLY", "0.8"),
                                  rows, scanmap, output, str(root / "store"),
                                  Path(__file__), 1, False)
    assert (model_folder / "model.cif").read_bytes() == prior, "Intake modified source fixture"
    return result, calls, output


def make_complete_intake(root):
    module = load_vendor()
    modification = json.dumps([{"location": "2", "residues": "K", "monoisotopicMassDelta": "42.010565"}])
    raw = [raw_row(), raw_row(scan_id="2", alpha_modifications=modification),
           raw_row(scan_id="3"), raw_row(scan_id="4", alpha_link_sites="3"),
           raw_row(scan_id="5", alpha_link_sites="-1"),
           raw_row(scan_id="6", alpha_positions="P00001-2:1-5"), raw_row(scan_id="7")]
    (observations, unique, model, matched), _, source = run_synthetic_mapping(
        module, root, raw, {"3": "taxid_9606/NEW_UNKNOWN_REAGENT"})
    unmatched = [{"pxd": "PXD999999", "scan_id": item["scan_id"], "source_row_index": index + 1,
                  "reason": "NO_STORED_AF3_PROTEIN_PAIR_MATCH", "raw_observation_json": json.dumps(item)}
                 for index, item in enumerate(raw) if index not in matched]
    csv_write(source / "xp_observations.csv", observations, module.OBS_FIELDS)
    csv_write(source / "xp_unique_pairs.csv", unique, module.UNIQUE_FIELDS)
    csv_write(source / "model_summary.csv", [model], module.MODEL_FIELDS)
    csv_write(source / "unmatched_observations.csv", unmatched)
    summary = {"pxd": "PXD999999", "mode": "XP_RUN", "state": "COMPLETE",
               "intake_version": "3.3.0", "geometry_scope": "ALL_LOCALIZED_MAPPED_OBSERVATIONS",
               "models_selected": 1, "models_in_catalog": 1,
               "raw_search_result_rows": len(raw), "matched_model_observation_rows": len(observations),
               "unique_modeled_site_and_chemistry_rows": len(unique), "unmatched_raw_rows": len(unmatched),
               "source": "SYNTHETIC FIXTURE; FAKE DISTANCES; NO SCIENTIFIC VALIDATION"}
    (source / "run_summary.json").write_text(json.dumps(summary))
    return source


def csv_read(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class IndependentMappingTests(unittest.TestCase):
    def setUp(self):
        self.mapper = load_vendor()

    def test_isoform_is_not_renamed_to_canonical(self):
        self.assertEqual(self.mapper.normal_accession("P00001-2"), "P00001-2")
        item = raw_row(alpha_positions="P00001-2:1-5")
        self.assertIsNone(self.mapper.candidate_orientation(item, "P00001", "P00002"))

    def test_ambiguous_accessions_are_not_resolved_by_dropping_alternatives(self):
        info, reason = self.mapper.selected_site(raw_row(alpha_positions="P00001:1-5;Q00001:1-5"), "alpha", "P00001")
        self.assertIsNone(info)
        self.assertTrue(reason)

    def test_homomer_chain_identity_is_not_guessed(self):
        item = raw_row(beta_positions="P00001:1-5")
        self.assertIsNone(self.mapper.candidate_orientation(item, "P00001", "P00001"))

    def test_unlocalized_position_does_not_become_zero(self):
        info, reason = self.mapper.selected_site(raw_row(alpha_link_sites="-1"), "alpha", "P00001")
        self.assertIsNone(info)
        self.assertIn("UNLOCALIZED", reason)

    def test_peptide_does_not_bridge_a_missing_numbered_residue(self):
        from Bio.PDB import Residue
        residues = [Residue.Residue((" ", position, " "), name, " ")
                    for position, name in ((1, "ALA"), (2, "LYS"), (4, "LYS"), (5, "ALA"), (6, "ALA"))]
        other = [Residue.Residue((" ", i, " "), "GLY", " ") for i in range(1, 6)]
        information, reason = self.mapper.selected_site(raw_row(), "alpha", "P00001")
        self.assertFalse(reason)
        mapped, reason = self.mapper.map_to_chain(information, "A", {"A": ("AKKAA", residues), "B": ("GGGGG", other)})
        self.assertIsNone(mapped, "Matching only the linked residue number hid a gap inside the peptide")
        self.assertTrue(reason)

    def test_same_sites_different_endpoint_modifications_stay_separate(self):
        modified = json.dumps([{"location": "2", "residues": "K", "monoisotopicMassDelta": "42.010565"}])
        rows = [raw_row(), raw_row(scan_id="2", alpha_modifications=modified)]
        with tempfile.TemporaryDirectory() as temporary:
            (observations, unique, state, matched), calls, _ = run_synthetic_mapping(self.mapper, Path(temporary), rows)
            self.assertEqual(state["state"], "COMPLETED", state)
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(observations), 2)
            self.assertEqual(len(unique), 2, "Modified and unmodified lysine states collapsed")
            self.assertEqual(len({r["pair_context_id"] for r in unique}), 2)
            self.assertEqual(sum(int(r["evidence_rows"]) for r in unique), 2)

    def test_swapped_alpha_beta_keeps_the_same_endpoint_context(self):
        first = raw_row()
        reverse = raw_row(scan_id="2", alpha_peptide=first["beta_peptide"],
                          alpha_positions=first["beta_positions"], alpha_link_sites=first["beta_link_sites"],
                          beta_peptide=first["alpha_peptide"], beta_positions=first["alpha_positions"],
                          beta_link_sites=first["alpha_link_sites"])
        with tempfile.TemporaryDirectory() as temporary:
            (observations, unique, state, matched), calls, _ = run_synthetic_mapping(self.mapper, Path(temporary), [first, reverse])
            self.assertEqual(state["state"], "COMPLETED", state)
            self.assertEqual(len(unique), 1)
            self.assertEqual(int(unique[0]["evidence_rows"]), 2)
            self.assertEqual(int(unique[0]["supporting_spectra"]), 2)

    def test_modified_endpoint_follows_protein_when_peptides_are_reversed(self):
        modified = json.dumps([{"location": "2", "residues": "K", "monoisotopicMassDelta": "42.010565"}])
        first = raw_row(alpha_modifications=modified)
        reverse = raw_row(scan_id="2", alpha_peptide=first["beta_peptide"],
                          alpha_positions=first["beta_positions"], alpha_link_sites=first["beta_link_sites"],
                          alpha_modifications=first["beta_modifications"], beta_peptide=first["alpha_peptide"],
                          beta_positions=first["alpha_positions"], beta_link_sites=first["alpha_link_sites"],
                          beta_modifications=first["alpha_modifications"])
        with tempfile.TemporaryDirectory() as temporary:
            (observations, unique, state, matched), calls, _ = run_synthetic_mapping(self.mapper, Path(temporary), [first, reverse])
            self.assertEqual(state["state"], "COMPLETED", state)
            self.assertEqual(len(unique), 1)
            self.assertIn("42.010565", unique[0]["endpoint_a_modifications"])
            self.assertEqual(json.loads(unique[0]["endpoint_b_modifications"]), [])

    def test_remote_peptide_modification_is_not_assigned_to_linked_lysine(self):
        # Location 3 is a different residue from the linked K at position 2.
        modification = json.dumps([{"location": "3", "residues": "K", "monoisotopicMassDelta": "42.010565"}])
        with tempfile.TemporaryDirectory() as temporary:
            (observations, unique, state, matched), calls, _ = run_synthetic_mapping(
                self.mapper, Path(temporary), [raw_row(alpha_modifications=modification)])
            self.assertEqual(state["state"], "COMPLETED", state)
            self.assertEqual(json.loads(unique[0]["endpoint_a_modifications"]), [])

    def test_unknown_chemistry_is_retained_and_sent_for_distance(self):
        with tempfile.TemporaryDirectory() as temporary:
            (observations, unique, state, matched), calls, _ = run_synthetic_mapping(
                self.mapper, Path(temporary), [raw_row()], {"1": "taxid_9606/NEW_UNKNOWN_REAGENT"})
            self.assertEqual(state["state"], "COMPLETED", state)
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(unique), 1)
            self.assertIn("NEW_UNKNOWN_REAGENT", unique[0]["search_group"])

    def test_engine_missing_distance_is_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            (observations, unique, state, matched), calls, _ = run_synthetic_mapping(
                self.mapper, Path(temporary), [raw_row(alpha_link_sites="3")])
            self.assertEqual(len(unique), 1)
            self.assertEqual(unique[0]["sasd_A"], "")
            self.assertEqual(unique[0]["xp"], "")


class IndependentPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from xp_policy_v33 import Policy
        cls.policy = Policy()

    def evaluate(self, **changes):
        return self.policy.evaluate(row(**changes), {"coordinate_check": "EUCLIDEAN_RECHECK_PASSED", "euclidean_recomputed_A": 10.0})

    def assert_no_primary(self, result):
        self.assertIn("xp_primary", result)
        self.assertIsNone(number(result["xp_primary"]), result)

    def test_unknown_reagent_retains_labeled_geometry_but_never_primary(self):
        result = self.evaluate(chemistry="unknown_new_reagent", search_group="taxid_9606/unknown_new_reagent")
        self.assert_no_primary(result)
        self.assertIsNone(number(result.get("xp_exploratory")))
        self.assertAlmostEqual(number(result["reference_geometry_score"]),
                               statistics.NormalDist(18.62, math.sqrt(35.94)).pdf(18.62), places=12)

    def test_conflicting_reagents_cannot_gain_primary_score(self):
        self.assert_no_primary(self.evaluate(chemistry="dss", search_group="taxid_9606/edc"))

    def test_noncovalent_search_does_not_become_covalent_evidence(self):
        result = self.evaluate(chemistry="NonCovalentBound", search_group="taxid_9606/NonCovalentBound")
        self.assert_no_primary(result)
        self.assertIsNone(number(result.get("xp_exploratory")))

    def test_all_400_ordered_sidechain_labels_have_explicit_chemistry_status(self):
        from chemistry_rules import assess
        supported = []
        for first in "ACDEFGHIKLMNPQRSTVWY":
            for second in "ACDEFGHIKLMNPQRSTVWY":
                result = assess(row(protein_a_aa=first, protein_b_aa=second))
                self.assertIn(result["chemistry_status"], {"SUPPORTED", "CONDITIONAL", "CONFLICTING", "UNRESOLVED"})
                if result["chemistry_status"] == "SUPPORTED":
                    supported.append((first, second))
        self.assertEqual(supported, [("K", "K")], "The DSS rule authorized an unsupported canonical sidechain pair")

    def test_search_configuration_is_not_experimental_reagent_confirmation(self):
        result = self.evaluate(chemistry_evidence_status="", chemistry_evidence="")
        self.assert_no_primary(result)
        self.assertGreater(number(result["xp_exploratory"]), 0)
        self.assertNotEqual(result.get("validation_status"), "VALIDATED")

    def test_dss_internal_valine_not_made_reactive_by_short_distance(self):
        self.assert_no_primary(self.evaluate(protein_a_aa="V", protein_a_site="45", pdb_site_a="45"))

    def test_dss_internal_methionine_is_not_inferred_as_n_terminus(self):
        self.assert_no_primary(self.evaluate(protein_a_aa="M", protein_a_site="45", pdb_site_a="45"))

    def test_blocked_lysine_cannot_gain_primary(self):
        mods = json.dumps([{"location": "2", "residues": "K", "monoisotopicMassDelta": "42.010565"}])
        self.assert_no_primary(self.evaluate(endpoint_a_modifications=mods))

    def test_unlocalized_acetylation_is_uncertainty_not_confirmed_chemical_conflict(self):
        from chemistry_rules import assess
        mods = json.dumps([{"location": "?", "residues": "K", "monoisotopicMassDelta": "42.010565",
                            "endpoint_localization": "UNRESOLVED"}])
        decision = assess(row(endpoint_a_modifications=mods))
        self.assertEqual(decision["chemistry_status"], "UNRESOLVED")
        self.assertEqual(decision["endpoint_status"], "UNRESOLVED_ENDPOINT")
        self.assert_no_primary(self.evaluate(endpoint_a_modifications=mods))

    def test_maleimide_blocked_cysteine_cannot_gain_primary(self):
        mods = json.dumps([{"location": "2", "residues": "C", "monoisotopicMassDelta": "57.02146"}])
        self.assert_no_primary(self.evaluate(chemistry="bmoe", search_group="taxid_9606/bmoe",
                                            protein_a_aa="C", protein_b_aa="C", endpoint_a_modifications=mods))

    def test_missing_and_nonfinite_distances_never_become_numeric_zero(self):
        for distance in ("", "-1", "nan", "inf"):
            with self.subTest(distance=distance):
                result = self.evaluate(sasd_A=distance, status="NO_SASD_RETURNED" if not distance else "SCORED")
                for field in SCORES:
                    self.assertIsNone(number(result.get(field)), (distance, field, result))

    def test_sasd_shorter_than_straight_line_is_not_promoted(self):
        result = self.evaluate(sasd_A="5", euclidean_A="10")
        for field in SCORES:
            self.assertIsNone(number(result.get(field)), (field, result))

    def test_mapping_failure_never_becomes_geometry_score(self):
        result = self.evaluate(status="UNIPROT_TO_CIF_NUMBERING_MISMATCH")
        for field in SCORES:
            self.assertIsNone(number(result.get(field)), (field, result))

    def test_common_reference_is_same_across_unknown_residue_pairs(self):
        values = []
        for aa1, aa2 in (("K", "K"), ("D", "E"), ("V", "L"), ("C", "C")):
            result = self.evaluate(chemistry="unknown_new_reagent", search_group="taxid_9606/unknown_new_reagent",
                                   protein_a_aa=aa1, protein_b_aa=aa2)
            values.append(number(result["reference_geometry_score"]))
            self.assert_no_primary(result)
        self.assertTrue(all(value == values[0] for value in values), values)

    def test_original_variance_and_cutoff_are_not_misinterpreted(self):
        at_peak = self.evaluate()
        expected = statistics.NormalDist(18.62, math.sqrt(35.94)).pdf(18.62)
        self.assertAlmostEqual(number(at_peak["xp_primary"]), expected, places=12)
        at_cutoff = self.evaluate(sasd_A="33")
        above = self.evaluate(sasd_A="33.0000001")
        self.assertGreater(number(at_cutoff["xp_primary"]), 0)
        self.assertEqual(number(above["xp_primary"]), 0)
        if "mnxl2016_contribution" in above:
            self.assertEqual(number(above["mnxl2016_contribution"]), -0.1)


class IndependentAnalyzerTests(unittest.TestCase):
    def test_complete_intake_retains_all_source_rows_and_distinct_contexts(self):
        from analyze_v33 import analyze
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = make_complete_intake(root)
            input_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source.rglob("*") if path.is_file()}
            output = root / "results"
            summary = analyze(source, output, "PXD999999")
            self.assertTrue(summary["input_accounting_ok"])
            observations = csv_read(output / "xp_observations.csv")
            unique = csv_read(output / "xp_unique_pairs.csv")
            unmatched = csv_read(output / "unmatched_observations.csv")
            self.assertEqual((len(observations), len(unique), len(unmatched)), (6, 4, 1))
            self.assertEqual({int(r["source_row_index"]) for r in observations + unmatched}, set(range(1, 8)))
            self.assertEqual(summary["numeric_xp_pairs"], 0)
            self.assertEqual(summary["exploratory_xp_pairs"], 1)
            self.assertEqual(summary["reference_geometry_pairs"], 3)
            self.assertIsNone(summary["scientifically_validated_xl_count"])
            self.assertEqual(len({r["pair_context_id"] for r in unique}), 4)
            for item in observations + unique:
                for field in SCORES + ("xp",):
                    self.assertNotEqual(number(item.get(field)), 9999, "Unverified legacy engine XP leaked into scoring")
            missing = next(r for r in unique if r["pdb_site_a"] == "3")
            self.assertTrue(all(number(missing.get(field)) is None for field in SCORES))
            unknown = next(r for r in unique if "NEW_UNKNOWN_REAGENT" in r["search_group"])
            self.assertIsNone(number(unknown["xp_primary"]))
            self.assertIsNone(number(unknown["xp_exploratory"]))
            self.assertGreater(number(unknown["reference_geometry_score"]), 0)
            conflict = next(r for r in unique if r["chemistry_status"] == "CONFLICTING")
            self.assertIsNone(number(conflict["xp_primary"]))
            self.assertEqual(conflict["discovery_shortlist_eligible"], "False")
            review = csv_read(output / "novelty_review_queue.csv")
            self.assertEqual(len(review), 6)
            for path, checksum in input_hashes.items():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), checksum, str(path))

    def test_old_filtered_intake_cannot_masquerade_as_full_v33_rerun(self):
        from analyze_v33 import analyze
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = make_complete_intake(root)
            summary = json.loads((source / "run_summary.json").read_text())
            summary["intake_version"] = "3.2.0"
            (source / "run_summary.json").write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError, "Old or filtered"):
                analyze(source, root / "results", "PXD999999")
            self.assertFalse((root / "results").exists())

    def test_lost_unlocalized_observation_fails_accounting(self):
        from analyze_v33 import analyze
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = make_complete_intake(root)
            observations = csv_read(source / "xp_observations.csv")
            observations = [r for r in observations if r["scan_id"] != "5"]
            csv_write(source / "xp_observations.csv", observations)
            summary = json.loads((source / "run_summary.json").read_text())
            summary["matched_model_observation_rows"] = len(observations)
            (source / "run_summary.json").write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError, "lost or invented"):
                analyze(source, root / "results", "PXD999999")

    def test_context_tampering_is_detected_before_rescoring(self):
        from analyze_v33 import analyze
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = make_complete_intake(root)
            unique = csv_read(source / "xp_unique_pairs.csv")
            unique[0]["chemistry"] = "edc"
            csv_write(source / "xp_unique_pairs.csv", unique)
            with self.assertRaisesRegex(ValueError, "reaction-context"):
                analyze(source, root / "results", "PXD999999")

    def test_descriptive_sample_sd_is_not_profile_sigma_and_not_spectrum_weighted(self):
        from analyze_v33 import score_statistics
        rows = [row(xp_primary=value, xp_exploratory="", reference_geometry_score="",
                    linker_normalized="DSS", xp_primary_profile_id="SYNTHETIC_TEST_PROFILE",
                    xp_primary_sigma_A="999", supporting_spectra=str(1000 if index == 0 else 1))
                for index, value in enumerate((0.01, 0.03, 0.05))]
        result = score_statistics(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["n_pair_contexts"], 3)
        self.assertAlmostEqual(result[0]["mean"], 0.03)
        self.assertAlmostEqual(result[0]["sample_sd"], statistics.stdev((0.01, 0.03, 0.05)))
        self.assertIn("not model sigma", result[0]["sd_definition"])


class IndependentDistanceAdapterTests(unittest.TestCase):
    def test_distance_adapter_never_calls_legacy_xp_equation(self):
        from extended_distance_engine import write_results
        first = ((2, "A", "LYS"), (2, "B", "LYS"))
        second = ((3, "A", "VAL"), (3, "B", "TYR"))

        def forbidden_legacy_score(*args, **kwargs):
            self.fail("Legacy XP equation was called by distance-only adapter")

        legacy = types.SimpleNamespace(pair_key=lambda pair: tuple(sorted(pair)), score_xl=forbidden_legacy_score)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic_engine_output.csv"
            counts = write_results(legacy, path, "SYNTHETIC ONLY", [first, second], {legacy.pair_key(first): (18.62, 10.0)})
            rows = csv_read(path)
            self.assertEqual(counts, {"DISTANCE_ONLY": 1, "NO_SASD_RETURNED": 1})
            self.assertTrue(all(item["xp"] == "" for item in rows))
            self.assertEqual(rows[0]["status"], "DISTANCE_ONLY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
