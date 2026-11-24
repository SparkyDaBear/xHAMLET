"""Operational tests use temporary files and fake child runners, never Jetstream."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


queue = load("tested_rerun_all_v33", "rerun_all.py")
installer = load("tested_install_v33", "install_v33.py")


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


class RerunInventoryTests(unittest.TestCase):
    def test_completed_failed_blocked_and_launch_only_are_all_prior_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            states = ("COMPLETE", "PARTIAL_FAILURE", "BLOCKED_BY_REFERENCE_POLICY")
            for n, state in enumerate(states, 1):
                pxd = f"PXD00000{n}"
                write_json(root / (pxd + "_run") / "results" / "run_summary.json",
                           {"pxd": pxd, "state": state, "version": "3.2"})
            write_json(root / "PXD000004_run" / "launch_manifest.json",
                       {"pxd": "PXD000004", "version": "3.1"})
            result = queue.scan_prior_runs([root])
            self.assertEqual([t["pxd"] for t in result["targets"]],
                             ["PXD000001", "PXD000002", "PXD000003", "PXD000004"])
            self.assertEqual(result["targets"][2]["prior_records"][0]["state"],
                             "BLOCKED_BY_REFERENCE_POLICY")
            self.assertEqual(result["targets"][3]["prior_records"][0]["state"], "NOT_RECORDED")

    def test_deduplication_keeps_every_distinct_metadata_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for version in ("v31", "v32"):
                write_json(root / ("PXD000001_" + version) / "run_summary.json",
                           {"pxd": "PXD000001", "version": version})
            result = queue.scan_prior_runs([root, root])
            self.assertEqual(len(result["targets"]), 1)
            self.assertEqual(len(result["targets"][0]["prior_records"]), 2)

    def test_directory_only_and_conflicting_metadata_never_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PXD000001_missing_summary").mkdir()
            write_json(root / "PXD000002_wrong" / "run_summary.json", {"pxd": "PXD000003"})
            result = queue.scan_prior_runs([root])
            self.assertEqual(result["targets"], [])
            self.assertEqual({r["pxd"] for r in result["uncertain_candidates"]},
                             {"PXD000001", "PXD000002", "PXD000003"})
            self.assertIn("PXD_METADATA_PATH_CONFLICT", [r["reason"] for r in result["warnings"]])

    def test_fixture_and_symlink_directories_are_not_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "tests" / "PXD999999_run" / "run_summary.json", {"pxd": "PXD999999"})
            (root / "PXD000001_symlink").symlink_to(root / "tests", target_is_directory=True)
            self.assertEqual(queue.scan_prior_runs([root])["targets"], [])

    def test_invalid_json_is_preserved_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PXD000001_run" / "run_summary.json"
            path.parent.mkdir()
            path.write_text("{broken")
            result = queue.scan_prior_runs([Path(tmp)])
            self.assertEqual(result["targets"], [])
            self.assertTrue(any("UNREADABLE_METADATA" in r["reason"] for r in result["warnings"]))
            self.assertEqual(path.read_text(), "{broken")

    def test_default_roots_do_not_require_guessed_directories_to_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            existing = home / "ncems-xp-test-work" / "pxd_xp_custom_runs"
            existing.mkdir(parents=True)
            roots = queue.default_scan_roots(home)
            self.assertIn(existing, roots)
            inventory = queue.scan_prior_runs(roots)
            self.assertTrue(any(r["state"] == "MISSING" for r in inventory["roots"]))
            self.assertFalse((home / "ncems-xp-test-work" / "pxd_xp_paper_runs").exists())

    def test_zip_and_tar_preserve_blocked_and_failed_prior_records_without_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with zipfile.ZipFile(root / "review.zip", "w") as archive:
                archive.writestr("PXD000001_run/results/run_summary.json",
                                 json.dumps({"pxd": "PXD000001", "state": "BLOCKED_BY_REFERENCE_POLICY", "version": "3.2"}))
                archive.writestr("tests/PXD999999_fixture/run_summary.json", json.dumps({"pxd": "PXD999999"}))
            with tarfile.open(root / "review.tar.gz", "w:gz") as archive:
                raw = json.dumps({"pxd": "PXD000002", "state": "PARTIAL_FAILURE", "version": "3.1"}).encode()
                member = tarfile.TarInfo("PXD000002_run/run_summary.json")
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
            result = queue.scan_prior_runs([root])
            self.assertEqual([t["pxd"] for t in result["targets"]], ["PXD000001", "PXD000002"])
            self.assertEqual(result["targets"][0]["prior_records"][0]["state"], "BLOCKED_BY_REFERENCE_POLICY")
            self.assertEqual(len(result["archives"]), 2)
            self.assertTrue(all(a["sha256"] for a in result["archives"]))
            self.assertFalse((root / "PXD000001_run").exists())
            self.assertFalse((root / "PXD000002_run").exists())

    def test_archive_limit_is_reported_as_incomplete_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "oversize.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("PXD000001_run/run_summary.json", json.dumps({"pxd": "PXD000001"}))
            with patch.object(queue, "ARCHIVE_MAX_BYTES", 1):
                result = queue.scan_prior_runs([path])
            self.assertEqual(result["targets"], [])
            self.assertEqual(result["archives"][0]["state"], "NOT_SCANNED_COMPRESSED_SIZE_LIMIT")
            self.assertTrue(result["warnings"])


class QueueExecutionTests(unittest.TestCase):
    def test_explicit_commit_requires_no_network(self):
        with patch.object(queue.urllib.request, "urlopen", side_effect=AssertionError("network not permitted")):
            source = queue.resolve_source("a" * 40)
        self.assertEqual(source["resolved_ref"], "a" * 40)

    def test_full_run_command_never_reuses_old_filtered_results(self):
        plan = {"runner": {"path": "/tmp/run_v33.py"}, "engine": {"path": "/tmp/engine.py"},
                "source": {"mode": "github", "resolved_ref": "b" * 40},
                "ncpus_per_pxd": 1, "model_timeout_seconds": 3600}
        command = queue.make_command(plan, "PXD000001", Path("/tmp/new-attempt"))
        self.assertNotIn("--from-run", command)
        self.assertEqual(command[command.index("--ref") + 1], "b" * 40)
        self.assertEqual(command[command.index("--out-root") + 1], "/tmp/new-attempt")

    def test_experimental_context_is_forwarded_without_relabeling(self):
        plan = {"runner": {"path": "/tmp/run_v33.py"}, "engine": {"path": "/tmp/engine.py"},
                "source": {"mode": "github", "resolved_ref": "b" * 40},
                "ncpus_per_pxd": 1, "model_timeout_seconds": 3600,
                "experimental_context": {"snapshot_path": "/tmp/frozen_context.json"}}
        command = queue.make_command(plan, "PXD000001", Path("/tmp/new-attempt"))
        self.assertEqual(command[command.index("--experimental-context") + 1], "/tmp/frozen_context.json")

    def test_exit_zero_without_v33_completion_is_not_claimed_complete(self):
        self.assertEqual(queue.outcome_for(0, []), "EXIT_ZERO_STATUS_UNVERIFIED")
        self.assertEqual(queue.outcome_for(0, [{"version": "3.1", "state": "COMPLETE"}]),
                         "EXIT_ZERO_STATUS_UNVERIFIED")
        self.assertEqual(queue.outcome_for(0, [{"version": "3.3.0", "state": "COMPLETE_NO_NUMERIC_XP"}]),
                         "COMPUTATION_COMPLETED")
        self.assertEqual(queue.outcome_for(4, []), "POLICY_OR_PREFLIGHT_STOP")
        self.assertEqual(queue.outcome_for(3, []), "PARTIAL_OR_FAILED")
        self.assertEqual(queue.outcome_for(130, []), "INTERRUPTED")
        self.assertEqual(queue.outcome_for(143, []), "INTERRUPTED")

    def test_fake_child_writes_new_output_and_durable_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = base / "package"
            package.mkdir()
            runner = package / "run_v33.py"
            runner.write_text(
                "import sys,json\nfrom pathlib import Path\n"
                "pxd=sys.argv[1]\np=Path(sys.argv[sys.argv.index('--out-root')+1])\n"
                "p.mkdir(parents=True,exist_ok=False)\n"
                "(p/'run_summary.json').write_text(json.dumps({'pxd':pxd,'version':'3.3.0','state':'COMPLETE_NO_NUMERIC_XP','numeric_xp_pairs':0,'exploratory_xp_pairs':2,'reference_geometry_pairs':1,'unique_pair_contexts':5,'score_counts':{'xp_primary':{'numeric':0},'xp_exploratory':{'numeric':2},'reference_geometry_score':{'numeric':1}}}))\n")
            plan = {"runner": {"path": str(runner)}, "engine": {"path": "/existing/engine.py"},
                    "source": {"mode": "github", "resolved_ref": "c" * 40},
                    "ncpus_per_pxd": 1, "model_timeout_seconds": 3600,
                    "out_root": str(base / "runs"),
                    "production_package": queue.production_package_snapshot(package)}
            ledger = base / "attempts.jsonl"
            with patch.object(queue, "require_mounted_volume", side_effect=lambda p: p):
                result = queue.run_one(plan, "plan-hash", "PXD000001", ledger, queue.ActiveChildren())
            self.assertEqual(result["outcome"], "COMPUTATION_COMPLETED")
            self.assertEqual(result["returncode"], 0)
            self.assertEqual([r["event"] for r in queue.read_ledger(ledger)], ["STARTING", "RUNNING", "FINISHED"])
            self.assertEqual(result["result_summaries"][0]["numeric_xp_pairs"], 0)
            self.assertEqual(result["result_summaries"][0]["exploratory_xp_pairs"], 2)
            self.assertEqual(result["result_summaries"][0]["reference_geometry_pairs"], 1)
            self.assertEqual(result["result_summaries"][0]["unique_pair_contexts"], 5)
            self.assertEqual(result["result_summaries"][0]["score_counts"]["xp_exploratory"]["numeric"], 2)
            self.assertEqual(result["scientific_validation"], "NOT_ESTABLISHED_BY_EXECUTION_STATUS")

    def test_changed_profile_blocks_launch_and_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = base / "package"
            package.mkdir()
            runner = package / "run_v33.py"
            runner.write_text("# test runner; must never execute\n")
            profile = package / "score_profiles.json"
            profile.write_text('{"profiles": []}')
            frozen = queue.production_package_snapshot(package)
            profile.write_text('{"profiles": [{"changed": true}]}')
            plan = {"runner": {"path": str(runner)}, "engine": {"path": "/existing/engine.py"},
                    "source": {"mode": "github", "resolved_ref": "c" * 40},
                    "ncpus_per_pxd": 1, "model_timeout_seconds": 3600,
                    "out_root": str(base / "runs"), "production_package": frozen}
            ledger = base / "attempts.jsonl"
            with patch.object(queue, "require_mounted_volume", side_effect=lambda p: p), \
                 patch.object(queue.subprocess, "Popen", side_effect=AssertionError("changed package must not launch")):
                result = queue.run_one(plan, "plan-hash", "PXD000001", ledger, queue.ActiveChildren())
            self.assertEqual(result["event"], "INTEGRITY_BLOCKED_NOT_LAUNCHED")
            self.assertIn("score_profiles.json", result["error"])
            self.assertEqual(queue.read_ledger(ledger)[0]["event"], "INTEGRITY_BLOCKED_NOT_LAUNCHED")
            self.assertFalse(Path(result["output_root"]).exists())

    def test_context_schema_rejects_duplicates_and_missing_citations(self):
        entry = {"pxd": "PXD000001", "search_group": "taxid_9606/dsbu", "chemistry_evidence": "Study methods citation",
                 "chemistry": "DSBU", "chemistry_evidence_status": "EXPERIMENT_REAGENT_CONFIRMED"}
        queue.validate_experimental_context({"schema": "NCEMS_EXPERIMENTAL_CONTEXT_V1", "entries": [entry]})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            queue.validate_experimental_context({"schema": "NCEMS_EXPERIMENTAL_CONTEXT_V1", "entries": [entry, entry]})
        with self.assertRaisesRegex(ValueError, "citation or record"):
            queue.validate_experimental_context({"schema": "NCEMS_EXPERIMENTAL_CONTEXT_V1", "entries": [{**entry, "chemistry_evidence": ""}]})
        with self.assertRaises(ValueError):
            queue.validate_experimental_context({"schema": "NCEMS_EXPERIMENTAL_CONTEXT_V1", "entries": [{**entry, "chemistry_evidence_status": True}]})

    def test_resume_does_not_repeat_completed_or_failed_attempts_implicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_file = root / "plan.json"
            plan_file.write_text("{}")
            ledger = root / "attempts.jsonl"
            plan_id = queue.sha256_file(plan_file)
            queue.append_ledger(ledger, {"plan_sha256": plan_id, "pxd": "PXD000001",
                                        "event": "FINISHED", "outcome": "RUN_ERROR"})
            args = argparse.Namespace(retry_incomplete=False, workers=2)
            plan = {"source": {"resolved_ref": "d" * 40}}
            with patch.object(queue, "run_one", side_effect=AssertionError("should not launch")):
                code = queue.execute_locked_plan(args, plan_file, plan, root / "runs", ledger, ["PXD000001"])
            self.assertEqual(code, 0)

    def test_malformed_ledger_is_not_silently_discarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            path.write_text('{"event":"RUNNING"}\n{broken')
            with self.assertRaisesRegex(ValueError, "incomplete or invalid"):
                queue.read_ledger(path)


class InstallerTests(unittest.TestCase):
    def make_source(self, parent: Path) -> Path:
        source = parent / "source"
        source.mkdir()
        (source / "run_v33.py").write_text("# fixture only\n")
        (source / "rerun_all.py").write_text("# fixture only\n")
        return source

    def test_no_mounted_volume_means_no_destination_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            destination = root / "missing-volume" / "package"
            with patch.object(installer, "mounted", return_value=False):
                with self.assertRaisesRegex(ValueError, "not mounted"):
                    installer.install(source, destination)
            self.assertFalse(destination.parent.exists())

    def test_new_install_identical_reuse_and_different_bytes_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            volume = root / "volume"
            volume.mkdir()
            destination = volume / "project" / "package"
            with patch.object(installer, "FIXED_VOLUME", volume), patch.object(installer, "mounted", return_value=True):
                installed = installer.install(source, destination)
                self.assertEqual(installed["state"], "NEW_SEPARATE_PACKAGE_INSTALLED")
                reused = installer.install(source, destination)
                self.assertEqual(reused["state"], "IDENTICAL_EXISTING_VERSION_REUSED")
                (source / "run_v33.py").write_text("# changed\n")
                with self.assertRaises(FileExistsError):
                    installer.install(source, destination)
                self.assertEqual((destination / "run_v33.py").read_text(), "# fixture only\n")

    def test_declared_checksum_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            (source / "SHA256SUMS.txt").write_text("0" * 64 + "  run_v33.py\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                installer.verify_declared_hashes(source, installer.file_manifest(source))


if __name__ == "__main__":
    unittest.main()
