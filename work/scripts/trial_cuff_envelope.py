"""Fit wrist-attached cuff radially around the multi-pose forearm envelope.

Diagnostic candidate only. Skin, skeleton, fingers and accepted torso untouched.
"""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];obj=bpy.data.objects['Object004'];skin=bpy.data.objects['Object009']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
base=json.loads((ROOT/'validation/cuff_wrist_candidates.json').read_text())
changes=base['candidate_weights']['cap_0.03']['Object004']
cases=[('braum_recall',f) for f in [60,65,70]]+[('braum_dance_loop',f) for f in [45,50,55]]+[('braum_spell4',f) for f in [3,15,17,26]]+[('braum_idle_01_loop',17),('braum_spell3_idle180',29),('braum_run_02',12),('braum_spell3_run0',14),('braum_spell3_run-90',14)]
data={};faces={};positions={};worst={}
for side,cid in [('L',810),('R',652)]:
    ids=set(next(c['indices'] for c in regions['Object009'] if c['id']==cid))
    faces[side]=[tuple(p.vertices) for p in skin.data.polygons if set(p.vertices)<=ids]
    elbow=rig.data.bones[side+'_Elbow'].head_local;axis=rig.data.bones[side+'_Hand'].head_local-elbow
    for index,w in changes.items():
        v=obj.data.vertices[int(index)]
        if (v.co.x>0)!=(side=='L'):continue
        t=(v.co-elbow).dot(axis)/axis.length_squared
        center=elbow+axis*t;radial=v.co-center
        data[index]=(side,center,radial.normalized(),radial.length,t)
        positions[index]=v.co.copy();worst[index]={'displacement':0}
for clip,frame in cases:
    a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame)
    ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    points=[v.co.copy() for v in mesh.vertices]
    transforms={n:rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted() for n in rig.data.bones.keys()}
    for index,(side,center,direction,radius,t) in data.items():
        w=changes[index]
        transform=Matrix([[sum(weight*transforms[n][i][j] for n,weight in w.items()) for j in range(4)] for i in range(4)])
        inverse=transform.inverted()
        tree=BVHTree.FromPolygons([inverse@p for p in points],faces[side])
        hit,normal,face,distance=tree.ray_cast(center,direction,.3)
        if hit is None:continue
        # Outward-only displacement, fading at the glove boundary. An excessive
        # required movement is retained in evidence, never silently clipped.
        fade=max(0,min(1,(1.02-t)/.07));fade=fade*fade*(3-2*fade)
        movement=max(0,distance+.004-radius)*fade
        if movement>worst[index]['displacement']:
            positions[index]=obj.data.vertices[int(index)].co+direction*movement
            worst[index]={'displacement':movement,'clip':clip,'frame':frame,'radius_before':radius,'skin_radius':distance}
    ev.to_mesh_clear()
report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'UNACCEPTED multi-pose radial envelope fit; no scene saved','candidate_weights':{'envelope':{'Object004':changes}},'candidate_positions':{'envelope':{'Object004':{i:list(p) for i,p in positions.items()}}},'cases':cases,'envelope':worst}
(ROOT/'validation/cuff_envelope_candidates.json').write_text(json.dumps(report,indent=2))
print('Max displacement',max(v['displacement'] for v in worst.values()),'moved',sum(v['displacement']>0 for v in worst.values()))
