"""Fifteen-pose torso diagnostics, explicit crease edges and protected-region comparison."""
from pathlib import Path
import bpy,json,hashlib,numpy as np,argparse,sys
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--candidate-weights');p.add_argument('--all-frames',action='store_true');p.add_argument('--case',action='append',help='Explicit clip:frame diagnostic; repeatable');p.add_argument('--output',default='torso_coupled_targeted_validation.json');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
r=json.loads((ROOT/'validation/torso_coupled_refinement.json').read_text());regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
allowed={n:set(v) for n,v in r['coupled_changes']['changed_indices'].items()}
candidate=None
positions={}
if args.candidate_weights:
 filename,key=args.candidate_weights.split(':');candidate=json.loads((ROOT/'validation'/filename).read_text())
 changes=candidate['candidate_weights'][key];allowed={n:{int(i) for i in weights} for n,weights in changes.items()}
 positions=candidate.get('candidate_positions',{}).get(key,{})
 assert all(set(map(int,values))<=allowed.get(name,set()) for name,values in positions.items())

cases=[('braum_recall',f) for f in [60,65,70]]+[('braum_dance_loop',f) for f in [45,50,55]]+[('braum_spell4',f) for f in [3,15,17,26]]+[('braum_idle_01_loop',17),('braum_spell3_idle180',29),('braum_run_02',12),('braum_spell3_run0',14),('braum_spell3_run-90',14)]
if args.all_frames:
 assert not args.case, 'Choose --all-frames or explicit --case arguments'
 assert candidate, '--all-frames requires explicit candidate weights'
 clips=json.loads((ROOT/'validation/draft_animation_samples.json').read_text())['animations']
 cases=[(c['name'],f) for c in clips for f in range(1,c['frames']+1)]
if args.case:cases=[(name,int(frame)) for name,frame in (c.rsplit(':',1) for c in args.case)]
report={'revisions':{},'candidate_weights':args.candidate_weights};baseline={};baseline_intersections={};baseline_mesh_contract={}
for label,file in [('before','clash_braum_torso.blend'),('after','clash_braum_torso.blend' if candidate else 'clash_braum_torso_coupled.blend')]:
 path=ROOT/'work/scenes'/file;bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
 rig=bpy.data.objects['Braum_Native'];objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
 if candidate:
  assert hashlib.sha256(path.read_bytes()).hexdigest()==candidate['scene_sha256']
  if label=='after':
   for name,weights in changes.items():
    obj=bpy.data.objects[name]
    for index,w in weights.items():
     index=int(index)
     for g in list(obj.data.vertices[index].groups):obj.vertex_groups[g.group].remove([index])
     for name,value in w.items():
      if value>0:obj.vertex_groups[name].add([index],value,'REPLACE')
    obj.data.update()
   for name,values in positions.items():
    for index,position in values.items():bpy.data.objects[name].data.vertices[int(index)].co=position
    bpy.data.objects[name].data.update()
 for o in objects:
  state=[(tuple(v.co),{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}) for v in o.data.vertices]
  contract=([tuple(p.vertices) for p in o.data.polygons],[[tuple(d.uv) for d in l.data] for l in o.data.uv_layers])
  if label=='before':baseline_mesh_contract[o.name]=contract
  else:assert contract==baseline_mesh_contract[o.name],(o.name,'topology or UV changed')
  if label=='before':baseline[o.name]=state
  else:
   for i,(p,w) in enumerate(state):
    if str(i) not in positions.get(o.name,{}):assert p==baseline[o.name][i][0],(o.name,i,'geometry changed')
    if i not in allowed.get(o.name,set()):assert w==baseline[o.name][i][1],(o.name,i,'protected weight changed')
 rows=[]
 # Cache polygon topology; vectorized broad-phase culling retains exactly the
 # original polygons and their IDs for Blender's existing BVH narrow phase.
 topology={}
 for o in objects:
  faces=[tuple(f.vertices) for f in o.data.polygons]
  width=max(map(len,faces),default=0)
  topology[o.name]=(faces,np.array([f+(f[-1],)*(width-len(f)) for f in faces],dtype=int))
 for clip,frame in cases:
  if frame==1:print(label,clip,flush=True)
  a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame);dep=bpy.context.evaluated_depsgraph_get()
  for n in allowed:
   o=bpy.data.objects[n];ev=o.evaluated_get(dep);m=ev.to_mesh();e=np.array([tuple(e.vertices) for e in o.data.edges]);p=np.array([tuple(v.co) for v in m.vertices]);rest=np.array([tuple(v.co) for v in o.data.vertices]);d=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)-np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1)
   ratios=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)/np.maximum(np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1),.0001)
   row={'max_edge_ratio':float(ratios.max()),'clip':clip,'frame':frame,'object':n,'max_elongation':float(d.max()),'p99_elongation':float(np.quantile(d,.99))}
   if n=='Object002':
    row['edge_1497_2321_length']=float(np.linalg.norm(p[1497]-p[2321]))
    row['target_edges']={f'{a}-{b}':float(np.linalg.norm(p[a]-p[b])) for a,b in [(1094,1095),(733,737),(148,150),(157,158),(143,190),(133,152),(190,331),(1096,1097),(145,146)]}
   if candidate:
    affected=[f.index for f in o.data.polygons if any(i in allowed[n] for i in f.vertices)]
    face_ids=[tuple(o.data.polygons[i].vertices) for i in affected]
    tree=BVHTree.FromPolygons(p.tolist(),face_ids);intersections=set()
    local_points=p[list({i for face in face_ids for i in face})]
    lower=local_points.min(axis=0)-1e-7;upper=local_points.max(axis=0)+1e-7
    for other in objects:
     if other.name=='Vanilla_Reference' or other.name=='Poro':continue
     other_ev=other.evaluated_get(dep);other_mesh=other_ev.to_mesh()
     other_points=np.empty(len(other_mesh.vertices)*3,dtype=np.float64)
     other_mesh.vertices.foreach_get('co',other_points);other_points=other_points.reshape(-1,3)
     transform=np.array(o.matrix_world.inverted()@other_ev.matrix_world)
     other_points=other_points@transform[:3,:3].T+transform[:3,3]
     other_faces,indices=topology[other.name]
     bounds=other_points[indices]
     nearby=np.flatnonzero(np.all(bounds.max(axis=1)>=lower,axis=1)&np.all(bounds.min(axis=1)<=upper,axis=1))
     if not len(nearby):
      other_ev.to_mesh_clear();continue
     other_tree=BVHTree.FromPolygons(other_points.tolist(),[other_faces[i] for i in nearby])
     for local,remote in tree.overlap(other_tree):
      remote=int(nearby[remote])
      if other==o and set(face_ids[local])&set(other_faces[remote]):continue
      intersections.add((affected[local],other.name,remote))
     other_ev.to_mesh_clear()
    k=(clip,frame,n)
    if label=='before':baseline_intersections[k]=intersections
    row['local_intersection_pairs']=len(intersections)
    row['new_local_intersections']=[list(v) for v in sorted(intersections-baseline_intersections[k])]
    row['removed_local_intersections']=[list(v) for v in sorted(baseline_intersections[k]-intersections)]
   rows.append(row);ev.to_mesh_clear()
 report['revisions'][label]={'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'poses':rows}
 (ROOT/'validation'/args.output).write_text(json.dumps(report,indent=2))
report['all_rest_geometry_and_unlisted_weights_unchanged']=not bool(positions)
report['unlisted_rest_geometry_and_weights_unchanged']=True
report['authored_candidate_positions']=positions
report['topology_and_uv_unchanged']=True
report['sample_count_per_revision']=len(cases)
report['intersection_scope']='Faces incident to changed vertices against all body and shield meshes; excludes shared-vertex self pairs, Vanilla_Reference and Poro. No runtime or whole-body collision certification.'
(ROOT/'validation'/args.output).write_text(json.dumps(report,indent=2))
for a,b in zip(report['revisions']['before']['poses'],report['revisions']['after']['poses']):
 if a['frame'] in [65,50,17,14]:print(a['clip'],a['object'],round(a['max_elongation'],5),'->',round(b['max_elongation'],5),'edge',a.get('edge_1497_2321_length'),b.get('edge_1497_2321_length'))

