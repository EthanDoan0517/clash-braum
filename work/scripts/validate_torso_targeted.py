"""Fifteen-pose torso diagnostics, explicit crease edges and protected-region comparison."""
from pathlib import Path
import bpy,json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[2]
r=json.loads((ROOT/'validation/torso_refinement.json').read_text());regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
allowed={n:set(v) for n,v in r['torso_changes']['changed_indices'].items()}

cases=[('braum_recall',f) for f in [60,65,70]]+[('braum_dance_loop',f) for f in [45,50,55]]+[('braum_spell4',f) for f in [3,15,17,26]]+[('braum_idle_01_loop',17),('braum_spell3_idle180',29),('braum_run_02',12),('braum_spell3_run0',14),('braum_spell3_run-90',14)]
report={'revisions':{}};baseline={}
for label,file in [('before','clash_braum_shoulders.blend'),('after','clash_braum_torso.blend')]:
 path=ROOT/'work/scenes'/file;bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
 rig=bpy.data.objects['Braum_Native'];objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
 for o in objects:
  state=[(tuple(v.co),{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}) for v in o.data.vertices]
  if label=='before':baseline[o.name]=state
  else:
   for i,(p,w) in enumerate(state):
    assert p==baseline[o.name][i][0],(o.name,i,'geometry changed')
    if i not in allowed.get(o.name,set()):assert w==baseline[o.name][i][1],(o.name,i,'protected weight changed')
 rows=[]
 for clip,frame in cases:
  a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame);dep=bpy.context.evaluated_depsgraph_get()
  for n in allowed:
   o=bpy.data.objects[n];ev=o.evaluated_get(dep);m=ev.to_mesh();e=np.array([tuple(e.vertices) for e in o.data.edges]);p=np.array([tuple(v.co) for v in m.vertices]);rest=np.array([tuple(v.co) for v in o.data.vertices]);d=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)-np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1)
   ratios=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)/np.maximum(np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1),.0001)
   row={'max_edge_ratio':float(ratios.max()),'clip':clip,'frame':frame,'object':n,'max_elongation':float(d.max()),'p99_elongation':float(np.quantile(d,.99))}
   if n=='Object002':
    row['edge_1497_2321_length']=float(np.linalg.norm(p[1497]-p[2321]))
    row['target_edges']={f'{a}-{b}':float(np.linalg.norm(p[a]-p[b])) for a,b in [(1094,1095),(733,737),(148,150),(157,158),(143,190),(133,152)]}
   rows.append(row);ev.to_mesh_clear()
 report['revisions'][label]={'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'poses':rows}
report['all_rest_geometry_and_unlisted_weights_unchanged']=True
(ROOT/'validation/torso_targeted_validation.json').write_text(json.dumps(report,indent=2))
for a,b in zip(report['revisions']['before']['poses'],report['revisions']['after']['poses']):
 if a['frame'] in [65,50,17,14]:print(a['clip'],a['object'],round(a['max_elongation'],5),'->',round(b['max_elongation'],5),'edge',a.get('edge_1497_2321_length'),b.get('edge_1497_2321_length'))
