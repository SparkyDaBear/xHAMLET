#!/usr/bin/env python3
"""Instrument the existing NCEMS Jwalk call sequence; leave its modules unchanged.

Outputs the legacy engine schema for compatibility and extra distance diagnostics.
The chemistry-aware calculation is performed in analyze_v33.py afterward.
"""
from __future__ import annotations
import argparse
import contextlib
import csv
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

from geometry_audit_v33 import sha256

EXPECTED_ENGINE_SHA = '4fb72ee71b6b050831a2bdf6a59e0629fd190074af1afa11e23661dba5ec3821'


def load_legacy():
    path = Path(os.environ['NCEMS_LEGACY_ENGINE']).expanduser().resolve(strict=True)
    expected = os.environ.get('NCEMS_EXPECTED_ENGINE_SHA', EXPECTED_ENGINE_SHA)
    if sha256(path) != expected:
        raise ValueError('Existing XP engine checksum changed; review before reusing its distance implementation')
    spec = importlib.util.spec_from_file_location('ncems_unchanged_legacy_engine', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def instrumented_jwalk(legacy, pdb: Path, pair_file: Path, out: Path, ncpus: int):
    from NCLEdetector.Jwalk import PDBTools, GridTools, SurfaceTools, SASDTools
    modules = (PDBTools, GridTools, SurfaceTools, SASDTools)
    hashes = {m.__name__:sha256(Path(m.__file__)) for m in modules}
    structure = PDBTools.read_PDB_file(str(pdb))
    grid = GridTools.makeGrid(structure, 1)
    pairs, first, second = GridTools.mark_CAlphas_pairs(grid, structure, str(pair_file))
    initial_pairs = [(tuple(a),tuple(b)) for a,b in pairs]
    first, second = SurfaceTools.check_solvent_accessibility_freesasa_both(
        str(pdb), first, second, str(pair_file), {}, ncpus)
    accessible_a, accessible_b = set(first), set(second)
    surface = GridTools.generate_solvent_accessible_surface(grid, structure, first, second)
    vox_a, removed_a = GridTools.find_surface_voxels(first, surface, str(pair_file))
    vox_b, removed_b = GridTools.find_surface_voxels(second, surface, str(pair_file))
    updated = SurfaceTools.update_crosslink_pairs(pairs, first, second, removed_a, removed_b)
    active = {legacy.pair_key((tuple(a),tuple(b))) for a,b in updated}
    diag = {}
    for a,b in initial_pairs:
        key = legacy.pair_key((a,b))
        if a not in accessible_a or b not in accessible_b:
            reason = 'ACCESSIBILITY_FILTER_REJECTED'
            evidence = 'Endpoint removed by installed Jwalk/FreeSASA accessibility filter; algorithmic evidence, not experimental proof'
        elif key not in active:
            reason = 'SURFACE_VOXEL_OR_PAIR_FILTER_REJECTED'
            evidence = 'Removed by installed surface-voxel/pair filtering; not a verified long distance'
        else:
            reason = 'NO_SASD_WITH_FINITE_SEARCH_LIMIT'
            evidence = 'Submitted to existing Jwalk with grid-search limit 50 A; exact missing-path reason unresolved'
        diag[key] = {'reason':reason,'evidence':evidence}
    sasds = SASDTools.parallel_BFS(vox_a,vox_b,surface,first,second,updated,50.0,1,ncpus,str(pair_file)) if updated else {}
    sasds = GridTools.remove_duplicates(sasds)
    sasds = SASDTools.get_euclidean_distances(sasds,str(pdb),'NULL','NULL')
    PDBTools.write_sasd_to_txt(sasds,str(pdb),str(out))
    distances={}
    for a,b,d,e in sasds:
        key=legacy.pair_key((tuple(a),tuple(b)))
        value=(float(d),float(e))
        if key in distances and distances[key] != value:
            raise ValueError('Conflicting Jwalk distances for the same pair')
        distances[key]=value
        diag[key]={'reason':'SASD_RETURNED','evidence':'Original installed Jwalk modules; no path correction or clipping'}
    return distances,hashes,diag


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--structure',type=Path,required=True)
    p.add_argument('--pairs',type=Path,required=True)
    p.add_argument('--outdir',type=Path,required=True)
    p.add_argument('--ncpus',type=int,default=1)
    p.add_argument('--check-only',action='store_true')
    a=p.parse_args(argv)
    report={}
    created=False
    try:
        if a.ncpus<1:
            raise ValueError('ncpus must be positive')
        legacy,legacy_path=load_legacy()
        from extended_distance_engine import install as install_all_20
        legacy = install_all_20(legacy)
        src=a.structure.expanduser().resolve(strict=True)
        out=a.outdir.resolve()
        if out.exists():
            raise FileExistsError('Output already exists')
        structure,residues=legacy.load_structure(src)
        pairs=legacy.select_pairs(residues,a.pairs,50000)
        out.mkdir(parents=True)
        created=True
        from Bio.PDB import PDBIO
        pdb=out/'input_structure.pdb'
        w=PDBIO(); w.set_structure(structure); w.save(str(pdb))
        pair_file=out/'residue_pairs.txt'
        pair_file.write_text(''.join(f'{x[0]}|{x[1]}|{y[0]}|{y[1]}|\n' for x,y in pairs))
        report={'state':'CHECK_ONLY' if a.check_only else 'STARTED',
                'created_utc':datetime.now(timezone.utc).isoformat(),
                'structure_sha256':sha256(src),'normalized_pdb_sha256':sha256(pdb),
                'legacy_engine_sha256':sha256(legacy_path),'adapter_sha256':sha256(Path(__file__)),
                'jwalk_max_dist_A':50.0,'voxel_A':1,'ncpus':a.ncpus,
                'n_pairs_requested':len(pairs),
                'distance_protocol':'existing_NCLEdetector_Jwalk_grid1A_search50A; NOT unlimited-search original-paper reproduction',
                'note':'Distance-only output: xp is intentionally blank. v3.3 analysis applies the chemistry policy.'}
        if not a.check_only:
            with (out/'jwalk.log').open('w') as log:
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                    distances,hashes,diag=instrumented_jwalk(legacy,pdb,pair_file,out,a.ncpus)
            report['jwalk_module_sha256']=hashes
            report['status_counts']=legacy.write_results(out/'xp_pairs.csv',src.stem,pairs,distances)
            report['state']='COMPLETED_WITH_UNSCORED_PAIRS' if report['status_counts'].get('NO_SASD_RETURNED') else 'COMPLETED'
            with (out/'distance_diagnostics.csv').open('w',newline='') as f:
                dw=csv.DictWriter(f,fieldnames=['chain1','residue1','chain2','residue2','reason','evidence'])
                dw.writeheader()
                for x,y in pairs:
                    info=diag.get(legacy.pair_key((x,y)),{'reason':'PAIR_NOT_RETURNED_BY_BACKEND','evidence':'No backend diagnostic available'})
                    dw.writerow({'chain1':x[1],'residue1':x[0],'chain2':y[1],'residue2':y[0],**info})
        (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print(f'{report["state"]}: {len(pairs)} requested pairs; output: {out}')
        return 0
    except Exception as e:
        if created:
            report.update(state='FAILED',error=f'{type(e).__name__}: {e}')
            (a.outdir/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print(f'ERROR: {type(e).__name__}: {e}',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
