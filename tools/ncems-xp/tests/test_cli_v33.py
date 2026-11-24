"""Real subprocess CLI integration with explicitly synthetic inputs/backend.

Runs run_v33 -> source_worker -> vendor -> jwalk_adapter -> analyze_v33.
The legacy engine bytes are hash-pinned. Only its NCLEdetector Jwalk imports are
substituted with a guarded fake backend. This does NOT validate real Jwalk paths.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "tests" / "fixtures_v33"
ENGINE = ROOT / "tests" / "fixtures" / "legacy_engine_source.py"
ENGINE_SHA = "4fb72ee71b6b050831a2bdf6a59e0629fd190074af1afa11e23661dba5ec3821"
FULL_PXDS = ("PXD998991", "PXD998992")
NO_MODEL_PXD = "PXD998993"
EMPTY_PXD = "PXD998994"


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def raw(scan="1", **changes):
    value = {"scan_id": scan, "charge": "3", "alpha_peptide": "AKKAA", "alpha_modifications": "[]",
             "alpha_positions": "P00001:1-5", "alpha_link_sites": "2", "beta_peptide": "GKKGG",
             "beta_modifications": "[]", "beta_positions": "P00002:1-5", "beta_link_sites": "2", "xi_score": "20"}
    value.update(changes)
    return value


def heavy_atom_cif(path):
    import numpy as np
    from Bio.PDB import MMCIFIO, StructureBuilder
    spec = importlib.util.spec_from_file_location("synthetic_legacy_atom_spec", ENGINE)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    builder = StructureBuilder.StructureBuilder()
    builder.init_structure("SYNTHETIC_NOT_PHYSICAL_MODEL")
    builder.init_model(0)
    serial = 0
    offsets = {"N": (-1, 0, 0), "CA": (0, 0, 0), "C": (1, 0, 0), "O": (1.2, 0.8, 0)}
    for chain, sequence, y in (("A", ("ALA", "LYS", "LYS", "ALA", "ALA"), 0),
                            ("B", ("GLY", "LYS", "LYS", "GLY", "GLY"), 10)):
        builder.init_chain(chain)
        builder.init_seg(" ")
        for position, name in enumerate(sequence, 1):
            builder.init_residue(name, " ", position, " ")
            names = ["N", "CA", "C", "O"] + legacy.SIDECHAIN[name].split()
            for index, atom in enumerate(names):
                serial += 1
                offset = offsets.get(atom, (0.1 * index, 0.2 * index, 0.1 * index))
                coord = np.array((3.8 * position + offset[0], y + offset[1], offset[2]))
                builder.init_atom(atom, coord, 20, 1, " ", f"{atom:>4}", serial, element=atom[0])
    writer = MMCIFIO()
    writer.set_structure(builder.get_structure())
    writer.save(str(path))


def fixture_tree(root):
    store = root / "synthetic_store"
    catalog = root / "synthetic_catalog.md"
    catalog_lines = ["# SYNTHETIC TEST FIXTURE ONLY; NO REAL DATA\n"]
    modification = json.dumps([{"location": "2", "residues": "K", "monoisotopicMassDelta": "42.010565"}])
    full_rows = [raw(), raw("2", alpha_modifications=modification), raw("3"), raw("4", alpha_link_sites="3"),
                 raw("5", alpha_link_sites="-1"), raw("6", alpha_positions="P00001-2:1-5"), raw("7")]
    for pxd in (*FULL_PXDS, NO_MODEL_PXD, EMPTY_PXD):
        rows = full_rows if pxd in FULL_PXDS else ([raw()] if pxd == NO_MODEL_PXD else [])
        search = store / pxd / "search_results"
        write_csv(search / "crosslinks.csv", rows, list(raw()))
        maps = [{"scan_id": r["scan_id"], "search_group": "taxid_9606/UNKNOWN_TEST_REAGENT" if r["scan_id"] == "3" else "taxid_9606/dss",
                 "search_stage": "crosslink", "run": "SYNTHETIC_ONLY", "scan": r["scan_id"]} for r in rows]
        write_csv(search / "scan_map.csv", maps, ["scan_id", "search_group", "search_stage", "run", "scan"])
        if pxd not in FULL_PXDS:
            continue
        job = "p00001__p00002__synthetic_cli"
        model = store / pxd / "af3_predictions" / job
        model.mkdir(parents=True)
        (model / "pair.json").write_text(json.dumps({"protein_a": "P00001", "protein_b": "P00002", "synthetic": True}))
        (model / "summary_confidences.json").write_text(json.dumps({"iptm": 0.8, "synthetic": True}))
        heavy_atom_cif(model / "model.cif")
        catalog_lines.append(f"### SYNTHETIC {pxd}\n**Dataset:** SYNTHETIC TEST ONLY. **ipTM:** 0.8.\n"
                             f"[AF3 model](../store/{pxd}/af3_predictions/{job}/model.cif)\n")
    catalog.write_text("\n".join(catalog_lines))
    return store, catalog


class SubprocessCLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parent = os.environ.get("NCEMS_CLI_QA_ROOT")
        if parent:
            Path(parent).mkdir(parents=True, exist_ok=True)
        cls.root = Path(tempfile.mkdtemp(prefix="SYNTHETIC_CLI_v33_", dir=parent))
        cls.preserve = bool(parent)
        cls.store, cls.catalog = fixture_tree(cls.root)
        cls.receipts = []
        cls.original = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in cls.store.rglob("*") if path.is_file()}
        cls.original[str(ENGINE)] = hashlib.sha256(ENGINE.read_bytes()).hexdigest()
        if cls.original[str(ENGINE)] != ENGINE_SHA:
            raise AssertionError("Legacy fixture does not match the pinned engine bytes")
        (cls.root / "READ_FIRST_SYNTHETIC_ONLY.txt").write_text(
            "These are fabricated technical test inputs and fake surface distances.\n"
            "The CLI, intake, adapter and analyzer ran as separate processes.\n"
            "No real NCLEdetector Jwalk paths or experimental data were validated.\n")

    @classmethod
    def tearDownClass(cls):
        same = all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected for path, expected in cls.original.items())
        record = {"created_utc": datetime.now(timezone.utc).isoformat(),
                  "scope": "SYNTHETIC SUBPROCESS INTEGRATION ONLY; FAKE SASD, NOT REAL JWALK",
                  "source_and_engine_unchanged": same, "receipts": cls.receipts,
                  "legacy_engine_sha256": ENGINE_SHA,
                  "backend_sha256": {str(p.relative_to(BACKEND)): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in BACKEND.rglob("*.py")}}
        (cls.root / "SYNTHETIC_CLI_VALIDATION.json").write_text(json.dumps(record, indent=2) + "\n")
        if not cls.preserve:
            shutil.rmtree(cls.root)
        if not same:
            raise AssertionError("Subprocess test mutated source inputs or pinned legacy engine")

    def launch(self, pxd, preflight=False, context=None):
        tag = pxd + ("_preflight" if preflight else "_context" if context else "_full")
        output = self.root / (tag + "_runs")
        trace = self.root / (tag + "_FAKE_BACKEND_TRACE.jsonl")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(BACKEND) + os.pathsep + env.get("PYTHONPATH", "")
        env["NCEMS_ALLOW_SYNTHETIC_BACKEND"] = "YES_FOR_TESTS"
        env["NCEMS_SYNTHETIC_BACKEND_TRACE"] = str(trace)
        command = [sys.executable, str(ROOT / "run_v33.py"), pxd, "--out-root", str(output),
                   "--engine", str(ENGINE), "--local-store", str(self.store), "--catalog", str(self.catalog),
                   "--ncpus", "1", "--model-timeout", "30"]
        if preflight:
            command.append("--preflight-only")
        if context:
            command += ["--experimental-context", str(context)]
        result = subprocess.run(command, env=env, cwd=self.root, capture_output=True, text=True, timeout=45)
        (self.root / (tag + "_CLI_LOG.txt")).write_text("SYNTHETIC BACKEND; NOT SCIENTIFIC OUTPUT\n" + result.stdout + result.stderr)
        receipt = {"pxd": pxd, "preflight": preflight, "returncode": result.returncode,
                   "command": command, "fake_backend_trace": str(trace)}
        self.receipts.append(receipt)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        paths = list(output.glob("*/results/run_summary.json"))
        self.assertEqual(len(paths), 1)
        receipt["result_summary"] = str(paths[0])
        summary = json.loads(paths[0].read_text())
        receipt["state"] = summary["state"]
        return summary, paths[0].parent, trace

    def test_confirmed_reagent_context_reaches_primary_without_validating_identification(self):
        context = self.root / 'SYNTHETIC_EXPERIMENT_CONTEXT.json'
        context.write_text(json.dumps({'schema': 'NCEMS_EXPERIMENTAL_CONTEXT_V1', 'entries': [{
            'pxd': FULL_PXDS[0], 'search_group': 'taxid_9606/dss', 'chemistry': 'DSS',
            'chemistry_evidence_status': 'EXPERIMENT_REAGENT_CONFIRMED',
            'chemistry_evidence': 'SYNTHETIC DECLARATION ONLY; NOT A REAL EXPERIMENT'}]}))
        summary, results, trace = self.launch(FULL_PXDS[0], context=context)
        self.assertEqual(summary['numeric_xp_pairs'], 1)
        self.assertEqual(summary['exploratory_xp_pairs'], 0)
        self.assertEqual(summary['reference_geometry_pairs'], 3)
        rows = read_csv(results / 'xp_unique_pairs.csv')
        primary = [r for r in rows if r['xp_primary'] != '']
        self.assertEqual(len(primary), 1)
        self.assertEqual(primary[0]['xp'], primary[0]['xp_primary'])
        self.assertEqual(primary[0]['validation_status'], 'REQUIRES_EXPERIMENTAL_VALIDATION')
        self.assertEqual(primary[0]['mnxl2016_violation_count'], '0')
        self.assertIsNone(summary['scientifically_validated_xl_count'])

    def test_two_pxd_full_subprocess_runs_preserve_chemistry_and_row_accounting(self):
        for pxd in FULL_PXDS:
            with self.subTest(pxd=pxd):
                summary, results, trace = self.launch(pxd)
                self.assertEqual(summary["pxd"], pxd)
                self.assertTrue(summary["input_accounting_ok"])
                self.assertEqual(summary["raw_search_result_rows"], 7)
                self.assertEqual(summary["model_observation_rows"], 6)
                self.assertEqual(summary["unmatched_source_rows"], 1)
                self.assertEqual(summary["unique_pair_contexts"], 4)
                self.assertEqual(summary["numeric_xp_pairs"], 0)
                self.assertEqual(summary["exploratory_xp_pairs"], 1)
                self.assertEqual(summary["reference_geometry_pairs"], 3)
                self.assertIsNone(summary["scientifically_validated_xl_count"])
                rows = read_csv(results / "xp_unique_pairs.csv")
                self.assertTrue(all(r["pxd"] == pxd for r in rows))
                self.assertTrue(all(r["xp"] == "" for r in rows))
                self.assertEqual(len({r["pair_context_id"] for r in rows}), 4)
                self.assertTrue(trace.exists(), "Fake backend was not reached through subprocess imports")
                events = [json.loads(line)["event"] for line in trace.read_text().splitlines()]
                self.assertIn("parallel_BFS_FAKE_FIXED_VALUES", events)
                model = next((results.parent / "distance_run" / "models").iterdir())
                self.assertTrue((model / "xp_engine" / "SYNTHETIC_FAKE_DISTANCES_NOT_JWALK.json").exists())
                self.assertTrue(all(r["xp"] == "" for r in read_csv(model / "xp_engine" / "xp_pairs.csv")))
                self.assertTrue((results / "NCEMS_XP_v33_results.zip").is_file())

    def test_no_model_dataset_keeps_unmatched_candidates(self):
        summary, results, trace = self.launch(NO_MODEL_PXD)
        self.assertEqual(summary["state"], "COMPLETE_NO_USABLE_GEOMETRY")
        self.assertEqual(summary["raw_search_result_rows"], 1)
        self.assertEqual(summary["unmatched_source_rows"], 1)
        self.assertEqual(summary["models_selected"], 0)
        self.assertEqual(len(read_csv(results / "novelty_review_queue.csv")), 1)
        self.assertFalse(trace.exists())

    def test_empty_dataset_keeps_zero_counts_without_scientific_success_claim(self):
        summary, results, trace = self.launch(EMPTY_PXD)
        self.assertEqual(summary["state"], "COMPLETE_NO_USABLE_GEOMETRY")
        self.assertEqual(summary["raw_search_result_rows"], 0)
        self.assertEqual(summary["unique_pair_contexts"], 0)
        self.assertTrue(summary["input_accounting_ok"])
        self.assertIsNone(summary["scientifically_validated_xl_count"])
        self.assertEqual(read_csv(results / "xp_observations.csv"), [])
        self.assertFalse(trace.exists())

    def test_preflight_maps_but_never_calls_fake_distance_backend(self):
        summary, results, trace = self.launch(FULL_PXDS[0], preflight=True)
        self.assertEqual(summary["state"], "PREFLIGHT_COMPLETE_NO_SCORING")
        self.assertEqual(summary["new_distances_calculated"], 0)
        self.assertEqual(summary["new_xp_calculated"], 0)
        self.assertEqual(summary["raw_search_result_rows"], 7)
        self.assertFalse(trace.exists())
        unique = read_csv(results / "xp_unique_pairs.csv")
        self.assertEqual(len(unique), 4)
        self.assertTrue(all(r["sasd_A"] == "" and r["xp"] == "" for r in unique))
        self.assertEqual(summary["validation_status"], "NOT_A_FULL_PIPELINE_VALIDATION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
