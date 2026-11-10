import contextlib
import io
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import sync_result_database as sync


class SyncScopeTests(unittest.TestCase):
    def parse(self, *args):
        with patch.object(sys, "argv", ["sync_result_database.py", *args]):
            return sync.parse_args()

    def test_scope_required_even_with_exclusions(self):
        for args in ((), ("--exclude-pxd", "PXD00*"), ("--dry-run",)):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    self.parse(*args)
                self.assertEqual(error.exception.code, 2)

    def test_all_explicit_and_snapshot_only_without_scope(self):
        self.assertTrue(self.parse("--all").all_pxds)
        self.assertIsNone(self.parse("--snapshot-only").pxd)

    def test_file_and_arguments_combine(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "pxds.txt"
            path.write_text("pxd000001, PXD000002 # done\nPXD000001\n")
            args = self.parse("--pxd", "PXD000002", "PXD03*", "--pxd-file", str(path))
            self.assertEqual(args.pxd, ["PXD000002", "PXD03*", "PXD000001"])
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.parse("--all", "--pxd-file", str(path))

    def test_empty_invalid_and_missing_files_rejected(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "pxds.txt"
            for contents in ("# empty\n", "not-a-pxd\n"):
                path.write_text(contents)
                with self.subTest(contents=contents), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        self.parse("--pxd-file", str(path))
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.parse("--pxd-file", str(path.with_name("missing.txt")))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.parse("--all", "--pxd", "PXD000001")

    def test_scoped_dry_run_scans_only_selected_project(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for pxd in ("PXD000001", "PXD000002"):
                (root / pxd).mkdir()
            config = root / "config.yaml"
            config.write_text("{}")
            output = io.StringIO()
            with patch.object(sys, "argv", [
                "sync_result_database.py", "--pxd", "PXD000002",
                "--data-dir", str(root), "--config", str(config), "--dry-run",
            ]), patch.object(sync, "catalog_files", return_value=[]) as scan, \
                    patch.object(sync, "open_database") as database, \
                    contextlib.redirect_stdout(output):
                self.assertEqual(sync.main(), 0)
            scan.assert_called_once_with(root / "PXD000002")
            database.assert_not_called()
            self.assertIn("Selected 1 PXD(s)", output.getvalue())


if __name__ == "__main__":
    unittest.main()
