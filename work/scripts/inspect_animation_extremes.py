"""Compare saved preview values with actual source ANM keys at flagged frames."""
from pathlib import Path
import sys,json
import bpy
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/tools'),str(ROOT/'work/scripts')]
from Aventurine.io import import_anm
from asset_formats import read_skl
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_rig_refined.blend'),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native']
names={j['hash']:j['name'] for j in read_skl(ROOT/'Braum.wad/9b8248658ce51711.skl')['joints']}
clips=json.loads((ROOT/'validation/draft_animation_samples.json').read_text())['animations']
report=[]
for clip_name,frame in [('braum_spell4',3),('braum_recall',65),('braum_dance_loop',50)]:
    clip=next(c for c in clips if c['name']==clip_name)
    anm=import_anm.read_anm(str(ROOT/clip['source']))
    action=bpy.data.actions[clip_name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    bpy.context.scene.frame_set(frame)
    row={'clip':clip_name,'frame':frame,'bones':[]}
    for track in anm.tracks:
        name=names.get(track.joint_hash)
        if not name:continue
        bone=rig.pose.bones[name]
        scales=[(f,list(p.scale)) for f,p in track.poses.items() if p.scale is not None]
        if not scales:continue
        lo=max((p for p in scales if p[0]<=frame-1),default=min(scales),key=lambda p:p[0])
        hi=min((p for p in scales if p[0]>=frame-1),default=max(scales),key=lambda p:p[0])
        translations=[(f,list(p.translation)) for f,p in track.poses.items() if p.translation is not None]
        tnear=sorted(translations,key=lambda p:abs(p[0]-(frame-1)))[:2]
        if max(abs(v-1) for v in bone.scale)>.1 or bone.location.length>.4 or name in ['Root','Pelvis','Spine1','Spine2','Spine3']:
            row['bones'].append({'bone':name,'saved_action_scale':list(bone.scale),'source_scale_keys':[lo,hi],
                'local_location':list(bone.location),'pose_world_position':list(bone.matrix.translation),
                'source_translation_keys':tnear})
    report.append(row)
(ROOT/'validation/animation_extremes.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
