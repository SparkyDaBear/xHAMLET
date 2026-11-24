#!/usr/bin/env python3
"""Run a frozen copy of the prior intake/mapping wrapper against a pinned source.
Only this package's in-memory objects are adapted; no installed file is edited.
"""
from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import types
import urllib.error


def child_run(*args, **kwargs):
    """Bound one model and terminate its entire subprocess family on failure."""
    timeout = kwargs.pop('timeout', int(os.environ.get('NCEMS_MODEL_TIMEOUT', '3600')))
    capture = kwargs.pop('capture_output', False)
    check = kwargs.pop('check', False)
    if capture:
        if 'stdout' in kwargs or 'stderr' in kwargs:
            raise ValueError('capture_output conflicts with explicit stream arguments')
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    kwargs['start_new_session'] = True
    process = subprocess.Popen(*args, **kwargs)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except BaseException:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
        # A parent may exit on TERM while a descendant ignores it. Terminate any
        # surviving members of that same model session before continuing.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        raise
    result = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    if check:
        result.check_returncode()
    return result


def main():
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Distance worker interrupted by signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    root=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('frozen_ncems_batch',root/'vendor'/'batch_v01.py')
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
    ref=os.environ['NCEMS_SOURCE_REF']
    if not re.fullmatch('[0-9a-f]{40}',ref) and ref!='LOCAL':
        raise ValueError('Source must be an exact Git commit or LOCAL')
    if ref!='LOCAL':
        mod.REPO_RAW='https://raw.githubusercontent.com/SparkyDaBear/xHAMLET/'+ref
    original_download=mod.obtain_bytes
    def retry_download(source,destination,max_bytes=60000000):
        for attempt in range(3):
            try:
                return original_download(source,destination,max_bytes)
            except urllib.error.HTTPError as e:
                if e.code not in (429,500,502,503,504) or attempt==2:
                    raise
            except (urllib.error.URLError,TimeoutError):
                if attempt==2:
                    raise
            time.sleep(2**attempt)
    mod.obtain_bytes=retry_download
    mod.subprocess=types.SimpleNamespace(run=child_run)
    return mod.main(sys.argv[1:])

if __name__=='__main__':
    raise SystemExit(main())
