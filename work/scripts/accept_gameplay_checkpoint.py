"""Record visual review and preserve a byte-identical, verified gameplay baseline."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[2]
def read(name):return json.loads((ROOT/'validation'/name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
source=ROOT/'work/scenes/clash_braum_torso.blend'
target=ROOT/'work/scenes/clash_braum_gameplay_accepted.blend'
expected='2501fd57112bb324515e56dc33cb986905f0e50813f5aa946c56ad27e24f030a'
assert sha(source)==expected
validation=read('gameplay_checkpoint_validation.json');export=read('model_gameplay_checkpoint_export.json')
assert validation['input_scene_sha256']['refined']==export['input_scene_sha256']==expected
assert validation['revisions']['refined']['total_frames']==3963
assert len(validation['revisions']['refined']['clips'])==59
assert validation['native_rest_contract_unchanged'] and validation['imported_action_channels_unchanged']
assert export['exact_native_joint_records'] and export['shield_rigid']
control=read('cuff_gameplay_identity_17.json');single=read('cuff_gameplay_single_17.json')
assert control['sample_count_per_revision']==single['sample_count_per_revision']==17
assert all(not r['new_local_intersections'] for r in control['revisions']['after']['poses'])
manifests=[]
for variant in ('parent','single','ties'):
    for view in ('front','reverse'):
        manifest=read(f'gameplay_{variant}_{view}_render_manifest.json')
        assert manifest['scene_sha256']==expected and len(manifest['renders'])==17
        assert manifest['resolution']==360 and manifest['ortho_scale']==5
        manifests.append(f'gameplay_{variant}_{view}_render_manifest.json')
if target.exists():assert sha(target)==expected
else:shutil.copyfile(source,target)
assert sha(target)==expected
report={'status':'ACCEPTED OFFLINE GAMEPLAY CUFF BASELINE; actual runtime gate remains open',
 'source':str(source.relative_to(ROOT)),'checkpoint':str(target.relative_to(ROOT)),'scene_sha256':expected,
 'changed_vertices':[],'changed_faces':[],'all_67_torso_seam_corrections_preserved':True,
 'decision':'Retain original cuff. No new tie is retained because comparisons show no meaningful gameplay improvement. End focused cuff pass; advance Stage 4.',
 'visual_review':{'reviewed_images':102,'cases':17,'views':2,'variants':3,'camera':'Orthographic scale 5, 360px square, directions (3,-7,8) and (-3,7,8). Offline approximation; fixed 72px/world-unit.',
 'finding':'No obvious open cuff hole, major local clipping or disruptive cuff silhouette change in normal-sized comparisons. Close-up cuff stretch/intersections remain visible; extreme arm extension and temporary shield shading are not declared solved.',
 'single_tie':'Vertex 871 closes up to 0.0284766 units (2.05px upper bound before projection/occlusion), but worsens incident elongation R17 0.0352516 to 0.0519370 and R3 0.0602723 to 0.0884581. No pixels differ by more than 8/255 in 34 gameplay views; not retained.',
 'all_28_ties':'No meaningful visible benefit; 27/28 individual attachments introduce strict diagnostic pairs in at least one of 17 poses. Existing all-tie surface warnings remain valid; no thresholds changed. All-tie gameplay differences total 27 pixels above 8/255 across 34 images, none above 32/255. Not retained.',
 'limitation':'This is a visual judgment on offline stills, not proof of invisible defects in every animation frame or the live game.'},
 'technical_diagnostics':{'control_new_pairs':0,'control_cases':17,'single_new_pairs':sum(len(r['new_local_intersections']) for r in single['revisions']['after']['poses']),
 'individual_analysis':'cuff_seam_measured_options.json','full_validation':'gameplay_checkpoint_validation.json','export':'model_gameplay_checkpoint_export.json',
 'full_frames':3963,'clips':59,'export_vertices':export['vertices'],'export_triangles':export['triangles'],'export_joints':export['joints']},
 'render_manifests':manifests,'next':'Stage 4 rigid shield planar reduction, then body reduction/atlas baking. Preserve this checkpoint; do not reopen cuff without a gameplay-visible regression.'}
(ROOT/'validation/gameplay_checkpoint_acceptance.json').write_text(json.dumps(report,indent=2))
print(report['status'],target.name)
