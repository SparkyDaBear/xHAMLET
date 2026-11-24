"""Independent coordinate checks and strict CSV I/O; no scoring in this module."""
from __future__ import annotations
import csv
import hashlib
import json
import math
from pathlib import Path
import re

def finite_number(value):
    try:
        n = float(value)
    except (ValueError, TypeError):
        return None
    return n if math.isfinite(n) else None

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        if not r.fieldnames or len(r.fieldnames) != len(set(r.fieldnames)):
            raise ValueError(f'Empty or duplicated CSV header: {path.name}')
        rows = list(r)
        if any(None in x or any(v is None for v in x.values()) for x in rows):
            raise ValueError(f'CSV row width does not match headers: {path.name}')
        return list(r.fieldnames), rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    temp = path.with_name(path.name + '.partial')
    with temp.open('x', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(fields)), extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    temp.replace(path)


def write_json(path: Path, value) -> None:
    temp = path.with_name(path.name + '.partial')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
    temp.replace(path)


def pair_key(r: dict) -> tuple | None:
    try:
        ends = tuple(sorted(((str(r['chain_a']), int(r['pdb_site_a'])),
                             (str(r['chain_b']), int(r['pdb_site_b'])))))
        return str(r['job']), str(r.get('search_group', '')), ends
    except (KeyError, TypeError, ValueError):
        return None


def safe_model_folder(source: Path, job: str) -> Path:
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', job) or job in ('.', '..'):
        raise ValueError('Unsafe model job identifier')
    path = (source / 'models' / job).resolve()
    models = (source / 'models').resolve()
    if models not in path.parents:
        raise ValueError('Model path escapes run directory')
    return path


class CoordinateAudit:
    """C-alpha arithmetic QC; does not independently recompute a surface path."""
    def __init__(self, source: Path):
        self.source = source
        self.cache = {}
        self.diagnostics = {}
        self.metadata = {}
        self.buried_logs = {}

    def for_row(self, row: dict) -> dict:
        job = row.get('job', '')
        folder = safe_model_folder(self.source, job)
        if job not in self.cache:
            self.cache[job] = None
            self.diagnostics[job] = {}
            self.metadata[job] = {}
            self.buried_logs[job] = set()
            log = folder / 'xp_engine' / 'jwalk.log'
            if log.exists():
                for line in log.read_text(errors='replace').splitlines():
                    found = re.fullmatch(r'Residue (\d+)-([A-Za-z0-9])-([A-Z]{3}) is buried', line.strip())
                    if found:
                        self.buried_logs[job].add((found.group(2), int(found.group(1))))
            sp = folder / 'xp_engine' / 'summary.json'
            if sp.exists():
                self.metadata[job] = json.loads(sp.read_text())
            dp = folder / 'xp_engine' / 'distance_diagnostics.csv'
            if dp.exists():
                for x in read_csv(dp)[1]:
                    k = tuple(sorted(((x['chain1'], int(x['residue1'])),
                                      (x['chain2'], int(x['residue2'])))))
                    self.diagnostics[job][k] = x
            pdb = folder / 'structure_for_xp.pdb'
            if pdb.exists():
                try:
                    from Bio.PDB import PDBParser
                    s = PDBParser(PERMISSIVE=False, QUIET=True).get_structure(job, str(pdb))
                    models = list(s.get_models())
                    if len(models) != 1:
                        raise ValueError('Multiple coordinate models')
                    coords = {}
                    for chain in models[0]:
                        for res in chain:
                            if res.id[0] == ' ' and not res.id[2].strip() and 'CA' in res:
                                coords[(chain.id, res.id[1])] = tuple(float(x) for x in res['CA'].coord)
                    self.cache[job] = coords
                except Exception as e:
                    self.cache[job] = {'error': f'{type(e).__name__}: {e}'}
        info = {'coordinate_check': 'CSV_ONLY_COORDINATES_NOT_AVAILABLE'}
        meta = self.metadata[job]
        if 'jwalk_max_dist_A' in meta:
            info['search_limit_A'] = meta['jwalk_max_dist_A']
        if 'distance_protocol' in meta:
            info['distance_protocol'] = meta['distance_protocol']
        k = pair_key(row)
        if k and k[2] in self.diagnostics[job]:
            d = self.diagnostics[job][k[2]]
            info.update(reason=d.get('reason', ''), evidence=d.get('evidence', ''))
        if k and not info.get('reason') and any(endpoint in self.buried_logs[job] for endpoint in k[2]):
            info.update(reason='BACKEND_LOG_REPORTED_NONACCESSIBLE',
                        evidence='Original per-model jwalk.log explicitly reports an endpoint as buried')
        coords = self.cache[job]
        if coords is None or k is None:
            return info
        if 'error' in coords:
            info.update(coordinate_check='COORDINATE_CHECK_FAILED', evidence=coords['error'])
            return info
        try:
            a, b = (coords[t] for t in k[2])
            d = math.dist(a, b)
            if not math.isfinite(d):
                raise ValueError('Nonfinite C-alpha coordinates')
            info.update(euclidean_recomputed_A=d, coordinate_check='EUCLIDEAN_RECHECK_PASSED')
            e = finite_number(row.get('euclidean_A'))
            if e is not None and abs(d-e) > 0.01:
                info['coordinate_check'] = 'EUCLIDEAN_MISMATCH'
            cif = folder / 'model.cif'
            expected = row.get('model_cif_sha256')
            if not cif.is_file() or not expected:
                info['coordinate_check'] = 'SOURCE_HASH_UNAVAILABLE'
            elif sha256(cif) != expected:
                info['coordinate_check'] = 'SOURCE_HASH_MISMATCH'
        except (KeyError, ValueError) as e:
            info.update(coordinate_check='COORDINATE_CHECK_FAILED', evidence=str(e))
        return info

