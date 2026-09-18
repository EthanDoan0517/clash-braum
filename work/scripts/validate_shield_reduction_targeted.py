"""Reload child and verify protected posed body plus rigid shield on 17 poses."""
from pathlib import Path
import json,sys,hashlib,argparse
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/scripts'),str(ROOT/'work/tools')]
from native_export import assert_native_rig
parser=argparse.ArgumentParser();parser.add_argument('--trial-report',default='shield_collapse_trial.json');parser.add_argument('--output',default='shield_collapse_targeted.json')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert all(Path(s).name==s for s in (args.trial_report,args.output))
trial=json.loads((ROOT/'validation'/args.trial_report).read_text())
cases=json.loads((ROOT/'validation/cuff_seam_individual_search.json').read_text())['cases']
baseline={};rows=[]
for label,filename in [('parent','clash_braum_torso.blend'),('trial',trial['scene'])]:
    path=ROOT/'work/scenes'/filename
    assert hashlib.sha256(path.read_bytes()).hexdigest()==trial['parent_sha256' if label=='parent' else 'scene_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    rig=bpy.data.objects['Braum_Native'];assert_native_rig(rig)
    for clip,frame in cases:
        action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(frame)
        dep=bpy.context.evaluated_depsgraph_get();body_error=0.;shield_error=0.
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH':continue
            ev=obj.evaluated_get(dep);mesh=ev.to_mesh();points=np.array([tuple(v.co) for v in mesh.vertices]);ev.to_mesh_clear()
            assert np.isfinite(points).all()
            if not obj.name.startswith('CCE_'):
                key=(clip,frame,obj.name)
                if label=='parent':baseline[key]=points
                else:
                    assert np.array_equal(points,baseline[key]),key
                    body_error=max(body_error,float(np.abs(points-baseline[key]).max()))
            else:
                bone=rig.pose.bones['Shield'];matrix=np.array(bone.matrix@bone.bone.matrix_local.inverted())
                rest=np.array([tuple(v.co) for v in obj.data.vertices]);expected=rest@matrix[:3,:3].T+matrix[:3,3]
                shield_error=max(shield_error,float(np.abs(expected-points).max()))
        assert shield_error<1e-5
        if label=='trial':rows.append({'clip':clip,'frame':frame,'protected_posed_body_max_error':body_error,'shield_rigid_max_error':shield_error})
out={'status':'PASS 17-pose protected body/rigid shield regression; Stage 4 trial, not promoted',
 'scene_sha256':trial['scene_sha256'],'poses':rows,'all_coordinates_finite':True,'native_rest_contract':True,
 'limits':'Not a new topology collision comparison, UV fidelity certificate, normal-map bake test or full animation validation. Surface mapping in generator is nearest-source sample correspondence, not exact face ancestry.'}
(ROOT/'validation'/args.output).write_text(json.dumps(out,indent=2))
print(out['status'])
