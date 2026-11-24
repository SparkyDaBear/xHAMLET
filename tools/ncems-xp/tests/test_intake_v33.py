"""Regression checks for source endpoint declarations and reagent-evidence types."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from intake_v33 import attach_endpoint, load_experimental_context
from xp_policy_v33 import Policy


class IntakeDeclarationTests(unittest.TestCase):
    def item(self, **raw):
        return {'alpha_modifications': '[]', 'raw_observation_json': json.dumps(raw)}

    def info(self, site=2):
        return {'peptide': 'AKKA', 'peptide_link_pos': site, 'protein_site': site, 'site_aa': 'K'}

    def test_missing_kind_remains_missing(self):
        item = self.item()
        attach_endpoint(item, 'a', 'alpha', self.info())
        self.assertEqual(item['endpoint_a_kind'], '')
        self.assertEqual(item['endpoint_a_annotation_status'], 'ENDPOINT_KIND_NOT_REPORTED')

    def test_nterminal_internal_position_rejected(self):
        item = self.item(alpha_endpoint_kind='PEPTIDE_NTERM')
        attach_endpoint(item, 'a', 'alpha', self.info())
        self.assertEqual(item['endpoint_a_kind'], 'UNRESOLVED_TERMINAL_ASSIGNMENT')
        self.assertEqual(item['endpoint_a_reported_kind'], 'PEPTIDE_NTERM')

    def test_cterminal_internal_position_rejected(self):
        item = self.item(alpha_endpoint_kind='PROTEIN_CTERM')
        attach_endpoint(item, 'a', 'alpha', self.info())
        self.assertEqual(item['endpoint_a_kind'], 'UNRESOLVED_TERMINAL_ASSIGNMENT')

    def test_valid_terminal_position_retains_declaration(self):
        item = self.item(alpha_endpoint_kind='PROTEIN_NTERM')
        attach_endpoint(item, 'a', 'alpha', self.info(1))
        self.assertEqual(item['endpoint_a_kind'], 'PROTEIN_NTERM')

    def test_nonstrings_cannot_confirm_reagent(self):
        for bad in (True, 1, {}, [], {'source': 'synthetic'}):
            with self.subTest(value=bad), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'context.json'
                path.write_text(json.dumps({'schema': 'NCEMS_EXPERIMENTAL_CONTEXT_V1', 'entries': [{
                    'pxd': 'PXD999999', 'search_group': '9606/dss', 'chemistry': 'DSS',
                    'chemistry_evidence_status': 'EXPERIMENT_REAGENT_CONFIRMED', 'chemistry_evidence': bad}]}))
                with self.assertRaises(ValueError):
                    load_experimental_context(str(path))

    def test_valid_context_and_duplicate_rejection(self):
        item = {'pxd': 'PXD999999', 'search_group': '9606/dss', 'chemistry': 'DSS',
                'chemistry_evidence_status': 'EXPERIMENT_REAGENT_CONFIRMED',
                'chemistry_evidence': 'SYNTHETIC DECLARATION FOR TEST ONLY'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'valid.json'
            path.write_text(json.dumps({'schema': 'NCEMS_EXPERIMENTAL_CONTEXT_V1', 'entries': [item]}))
            self.assertEqual(load_experimental_context(str(path))[('PXD999999', '9606/dss')], item)
            second = Path(folder) / 'duplicates.json'
            second.write_text(json.dumps({'schema': 'NCEMS_EXPERIMENTAL_CONTEXT_V1', 'entries': [item, item]}))
            with self.assertRaises(ValueError):
                load_experimental_context(str(second))


if __name__ == '__main__':
    unittest.main()
