"""Map CCE physical components against actual evaluated hand surfaces, without edits."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];o=bpy.data.objects['Object002']
print('143 coincident',[(v.index,list(v.co)) for v in o.data.vertices if (v.co-o.data.vertices[143].co).length<.001])
components=[]
for o in [o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('CCE_')]:
 parent=list(range(len(o.data.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(a,b):parent[root(b)]=root(a)
 positions={}
 for e in o.data.edges:union(*e.vertices)
 for v in o.data.vertices:
  key=tuple(round(x,5) for x in v.co)
  if key in positions:union(v.index,positions[key])
  positions[key]=v.index
 groups={}
 for v in o.data.vertices:groups.setdefault(root(v.index),[]).append(v.index)
 for ids in groups.values():
  idset=set(ids);faces=[tuple(p.vertices) for p in o.data.polygons if all(i in idset for i in p.vertices)]
  if faces:components.append({'object':o.name,'id':min(ids),'indices':ids,'faces':faces,'bounds':[[min(o.data.vertices[i].co[a] for i in ids),max(o.data.vertices[i].co[a] for i in ids)] for a in range(3)]})
rows=[]
for clip,f in [('braum_spell3_run0',14),('braum_spell3_idle180',29),('braum_spell4',15),('braum_spell4',26)]:
 a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f);dep=bpy.context.evaluated_depsgraph_get()
 shields={}
 for c in components:
  if c['object'] not in shields:
   o=bpy.data.objects[c['object']];ev=o.evaluated_get(dep);m=ev.to_mesh();shields[o.name]=[ev.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear()
 row={'clip':clip,'frame':f,'hands':{}}
 for side in ['L','R']:
  palm=rig.matrix_world@((rig.pose.bones[side+'_Hand'].head+rig.pose.bones[side+'_Middle1'].head)*.5)
  samples=[]
  for name in ['Object004','Object009']:
   o=bpy.data.objects[name];ev=o.evaluated_get(dep);m=ev.to_mesh()
   for v in o.data.vertices:
    # Actual palm shell: predominantly hand/wrist weights, excludes finger chains.
    if sum(g.weight for g in v.groups if o.vertex_groups[g.group].name in [side+'_Hand',side+'_Wrist'])>.5:
     samples.append((name,v.index,ev.matrix_world@m.vertices[v.index].co))
   ev.to_mesh_clear()
  hits=[]
  for c in components:
   tree=BVHTree.FromPolygons(shields[c['object']],c['faces']);hit=tree.find_nearest(palm)
   distances=[(tree.find_nearest(p)[3],n,i) for n,i,p in samples]
   if distances:
    ds=sorted(x[0] for x in distances)
    hits.append({'object':c['object'],'id':c['id'],'joint_distance':hit[3],'nearest_world':list(hit[0]),'palm_surface_min':ds[0],'palm_surface_median':ds[len(ds)//2],'closest_palm_vertex':min(distances)[1:]})
  row['hands'][side]={'palm_vertices':len(samples),'nearest_components':sorted(hits,key=lambda x:x['palm_surface_min'])[:8]}
 rows.append(row)
report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'Physical CCE shells welded at rounded rest positions; actual hand-weighted vertex samples to shell triangles. Min/median are unsigned proximity diagnostics, not enclosure/contact approval.','components':components,'poses':rows}
(ROOT/'validation/local_handle_diagnostics.json').write_text(json.dumps(report,indent=2))
for row in rows:
 print(row['clip'],row['frame'],{s:h['nearest_components'][:2] for s,h in row['hands'].items()})
print('components',len(components))
