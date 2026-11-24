#!/usr/bin/env python3
"""Conservative PXD -> observed site mapping -> existing NCEMS XP engine.

Input: xHAMLET GitHub store AF3 model/crosslinks/scan_map and AF3_CROSSLINK_DATASETS.
Output: per-observation audit, unique mapped crosslinks, unmatched rows, per-model logs.
Never edits source store, ReLink volumes, conda environments, or xp_pipeline.py.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

from Bio.PDB import MMCIFParser, PDBIO
from Bio.SeqUtils import seq1

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from intake_v33 import (CONTEXT_FIELDS, attach_endpoint, context_id,
                        experimental_context, canonical_json, check_output_location)

REPO_RAW = 'https://raw.githubusercontent.com/SparkyDaBear/xHAMLET/main'
CATALOG_REL = 'assets/AF3_CROSSLINK_DATASETS.md'
SUPPORTED_AA = frozenset('ACDEFGHIKLMNPQRSTVWY')  # v3.1: site mapping for all 20; reactivity checked later
ACCESSION_RANGE_RE = re.compile(r'^([^:;]+):(\d+)-(\d+)$')
MODEL_RE = re.compile(r'\[AF3 model\]\(\.\./store/(PXD\d{6})/af3_predictions/([^/)]+)/model\.cif\)')
PXD_RE = re.compile(r'^PXD\d{6}$')
SEP = '|'

OBS_FIELDS = [
    'pxd','job','dataset','protein_a','protein_b','iptm','scan_id','search_group',
    'search_stage','run','scan','charge','xi_score','alpha_peptide','beta_peptide',
    'alpha_modifications','beta_modifications','alpha_positions','beta_positions',
    'alpha_link_sites','beta_link_sites','ambiguous_source_mapping','protein_a_site',
    'protein_a_aa','protein_b_site','protein_b_aa','chain_a','pdb_site_a',
    'chain_b','pdb_site_b','status','sasd_A','euclidean_A','xp','xp_engine_status',
    'geometry_flag','score_model','detail'
]
UNIQUE_FIELDS = [
    'pxd','job','dataset','protein_a','protein_b','iptm','search_group','chemistry',
    'protein_a_site','protein_a_aa','protein_b_site','protein_b_aa','chain_a',
    'pdb_site_a','chain_b','pdb_site_b','supporting_spectra','evidence_rows',
    'scan_ids','max_xi_score','status','sasd_A','euclidean_A','xp',
    'xp_engine_status','geometry_flag','score_model',
    'chemistry_scope','model_cif_sha256'
]
UNMATCHED_FIELDS = [
    'pxd','scan_id','search_group','alpha_positions','beta_positions',
    'alpha_link_sites','beta_link_sites','xi_score','reason'
]
OBS_FIELDS = list(dict.fromkeys(OBS_FIELDS + CONTEXT_FIELDS + ['model_cif_sha256']))
UNIQUE_FIELDS = list(dict.fromkeys(UNIQUE_FIELDS + CONTEXT_FIELDS))
UNMATCHED_FIELDS = list(dict.fromkeys(UNMATCHED_FIELDS + ['source_row_index', 'raw_observation_json',
    'alpha_peptide', 'beta_peptide', 'alpha_modifications', 'beta_modifications']))
MODEL_FIELDS = ['pxd','job','protein_a','protein_b','dataset','iptm',
                'matching_observation_rows','eligible_unique_site_pairs',
                'scored_pairs','state','detail','model_cif_sha256']

@dataclass(frozen=True)
class Entry:
    pxd: str
    job: str
    dataset: str
    catalog_iptm: str


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, '') for k in fields})


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def parse_catalog(text: str, pxd: str) -> list[Entry]:
    entries = []
    dataset, iptm = '', ''
    for line in text.splitlines():
        if line.startswith('### '):
            dataset, iptm = '', ''
        if line.startswith('**Dataset:**'):
            m = re.search(r'\*\*Dataset:\*\*\s*(.+?)\.\s+\*\*ipTM:\*\*\s*([0-9.]+)', line)
            if m:
                dataset, iptm = m.group(1), m.group(2).rstrip('.')
        m = MODEL_RE.search(line)
        if m and m.group(1) == pxd:
            entries.append(Entry(pxd, m.group(2), dataset, iptm))
    if len({e.job for e in entries}) != len(entries):
        raise ValueError('Catalog has repeated model job names; explicit review needed.')
    return sorted(entries, key=lambda x: x.job)


def normal_accession(accession: str) -> str:
    # Isoform identity must survive mapping. No canonical-coordinate projection is inferred.
    return accession.strip().upper()


def parse_positions(value: str) -> list[tuple[str,int,int]]:
    result = []
    for part in value.split(';'):
        part = part.strip()
        m = ACCESSION_RANGE_RE.fullmatch(part)
        if not m:
            return []
        result.append((normal_accession(m.group(1)),int(m.group(2)),int(m.group(3))))
    return result


def candidate_orientation(row: dict, protein_a: str, protein_b: str) -> str | None:
    """Match only when each peptide could belong to the model's distinct proteins."""
    first = {p[0] for p in parse_positions(row['alpha_positions'])}
    second = {p[0] for p in parse_positions(row['beta_positions'])}
    if protein_a == protein_b:
        return None  # homomer chain assignment requires additional evidence
    if protein_a in first and protein_b in second:
        return 'forward'
    if protein_b in first and protein_a in second:
        return 'reverse'
    return None


def selected_site(row: dict, prefix: str, accession: str) -> tuple[dict | None,str]:
    peptide = row[f'{prefix}_peptide'].strip().upper()
    positions = parse_positions(row[f'{prefix}_positions'])
    # Even multiple identical isoform mappings are not independent confirmations.
    if len(positions) != 1:
        return None, 'AMBIGUOUS_OR_INVALID_PROTEIN_POSITIONS'
    if positions[0][0] != accession:
        return None, 'PROTEIN_ACCESSION_MISMATCH'
    if not peptide or not re.fullmatch('[A-Z]+', peptide):
        return None, 'INVALID_PEPTIDE_SEQUENCE'
    try:
        site = int(row[f'{prefix}_link_sites'])
    except (TypeError,ValueError):
        return None, 'INVALID_LINK_SITE'
    if site == -1:
        return None, 'UNLOCALIZED_LINK_SITE'
    if not (1 <= site <= len(peptide)):
        return None, 'OUT_OF_RANGE_LINK_SITE'
    _, start, end = positions[0]
    if end - start + 1 != len(peptide):
        return None, 'PEPTIDE_RANGE_LENGTH_MISMATCH'
    return {'peptide':peptide,'protein_site':start+site-1,
            'site_aa':peptide[site-1],'peptide_link_pos':site}, ''


def obtain_bytes(source: str, destination: Path, max_bytes: int = 60000000) -> None:
    """Copy/download to a new destination atomically; never overwrite originals."""
    if destination.exists():
        raise FileExistsError(f'Output already exists: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial=destination.with_name(destination.name+'.partial')
    if partial.exists():
        raise FileExistsError(f'Stale partial download requires manual review: {partial}')
    try:
        if source.startswith('https://'):
            request=urllib.request.Request(source,headers={'User-Agent':'NCEMS-PXD-XP-research/0.1'})
            with urllib.request.urlopen(request,timeout=60) as response:
                with partial.open('xb') as out:
                    total=0
                    while True:
                        block=response.read(1024*1024)
                        if not block:
                            break
                        total+=len(block)
                        if total>max_bytes:
                            raise ValueError(f'Download exceeds safety limit ({max_bytes} bytes)')
                        out.write(block)
        else:
            p=Path(source)
            if p.stat().st_size>max_bytes:
                raise ValueError('Input exceeds safety limit')
            with p.open('rb') as inp,partial.open('xb') as out:
                shutil.copyfileobj(inp,out)
        if destination.exists():
            raise FileExistsError(f'Output was created concurrently: {destination}')
        partial.rename(destination)
    except Exception:
        if partial.exists():
            partial.unlink()
        raise


def source_path(base: str | None, relative_path: str) -> str:
    """Relative input starts with 'PXDnnnnnn/'. """
    if base:
        return str(Path(base) / relative_path)
    return f'{REPO_RAW}/store/{relative_path}'


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def load_model(cif: Path):
    model_struct = MMCIFParser(QUIET=True, auth_chains=True, auth_residues=True).get_structure('af3',str(cif))
    models = list(model_struct.get_models())
    if len(models) != 1:
        raise ValueError('Expected exactly one AF3 coordinate model')
    model = models[0]
    chains = list(model.get_chains())
    if sorted(c.id for c in chains) != ['A','B']:
        raise ValueError('AF3 chain IDs are not exactly A/B; manual mapping needed')
    chain_data = {}
    for chain in chains:
        residues = [r for r in chain if r.id[0] == ' ']
        if len(residues) != len(list(chain)):
            raise ValueError('Nonprotein records in CIF; manual preparation needed')
        for r in residues:
            if r.id[2].strip() or r.is_disordered() or not 1 <= r.id[1] <= 9999:
                raise ValueError('Insertion code, alt conformer, or out-of-range residue numbering')
            if not (len(r.resname)==3 and seq1(r.resname) in 'ACDEFGHIKLMNPQRSTVWY'):
                raise ValueError('Unknown residue in CIF')
        sequence = ''.join(seq1(r.resname) for r in residues)
        chain_data[chain.id] = (sequence,residues)
    return model_struct, chain_data


def map_to_chain(site_info: dict, chain: str, chain_data: dict) -> tuple[dict | None,str]:
    sequence, residues = chain_data[chain]
    pep = site_info['peptide']
    start = sequence.find(pep)
    if start < 0:
        return None, 'PEPTIDE_NOT_IN_EXPECTED_CHAIN'
    if sequence.find(pep,start+1) >= 0:
        return None, 'PEPTIDE_REPEATED_IN_EXPECTED_CHAIN'
    other = 'B' if chain == 'A' else 'A'
    if pep in chain_data[other][0]:
        return None, 'PEPTIDE_MATCHES_BOTH_CHAINS'
    expected_start = site_info['protein_site'] - site_info['peptide_link_pos'] + 1
    if any(residues[start+j].id[1] != expected_start+j for j in range(len(pep))):
        return None, 'UNIPROT_TO_CIF_NUMBERING_MISMATCH'
    r = residues[start+site_info['peptide_link_pos']-1]
    actual_aa = seq1(r.resname)
    if actual_aa != site_info['site_aa']:
        return None, 'LINK_AA_SEQUENCE_MISMATCH'
    if r.id[1] != site_info['protein_site']:
        return None, 'UNIPROT_TO_CIF_NUMBERING_MISMATCH'
    return {'chain':chain,'pdb_site':r.id[1], 'site_aa':actual_aa}, ''


def prepare_pdb(structure, outpath: Path):
    writer=PDBIO()
    writer.set_structure(structure)
    writer.save(str(outpath))
    if outpath.stat().st_size < 100:
        raise ValueError('PDB conversion unexpectedly empty')


def engine_pair_key(c1, r1, c2, r2):
    return tuple(sorted(((str(c1),int(r1)), (str(c2),int(r2)))))


def model_observation_base(pxd, job, dataset, iptm, a, b, r, scanmap):
    lookup = scanmap.get(r['scan_id'],{})
    group = lookup.get('search_group', '')
    context = {'chemistry': group.rstrip('/').rsplit('/', 1)[-1] if group else '',
               'chemistry_evidence_status': 'SEARCH_CONFIGURATION_ONLY',
               'chemistry_evidence': 'Frozen scan_map.csv search_group; not an independently confirmed experimental reagent'}
    context.update(experimental_context(pxd, group))
    context['source_chemistry_evidence_status'] = context['chemistry_evidence_status']
    return {
        **context, 'raw_observation_json': canonical_json(r),
        'pxd':pxd,'job':job,'dataset':dataset,'protein_a':a,'protein_b':b,
        'iptm':iptm,'scan_id':r.get('scan_id',''),
        'search_group':lookup.get('search_group',''),
        'search_stage':lookup.get('search_stage',''),
        'run':lookup.get('run',''),'scan':lookup.get('scan',''),
        'charge':r.get('charge',''),'xi_score':r.get('xi_score',''),
        **{k:r.get(k,'') for k in ['alpha_peptide','beta_peptide','alpha_modifications',
          'beta_modifications','alpha_positions','beta_positions',
          'alpha_link_sites','beta_link_sites']},
        'ambiguous_source_mapping': 'YES' if len(parse_positions(r['alpha_positions']))!=1 or len(parse_positions(r['beta_positions']))!=1 else 'NO',
        'chain_a':'A','chain_b':'B','status':'','detail':'','sasd_A':'',
        'euclidean_A':'','xp':'','xp_engine_status':'','geometry_flag':'',
        'score_model':''
    }


def attach_engine(observations: list[dict], engine_rows: list[dict], check_only: bool, fallback_status: str) -> None:
    indexed = {}
    for r in engine_rows:
        try:
            key = engine_pair_key(r['chain1'],r['residue1'],r['chain2'],r['residue2'])
        except (ValueError,KeyError):
            continue
        if key in indexed:
            raise ValueError('XP engine output contained duplicate residue pair')
        indexed[key]=r
    for obs in observations:
        if obs['status'] != 'MAPPED_FOR_XP':
            continue
        if check_only:
            obs['status'] = 'MAPPED_CHECK_ONLY'
            continue
        if fallback_status:
            obs['status'] = fallback_status
            continue
        key=engine_pair_key(obs['chain_a'],obs['pdb_site_a'],obs['chain_b'],obs['pdb_site_b'])
        r=indexed.get(key)
        if not r:
            obs['status']='ENGINE_RESULT_MISSING'
            continue
        for src,dst in [('sasd_A','sasd_A'),('euclidean_A','euclidean_A'),
                        ('xp','xp'),('status','xp_engine_status'),('score_model','score_model')]:
            obs[dst] = r.get(src,'')
        obs['status']=r.get('status','ENGINE_STATUS_MISSING')
        try:
            if obs['sasd_A'] not in ('',None) and obs['euclidean_A'] not in ('',None):
                sasd,euclidean=float(obs['sasd_A']),float(obs['euclidean_A'])
                if sasd >= 0 and sasd+0.05 < euclidean:
                    obs['geometry_flag']='SASD_BELOW_EUCLIDEAN_REVIEW'
        except (ValueError,TypeError):
            obs['geometry_flag']='NONNUMERIC_DISTANCE_REVIEW'


def unique_rows(observations: list[dict], model_cif_hash: str) -> list[dict]:
    grouped = defaultdict(list)
    eligible_states = {'MAPPED_FOR_XP','MAPPED_CHECK_ONLY','SCORED','ABOVE_SCORE_CUTOFF',
                       'NO_SASD_RETURNED','JWALK_MINUS_ONE','DISTANCE_ONLY_NONLEGACY','ENGINE_FAILED',
                       'ENGINE_RESULT_MISSING','ENGINE_STATUS_MISSING','INPUT_CHECK_FAILED',
                       'REFERENCE_PROFILE_NOT_SELECTED','DISTANCE_ONLY','MODEL_FAILED'}
    for r in observations:
        if r['status'] not in eligible_states:
            continue
        if not r.get('pdb_site_a') or not r.get('pdb_site_b'):
            continue
        r['pair_context_id'] = context_id(r)
        key=(r['job'], r['pair_context_id'])
        grouped[key].append(r)
    result=[]
    for k,rows in sorted(grouped.items()):
        base=rows[0]
        ids=sorted({r['scan_id'] for r in rows},key=lambda s:(0,int(s)) if str(s).isdigit() else (1,str(s)))
        try:
            score=str(max(float(r['xi_score']) for r in rows))
        except (TypeError,ValueError):
            score=''
        result.append({
            **{field:base.get(field,'') for field in UNIQUE_FIELDS},
            'chemistry':base.get('chemistry',''),
            'supporting_spectra':len(ids),'evidence_rows':len(rows),
            'scan_ids':';'.join(ids),'max_xi_score':score,
            'chemistry_scope':'V33_POLICY_TO_BE_APPLIED',
            'model_cif_sha256':model_cif_hash,
        })
    return result


def get_engine_rows(engine_out:Path) -> list[dict]:
    path=engine_out/'xp_pairs.csv'
    if not path.exists():
        raise RuntimeError('XP engine reported success but xp_pairs.csv is missing')
    return read_csv(path)


def run_model(entry: Entry, raw_rows: list[dict], scanmap:dict,
              root:Path, base:str|None, engine:Path,ncpus:int,check_only:bool) -> tuple[list[dict],list[dict],dict,set[int]]:
    job=entry.job
    folder=root/'models'/job
    folder.mkdir(parents=True,exist_ok=False)
    model_json={}
    obs=[]
    matched=set()
    status='STARTED'
    detail=''
    cif_hash=''
    a=b=''
    iptm=entry.catalog_iptm
    try:
        pair_path=folder/'pair.json'
        obtain_bytes(source_path(base,f'{entry.pxd}/af3_predictions/{job}/pair.json'),pair_path)
        model_json=json.loads(pair_path.read_text())
        a=normal_accession(model_json['protein_a'])
        b=normal_accession(model_json['protein_b'])
        if a==b:
            raise ValueError('Homomeric model; chain-to-protein mapping needs explicit review')
        if not job.startswith(a.lower()+'__'+b.lower()+'__'):
            raise ValueError('pair.json protein order inconsistent with model job name')
        for idx,r in enumerate(raw_rows):
            direction=candidate_orientation(r,a,b)
            if direction:
                item=model_observation_base(entry.pxd,job,entry.dataset,iptm,a,b,r,scanmap)
                item['_direction']=direction
                item['source_orientation']=direction
                item['source_row_index']=idx+1
                obs.append(item)
                matched.add(idx)
        if not obs:
            status='NO_MATCHING_OBSERVATIONS'
        else:
            confidence=folder/'summary_confidences.json'
            obtain_bytes(source_path(base,f'{entry.pxd}/af3_predictions/{job}/summary_confidences.json'),confidence)
            conf=json.loads(confidence.read_text())
            if 'iptm' in conf:
                iptm=conf['iptm']
                for item in obs:
                    item['iptm']=iptm
            cif=folder/'model.cif'
            obtain_bytes(source_path(base,f'{entry.pxd}/af3_predictions/{job}/model.cif'),cif)
            cif_hash=digest(cif)
            structure,chain_data=load_model(cif)
            prepared=folder/'structure_for_xp.pdb'
            prepare_pdb(structure,prepared)
            valid_pairs=set()
            for item in obs:
                direction=item.pop('_direction')
                # Missing chemistry does not prevent geometry for a localized observation.
                if item['search_stage'] and item['search_stage'] != 'crosslink':
                    item['status']='NOT_CROSSLINK_SEARCH_STAGE'
                    continue
                raw={k:item[k] for k in ['alpha_peptide','alpha_positions','alpha_link_sites',
                                         'beta_peptide','beta_positions','beta_link_sites']}
                first='alpha' if direction=='forward' else 'beta'
                second='beta' if direction=='forward' else 'alpha'
                info_a,reason=selected_site(raw,first,a)
                if reason:
                    item['status']=reason
                    continue
                info_b,reason=selected_site(raw,second,b)
                if reason:
                    item['status']=reason
                    continue
                attach_endpoint(item, 'a', first, info_a)
                attach_endpoint(item, 'b', second, info_b)
                item['model_cif_sha256']=cif_hash
                item['protein_a_site']=info_a['protein_site']
                item['protein_a_aa']=info_a['site_aa']
                item['protein_b_site']=info_b['protein_site']
                item['protein_b_aa']=info_b['site_aa']
                if info_a['site_aa'] not in SUPPORTED_AA or info_b['site_aa'] not in SUPPORTED_AA:
                    item['status']='UNSUPPORTED_AA_IN_XP_MODEL'
                    continue
                mapped_a,reason=map_to_chain(info_a,'A',chain_data)
                if reason:
                    item['status']=reason
                    continue
                mapped_b,reason=map_to_chain(info_b,'B',chain_data)
                if reason:
                    item['status']=reason
                    continue
                item['pdb_site_a']=mapped_a['pdb_site']
                item['pdb_site_b']=mapped_b['pdb_site']
                item['pair_context_id']=context_id(item)
                item['status']='MAPPED_FOR_XP'
                key=engine_pair_key('A',item['pdb_site_a'],'B',item['pdb_site_b'])
                valid_pairs.add(key)
            # v3.3 discovery: geometry is calculated for every localized, mapped
            # observed pair. Parameter availability never filters the distance request.
            if valid_pairs:
                pairs_csv=folder/'observed_pairs.csv'
                save_csv(pairs_csv,['chain1','residue1','chain2','residue2'],
                         [{'chain1':x[0][0],'residue1':x[0][1],
                           'chain2':x[1][0],'residue2':x[1][1]} for x in sorted(valid_pairs)])
                command=[sys.executable,str(engine),'--structure',str(prepared),
                         '--pairs',str(pairs_csv),'--outdir',str(folder/'xp_engine'),
                         '--ncpus',str(ncpus)]
                if check_only:
                    command.append('--check-only')
                write_json(folder/'engine_command.json',command)
                completed=subprocess.run(command,capture_output=True,text=True,check=False)
                (folder/'engine_stdout.txt').write_text(completed.stdout,encoding='utf-8')
                (folder/'engine_stderr.txt').write_text(completed.stderr,encoding='utf-8')
                if completed.returncode != 0:
                    attach_engine(obs,[],check_only=False,fallback_status='INPUT_CHECK_FAILED' if check_only else 'ENGINE_FAILED')
                    status='ENGINE_FAILED'
                    detail=f'Engine exit code {completed.returncode}; read engine_stderr.txt'
                else:
                    xp_rows=[] if check_only else get_engine_rows(folder/'xp_engine')
                    attach_engine(obs,xp_rows,check_only,'')
                    status='CHECK_ONLY' if check_only else 'COMPLETED'
            else:
                status=('REFERENCE_BLOCKED' if any(r['status']=='REFERENCE_PROFILE_NOT_SELECTED' for r in obs) else 'NO_VALID_RESIDUE_PAIRS')
    except Exception as exc:
        status='MODEL_FAILED'
        detail=f'{type(exc).__name__}: {exc}'
        for item in obs:
            if item['status']=='MAPPED_FOR_XP':
                item['status']='MODEL_FAILED'
            if not item['status']:
                item['status']='MODEL_FAILED'
                item['detail']=detail
    finally:
        # Preserve an observation audit even when this model cannot be prepared.
        for item in obs:
            item.pop('_direction',None)
        uniq=unique_rows(obs,cif_hash)
        model_result={
            'pxd':entry.pxd,'job':job,'protein_a':a,'protein_b':b,'dataset':entry.dataset,
            'iptm':iptm,'matching_observation_rows':len(obs),
            'eligible_unique_site_pairs':len(uniq),
            'scored_pairs':sum(1 for r in uniq if r['status']=='SCORED'),
            'state':status,'detail':detail,'model_cif_sha256':cif_hash,
        }
        save_csv(folder/'observations.csv',OBS_FIELDS,obs)
        save_csv(folder/'unique_pairs.csv',UNIQUE_FIELDS,uniq)
        write_json(folder/'model_status.json',model_result)
    return obs,uniq,model_result,matched


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pxd',required=True,help='e.g., PXD064931')
    p.add_argument('--engine',required=True,type=Path,help='EXISTING, tested xp_pipeline.py; never modified')
    p.add_argument('--outdir',required=True,type=Path,help='NEW output directory (not in ReLink store)')
    p.add_argument('--catalog',type=Path,help='Offline path to AF3_CROSSLINK_DATASETS.md; else public GitHub')
    p.add_argument('--local-store',type=Path,help='Offline/local xHAMLET store/ root; read only')
    p.add_argument('--max-models',type=int,default=0,help='0 = full PXD; 1 = one-pair smoke test')
    p.add_argument('--ncpus',type=int,default=1)
    p.add_argument('--check-only',action='store_true',help='Prepare and validate; NO Jwalk/XP scoring')
    args=p.parse_args(argv)
    if not PXD_RE.fullmatch(args.pxd.upper()):
        p.error('--pxd must be PXD plus exactly six digits')
    args.pxd=args.pxd.upper()
    if args.ncpus<1 or args.max_models<0:
        p.error('--ncpus must be positive; --max-models nonnegative')
    engine=args.engine.expanduser().resolve(strict=True)
    if not engine.is_file():
        p.error('--engine must point to an existing file')
    root=args.outdir.expanduser().resolve()
    try:
        check_output_location(root)
    except ValueError as exc:
        p.error(str(exc))
    if root.exists():
        p.error('Output already exists; pick a NEW --outdir to avoid overwriting previous results')
    local_store=args.local_store.expanduser().resolve(strict=True) if args.local_store else None
    if local_store and (root==local_store or local_store in root.parents):
        p.error('Output must be separate from original data store')
    if args.catalog and (root==args.catalog.resolve() or root==args.catalog.resolve().parent):
        p.error('Output must be separate from source catalog')
    root.mkdir(parents=True,exist_ok=False)
    success=False
    try:
        assets=root/'inputs'
        assets.mkdir()
        catalog=assets/'AF3_CROSSLINK_DATASETS.md'
        obtain_bytes(str(args.catalog) if args.catalog else REPO_RAW+'/'+CATALOG_REL,catalog,max_bytes=3000000)
        entries=parse_catalog(catalog.read_text(encoding='utf-8'),args.pxd)
        total_models=len(entries)
        # With no AF3 model, preserve every raw observation as unmatched.
        if args.max_models:
            entries=entries[:args.max_models]
        store_root=str(local_store) if local_store else None
        crosslinks=assets/'crosslinks.csv'
        scanmap_path=assets/'scan_map.csv'
        obtain_bytes(source_path(store_root,f'{args.pxd}/search_results/crosslinks.csv'),crosslinks)
        obtain_bytes(source_path(store_root,f'{args.pxd}/search_results/scan_map.csv'),scanmap_path)
        raw_rows=read_csv(crosslinks)
        expected={'scan_id','alpha_peptide','alpha_positions','alpha_link_sites','beta_peptide',
                  'beta_positions','beta_link_sites','xi_score'}
        if raw_rows and not expected.issubset(raw_rows[0]):
            raise ValueError('Unexpected crosslinks.csv schema')
        scanrows=read_csv(scanmap_path)
        scanmap={r['scan_id']:r for r in scanrows}
        if len(scanmap)!=len(scanrows):
            raise ValueError('Duplicate scan IDs in scan_map.csv')
        obs_all=[]
        uniq_all=[]
        model_results=[]
        matched_indices=set()
        for i,entry in enumerate(entries,1):
            print(f'[{i}/{len(entries)}] {args.pxd} {entry.job}',flush=True)
            obs,uniq,result,matched=run_model(entry,raw_rows,scanmap,root,store_root,engine,args.ncpus,args.check_only)
            obs_all.extend(obs)
            uniq_all.extend(uniq)
            model_results.append(result)
            matched_indices.update(matched)
            print(f'    {result["state"]}: {len(obs)} observations; {len(uniq)} unique candidate sites',flush=True)
        unmatched=[]
        for i,r in enumerate(raw_rows):
            if i in matched_indices:
                continue
            group=scanmap.get(r['scan_id'],{}).get('search_group','')
            unmatched.append({**r, 'source_row_index':i+1, 'raw_observation_json':canonical_json(r),
                'pxd':args.pxd,'scan_id':r['scan_id'],'search_group':group,
                'alpha_positions':r['alpha_positions'],'beta_positions':r['beta_positions'],
                'alpha_link_sites':r['alpha_link_sites'],'beta_link_sites':r['beta_link_sites'],
                'xi_score':r['xi_score'],
                'reason':'NO_MATCH_IN_SELECTED_AF3_MODELS' if len(entries)<total_models else 'NO_STORED_AF3_PROTEIN_PAIR_MATCH'})
        save_csv(root/'xp_observations.csv',OBS_FIELDS,obs_all)
        save_csv(root/'xp_unique_pairs.csv',UNIQUE_FIELDS,uniq_all)
        save_csv(root/'unmatched_observations.csv',UNMATCHED_FIELDS,unmatched)
        save_csv(root/'model_summary.csv',MODEL_FIELDS,model_results)
        model_states=Counter(r['state'] for r in model_results)
        failed=bool(model_states.get('MODEL_FAILED') or model_states.get('ENGINE_FAILED'))
        scored=sum(1 for r in uniq_all if r['status']=='SCORED')
        run_state=('PARTIAL_FAILURE' if failed else
                   'CHECK_ONLY_COMPLETE' if args.check_only else
                   'COMPLETE_NO_SCORED_PAIRS' if scored==0 else 'COMPLETE')
        summary={
            'state':run_state,
            'mode':'CHECK_ONLY_NO_XP' if args.check_only else 'XP_RUN',
            'intake_version':'3.3.0', 'geometry_scope':'ALL_LOCALIZED_MAPPED_OBSERVATIONS',
            'distinct_raw_rows_with_model_match':len(matched_indices),
            'input_accounting_ok':len(matched_indices)+len(unmatched)==len(raw_rows),
            'pxd':args.pxd,'models_in_catalog':total_models,'models_selected':len(entries),
            'raw_search_result_rows':len(raw_rows),
            'matched_model_observation_rows':len(obs_all),
            'unmatched_raw_rows':len(unmatched),
            'unique_modeled_site_and_chemistry_rows':len(uniq_all),
            'unique_modeled_site_rows_ignoring_chemistry':len({(r['job'],r['chain_a'],r['pdb_site_a'],r['chain_b'],r['pdb_site_b']) for r in uniq_all}),
            'observation_status_counts':dict(Counter(r['status'] for r in obs_all)),
            'model_state_counts':dict(model_states),
            'xp_scored_unique_rows':scored,
            'engine_sha256':digest(engine),'catalog_sha256':digest(catalog),
            'crosslinks_sha256':digest(crosslinks),'scan_map_sha256':digest(scanmap_path),
            'source':'local-store:'+str(local_store) if local_store else REPO_RAW,
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'limitations':['Distance-only intake: chemistry-aware scores are calculated in v3.3 analysis.',
                           'XP is a Gaussian density, not an experimental event probability.',
                           'Model chain order assumes pair.json protein_a -> A, protein_b -> B; peptides and numbering are verified.',
                           'Ambiguous and unlocalized observations remain unscored, not XP=0.',
                           'No UniProt H1/H2 annotations or cross-PXD statistical inference calculated.',
                           'Jwalk numerical and AF3 geometry anomalies still require review.']
        }
        write_json(root/'run_summary.json',summary)
        print('=== COMBINED OUTPUTS ===')
        for f in ('xp_unique_pairs.csv','xp_observations.csv','unmatched_observations.csv','model_summary.csv','run_summary.json'):
            print(root/f)
        print('STATUS:',summary['state'],summary['model_state_counts'])
        success=True
        return 3 if failed else 0
    except Exception as exc:
        write_json(root/'batch_error.json',{'error':f'{type(exc).__name__}: {exc}',
                                             'created_utc':datetime.now(timezone.utc).isoformat()})
        print(f'ERROR: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 2
    finally:
        if not success:
            print(f'Existing partial files preserved at: {root}',file=sys.stderr)

if __name__=='__main__':
    raise SystemExit(main())
