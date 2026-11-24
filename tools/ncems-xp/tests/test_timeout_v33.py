"""Concrete regression: a timed-out model must not leave a working child process."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_worker import child_run


def process_has_stopped(stat_path):
    """Read /proc directly: an exit can race with any prior existence check."""
    try:
        record = stat_path.read_text()
    except (FileNotFoundError, ProcessLookupError):
        return True
    return record.rsplit(") ", 1)[1].split()[0] in {"Z", "X"}


class ModelTimeoutTests(unittest.TestCase):
    def test_success_keeps_capture_and_returncode(self):
        result = child_run([sys.executable, '-c', 'print("synthetic child")'],
                           capture_output=True, text=True, timeout=5, check=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'synthetic child')

    def test_timeout_stops_descendant(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'child_pid.txt'
            code = ('import subprocess,sys,time; from pathlib import Path; '
                    'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
                    'Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(30)')
            with self.assertRaises(subprocess.TimeoutExpired):
                child_run([sys.executable, '-c', code, str(path)], capture_output=True, text=True, timeout=1)
            pid = int(path.read_text())
            state = Path('/proc') / str(pid) / 'stat'
            for attempt in range(20):
                if process_has_stopped(state):
                    break
                time.sleep(0.05)
            self.assertTrue(process_has_stopped(state),
                            'Model descendant remains alive after timeout')


if __name__ == '__main__':
    unittest.main()
