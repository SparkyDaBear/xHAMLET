#!/usr/bin/env python3
"""PXD -> frozen ReLink/AF3 inputs -> all mapped distances -> three score channels.

Writes a new XP run. Does not run ReLink, install dependencies, or edit an existing
engine, environment, source dataset, or result. Defaults to discovery accounting.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import urllib.request
import zipfile

from analyze_v33 import analyze
from geometry_audit_v33 import sha256, write_json
from intake_v33 import check_output_location, load_experimental_context
from jwalk_adapter import EXPECTED_ENGINE_SHA
from xp_policy_v33 import Policy, VERSION

ROOT = Path(__file__).resolve().parent
DEFAULT_PROJECT = Path('/media/volume/xhamlet-data-5/NCEMS_XP_v33')


def resolve_ref(ref):
    if re.fullmatch('[0-9a-f]{40}', ref):
        return ref
    if not re.fullmatch('[A-Za-z0-9_.-]+', ref):
        raise ValueError('Use a simple branch/tag or an exact lowercase 40-character commit')
    url = 'https://api.github.com/repos/SparkyDaBear/xHAMLET/commits/' + ref
    request = urllib.request.Request(url, headers={'User-Agent': 'NCEMS-XP-v3.3', 'Accept': 'application/vnd.github+json'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            commit = json.loads(response.read(2_000_000))['sha']
    except Exception as exc:
        raise RuntimeError('Cannot freeze GitHub snapshot. No fallback to changing main. Supply a verified --ref or retry.') from exc
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('GitHub did not return a full commit identifier')
    return commit


def bundle(results):
    path = results / 'NCEMS_XP_v33_results.zip'
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(results.rglob('*')):
            if file.is_file() and file != path and not file.name.endswith('.partial'):
                archive.write(file, file.relative_to(results))
    return path


def package_hashes():
    return {str(path.relative_to(ROOT)): sha256(path) for path in sorted(ROOT.rglob('*'))
            if path.is_file() and path.suffix in ('.py', '.json')
            and '__pycache__' not in path.parts and 'tests' not in path.relative_to(ROOT).parts}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pxd')
    parser.add_argument('--out-root', type=Path, default=DEFAULT_PROJECT / 'runs')
    parser.add_argument('--engine', type=Path, default=Path.home() / 'ncems-xp-test-work/PXD010470_Structure_Only_Pilot/pipeline/xp_pipeline.py')
    parser.add_argument('--ref', default='main')
    parser.add_argument('--local-store', type=Path)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--experimental-context', type=Path, help='Optional reviewed, cited PXD/search-group reagent evidence')
    parser.add_argument('--from-v33', type=Path, help='Only a full v3.3 distance intake may be reused explicitly')
    parser.add_argument('--preflight-only', action='store_true', help='Map and check inputs; no new Jwalk distances or XP')
    parser.add_argument('--ncpus', type=int, default=1)
    parser.add_argument('--model-timeout', type=int, default=3600)
    parser.add_argument('--max-models', type=int, default=0, help='0 processes all stored catalog models; positive values explicitly mark a subset')
    args = parser.parse_args(argv)
    args.pxd = args.pxd.upper()
    if not re.fullmatch('PXD[0-9]{6}', args.pxd):
        parser.error('Use PXD plus exactly six digits')
    if args.ncpus < 1 or args.model_timeout < 1 or args.max_models < 0:
        parser.error('Invalid resource limit')
    if bool(args.local_store) != bool(args.catalog):
        parser.error('--local-store and --catalog must be supplied together')
    if args.from_v33 and (args.local_store or args.experimental_context or args.preflight_only):
        parser.error('Explicit reuse cannot change inputs/context or be combined with preflight')
    runroot = None
    lock = None
    saved_handlers = {}
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Interrupted by signal ' + str(signum))
    try:
        for signum in (signal.SIGTERM, signal.SIGINT):
            saved_handlers[signum] = signal.signal(signum, interrupted)
        output = check_output_location(args.out_root)
        sources = [p.expanduser().resolve(strict=True) for p in (args.local_store, args.from_v33) if p]
        if any(output == p or p in output.parents or output in p.parents for p in sources):
            raise ValueError('Output must be separate from input directories')
        engine = args.engine.expanduser().resolve(strict=True)
        if not engine.is_file() or sha256(engine) != EXPECTED_ENGINE_SHA:
            raise ValueError('Existing distance engine hash does not match the verified legacy source. No installation or change performed.')
        if args.experimental_context:
            load_experimental_context(str(args.experimental_context.expanduser().resolve(strict=True)))
        ref = 'LOCAL' if args.local_store else ('REUSE_V33' if args.from_v33 else resolve_ref(args.ref))
        output.mkdir(parents=True, exist_ok=True)
        lockroot = Path.home() / 'ncems-xp-test-work/pxd_xp_paper_runs/.locks'
        lockroot.mkdir(parents=True, exist_ok=True)
        lock = (lockroot / (args.pxd + '.lock')).open('a+')
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another XP run for this PXD is active') from exc
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        runroot = output / f'{args.pxd}_xp_v33_{stamp}_{os.getpid()}'
        runroot.mkdir(exist_ok=False)
        policy = Policy(mode='discovery')
        policy.snapshot(runroot / 'reference_snapshot')
        policy = Policy(runroot / 'reference_snapshot', mode='discovery')
        manifest = {'pxd': args.pxd, 'version': VERSION, 'source_ref': ref,
                    'command': list(argv) if argv is not None else sys.argv[1:],
                    'created_utc': datetime.now(timezone.utc).isoformat(),
                    'input_mode': 'explicit_v33_reuse' if args.from_v33 else 'fresh_full_distance_intake',
                    'max_models': args.max_models, 'preflight_only': args.preflight_only,
                    'engine_path': str(engine), 'engine_sha256': sha256(engine),
                    'software_sha256': package_hashes(), 'policy': policy.manifest(),
                    'validation_status': 'NOT_EXPERIMENTALLY_VALIDATED',
                    'relink_success_provenance': 'PUBLISHED_EXPORTS_ONLY; NOT_A_VERIFIED_SUCCESS_RUN_MANIFEST'}
        context = None
        if args.experimental_context:
            context = runroot / 'experimental_context.json'
            shutil.copyfile(args.experimental_context.expanduser().resolve(strict=True), context)
            manifest['experimental_context_sha256'] = sha256(context)
        write_json(runroot / 'launch_manifest.json', manifest)
        print('NCEMS XP:', args.pxd, VERSION, 'MODE: discovery', flush=True)
        if args.from_v33:
            source = args.from_v33.expanduser().resolve(strict=True)
        else:
            source = runroot / 'distance_run'
            command = [sys.executable, str(ROOT / 'source_worker.py'), '--pxd', args.pxd,
                       '--engine', str(ROOT / 'jwalk_adapter.py'), '--outdir', str(source),
                       '--ncpus', str(args.ncpus), '--max-models', str(args.max_models)]
            if args.local_store:
                command += ['--local-store', str(args.local_store.expanduser().resolve(strict=True)),
                            '--catalog', str(args.catalog.expanduser().resolve(strict=True))]
            if args.preflight_only:
                command.append('--check-only')
            env = os.environ.copy()
            for key in tuple(env):
                if key.startswith('NCEMS_REFERENCE_') or key == 'NCEMS_EXPERIMENTAL_CONTEXT':
                    env.pop(key)
            env.update(NCEMS_SOURCE_REF=ref, NCEMS_LEGACY_ENGINE=str(engine),
                       NCEMS_EXPECTED_ENGINE_SHA=EXPECTED_ENGINE_SHA,
                       NCEMS_MODEL_TIMEOUT=str(args.model_timeout), OMP_NUM_THREADS='1',
                       OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONUNBUFFERED='1')
            if context:
                env['NCEMS_EXPERIMENTAL_CONTEXT'] = str(context)
            work = runroot / 'working'
            work.mkdir()
            with (runroot / 'pipeline.log').open('x') as log:
                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, bufsize=1, env=env, cwd=work, start_new_session=True)
                try:
                    for line in proc.stdout:
                        print(line, end='', flush=True)
                        log.write(line)
                        log.flush()
                    rc = proc.wait()
                except BaseException:
                    if proc.poll() is None:
                        os.killpg(proc.pid, signal.SIGTERM)
                        try:
                            proc.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(proc.pid, signal.SIGKILL)
                            proc.wait()
                    raise
            if rc not in (0, 3) or not (source / 'run_summary.json').is_file():
                raise RuntimeError('Distance intake did not finish; see preserved pipeline.log and partial inputs')
        results = runroot / 'results'
        if args.preflight_only:
            results.mkdir()
            for name in ('xp_unique_pairs.csv', 'xp_observations.csv', 'model_summary.csv', 'unmatched_observations.csv'):
                shutil.copyfile(source / name, results / name)
            summary = json.loads((source / 'run_summary.json').read_text())
            summary.update(version=VERSION, state='PREFLIGHT_PARTIAL_FAILURE_NO_SCORING' if rc == 3 else 'PREFLIGHT_COMPLETE_NO_SCORING',
                           preflight_only=True, new_distances_calculated=0, new_xp_calculated=0,
                           validation_status='NOT_A_FULL_PIPELINE_VALIDATION')
            write_json(results / 'run_summary.json', summary)
        else:
            summary = analyze(source, results, args.pxd, policy)
        shutil.copyfile(runroot / 'launch_manifest.json', results / 'launch_manifest.json')
        if context:
            shutil.copyfile(context, results / context.name)
        archive = bundle(results)
        print('RESULTS:', results)
        print('BUNDLE:', archive)
        print('STATUS:', summary['state'], 'primary:', summary.get('numeric_xp_pairs', 0),
              'exploratory:', summary.get('exploratory_xp_pairs', 0),
              'reference geometry:', summary.get('reference_geometry_pairs', 0))
        return 3 if 'PARTIAL_FAILURE' in summary['state'] else 0
    except (Exception, KeyboardInterrupt) as exc:
        if runroot:
            record = {'pxd': args.pxd, 'version': VERSION,
                      'state': 'INTERRUPTED_NOT_COMPLETED' if isinstance(exc, KeyboardInterrupt) else 'FAILED_NOT_COMPLETED',
                      'error_type': type(exc).__name__, 'error': str(exc),
                      'created_utc': datetime.now(timezone.utc).isoformat()}
            write_json(runroot / 'pipeline_error.json', record)
            results = runroot / 'results'
            results.mkdir(exist_ok=True)
            if not (results / 'run_summary.json').exists():
                write_json(results / 'run_summary.json', record)
        print('ERROR:', type(exc).__name__, str(exc), file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 2
    finally:
        for signum, previous in saved_handlers.items():
            signal.signal(signum, previous)
        if lock:
            lock.close()


if __name__ == '__main__':
    raise SystemExit(main())
