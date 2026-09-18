"""Record native palm landmarks in Shield bind space; not a contact pass test."""
from pathlib import Path
import bpy,json,hashlib,argparse,sys
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--scene',default='clash_braum_deformation.blend')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert Path(args.scene).name==args.scene
source=ROOT/'work/scenes'/args.scene
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];rows=[]
cases=[(a.name,round(sum(a.frame_range)/2)) for a in bpy.data.actions
       if a.name.startswith(('braum_spell3_idle','braum_spell3_run'))]
cases += [('braum_spell4',f) for f in (3,15,26)]
for clip,frame in sorted(cases):
    action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    bpy.context.scene.frame_set(frame)
    shield=rig.pose.bones['Shield']
    to_bind=shield.bone.matrix_local@shield.matrix.inverted()
    hands={}
    for side in ('L','R'):
        palm=(rig.pose.bones[side+'_Hand'].head+rig.pose.bones[side+'_Middle1'].head)*.5
        hands[side]={'native_palm_world':list(rig.matrix_world@palm),'shield_bind_space':list(to_bind@palm)}
    rows.append({'clip':clip,'frame':frame,'hands':hands})
report={'scene':args.scene,'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'method':'Midpoint of native Hand and Middle1 joint heads mapped by inverse Shield deformation. Landmarks are not evaluated palm surfaces or measured handle contacts. No runtime snap constraints simulated.',
        'poses':rows}
(ROOT/'validation/grip_targets.json').write_text(json.dumps(report,indent=2))
print('Recorded',len(rows),'poses')
