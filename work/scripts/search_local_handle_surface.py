"""Surface-constrained local grip search in running E, no scene saved."""
from pathlib import Path
import bpy,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_torso.blend'),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];a=bpy.data.actions['braum_spell3_run0'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(14);dep=bpy.context.evaluated_depsgraph_get()
palm=(rig.pose.bones['L_Index1'].head+rig.pose.bones['L_Pinky1'].head)*.5
axis=(rig.pose.bones['L_Index1'].head-rig.pose.bones['L_Pinky1'].head).normalized();forward=(rig.pose.bones['L_Middle1'].head-rig.pose.bones['L_Hand'].head).normalized()
r=json.loads((ROOT/'validation/local_handle_diagnostics.json').read_text());c=next(c for c in r['components'] if c['object']=='CCE_mesh_14.001' and c['id']==20)
o=bpy.data.objects[c['object']];ev=o.evaluated_get(dep);m=ev.to_mesh();rail=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],c['faces']);ev.to_mesh_clear();direction=(rail.find_nearest(palm)[0]-palm).normalized()
points=[];faces=[];palm_points=[];digit_points=[]
for name in ['Object004','Object009']:
 o=bpy.data.objects[name];ev=o.evaluated_get(dep);m=ev.to_mesh();off=len(points);pp=[ev.matrix_world@v.co for v in m.vertices];points.extend(pp);faces.extend(tuple(off+i for i in p.vertices) for p in m.polygons)
 for v in o.data.vertices:
  if sum(g.weight for g in v.groups if o.vertex_groups[g.group].name=='L_Hand')>.5:palm_points.append(pp[v.index])
  elif sum(g.weight for g in v.groups if o.vertex_groups[g.group].name.startswith('L_') and any(s in o.vertex_groups[g.group].name for s in ['Index','Middle','Ring','Pinky']))>.5:digit_points.append(pp[v.index])
 ev.to_mesh_clear()
body=BVHTree.FromPolygons(points,faces)
def geometry(segments):
 verts=[];faces=[]
 for start,end,radius in segments:
  z=(end-start).normalized();x=z.cross(Vector((0,0,1)))
  if x.length<.01:x=z.cross(Vector((0,1,0)))
  x.normalize();y=z.cross(x);off=len(verts)
  for p in [start,end]:
   for k in range(12):verts.append(p+radius*(x*math.cos(k*math.tau/12)+y*math.sin(k*math.tau/12)))
  for k in range(12):faces.append((off+k,off+(k+1)%12,off+12+(k+1)%12,off+12+k))
  faces.extend([tuple(off+k for k in reversed(range(12))),tuple(off+12+k for k in range(12))])
 return verts,faces
rows=[]
for half in [.065,.085,.105]:
 for offset in [.035,.05,.065,.08,.095,.11,.125,.14]:
  for advance in [-.04,-.02,0,.02,.04,.06]:
   center=palm+direction*offset+forward*advance;ends=[center-axis*half,center+axis*half];anchors=[rail.find_nearest(p)[0] for p in ends]
   v,f=geometry([(ends[0],ends[1],.014),(anchors[0],ends[0],.009),(ends[1],anchors[1],.009)]);tree=BVHTree.FromPolygons(v,f);hits=tree.overlap(body)
   if hits:continue
   bar=BVHTree.FromPolygons(v[:24],f[:14]);dist=sorted(bar.find_nearest(p)[3] for p in palm_points);digits=sorted(bar.find_nearest(p)[3] for p in digit_points)
   rows.append({'half_length':half,'offset':offset,'advance':advance,'palm_min':dist[0],'palm_q25':dist[len(dist)//4],'digit_min':digits[0],'digit_q25':digits[len(digits)//4],'score':dist[len(dist)//4]+digits[len(digits)//4]})
rows.sort(key=lambda r:r['score']);(ROOT/'validation/local_handle_surface_search.json').write_text(json.dumps({'method':'144 bounded running-E trials; reject triangle intersections against full Object004/Object009, rank unsigned palm/digit distances to bar. No multi-pose or visual acceptance implied.','collision_free':rows},indent=2));print(json.dumps(rows[:5],indent=2))

