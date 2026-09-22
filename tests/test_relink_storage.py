import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pxd_enhancer.relink_runner import ReLinkRunner


class ReLinkStorageTests(unittest.TestCase):
    def _run_nextflow(self, returncode: int, external_work: bool = False):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relink_dir = root / "relink"
            relink_dir.mkdir()
            runner = ReLinkRunner(str(relink_dir))
            completed = subprocess.CompletedProcess([], returncode, stdout="pipeline output")
            cleaned = subprocess.CompletedProcess([], 0, stdout="cleaned")
            extra_args = ["-work-dir", str(root / "nextflow-work")] if external_work else None
            if external_work:
                (root / "nextflow-work").mkdir()
            with patch("pxd_enhancer.relink_runner.subprocess.run", side_effect=[completed, cleaned]) as run:
                result = runner.run_nextflow(
                    input_sdrf=root / "input.sdrf.tsv",
                    fasta_path=root / "input.fasta",
                    raw_root_dir=root / "raw",
                    xi_linear_config=root / "linear.conf",
                    xi_crosslink_config=root / "crosslink.conf",
                    outdir=root / "results",
                    profile="singularity",
                    resume=True,
                    run_name="xhamlet_pxd_test",
                    extra_args=extra_args,
                )
            return result, run.call_args_list

    def test_successful_run_is_named_resumed_and_cleaned(self):
        result, calls = self._run_nextflow(0)

        command = calls[0].args[0]
        self.assertIn("-resume", command)
        self.assertEqual(command[command.index("-name") + 1], "xhamlet_pxd_test")
        self.assertEqual(calls[1].args[0], ["nextflow", "clean", "xhamlet_pxd_test", "-f"])
        self.assertEqual(result["cleanup"]["returncode"], 0)

    def test_failed_run_is_cleaned_to_limit_disk_growth(self):
        result, calls = self._run_nextflow(1)

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1].args[0], ["nextflow", "clean", "xhamlet_pxd_test", "-f"])
        self.assertEqual(result["cleanup"]["returncode"], 0)

    def test_relink_publish_mode_is_hard_link(self):
        config = (REPO_ROOT / "tools" / "relink" / "nextflow.config").read_text()
        self.assertIn("publish_dir_mode           = 'link'", config)

    def test_nextflow_run_name_limit(self):
        pxd = "pxd052552"
        taxid = "9913"
        digest = "0123456789"
        run_name = f"xhamlet_{pxd}_{taxid}_{digest}_{10**19}"

        self.assertLessEqual(len(run_name), 80)

    def test_parser_scan_errors_keep_nonempty_mzml(self):
        module = (
            REPO_ROOT
            / "tools"
            / "relink"
            / "modules"
            / "bigbio"
            / "thermorawfileparser"
            / "main.nf"
        ).read_text()

        self.assertIn("parser_status=\\${PIPESTATUS[0]}", module)
        self.assertIn("! -s '${rawfile.baseName}.mzML'", module)

    def test_parser_stages_local_raw_with_symlink(self):
        module = (
            REPO_ROOT
            / "tools"
            / "relink"
            / "modules"
            / "bigbio"
            / "thermorawfileparser"
            / "main.nf"
        ).read_text()

        self.assertIn("'symlink'", module)
        self.assertNotIn("task.attempt == 1", module)

    def test_cross_filesystem_work_uses_copy_publication(self):
        with patch.object(ReLinkRunner, "_paths_share_device", return_value=False):
            result, calls = self._run_nextflow(0, external_work=True)

        command = calls[0].args[0]
        self.assertEqual(command[command.index("--publish_dir_mode") + 1], "copy")
        self.assertEqual(result["returncode"], 0)

    def test_cli_propagates_relink_failure(self):
        main_source = (REPO_ROOT / "src" / "main.py").read_text()

        self.assertIn('stages.get("relink") == "failed"', main_source)
        self.assertIn("if failed:\n        sys.exit(1)", main_source)


if __name__ == "__main__":
    unittest.main()
