from pathlib import Path
import bpy,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_animation_review.blend'),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];results=[]
for name,frame in [('braum_idle_01_loop',17),('braum_spell3_idle0',17),('braum_run_02',12)]:
    rig.animation_data.action=bpy.data.actions[name]
    if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    bpy.context.scene.frame_set(frame)
    shield=rig.pose.bones['Shield'];unpose=shield.bone.matrix_local@shield.matrix.inverted()
    results.append(dict(clip=name,frame=frame,hands_in_shield_bind={hand:list(unpose@rig.pose.bones[hand].matrix.translation) for hand in ['L_Hand','R_Hand']}))
print(json.dumps(results,indent=2))
(ROOT/'validation/shield_grip_landmarks.json').write_text(json.dumps(results,indent=2))
# Identify the material/group making the collar protrusion from world vertices.
rig.animation_data.action=bpy.data.actions['braum_idle_01_loop']
if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(17);deps=bpy.context.evaluated_depsgraph_get()
out=[]
for obj in bpy.context.scene.objects:
    if obj.type!='MESH' or 'source_obj_group' not in obj:continue
    ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
    selected=[v.index for v in mesh.vertices if v.co.z>1.6 and abs(v.co.x)>.17]
    for vi in selected:
        v=obj.data.vertices[vi]
        out.append(dict(group=obj['source_obj_group'],vertex=vi,posed=list(mesh.vertices[vi].co),rest=list(v.co),weights={obj.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}))
    ev.to_mesh_clear()
(ROOT/'validation/collar_weight_diagnostic.json').write_text(json.dumps(out,indent=2))
print('collar diagnostic vertices',len(out))
