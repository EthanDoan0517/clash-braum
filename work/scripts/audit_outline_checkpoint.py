"""Verify recovered half-strength evidence without regenerating scenes or exports."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def read(name):
    return json.loads((ROOT / 'validation' / name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


candidate = read('torso_local_alternatives.json')
full = read('torso_outline_validation.json')
parent = read('torso_validation.json')
export = read('model_torso_outline_export.json')
target = read('torso_outline_half_targeted.json')
key = 'torso_local_alternatives.json:outline_s0.5'
scene_hash = sha(ROOT / 'work/scenes/clash_braum_torso.blend')
assert scene_hash == candidate['scene_sha256'] == full['input_scene_sha256']['refined'] == export['input_scene_sha256']
assert full['candidate_weights'] == export['candidate_weights'] == target['candidate_weights'] == key
weights = candidate['candidate_weights']['outline_s0.5']
assert weights == full['authored_candidate_weights'] == export['authored_candidate_weights']
assert set(weights) == {'Object002'} and set(weights['Object002']) == {'143'}
clips = read('draft_animation_samples.json')['animations']
expected = [(c['name'], c['frames']) for c in clips]
assert len(expected) == 59 and sum(n for _, n in expected) == 3963
assert [(c['clip'], c['frames_checked']) for c in full['revisions']['refined']['clips']] == expected
for clip in clips:
    assert sha(ROOT / clip['source']) == full['source_anm_sha256'][clip['name']]
revision = full['revisions']['refined']
assert revision['total_frames'] == 3963
assert revision['all_coordinates_finite'] and revision['normalized_max_four_weights']
assert full['native_rest_contract_unchanged'] and full['imported_action_channels_unchanged']
assert revision['rigid_component_max_position_error'] < 1e-5
assert len(revision['digit_assignments']) == 10
assert export['exact_native_joint_records'] and export['shield_rigid']
assert target['all_rest_geometry_and_unlisted_weights_unchanged'] and target['topology_and_uv_unchanged']
assert target['revisions'] == read('torso_outline_half_culling_check.json')['revisions']
comparison = {}
for name, metrics in revision['edge_stretch_metrics'].items():
    before = parent['revisions']['refined']['edge_stretch_metrics'][name]
    comparison[name] = {k: metrics[k] - before[k] for k in ('max_edge_ratio', 'max_p99_edge_ratio')}
report = {
    'candidate': key, 'parent_scene_sha256': scene_hash,
    'recovered_full_structural_validation_verified': True,
    'source_anm_hashes_verified': 59,
    'candidate_export_report_verified': True,
    'optimized_targeted_results_exactly_equal_original': True,
    'all_frame_edge_metric_delta_from_accepted_torso': comparison,
    'candidate_export_files_sha256': {p.name: sha(p) for p in sorted((ROOT / 'build/model_torso_outline').glob('braum_clash.*'))},
    'candidate_saved_or_promoted_by_this_script': False,
}
local_path = ROOT / 'validation/torso_outline_half_all_frame_local.json'
if local_path.exists():
    local = json.loads(local_path.read_text())
    if local.get('sample_count_per_revision') == 3963:
        assert local['candidate_weights'] == key
        rows = local['revisions']['after']['poses']
        assert len(rows) == 3963
        failures = [r for r in rows if r['new_local_intersections']]
        report['all_frame_local_surface_check_complete'] = True
        report['frames_with_new_local_intersections'] = len(failures)
        report['new_intersection_frame_details'] = failures
        report['removed_pair_frame_occurrences'] = sum(len(r['removed_local_intersections']) for r in rows)
        report['local_surface_regression_passed'] = not failures
        report['candidate_disposition'] = 'REJECTED: new local intersections; retain accepted torso parent' if failures else 'Surface check passed; promotion still requires visual acceptance'
    else:
        report['all_frame_local_surface_check_complete'] = False
(ROOT / 'validation/torso_outline_recovery_audit.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k not in ('all_frame_edge_metric_delta_from_accepted_torso', 'new_intersection_frame_details')}, indent=2))
