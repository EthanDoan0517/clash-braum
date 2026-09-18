"""Compare native/Clash shield proximity at the same native palm landmarks.
Distances to any shield surface are diagnostic, not handle contact approval.
"""
from pathlib import Path
import bpy,json,hashlib,argparse,sys
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--scene',default='clash_braum_shoulders.blend');p.add_argument('--output',default='native_grip_comparison.json')
p.add_argument('--trial-left-offset',action='store_true',help='Unsaved trial: offset CCE toward running-E left palm, retaining 0.0245 proximity')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert all(Path(n).name==n for n in [args.scene,args.output])
source=ROOT/'work/scenes'/args.scene
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];native=bpy.data.objects['Vanilla_Reference']
shield_group=native.vertex_groups['Shield'].index
native_ids={v.index for v in native.data.vertices if any(g.group==shield_group and g.weight>.999 for g in v.groups)}
polys=[tuple(p.vertices) for p in native.data.polygons if all(i in native_ids for i in p.vertices)]
assert polys
trial=None
if args.trial_left_offset:
 a=bpy.data.actions['braum_spell3_run0'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(14)
 dep=bpy.context.evaluated_depsgraph_get();palm=rig.matrix_world@((rig.pose.bones['L_Hand'].head+rig.pose.bones['L_Middle1'].head)*.5)
 closest=None;objects=[o for o in bpy.context.scene.objects if o.name.startswith('CCE_') and o.type=='MESH']
 for o in objects:
  ev=o.evaluated_get(dep);mesh=ev.to_mesh();tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons]);hit=tree.find_nearest(palm)
  if closest is None or hit[3]<closest[3]:closest=hit
  ev.to_mesh_clear()
 delta_world=(palm-closest[0]).normalized()*(closest[3]-.0245)
 shield=rig.pose.bones['Shield'];deformation=rig.matrix_world@shield.matrix@shield.bone.matrix_local.inverted()
 delta_bind=deformation.to_3x3().inverted()@delta_world
 for o in objects:
  local_delta=o.matrix_world.to_3x3().inverted()@rig.matrix_world.to_3x3()@delta_bind
  for v in o.data.vertices:v.co+=local_delta
  o.data.update()
 trial={'status':'Unsaved diagnostic trial, not a production correction','bind_offset':list(delta_bind),'world_offset_at_run14':list(delta_world),'target_distance':.0245}
cases=json.loads((ROOT/'validation/grip_targets.json').read_text())['poses'];rows=[]
for case in cases:
 a=bpy.data.actions[case['clip']];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(case['frame']);dep=bpy.context.evaluated_depsgraph_get()
 trees={}
 for label,objects in [('native',[native]),('clash',[o for o in bpy.context.scene.objects if o.name.startswith('CCE_') and o.type=='MESH'])]:
  points=[];faces=[]
  for o in objects:
   ev=o.evaluated_get(dep);mesh=ev.to_mesh();offset=len(points);points.extend(ev.matrix_world@v.co for v in mesh.vertices)
   faces.extend([tuple(i+offset for i in face) for face in (polys if label=='native' else [p.vertices for p in mesh.polygons])]);ev.to_mesh_clear()
  trees[label]=BVHTree.FromPolygons(points,faces)
 row={'clip':case['clip'],'frame':case['frame'],'hands':{}}
 for side in ['L','R']:
  palm=rig.matrix_world@((rig.pose.bones[side+'_Hand'].head+rig.pose.bones[side+'_Middle1'].head)*.5)
  row['hands'][side]={label: {'distance':tree.find_nearest(palm)[3],'nearest_world':list(tree.find_nearest(palm)[0])} for label,tree in trees.items()}
 rows.append(row)
report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'trial':trial,'native_shield_vertices':len(native_ids),'native_shield_faces':len(polys),'method':'World-space joint palm midpoint to nearest evaluated shield surface; native Shield-weighted faces only. Not a palm-surface or handle-specific test; no runtime snapping simulated.','poses':rows}
(ROOT/'validation'/args.output).write_text(json.dumps(report,indent=2))
for row in rows:
 print(row['clip'],row['frame'],{s:{k:round(v['distance'],4) for k,v in h.items()} for s,h in row['hands'].items()})
