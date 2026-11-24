"""Lossless context handling for reported, localized ReLink observations.

Nothing in this module infers a covalent reaction from an amino-acid letter.
Original peptide modification arrays remain in the observation export.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from functools import lru_cache
import re


CONTEXT_FIELDS = [
    'pair_context_id', 'chemistry', 'chemistry_evidence_status',
    'chemistry_evidence', 'source_chemistry_evidence_status', 'source_row_index', 'source_orientation',
    'raw_observation_json',
] + [f'endpoint_{side}_{name}' for side in ('a', 'b') for name in (
    'kind', 'blocked', 'evidence', 'modifications', 'modification_localization',
    'raw_peptide_modifications', 'source_prefix', 'peptide_link_pos',
    'reported_kind', 'annotation_status')]


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def endpoint_modifications(value, peptide_link_pos, peptide_length, endpoint_kind='SIDECHAIN'):
    """Select only modifications known to affect this endpoint.

    ReLink JSON positions are one-based peptide positions. Terminal and malformed
    positions are retained as unresolved unless an explicit matching terminal
    endpoint is supplied. This deliberately avoids calling a peptide terminus a
    protein terminus or dropping an ambiguously localized modification.
    """
    if value is None or str(value).strip() == '':
        return '', 'MODIFICATIONS_NOT_REPORTED'
    try:
        records = json.loads(value) if isinstance(value, str) else value
    except (ValueError, TypeError):
        records = [{'unresolved_annotation': str(value)}]
    if not isinstance(records, list):
        records = [records]
    selected, uncertain = [], False
    kind = str(endpoint_kind or 'SIDECHAIN').upper()
    for record in records:
        if not isinstance(record, dict):
            selected.append({'unresolved_annotation': record})
            uncertain = True
            continue
        raw = record.get('location', record.get('position'))
        try:
            pos = int(str(raw))
        except (ValueError, TypeError):
            pos = None
        if pos is not None and 1 <= pos <= peptide_length:
            if pos == peptide_link_pos:
                selected.append(record)
        elif pos == 0 and kind in ('PROTEIN_NTERM', 'PEPTIDE_NTERM'):
            selected.append(record)
        elif pos == peptide_length + 1 and kind in ('PROTEIN_CTERM', 'PEPTIDE_CTERM'):
            selected.append(record)
        else:
            selected.append({**record, 'endpoint_localization': 'UNRESOLVED'})
            uncertain = True
    return canonical_json(selected), ('UNRESOLVED_MODIFICATION_LOCALIZATION' if uncertain
                                      else 'ENDPOINT_LOCALIZATION_CHECKED')


def attach_endpoint(item, side, raw_prefix, info):
    prefix = f'endpoint_{side}_'
    raw = json.loads(item.get('raw_observation_json') or '{}')
    # Optional input annotations must be oriented with the peptide, not with the
    # AF3 chain. Unannotated residues default to a sidechain hypothesis.
    kind = raw.get(raw_prefix + '_endpoint_kind', '')
    reported_kind = kind
    annotation_status = 'AS_REPORTED' if kind else 'ENDPOINT_KIND_NOT_REPORTED'
    from chemistry_rules import _kind
    group = _kind(kind, info['site_aa'])[0]
    if ((group in ('PROTEIN_NTERM', 'PEPTIDE_NTERM') and info['peptide_link_pos'] != 1)
            or (group in ('PROTEIN_CTERM', 'PEPTIDE_CTERM') and info['peptide_link_pos'] != len(info['peptide']))):
        kind = 'UNRESOLVED_TERMINAL_ASSIGNMENT'
        annotation_status = 'TERMINAL_KIND_CONTRADICTS_PEPTIDE_LINK_POSITION'
    mods = item.get(raw_prefix + '_modifications', '')
    selected, status = endpoint_modifications(mods, info['peptide_link_pos'], len(info['peptide']), kind)
    item.update({
        prefix + 'kind': kind,
        prefix + 'blocked': raw.get(raw_prefix + '_endpoint_blocked', ''),
        prefix + 'evidence': raw.get(raw_prefix + '_endpoint_evidence', ''),
        prefix + 'modifications': selected,
        prefix + 'modification_localization': status,
        prefix + 'raw_peptide_modifications': mods,
        prefix + 'source_prefix': raw_prefix,
        prefix + 'peptide_link_pos': info['peptide_link_pos'],
        prefix + 'reported_kind': reported_kind,
        prefix + 'annotation_status': annotation_status,
    })


def context_id(row):
    """Distinct reaction/PTM contexts never collapse just because sites match."""
    ends = []
    for side in ('a', 'b'):
        ends.append({
            'protein': row.get(f'protein_{side}', ''),
            'site': str(row.get(f'protein_{side}_site', '')),
            'aa': row.get(f'protein_{side}_aa', ''),
            'chain': row.get(f'chain_{side}', ''),
            'pdb_site': str(row.get(f'pdb_site_{side}', '')),
            **{name: row.get(f'endpoint_{side}_{name}', '') for name in (
                'kind', 'blocked', 'evidence', 'modifications', 'modification_localization',
                'reported_kind', 'annotation_status')},
        })
    payload = {'ends': sorted(ends, key=canonical_json),
               'search_group': row.get('search_group', ''),
               'chemistry': row.get('chemistry', ''),
               'chemistry_evidence_status': row.get('source_chemistry_evidence_status', row.get('chemistry_evidence_status', '')),
               'chemistry_evidence': row.get('chemistry_evidence', '')}
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


@lru_cache(maxsize=4)
def load_experimental_context(path):
    """Read an immutable per-run snapshot once; reject type-changing evidence."""
    data = json.loads(Path(path).read_text())
    if data.get('schema') != 'NCEMS_EXPERIMENTAL_CONTEXT_V1' or not isinstance(data.get('entries'), list):
        raise ValueError('Invalid experimental-context schema')
    indexed = {}
    for item in data['entries']:
        if not isinstance(item, dict):
            raise ValueError('Each experimental-context entry must be an object')
        for field in ('pxd', 'search_group', 'chemistry', 'chemistry_evidence_status', 'chemistry_evidence'):
            if not isinstance(item.get(field), str) or (field != 'search_group' and not item[field].strip()):
                raise ValueError('Experimental-context field must be a string: ' + field)
        if not re.fullmatch(r'PXD[0-9]{6}', item['pxd']):
            raise ValueError('Invalid experimental-context PXD')
        if item['chemistry_evidence_status'] not in ('EXPERIMENT_REAGENT_CONFIRMED', 'SEARCH_CONFIGURATION_ONLY', 'UNRESOLVED'):
            raise ValueError('Invalid experimental-context evidence status')
        key = (item['pxd'], item['search_group'])
        if key in indexed:
            raise ValueError('Duplicate PXD/search-group experimental context')
        indexed[key] = item
    return indexed


def experimental_context(pxd, search_group):
    """Optional reviewed reagent evidence; exact PXD AND search group required."""
    path = os.environ.get('NCEMS_EXPERIMENTAL_CONTEXT')
    if not path:
        return {}
    match = load_experimental_context(path).get((pxd, search_group), {})
    return {k: match[k] for k in ('chemistry', 'chemistry_evidence_status', 'chemistry_evidence') if k in match}


def check_output_location(path, required_mount=None):
    path = Path(path).expanduser().resolve()
    media = Path('/media/volume')
    volume = Path(required_mount or '/media/volume/xhamlet-data-5').resolve()
    if path == media or media in path.parents:
        mounted = os.path.ismount(volume)
        if not mounted:
            import re
            try:
                mounted = any(Path(re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), line.split()[4])) == volume
                              for line in Path('/proc/self/mountinfo').read_text().splitlines())
            except (OSError, IndexError):
                mounted = False
        if path == volume or volume not in path.parents or not mounted:
            raise ValueError('Output under /media/volume requires a mounted xhamlet-data-5 and a separate subdirectory')
    return path
