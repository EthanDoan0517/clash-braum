"""Bounded single-vertex backoff at exact failed frames plus original art poses."""
from pathlib import Path
import json
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
source = json.loads((ROOT / 'validation/torso_local_alternatives.json').read_text())
failed = json.loads((ROOT / 'validation/torso_outline_recovery_audit.json').read_text())['new_intersection_frame_details']
targeted = json.loads((ROOT / 'validation/torso_outline_half_targeted.json').read_text())
cases = sorted({(r['clip'], r['frame']) for r in failed + targeted['revisions']['before']['poses']})
before = source['endpoint_data']['143']['weights']
half = source['candidate_weights']['outline_s0.5']['Object002']['143']
candidate = {'scene_sha256': source['scene_sha256'], 'method': 'Single-vertex interpolation toward original torso weights; diagnostic only', 'candidate_weights': {}}
for amount in (.75, .5, .25, .125, .0625):
    weights = {k: before[k] + amount * (half[k] - before[k]) for k in before}
    total = sum(weights.values())
    candidate['candidate_weights'][f'half_times_{amount}'] = {'Object002': {'143': {k: v / total for k, v in weights.items()}}}
(ROOT / 'validation/torso_outline_backoff_candidates.json').write_text(json.dumps(candidate, indent=2))
summary = {'cases': cases, 'trials': [], 'scope': 'Exact half-strength failure frames plus original 15 poses; no scene saves or acceptance'}
for key in candidate['candidate_weights']:
    output = f'torso_outline_backoff_{key}.json'
    sys.argv = ['validate', '--', '--candidate-weights', f'torso_outline_backoff_candidates.json:{key}', '--output', output]
    for clip, frame in cases:
        sys.argv += ['--case', f'{clip}:{frame}']
    runpy.run_path(str(ROOT / 'work/scripts/validate_torso_coupled_targeted.py'), run_name='__main__')
    result = json.loads((ROOT / 'validation' / output).read_text())
    rows = result['revisions']['after']['poses']
    bad = [r for r in rows if r['new_local_intersections']]
    summary['trials'].append({'candidate': key, 'failure_frames': len(bad), 'new_pair_occurrences': sum(len(r['new_local_intersections']) for r in bad), 'failures': bad, 'target_poses': [r for r in rows if (r['clip'], r['frame']) in [('braum_spell4', 17), ('braum_dance_loop', 50)]]})
    (ROOT / 'validation/torso_outline_backoff_search.json').write_text(json.dumps(summary, indent=2))
    print('BACKOFF', key, 'failure frames', len(bad), flush=True)
