"""Actual triangle intersections and preservation checks for an auxiliary handle trial."""
from pathlib import Path
import bpy,json,sys,argparse,hashlib
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--scene',required=True);p.add_argument('--output',required=True);args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
def state(o):return {'vertices':[(tuple(v.co),tuple((o.vertex_groups[g.group].name,g.weight) for g in v.groups)) for v in o.data.vertices],'faces':[tuple(p.vertices) for p in o.data.polygons],'uv':[[tuple(d.uv) for d in l.data] for l in o.data.uv_layers]}
source=ROOT/'work/scenes/clash_braum_torso.blend';bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False);before={o.name:state(o) for o in bpy.context.scene.objects if o.type=='MESH'}
path=ROOT/'work/scenes'/args.scene;bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
for n,s in before.items():assert state(bpy.data.objects[n])==s,n
rig=bpy.data.objects['Braum_Native'];handle=bpy.data.objects['CCE_auxiliary_grip_trial'];rows=[]
for c in json.loads((ROOT/'validation/grip_targets.json').read_text())['poses']:
 a=bpy.data.actions[c['clip']];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(c['frame']);dep=bpy.context.evaluated_depsgraph_get()
 ev=handle.evaluated_get(dep);m=ev.to_mesh();tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(p.vertices) for p in m.polygons]);ev.to_mesh_clear();hits={};near={}
 for o in [o for o in bpy.context.scene.objects if o.type=='MESH' and 'source_obj_group' in o]:
  ev=o.evaluated_get(dep);m=ev.to_mesh();points=[ev.matrix_world@v.co for v in m.vertices];bodytree=BVHTree.FromPolygons(points,[tuple(p.vertices) for p in m.polygons]);pairs=tree.overlap(bodytree)
  if pairs:hits[o.name]={'face_pairs':len(pairs),'handle_faces':sorted(set(i for i,j in pairs)),'body_faces':sorted(set(j for i,j in pairs))}
  if o.name in ['Object004','Object009']:
   for side in ['L','R']:
    ids=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if o.vertex_groups[g.group].name.startswith(side+'_') and any(n in o.vertex_groups[g.group].name for n in ['Hand','Thumb','Index','Middle','Ring','Pinky']))>.5]
    near[o.name+'_'+side]=min(tree.find_nearest(points[i])[3] for i in ids)
  ev.to_mesh_clear()
 rows.append({'clip':c['clip'],'frame':c['frame'],'intersections':hits,'hand_vertex_proximity':near})
report={'scene':args.scene,'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'all_original_mesh_geometry_weights_topology_uv_exact':True,'method':'BVH triangle intersection pairs with all source body groups; unsigned hand/digit vertex proximity to auxiliary handle only. Does not detect fully enclosed disconnected surfaces or prove pressure contact.','poses':rows}
(ROOT/'validation'/args.output).write_text(json.dumps(report,indent=2))
for r in rows:print(r['clip'],r['frame'],{n:v['face_pairs'] for n,v in r['intersections'].items()},r['hand_vertex_proximity'].get('Object004_L'))
