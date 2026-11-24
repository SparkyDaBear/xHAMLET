"""Opt-in extension of the frozen distance adapter to ALL 20 standard residues.

This does not change the scientific domain of the legacy score_XL function.
For non-K/S/T/Y/M pairs, Jwalk returns a distance and legacy XP stays blank.
The main parameter resolver later decides whether a chemistry-specific model exists.
"""
from __future__ import annotations
import csv
import itertools
import math
from pathlib import Path

AA3_TO_1 = {
    'ALA':'A','CYS':'C','ASP':'D','GLU':'E','PHE':'F','GLY':'G',
    'HIS':'H','ILE':'I','LYS':'K','LEU':'L','MET':'M','ASN':'N',
    'PRO':'P','GLN':'Q','ARG':'R','SER':'S','THR':'T','VAL':'V',
    'TRP':'W','TYR':'Y',
}


def load_structure(legacy, path):
    from Bio.PDB import PDBParser
    path = Path(path)
    if path.suffix.lower() != '.pdb':
        raise ValueError('Require a prepared PDB structure')
    s = PDBParser(PERMISSIVE=False, QUIET=True).get_structure(path.stem, str(path))
    models = list(s.get_models())
    if len(models) != 1:
        raise ValueError('Only one coordinate model supported')
    residues = {}
    for chain in models[0]:
        if len(chain.id) != 1 or not chain.id.isalnum():
            raise ValueError('Chain ID must be one alphanumeric character')
        for res in chain:
            hetero, num, insert = res.id
            if hetero.strip() or insert.strip() or not 1 <= num <= 9999:
                raise ValueError(f'Unsupported residue identifier {chain.id}:{res.id}')
            name = res.get_resname().upper()
            if name not in AA3_TO_1 or name not in legacy.SIDECHAIN:
                raise ValueError(f'Nonstandard residue {chain.id}:{num}:{name}')
            if res.is_disordered() or any(atom.is_disordered() for atom in res):
                raise ValueError('Disordered atom or residue needs manual selection')
            required = set('N CA C O'.split()) | set(legacy.SIDECHAIN[name].split())
            if required - set(res.child_dict):
                raise ValueError(f'Incomplete heavy atoms at {chain.id}:{num}')
            if any(not all(math.isfinite(float(x)) for x in atom.coord) for atom in res):
                raise ValueError('Nonfinite atomic coordinates')
            residues[(num, chain.id, name)] = res
    if len(residues) < 2:
        raise ValueError('At least two standard residues are required')
    return s, residues


def select_pairs(legacy, residues, pairs_csv, max_pairs):
    if pairs_csv is None:
        raise ValueError('Explicit observed residue pair list is mandatory for full-AA mode')
    lookup = {(r[1], r[0]): r for r in residues}
    pairs = []
    with Path(pairs_csv).open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        required = {'chain1', 'residue1', 'chain2', 'residue2'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Observed pair CSV requires chain1,residue1,chain2,residue2')
        for line, row in enumerate(reader, 2):
            try:
                a = lookup[(row['chain1'].strip(), int(row['residue1']))]
                b = lookup[(row['chain2'].strip(), int(row['residue2']))]
            except (TypeError, KeyError, ValueError) as exc:
                raise ValueError(f'Pair line {line} not in prepared structure') from exc
            if a == b:
                raise ValueError('Self-pair is not a valid cross-link')
            pairs.append(legacy.pair_key((a, b)))
            if len(pairs) > max_pairs:
                raise ValueError('Too many observed residue pairs')
    if not pairs or len(set(pairs)) != len(pairs):
        raise ValueError('Pair list must be nonempty with no duplicates')
    return pairs


def write_results(legacy, path, model, pairs, distances):
    known = {legacy.pair_key(p) for p in pairs}
    if set(distances) - known:
        raise ValueError('Jwalk output contains unrequested residue pairs')
    cols = ['structure_id','chain1','residue1','aa1','chain2','residue2','aa2',
            'sasd_A','euclidean_A','xp','status','score_model']
    counts = {}
    with Path(path).open('w', newline='', encoding='utf-8') as handle:
        writer=csv.DictWriter(handle, fieldnames=cols)
        writer.writeheader()
        for a,b in pairs:
            aa1,aa2=AA3_TO_1[a[2]],AA3_TO_1[b[2]]
            row={'structure_id':model,'chain1':a[1],'residue1':a[0],'aa1':aa1,
                 'chain2':b[1],'residue2':b[0],'aa2':aa2,'sasd_A':'',
                 'euclidean_A':'','xp':'','status':'','score_model':'DISTANCE_ONLY_V33_OBSERVED_PAIRS'}
            found=distances.get(legacy.pair_key((a,b)))
            if found is None:
                row['status']='NO_SASD_RETURNED'
            else:
                d,e=(float(t) for t in found)
                if not all(math.isfinite(t) for t in (d,e)) or e<0 or d<0:
                    raise ValueError('Jwalk returned invalid distance; no silent adjustment')
                row['sasd_A'],row['euclidean_A']=d,e
                row['status']='DISTANCE_ONLY'
                row['score_model']='DISTANCE_ONLY_V33_NO_LEGACY_XP'
            counts[row['status']]=counts.get(row['status'],0)+1
            writer.writerow(row)
    return counts


def install(legacy):
    """Patch only the in-memory import, never installed source files."""
    legacy.load_structure = lambda path: load_structure(legacy, path)
    legacy.select_pairs = lambda residues, path, count: select_pairs(legacy, residues, path, count)
    legacy.write_results = lambda path, model, pairs, distances: write_results(legacy,path,model,pairs,distances)
    return legacy
