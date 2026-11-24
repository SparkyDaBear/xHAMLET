"""Independent Gaussian checks and negative policy fixtures; synthetic only."""
import copy
import itertools
import json
import math
from pathlib import Path
import statistics
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from xp_policy_v33 import Policy, METRIC, FIELDS

DIAG = {"coordinate_check": "EUCLIDEAN_RECHECK_PASSED", "euclidean_recomputed_A": 10.0,
        "distance_protocol": "SYNTHETIC_TEST_GEOMETRY"}


def row(a="K", b="K", chemistry="DSBU", **kwargs):
    out = {"protein_a": "SYNTHETIC_A", "protein_b": "SYNTHETIC_B",
           "protein_a_aa": a, "protein_b_aa": b, "protein_a_site": "10", "protein_b_site": "20",
           "chain_a": "A", "chain_b": "B", "pdb_site_a": "10", "pdb_site_b": "20",
           "chemistry": chemistry, "search_group": "taxid_9606/" + chemistry,
           "chemistry_evidence_status": "EXPERIMENT_REAGENT_CONFIRMED",
           "chemistry_evidence": "SYNTHETIC TEST DECLARATION, not real experimental evidence",
           "status": "SCORED", "sasd_A": 20.0, "euclidean_A": 10.0, "distance_metric": METRIC}
    out.update(kwargs)
    return out


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.p = Policy()

    def assert_unscored(self, result):
        for key in ("xp", "xp_primary", "xp_exploratory", "reference_geometry_score"):
            self.assertEqual(result[key], "", key)

    def test_dsbu_kk_literal_independent_normal_density(self):
        out = self.p.evaluate(row(sasd_A=19.7), DIAG)
        self.assertAlmostEqual(out["xp_primary"], statistics.NormalDist(19.7, 6.4).pdf(19.7), places=15)
        self.assertEqual(out["xp"], out["xp_primary"])
        self.assertEqual(out["xp_exploratory"], "")
        self.assertEqual(out["validation_status"], "REQUIRES_EXPERIMENTAL_VALIDATION")

    def test_dss_bs3_use_published_variance_not_sd(self):
        for reagent in ("DSS", "BS3"):
            out = self.p.evaluate(row(chemistry=reagent, sasd_A=18.62), DIAG)
            self.assertAlmostEqual(out["xp_primary"], statistics.NormalDist(18.62, math.sqrt(35.94)).pdf(18.62), places=15)
            self.assertEqual(out["scoring_convention"], "XP_ZERO_CUTOFF_ADAPTATION_OF_MNXL2016")
            self.assertEqual(out["mnxl2016_contribution"], out["xp_primary"])

    def test_original_negative_penalty_not_confused_with_xp_zero(self):
        out = self.p.evaluate(row(chemistry="DSS", sasd_A=40), DIAG)
        self.assertEqual(out["xp_primary"], 0.0)
        self.assertEqual(out["mnxl2016_contribution"], -0.1)
        self.assertEqual(out["mnxl2016_violation_count"], 1)
        self.assertEqual(out["mnxl2016_violation_excess_A"], 7.0)
        self.assertEqual(out["mnxl2016_nonaccessible_count"], 0)

    def test_mnxl_violation_boundary_has_known_zero(self):
        out = self.p.evaluate(row(chemistry="BS3", sasd_A=33), DIAG)
        self.assertEqual(out["mnxl2016_violation_count"], 0)
        self.assertEqual(out["mnxl2016_violation_excess_A"], 0.0)
        self.assertEqual(out["mnxl2016_nonaccessible_count"], 0)
        self.assertGreater(out["mnxl2016_contribution"], 0)

    def test_explicit_backend_nonaccessible_penalty_is_separate_from_xp(self):
        for reason in ("ACCESSIBILITY_FILTER_REJECTED", "BACKEND_LOG_REPORTED_NONACCESSIBLE"):
            out = self.p.evaluate(row(chemistry="DSS", sasd_A="", status="NO_SASD_RETURNED"), {**DIAG, "reason": reason})
            self.assert_unscored(out)
            self.assertEqual(out["mnxl2016_contribution"], -0.1)
            self.assertEqual(out["mnxl2016_nonaccessible_count"], 1)
            self.assertEqual(out["mnxl2016_violation_count"], "")
            self.assertEqual(out["mnxl2016_violation_excess_A"], "")
            self.assertIn("BACKEND_NONACCESSIBILITY", out["mnxl2016_status"])

    def test_missing_finite_search_path_is_not_mnxl_nonaccessibility(self):
        for reason in ("NO_SASD_WITH_FINITE_SEARCH_LIMIT", "SURFACE_VOXEL_OR_PAIR_FILTER_REJECTED", ""):
            out = self.p.evaluate(row(chemistry="BS3", sasd_A="", status="NO_SASD_RETURNED"), {**DIAG, "reason": reason})
            self.assert_unscored(out)
            for key in ("mnxl2016_contribution", "mnxl2016_nonaccessible_count", "mnxl2016_violation_count", "mnxl2016_violation_excess_A"):
                self.assertEqual(out[key], "", key)

    def test_nonaccessibility_penalty_requires_coordinate_qc(self):
        for diag in ({"reason": "ACCESSIBILITY_FILTER_REJECTED"},
                     {**DIAG, "reason": "ACCESSIBILITY_FILTER_REJECTED", "coordinate_check": "SOURCE_HASH_MISMATCH"}):
            out = self.p.evaluate(row(chemistry="DSS", sasd_A="", status="NO_SASD_RETURNED"), diag)
            self.assert_unscored(out)
            self.assertEqual(out["mnxl2016_contribution"], "")
            self.assertEqual(out["mnxl2016_nonaccessible_count"], "")

    def test_nonaccessibility_penalty_requires_confirmed_original_chemistry_scope(self):
        for r in (row(chemistry="DSBU", sasd_A=""),
                  row(chemistry="DSS", sasd_A="", chemistry_evidence_status="SEARCH_CONFIGURATION_ONLY"),
                  row("K", "S", "DSS", sasd_A="")):
            out = self.p.evaluate(r, {**DIAG, "reason": "ACCESSIBILITY_FILTER_REJECTED"})
            self.assertEqual(out["mnxl2016_contribution"], "")
            self.assertEqual(out["mnxl2016_nonaccessible_count"], "")

    def test_nonfinite_distance_never_becomes_nonaccessibility_penalty(self):
        for distance in (float("nan"), float("inf"), "not-a-distance", -2):
            out = self.p.evaluate(row(chemistry="DSS", sasd_A=distance), {**DIAG, "reason": "ACCESSIBILITY_FILTER_REJECTED"})
            self.assert_unscored(out)
            self.assertEqual(out["mnxl2016_contribution"], "")

    def test_search_config_only_keeps_known_model_exploratory(self):
        r = row(chemistry_evidence_status="", chemistry_evidence="")
        out = self.p.evaluate(r, DIAG)
        self.assertEqual(out["xp_primary"], "")
        self.assertGreater(out["xp_exploratory"], 0)
        self.assertEqual(out["chemistry_evidence_status"], "SEARCH_CONFIG_ASSUMPTION")
        self.assertIn("LITERAL_PUBLISHED", out["xp_exploratory_parameter_basis"])

    def test_confirmed_word_alone_is_not_evidence(self):
        out = self.p.evaluate(row(chemistry_evidence=""), DIAG)
        self.assertEqual(out["xp_primary"], "")
        self.assertEqual(out["chemistry_evidence_status"], "CONFIRMATION_EVIDENCE_MISSING")

    def test_nonkk_published_and_generalized_are_exploratory(self):
        literal = self.p.evaluate(row("K", "S", sasd_A=15.9), DIAG)
        self.assertEqual(literal["xp"], "")
        self.assertAlmostEqual(literal["xp_exploratory"], statistics.NormalDist(15.9, 5.1).pdf(15.9), places=15)
        generalized = self.p.evaluate(row("Y", "Y"), DIAG)
        self.assertEqual(generalized["xp_primary"], "")
        self.assertGreater(generalized["xp_exploratory"], 0)
        self.assertIn("HEURISTIC", generalized["xp_exploratory_parameter_basis"])

    def test_dsso_kk_is_generalized_not_published_calibration(self):
        out = self.p.evaluate(row(chemistry="DSSO"), DIAG)
        self.assertEqual(out["xp_primary"], "")
        # Manufacturer MAN0016303 Rev. B.0 page 1 specifies 10.3 A,
        # distinct from the legacy 10.1 A convention. Transfer stays exploratory.
        self.assertEqual(self.p.profiles["generalized_source_model"]["spacer_length_A"]["DSSO"], 10.3)
        self.assertAlmostEqual(out["xp_exploratory_mu_A"], 17.5)
        self.assertAlmostEqual(out["xp_exploratory_sigma_A"], 16.9 / 3)
        self.assertAlmostEqual(out["xp_exploratory_cutoff_A"], 31.9)
        self.assertIn("HEURISTIC", out["xp_exploratory_parameter_basis"])

    def test_internal_methionine_receives_diagnostic_not_xp(self):
        out = self.p.evaluate(row("M", "M"), DIAG)
        self.assertEqual(out["xp_primary"], "")
        self.assertEqual(out["xp_exploratory"], "")
        self.assertGreater(out["reference_geometry_score"], 0)
        self.assertFalse(out["discovery_shortlist_eligible"])

    def test_explicit_m_terminal_is_exploratory_with_unverified_convention(self):
        out = self.p.evaluate(row("M", "T", protein_a_site="1", endpoint_a_kind="PROTEIN_NTERM",
                                 endpoint_a_blocked=False, endpoint_a_evidence="Synthetic explicit terminal localization"), DIAG)
        self.assertEqual(out["xp_primary"], "")
        self.assertGreater(out["xp_exploratory"], 0)
        self.assertIn("AUTHOR_CONFIRMATION", out["xp_exploratory_parameter_basis"])

    def test_lysine_terminal_does_not_borrow_sidechain_length(self):
        out = self.p.evaluate(row(endpoint_a_kind="PROTEIN_NTERM", endpoint_a_blocked=False,
                                 endpoint_a_evidence="Synthetic explicit terminal evidence"), DIAG)
        self.assertEqual(out["xp_primary"], "")
        self.assertEqual(out["xp_exploratory"], "")
        self.assertIn("TERMINAL_ENDPOINT_PARAMETER", out["parameter_status"])

    def test_edc_valid_vs_conflicting_both_retained_with_separate_states(self):
        good = self.p.evaluate(row("D", "K", "EDC"), DIAG)
        bad = self.p.evaluate(row("K", "K", "EDC"), DIAG)
        self.assertEqual(good["chemistry_status"], "SUPPORTED")
        self.assertEqual(bad["chemistry_status"], "CONFLICTING")
        for out in (good, bad):
            self.assertEqual(out["xp_primary"], "")
            self.assertEqual(out["xp_exploratory"], "")
            self.assertGreater(out["reference_geometry_score"], 0)
        self.assertFalse(bad["discovery_shortlist_eligible"])

    def test_unknown_new_pairs_have_explicit_counterfactual_geometry_only(self):
        out = self.p.evaluate(row("W", "F", "NEW_REAGENT"), DIAG)
        self.assertEqual(out["xp"], "")
        self.assertEqual(out["xp_exploratory"], "")
        self.assertAlmostEqual(out["reference_geometry_score"], statistics.NormalDist(18.62, math.sqrt(35.94)).pdf(20), places=15)
        self.assertIn("NOT_XP", out["reference_geometry_interpretation"])

    def test_blocked_and_ambiguous_modifications_never_primary(self):
        for mod in ("Acetyl (K)", "unknown modification"):
            out = self.p.evaluate(row(endpoint_a_modifications=mod), DIAG)
            self.assertEqual(out["xp_primary"], "")
            self.assertEqual(out["xp_exploratory"], "")

    def test_missing_negative_nonfinite_distance_never_zero(self):
        for distance in ("", None, -1, float("nan"), float("inf")):
            self.assert_unscored(self.p.evaluate(row(sasd_A=distance), DIAG))

    def test_mapping_or_identical_physical_endpoint_rejected(self):
        for change in ({"protein_a_site": "-1"}, {"pdb_site_a": ""},
                       {"status": "UNIPROT_TO_CIF_NUMBERING_MISMATCH"},
                       {"chain_b": "A", "pdb_site_b": "10"}):
            self.assert_unscored(self.p.evaluate(row(**change), DIAG))

    def test_same_protein_position_on_different_chains_is_not_same_endpoint(self):
        r = row(protein_b="SYNTHETIC_A", protein_b_site="10", pdb_site_b="10")
        self.assertGreater(self.p.evaluate(r, DIAG)["xp_primary"], 0)

    def test_source_and_coordinate_geometry_flags_are_not_cleared(self):
        self.assert_unscored(self.p.evaluate(row(geometry_flag="MANUAL_REVIEW"), DIAG))
        self.assert_unscored(self.p.evaluate(row(), {**DIAG, "coordinate_check": "EUCLIDEAN_MISMATCH"}))
        self.assert_unscored(self.p.evaluate(row(), {}))
        self.assert_unscored(self.p.evaluate(row(sasd_A=9), DIAG))

    def test_no_uncompleted_or_checkonly_scores(self):
        for state in ("ENGINE_FAILED", "MAPPED_CHECK_ONLY", "MAPPED_FOR_XP"):
            self.assert_unscored(self.p.evaluate(row(status=state), DIAG))

    def test_no_euclidean_as_sasd_substitution(self):
        self.assert_unscored(self.p.evaluate(row(distance_metric="CA_EUCLIDEAN"), DIAG))

    def test_cutoff_zero_legitimate_only_after_all_gates(self):
        self.assertGreater(self.p.evaluate(row(sasd_A=34.1), DIAG)["xp_primary"], 0)
        self.assertEqual(self.p.evaluate(row(sasd_A=math.nextafter(34.1, math.inf)), DIAG)["xp_primary"], 0)

    def test_discovery_geometry_not_blocked_by_unknown_parameters(self):
        for a, b in itertools.combinations_with_replacement("ACDEFGHIKLMNPQRSTVWY", 2):
            self.assertTrue(self.p.decision(row(a, b, "NEW_REAGENT"))["distance_eligible"])
        self.assertFalse(Policy(mode="strict").decision(row("D", "K", "EDC"))["distance_eligible"])

    def test_fields_serializable_and_input_unchanged(self):
        r = row()
        before = copy.deepcopy(r)
        out = self.p.evaluate(r, DIAG)
        self.assertEqual(r, before)
        self.assertEqual(len(FIELDS), len(set(FIELDS)))
        json.dumps(out, allow_nan=False)

    def test_snapshot_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "snapshot"
            self.p.snapshot(target)
            other = Policy(target)
            self.assertEqual(self.p.evaluate(row(), DIAG), other.evaluate(row(), DIAG))
            with self.assertRaises(FileExistsError):
                self.p.snapshot(target)


if __name__ == "__main__":
    unittest.main()
