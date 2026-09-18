"""Finalize trial disposition and verify preserved checkpoint hashes."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parent=ROOT/'work/scenes/clash_braum_torso.blend'
assert sha(parent)==json.loads((ROOT/'validation/torso_candidate_render_manifest.json').read_text())['scene_sha256']
# Recover exact initial geometry metadata from its restored, original trial scene.
p=ROOT/'work/scenes/clash_braum_handle_trial.blend'
bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];a=bpy.data.actions['braum_spell3_run0'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(14)
o=bpy.data.objects['CCE_auxiliary_grip_trial'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
def center(start):
 from mathutils import Vector
 return list(sum((ev.matrix_world@m.vertices[i].co for i in range(start,start+12)),Vector())/12)
r=json.loads((ROOT/'validation/local_handle_trial.json').read_text());r.update(offset=.035,scene_sha256=sha(p),world_run14_ends=[center(0),center(12)],world_run14_anchors=[center(24),center(60)],status='REJECTED: glove triangle intersections in all running-E samples. Original trial scene restored from its Blender backup after a trial-output naming bug; original render hashes verified.')
r['world_run14_center']=[(x+y)/2 for x,y in zip(*r['world_run14_ends'])];ev.to_mesh_clear();(ROOT/'validation/local_handle_trial.json').write_text(json.dumps(r,indent=2))
for label in ['local_handle_trial_front','local_handle_trial_reverse']:
 manifest=json.loads((ROOT/'validation'/f'{label}_render_manifest.json').read_text());assert manifest['scene_sha256']==sha(p),label
r=json.loads((ROOT/'validation/torso_coupled_refinement.json').read_text());r['disposition']='REJECTED after visual review: small new dance50 silhouette notch. Numerical improvement alone is insufficient.';(ROOT/'validation/torso_coupled_refinement.json').write_text(json.dumps(r,indent=2))
for label,reason in [('handle_surface_trial','Glove intersections remain in running E: 55 triangle pairs at run0/14.'),('handle_knuckle_trial','Glove intersections remain in running E: 73 triangle pairs at run0/14.'),('handle_normal_trial','No body triangle intersections in 13 E/R samples, but visible open palm/finger separation and conspicuous side support remain. Not a convincing grip.')]:
 p=ROOT/'validation'/f'local_{label}.json';r=json.loads(p.read_text());r['status']='REJECTED / diagnostic only: '+reason;r['scene_sha256']=sha(ROOT/'work/scenes'/f'clash_braum_{label}.blend');p.write_text(json.dumps(r,indent=2))
report={'current_scene':'work/scenes/clash_braum_torso.blend','current_scene_sha256':sha(parent),'accepted_new_checkpoint':False,'torso_disposition':'Preserve all 67 original seam corrections. Endpoint143 .1 blend lowers R17/dance maxima but produces small new dance50 silhouette notch. Larger local blends worsen p99 or neighboring strain.','grip_disposition':'Nearest running-E left surface is side rail CCE_mesh_14.001 physical shell20, not the central right-hand hardware940 in CCE_mesh_13.001. Auxiliary handle trials either intersect the glove or leave an open grip. None accepted.','full_validation_and_export':'Not run: no visually preferable candidate accepted; parent full validation and export remain authoritative.','next_action':'Model a contoured local side grip from actual glove palm and finger surfaces, with support endpoints outside the thumb/pinky envelope. A straight joint-centered bar is not adequate. Use 13-pose triangle intersections plus matched front/reverse hand-surface views; preserve existing CCE geometry and all body weights. Recall cuff and remaining torso art gates remain open.'}
(ROOT/'validation/stage3_local_review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
