"""Score a complete v3.3 distance intake without discarding candidate evidence."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import statistics

from geometry_audit_v33 import CoordinateAudit, finite_number, read_csv, write_csv, write_json, sha256
from intake_v33 import context_id
from xp_policy_v33 import Policy, FIELDS, VERSION, METRIC

REQUIRED = ('xp_unique_pairs.csv', 'xp_observations.csv', 'model_summary.csv',
            'unmatched_observations.csv', 'run_summary.json')
CHANNELS = ('xp_primary', 'xp_exploratory', 'reference_geometry_score')


def pair_key(row):
    if not row.get('pdb_site_a') or not row.get('pdb_site_b'):
        return None
    expected = context_id(row)
    if row.get('pair_context_id') != expected:
        raise ValueError('Missing or inconsistent v3.3 reaction-context identity; full intake rerun required')
    return row.get('job', ''), expected


def score_statistics(rows):
    groups = defaultdict(list)
    for row in rows:
        for channel in CHANNELS:
            value = finite_number(row.get(channel))
            if value is None:
                continue
            prefix = 'reference_geometry' if channel == 'reference_geometry_score' else channel
            key = (row['pxd'], row['job'], row.get('linker_normalized', ''), channel,
                   row.get(prefix + '_profile_id', ''))
            groups[key].append(value)
    out = []
    for key, values in sorted(groups.items()):
        out.append(dict(zip(('pxd', 'job', 'linker_normalized', 'score_channel', 'profile_id'), key),
                        n_pair_contexts=len(values), n_positive=sum(x > 0 for x in values),
                        n_zero=sum(x == 0 for x in values), sum=sum(values),
                        mean=statistics.mean(values), median=statistics.median(values),
                        sample_sd=statistics.stdev(values) if len(values) > 1 else '',
                        sd_definition='Sample SD across unique scored reaction contexts (n-1); not model sigma or uncertainty',
                        scope='Descriptive; dependent observations and selection bias prevent inferential interpretation'))
    return out


def _numeric_counts(rows, channel):
    values = [finite_number(r.get(channel)) for r in rows]
    return {'numeric': sum(v is not None for v in values),
            'positive': sum(v is not None and v > 0 for v in values),
            'zero': sum(v == 0 for v in values), 'missing': sum(v is None for v in values)}


def analyze(source, out, pxd, policy=None):
    source, out = Path(source).resolve(strict=True), Path(out).resolve()
    if out.exists():
        raise FileExistsError('Output exists; no previous result may be overwritten')
    if source == out or source in out.parents or out in source.parents:
        raise ValueError('Output must be separate from source distance files')
    for name in REQUIRED:
        if not (source / name).is_file():
            raise FileNotFoundError('Incomplete distance intake: ' + name)
    run = json.loads((source / 'run_summary.json').read_text())
    if run.get('pxd') != pxd or run.get('mode') != 'XP_RUN':
        raise ValueError('Expected completed distance intake for the requested PXD')
    if run.get('intake_version') != '3.3.0' or run.get('geometry_scope') != 'ALL_LOCALIZED_MAPPED_OBSERVATIONS':
        raise ValueError('Old or filtered distance exports are not silently reused; perform a full v3.3 rerun')
    uf, unique = read_csv(source / 'xp_unique_pairs.csv')
    of, observations = read_csv(source / 'xp_observations.csv')
    mf, models = read_csv(source / 'model_summary.csv')
    nf, unmatched = read_csv(source / 'unmatched_observations.csv')
    checks = [(models, 'models_selected'), (observations, 'matched_model_observation_rows'),
              (unique, 'unique_modeled_site_and_chemistry_rows'), (unmatched, 'unmatched_raw_rows')]
    for records, count_name in checks:
        if len(records) != run.get(count_name):
            raise ValueError('Source accounting mismatch: ' + count_name)
        if any(r.get('pxd') != pxd for r in records):
            raise ValueError('Mixed or missing PXD identifiers')
    model_ids = [r['job'] for r in models]
    if len(set(model_ids)) != len(model_ids):
        raise ValueError('Repeated model identity')
    keys = [pair_key(r) for r in unique]
    if None in keys or len(set(keys)) != len(keys):
        raise ValueError('Unique reaction contexts are missing or duplicated')
    supports = defaultdict(list)
    for r in observations:
        key = pair_key(r)
        if key:
            supports[key].append(r)
    for row, key in zip(unique, keys):
        matches = supports.get(key, [])
        scans = {r['scan_id'] for r in matches}
        if int(row['evidence_rows']) != len(matches) or int(row['supporting_spectra']) != len(scans):
            raise ValueError('Unique/observation support counts disagree')
        if set(filter(None, row['scan_ids'].split(';'))) != scans:
            raise ValueError('Unique/observation scan identities disagree')
        for match in matches:
            for field in ('sasd_A', 'euclidean_A'):
                x, y = finite_number(row.get(field)), finite_number(match.get(field))
                if (x is None) != (y is None) or (x is not None and not math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12)):
                    raise ValueError('Unique/observation distance conflict: ' + field)
    if set(supports) != set(keys):
        raise ValueError('Mapped observations missing from unique-context audit')
    # One source row may be represented in more than one stored AF3 model. The
    # accounting below is over original rows, not over model-observation copies.
    matched_ids = {int(r['source_row_index']) for r in observations}
    unmatched_ids = {int(r['source_row_index']) for r in unmatched}
    if matched_ids & unmatched_ids or len(unmatched_ids) != len(unmatched):
        raise ValueError('Unmatched source rows duplicate or overlap mapped-source rows')
    if matched_ids | unmatched_ids != set(range(1, int(run['raw_search_result_rows']) + 1)):
        raise ValueError('At least one original ReLink observation was lost or invented')
    policy = policy or Policy(mode='discovery')
    audit = CoordinateAudit(source)
    scored_unique = []
    for row in unique:
        result = policy.evaluate({**row, 'distance_metric': METRIC}, audit.for_row(row))
        result['intake_status'] = row.get('status', '')
        result['status'] = result['score_status']
        result['score_model'] = result.get('parameter_profile', '')
        scored_unique.append(result)
    by_key = {key: row for key, row in zip(keys, scored_unique)}
    scored_obs = []
    for row in observations:
        key = pair_key(row)
        if key in by_key:
            value = by_key[key]
            result = {**row, **{field: value.get(field, '') for field in FIELDS}}
            result['legacy_xp_unverified'] = row.get('xp', '')
            result['legacy_score_status'] = row.get('status', '')
            result['intake_status'] = row.get('status', '')
            result['status'] = value['score_status']
            result['score_model'] = value.get('parameter_profile', '')
        else:
            result = policy.evaluate({**row, 'distance_metric': METRIC})
            result['intake_status'] = row.get('status', '')
            result['status'] = result['score_status']
        scored_obs.append(result)
    out.mkdir(parents=True, exist_ok=False)
    backup = out / 'distance_intake_tables'
    backup.mkdir()
    for name in REQUIRED:
        shutil.copyfile(source / name, backup / name)
    policy.snapshot(out / 'reference_snapshot')
    extra = ['intake_status', *FIELDS]
    write_csv(out / 'xp_unique_pairs.csv', scored_unique, uf + extra)
    write_csv(out / 'xp_observations.csv', scored_obs, of + extra)
    write_csv(out / 'unmatched_observations.csv', unmatched, nf)
    # Review records retain candidates regardless of whether a numerical score is
    # available. No automatic experimental-validation status is ever assigned.
    queue = []
    for row in scored_unique:
        queue.append({**row, 'review_record_type': 'UNIQUE_MAPPED_REACTION_CONTEXT',
                      'review_priority': 'CHEMISTRY_CONFLICT' if row.get('chemistry_status') == 'CONFLICTING'
                      else 'SOURCE_SCOPED_SCORE_NEEDS_IDENTIFICATION_VALIDATION' if finite_number(row.get('xp_primary')) is not None
                      else 'EXPLORATORY_OR_UNKNOWN_REQUIRES_REVIEW'})
    for row in scored_obs:
        if pair_key(row) is None:
            queue.append({**row, 'review_record_type': 'UNMAPPED_MODEL_OBSERVATION', 'review_priority': 'MAPPING_REVIEW'})
    for row in unmatched:
        queue.append({**row, 'review_record_type': 'NO_STORED_MODEL_MATCH',
                      'review_priority': 'MODEL_OR_MAPPING_REQUIRED', 'validation_status': 'REQUIRES_EXPERIMENTAL_VALIDATION',
                      'review_reason': row.get('reason', '')})
    qfields = list(dict.fromkeys(['review_record_type', 'review_priority'] + uf + of + nf + extra))
    write_csv(out / 'novelty_review_queue.csv', queue, qfields)
    model_out = []
    for model in models:
        rows = [r for r in scored_unique if r['job'] == model['job']]
        mnxl = [finite_number(r.get('mnxl2016_contribution')) for r in rows]
        mnxl = [v for v in mnxl if v is not None]
        violations = [finite_number(r.get('mnxl2016_violation_count')) for r in rows]
        violations = [v for v in violations if v is not None]
        excess = [finite_number(r.get('mnxl2016_violation_excess_A')) for r in rows]
        excess = [v for v in excess if v is not None]
        inaccessible = [finite_number(r.get('mnxl2016_nonaccessible_count')) for r in rows]
        inaccessible = [v for v in inaccessible if v is not None]
        model_out.append({**model, 'n_pair_contexts': len(rows),
                          'n_primary_numeric': _numeric_counts(rows, 'xp_primary')['numeric'],
                          'n_exploratory_numeric': _numeric_counts(rows, 'xp_exploratory')['numeric'],
                          'n_reference_geometry_numeric': _numeric_counts(rows, 'reference_geometry_score')['numeric'],
                          'mnxl2016_sum_known_contributions': sum(mnxl) if mnxl else '',
                          'mnxl2016_n_known_contributions': len(mnxl),
                          'mnxl2016_n_missing_or_outside_scope': len(rows) - len(mnxl),
                          'mnxl2016_NoV_known_distances': sum(violations) if violations else '',
                          'mnxl2016_SoVD_known_distances_A': sum(excess) if excess else '',
                          'mnxl2016_n_backend_nonaccessible': sum(inaccessible) if inaccessible else '',
                          'mnxl2016_ensemble_normalized_score': '',
                          'mnxl2016_normalization_status': 'NOT_APPLIED; CONTEXT_COUNTS_ARE_NOT_AN_INDEPENDENT_MODEL_ENSEMBLE',
                          'scientifically_validated_links': '',
                          'validation_status': 'NOT_ESTABLISHED_BY_THIS_PIPELINE'})
    write_csv(out / 'model_summary.csv', model_out, mf + ['n_pair_contexts', 'n_primary_numeric',
              'n_exploratory_numeric', 'n_reference_geometry_numeric',
              'mnxl2016_sum_known_contributions', 'mnxl2016_n_known_contributions',
              'mnxl2016_n_missing_or_outside_scope', 'mnxl2016_NoV_known_distances',
              'mnxl2016_SoVD_known_distances_A', 'mnxl2016_n_backend_nonaccessible',
              'mnxl2016_ensemble_normalized_score', 'mnxl2016_normalization_status',
              'scientifically_validated_links', 'validation_status'])
    stats = score_statistics(scored_unique)
    statfields = ['pxd', 'job', 'linker_normalized', 'score_channel', 'profile_id', 'n_pair_contexts',
                  'n_positive', 'n_zero', 'sum', 'mean', 'median', 'sample_sd', 'sd_definition', 'scope']
    write_csv(out / 'score_statistics.csv', stats, statfields)
    counts = {channel: _numeric_counts(scored_unique, channel) for channel in CHANNELS}
    failed = run.get('state') == 'PARTIAL_FAILURE' or any(m['state'] in ('MODEL_FAILED', 'ENGINE_FAILED') for m in models)
    numeric_any = sum(any(finite_number(r.get(c)) is not None for c in CHANNELS) for r in scored_unique)
    state = 'PARTIAL_FAILURE' if failed else ('COMPLETE_WITH_NUMERIC_OUTPUTS' if numeric_any else 'COMPLETE_NO_USABLE_GEOMETRY')
    summary = {
        'pxd': pxd, 'version': VERSION, 'state': state, 'input_run': str(source),
        'created_utc': datetime.now(timezone.utc).isoformat(), 'policy': policy.manifest(),
        'raw_search_result_rows': run['raw_search_result_rows'],
        'distinct_source_rows_with_model_match': len(matched_ids), 'unmatched_source_rows': len(unmatched),
        'model_observation_rows': len(observations), 'unique_pair_contexts': len(scored_unique),
        'input_accounting_ok': True, 'models_selected': len(models), 'models_in_catalog': run['models_in_catalog'],
        'full_catalog_processed': len(models) == run['models_in_catalog'],
        'score_counts': counts, 'numeric_xp_pairs': counts['xp_primary']['numeric'],
        'exploratory_xp_pairs': counts['xp_exploratory']['numeric'],
        'reference_geometry_pairs': counts['reference_geometry_score']['numeric'],
        'pairs_without_any_numeric_output': len(scored_unique) - numeric_any,
        'chemistry_status_counts': dict(Counter(r['chemistry_status'] for r in scored_unique)),
        'score_status_counts': dict(Counter(r['score_status'] for r in scored_unique)),
        'model_state_counts': dict(Counter(r['state'] for r in models)),
        'scientifically_validated_xl_count': None,
        'scientific_validation_status': 'NOT_ESTABLISHED_BY_PROCESS_COMPLETION_OR_SCORE',
        'source': run.get('source', ''),
        'input_sha256': {name: sha256(source / name) for name in REQUIRED},
        'limitations': [
            'Gaussian scores are densities in inverse angstrom, not probabilities of true links.',
            'Unknown-chemistry common-reference geometry is counterfactual and not chemistry-specific XP.',
            'A search configuration is not independent evidence of the reagent used.',
            'A missing value is not zero; zero means a usable distance exceeded that profile cutoff.',
            'One source row can map to multiple stored models; unique contexts are model-specific.',
            'Homomer chain assignment, unknown isoform projection and unlocalized links require additional evidence.',
            'This pipeline does not re-search spectra, estimate FDR, or validate novel covalent chemistry.',
            'Sample SD summarizes scores; sigma_A is a model parameter, not uncertainty in a candidate score.',
        ],
    }
    write_json(out / 'run_summary.json', summary)
    artifact_names = {'pair.json', 'summary_confidences.json', 'model.cif', 'structure_for_xp.pdb',
                      'input_structure.pdb', 'summary.json', 'distance_diagnostics.csv', 'xp_pairs.csv',
                      'engine_command.json', 'crosslinks.csv', 'scan_map.csv', 'AF3_CROSSLINK_DATASETS.md'}
    artifacts = [{'relative_path': str(path.relative_to(source)), 'size_bytes': path.stat().st_size,
                  'sha256': sha256(path)} for path in sorted(source.rglob('*'))
                 if path.is_file() and path.name in artifact_names]
    write_json(out / 'input_artifact_manifest.json', {'source_root': str(source), 'artifacts': artifacts,
               'note': 'Complete copied sources and backend logs remain in distance_run; this manifest identifies their bytes.'})
    (out / 'READ_RESULTS.txt').write_text(
        'NCEMS XP v3.3 — read run_summary.json before interpreting CSVs.\n\n'
        'xp is an alias for xp_primary only. xp_primary requires source-scoped parameters,\n'
        'compatible endpoints and declared experimental reagent evidence. It is not XL validation.\n'
        'xp_exploratory contains exact-profile scores under unconfirmed search chemistry or\n'
        'documented model transfers. It is separate from primary XP.\n'
        'reference_geometry_score applies the same explicit reference function to usable\n'
        'geometry. It cannot validate unknown chemistry. A chemistry-conflicting diagnostic\n'
        'is excluded from chemistry-supported discovery candidates.\n'
        'Blank means unscored/unavailable. Zero means above the specific profile cutoff.\n'
        'Every source observation is retained in xp_observations.csv or unmatched_observations.csv;\n'
        'model-specific copies are possible. novelty_review_queue.csv includes all mapped contexts\n'
        'and unresolved observations. Review raw spectra/localization/FDR/chemistry before any claim.\n'
        'score_statistics.csv keeps profile and score channel separate. sample_sd is descriptive;\n'
        'it is not sigma_A or a confidence interval. Original geometry and hashes remain in the run.\n'
    )
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pxd')
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    result = analyze(args.source, args.out, args.pxd.upper())
    print(json.dumps(result, indent=2))
    return 3 if result['state'] == 'PARTIAL_FAILURE' else 0


if __name__ == '__main__':
    raise SystemExit(main())
