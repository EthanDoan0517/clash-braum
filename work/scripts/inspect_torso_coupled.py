"""Bounded coupled edge trial; preserves all scenes and reports every competing pose."""
from pathlib import Path
import bpy,json,numpy as np,hashlib,argparse,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--local',action='store_true');parser.add_argument('--intersections',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
o=bpy.data.objects['Object002'];rig=bpy.data.objects['Braum_Native']
r=json.loads((ROOT/'validation/torso_refinement.json').read_text())
clusters=r['torso_changes']['clusters']
w=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in o.data.vertices]
rest=np.array([tuple(v.co) for v in o.data.vertices]);edges=np.array([tuple(e.vertices) for e in o.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
cases=[(p['clip'],p['frame']) for p in json.loads((ROOT/'validation/torso_targeted_validation.json').read_text())['revisions']['after']['poses']]
def assign(i,weights):
 for g in list(o.data.vertices[i].groups):o.vertex_groups[g.group].remove([i])
 weights=dict(sorted(weights.items(),key=lambda x:-x[1])[:4]);s=sum(weights.values())
 for n,v in weights.items():
  if v>0:o.vertex_groups[n].add([i],v/s,'REPLACE')
def measure():
 rows=[]
 for clip,f in cases:
  a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear()
  d=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);rows.append(dict(clip=clip,frame=f,max_elongation=float((d-length).max()),p99=float(np.quantile(d-length,.99)),max_ratio=float((d/np.maximum(length,.0001)).max()),target_lengths={f'{a}-{b}':float(np.linalg.norm(p[a]-p[b])) for a,b in [(143,190),(1094,1095),(733,737),(148,150),(157,158),(1096,1097),(145,146)]}))
 return rows
report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'endpoint_data':{str(i):{'rest':rest[i].tolist(),'weights':w[i],'cluster':next((c for c in clusters if i in c),[i])} for i in [143,190]},'trials':{'baseline':measure()},'candidate_weights':{}}
if args.local:
 # Coordinated lower-ring displacement, confined below the accepted seam band.
 original_trial=json.loads((ROOT/'validation/torso_coupled_refinement.json').read_text())['coupled_changes']['after']
 delta={n:original_trial.get(n,0)-w[143].get(n,0) for n in w[143]}
 seam_ids={i for c in clusters for i in c}
 component=set(next(c['indices'] for c in json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']['Object002'] if c['id']==0))
 candidates={}
 for radius in [.045,.065,.085]:
  for strength in [.5,1.0]:
   changes={}
   for i in component-seam_ids:
    distance=float(np.linalg.norm(rest[i]-rest[143]))
    if distance>=radius or rest[i,2]>=1.30 or set(w[i])!=set(delta):continue
    fade=(1-(distance/radius)**2)**2*strength
    changes[str(i)]={n:v+delta[n]*fade for n,v in w[i].items()}
   candidates[f'ring_r{radius}_s{strength}']=changes
 for target in ['Spine1','Spine2','Spine3']:
  for strength in [.25,.5,1.0]:
   changes={}
   for i in [190,331]:
    weights=w[i].copy();amount=weights['R_Shoulder_Twist_Helper']*strength
    weights['R_Shoulder_Twist_Helper']-=amount;weights[target]+=amount;changes[str(i)]=weights
   candidates[f'helper_{target}_s{strength}']=changes
 # Solve a different direction: edge shortening with strong resistance to
 # normal motion at the two diagnostic poses, using existing four supports.
 names=list(w[143]);matrix=[];rhs=[]
 for clip,frame in [('braum_spell4',17),('braum_dance_loop',50)]:
  a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame)
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
  normal=np.array(m.vertices[143].normal);direction=np.array((m.vertices[190].co-m.vertices[143].co).normalized())
  positions=np.array([tuple(rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@Vector(rest[143])) for n in names]);basis=(positions[:3]-positions[3]).T
  matrix.extend([normal@basis*10,direction@basis]);rhs.extend([0,.005]);ev.to_mesh_clear()
 matrix.extend(np.eye(3)*.01);rhs.extend([0,0,0]);solution=np.linalg.lstsq(matrix,rhs,rcond=None)[0];dw=dict(zip(names,[*solution,-sum(solution)]))
 report['tangent_solution_delta']=dw
 for strength in [.5,1.0]:
  weights={n:v+strength*dw[n] for n,v in w[143].items()}
  if min(weights.values())>=0:candidates[f'tangent_s{strength}']={'143':weights}
 # Explicit image-outline constraints avoid assuming a smoothed vertex normal
 # is the normal of the visible polygonal silhouette.
 outline=[];shortening=[];outline_data=[]
 for clip,frame in [('braum_spell4',17),('braum_dance_loop',50)]:
  a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame)
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();view=Vector((3,7,2)).normalized();neighbors=[]
  for edge in o.data.edges:
   if 143 not in edge.vertices:continue
   faces=[f for f in m.polygons if all(i in f.vertices for i in edge.vertices)]
   signs=[f.normal.dot(view) for f in faces]
   if len(signs)==1 or min(signs)*max(signs)<0:neighbors.extend(i for i in edge.vertices if i!=143)
  if len(neighbors) in (0,2):
   if neighbors:
    tangent=(m.vertices[neighbors[1]].co-m.vertices[neighbors[0]].co).normalized();normal=np.array(view.cross(tangent).normalized())
   else:normal=np.array(m.vertices[143].normal)
   positions=np.array([tuple(rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@Vector(rest[143])) for n in names]);basis=(positions[:3]-positions[3]).T
   outline.append(normal@basis);shortening.append(np.array((m.vertices[190].co-m.vertices[143].co).normalized())@basis)
  outline_data.append({'clip':clip,'neighbors':neighbors});ev.to_mesh_clear()
 report['silhouette_neighbors']=outline_data
 if len(outline)==2:
  _,_,vt=np.linalg.svd(np.array(outline));direction=vt[-1];rates=np.array(shortening)@direction
  amplitude=float(rates.sum()*.005/(rates@rates+1e-8));solution=direction*amplitude
  dw=dict(zip(names,[*solution,-sum(solution)]));report['outline_solution_delta']=dw
  for strength in [.25,.5,1.0]:
   weights={n:v+dw[n]*strength for n,v in w[143].items()}
   if min(weights.values())>=0:candidates[f'outline_s{strength}']={'143':weights}
 for label,changes in candidates.items():
  for i,weights in changes.items():assign(int(i),weights)
  o.data.update();report['trials'][label]=measure()
  report['candidate_weights'][label]={'Object002':{i:{o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[int(i)].groups} for i in changes}}
  for i in changes:assign(int(i),w[int(i)])
  o.data.update()
 report['method']='In-memory local alternatives: taper the earlier delta over a bounded lower ring, or transfer only the helper share in equal-weight seam cluster190/331 to a native spine bone. No scene saved.'
 (ROOT/'validation/torso_local_alternatives.json').write_text(json.dumps(report,indent=2))
 for label,rows in report['trials'].items():
  print(label,len(report['candidate_weights'].get(label,{}).get('Object002',{})),[(x['clip'],x['frame'],round(x['max_elongation'],6),round(x['p99'],6),round(x['target_lengths']['143-190'],6)) for x in rows if (x['clip'],x['frame']) in [('braum_dance_loop',50),('braum_spell4',17)]])
 raise SystemExit
for endpoint,donor in [(143,190),(190,143)]:
 group=next((c for c in clusters if endpoint in c),[endpoint])
 for alpha in [.1,.25,.5]:
  for i in group:assign(i,{n:(1-alpha)*w[i].get(n,0)+alpha*w[donor].get(n,0) for n in w[i].keys()|w[donor].keys()})
  o.data.update();label=f'endpoint{endpoint}_alpha{alpha}';report['trials'][label]=measure()
  for i in group:assign(i,w[i])
  o.data.update()
(ROOT/'validation/torso_coupled_trials.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['endpoint_data']))
for k,rows in report['trials'].items():
 print(k,[(x['clip'],x['frame'],round(x['max_elongation'],6),round(x['p99'],6),round(x['target_lengths']['143-190'],6)) for x in rows if x['frame'] in [50,17,14]])
