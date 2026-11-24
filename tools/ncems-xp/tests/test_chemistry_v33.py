"""Synthetic reaction-rule examples; not experimental identification validation."""
import itertools
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chemistry_rules import assess, endpoint, identify, load_rules


def row(a="K", b="K", chemistry="DSBU", **kwargs):
    out = {"protein_a_aa": a, "protein_b_aa": b,
           "protein_a_site": "10", "protein_b_site": "20",
           "chemistry": chemistry, "search_group": "taxid_9606/" + chemistry}
    out.update(kwargs)
    return out


class ReactionRulesTests(unittest.TestCase):
    def test_amine_pair_supported_with_documented_assumptions(self):
        r = assess(row())
        self.assertEqual(r["chemistry_status"], "SUPPORTED")
        self.assertIn("UNMODIFIED_REACTIVE_GROUP_ASSUMED", r["endpoint_assumptions"])
        self.assertEqual(r["validation_status"], "REQUIRES_EXPERIMENTAL_VALIDATION")

    def test_internal_methionine_is_not_terminal_amine(self):
        for pair in [("M", "M"), ("M", "K"), ("M", "T")]:
            self.assertEqual(assess(row(*pair))["chemistry_status"], "CONFLICTING")

    def test_first_methionine_is_not_inferred_to_be_free_terminus(self):
        r = assess(row("M", "T", protein_a_site="1"))
        self.assertEqual(r["chemistry_status"], "UNRESOLVED")
        self.assertIn("POSITION_ONE", r["chemistry_review_reason"])

    def test_terminal_kind_requires_evidence_and_free_group(self):
        r = row("M", "K", protein_a_site="1", endpoint_a_kind="PROTEIN_NTERM")
        self.assertEqual(assess(r)["chemistry_status"], "UNRESOLVED")
        r.update(endpoint_a_blocked=False, endpoint_a_evidence="Synthetic explicit terminal localization")
        self.assertEqual(assess(r)["chemistry_status"], "SUPPORTED")
        r["endpoint_a_blocked"] = True
        self.assertEqual(assess(r)["chemistry_status"], "CONFLICTING")

    def test_mature_nonmethionine_terminus_not_forced_to_position_one(self):
        r = row("A", "K", protein_a_site="26", endpoint_a_kind="PROTEIN_NTERM",
                endpoint_a_blocked=False, endpoint_a_evidence="Synthetic experimentally mapped cleavage")
        self.assertEqual(assess(r)["chemistry_status"], "SUPPORTED")

    def test_explicit_lysine_sidechain_at_position_one_is_distinct(self):
        r = row(protein_a_site="1")
        self.assertEqual(assess(r)["chemistry_status"], "UNRESOLVED")
        r["endpoint_a_kind"] = "SIDECHAIN_AMINE"
        self.assertEqual(assess(r)["chemistry_status"], "SUPPORTED")

    def test_acetylated_lysine_blocks_even_when_blocked_flag_is_false(self):
        r = row(endpoint_a_blocked=False, endpoint_a_modifications="Acetyl (K)")
        self.assertEqual(assess(r)["chemistry_status"], "CONFLICTING")
        r["endpoint_a_modifications"] = json.dumps([{"residues": "K", "monoisotopicMassDelta": "42.010565"}])
        self.assertEqual(assess(r)["chemistry_status"], "CONFLICTING")

    def test_unknown_modification_does_not_pass_as_unmodified(self):
        self.assertEqual(assess(row(endpoint_a_modifications="unknown adduct"))["chemistry_status"], "UNRESOLVED")

    def test_empty_reported_modifications_can_be_assessed(self):
        self.assertEqual(assess(row(endpoint_a_modifications="[]", endpoint_b_modifications=[]))["chemistry_status"], "SUPPORTED")

    def test_modification_scope_mismatch_requires_review(self):
        r = row(endpoint_a_modifications=[{"residues": "M", "monoisotopicMassDelta": "15.99491"}])
        self.assertEqual(assess(r)["chemistry_status"], "UNRESOLVED")

    def test_edc_has_directional_acid_amine_rule(self):
        x = assess(row("D", "K", "EDC"))
        y = assess(row("K", "E", "EDC"))
        self.assertEqual(x["chemistry_status"], "SUPPORTED")
        self.assertEqual(x["reaction_orientation"], "A_CARBOXYL_B_AMINE")
        self.assertEqual(y["reaction_orientation"], "A_AMINE_B_CARBOXYL")
        for a, b in (("K", "K"), ("D", "E"), ("C", "K")):
            self.assertEqual(assess(row(a, b, "EDC"))["chemistry_status"], "CONFLICTING")

    def test_edc_nhs_activation_alias_is_explicit(self):
        r = row("D", "K", "EDC", chemistry_raw="EDC + NHS")
        self.assertEqual(assess(r)["chemistry_status"], "SUPPORTED")
        self.assertEqual(assess(row(chemistry_raw="DSS + BS3"))["chemistry_status"], "UNRESOLVED")

    def test_c_terminal_carboxyl_requires_explicit_evidence(self):
        r = row("A", "K", "EDC", endpoint_a_kind="PROTEIN_CTERM",
                endpoint_a_blocked=False, endpoint_a_evidence="Synthetic terminal evidence")
        self.assertEqual(assess(r)["chemistry_status"], "SUPPORTED")
        r["endpoint_a_modifications"] = "Amidation"
        self.assertEqual(assess(r)["chemistry_status"], "CONFLICTING")

    def test_cysteine_thiol_free_vs_occupied(self):
        r = row("C", "C", "BMOE")
        self.assertEqual(assess(r)["chemistry_status"], "SUPPORTED")
        r["endpoint_a_modifications"] = '[{"location":"10","residues":"C","monoisotopicMassDelta":"57.02146"}]'
        self.assertEqual(assess(r)["chemistry_status"], "CONFLICTING")
        self.assertEqual(assess(row("K", "C", "BMOE"))["chemistry_status"], "CONFLICTING")

    def test_heterobifunctional_orientation(self):
        self.assertEqual(assess(row("K", "C", "SMCC"))["reaction_orientation"], "A_AMINE_B_THIOL")
        self.assertEqual(assess(row("C", "K", "SULFO-SMCC"))["reaction_orientation"], "A_THIOL_B_AMINE")

    def test_nhs_hydroxyls_are_conditional_not_primary_rules(self):
        for a, b in (("K", "S"), ("K", "T"), ("K", "Y"), ("S", "T"), ("Y", "Y")):
            self.assertEqual(assess(row(a, b))["chemistry_status"], "CONDITIONAL")

    def test_photo_capture_is_conditional_even_with_amine_anchor(self):
        r = assess(row("K", "W", "SULFO-SDA"))
        self.assertEqual(r["chemistry_status"], "CONDITIONAL")
        self.assertIn("ACTIVATION_REQUIRE_REVIEW", r["chemistry_review_reason"])

    def test_unknown_and_conflicting_identity_remain_separate(self):
        self.assertEqual(assess(row("A", "V", "NEW_REAGENT"))["chemistry_status"], "UNRESOLVED")
        r = row(chemistry="DSBU", search_group="taxid_9606/EDC")
        self.assertEqual(assess(r)["chemistry_status"], "CONFLICTING")

    def test_noncovalent_search_is_not_covalent_evidence(self):
        self.assertEqual(assess(row(chemistry="NonCovalentBound"))["chemistry_status"], "CONFLICTING")

    def test_incompatible_explicit_group_not_silently_coerced(self):
        self.assertEqual(assess(row("M", "K", endpoint_a_kind="SIDECHAIN_AMINE"))["chemistry_status"], "UNRESOLVED")

    def test_all_labels_receive_decision_without_forcing_eligibility(self):
        states = [assess(row(a, b))["chemistry_status"] for a, b in itertools.combinations_with_replacement("ACDEFGHIKLMNPQRSTVWY", 2)]
        self.assertEqual(len(states), 210)
        self.assertLess(states.count("SUPPORTED"), 210)
        self.assertGreater(states.count("CONFLICTING"), 0)


if __name__ == "__main__":
    unittest.main()
