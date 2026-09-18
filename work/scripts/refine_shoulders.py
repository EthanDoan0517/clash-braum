"""Spatially regularize vest/sleeve weights from the deformation checkpoint."""
from pathlib import Path
import bpy,json,sys,hashlib,math
import numpy as np
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/scripts'),str(ROOT/'work/tools')]
from native_export import assert_native_rig
source=ROOT/'work/scenes/clash_braum_deformation.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
report=json.loads((ROOT/'validation/deformation_refinement.json').read_text())
report['shoulder_input_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
def ids(n,c):return next(x['indices'] for x in regions[n] if x['id']==c)
def assign(o,i,w):
 w=dict(sorted(((n,v) for n,v in w.items() if v>1e-6),key=lambda kv:-kv[1])[:4]);total=sum(w.values());assert total>0
 for g in list(o.data.vertices[i].groups):o.vertex_groups[g.group].remove([i])
 for n,v in w.items():(o.vertex_groups.get(n) or o.vertex_groups.new(name=n)).add([i],v/total,'REPLACE')
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
# Weld rest-position duplicates before sampling so UV/hard-normal splits do
# not bias the spatial field. Both garment layers sample the same field.
nodes={};names=[b.name for b in rig.data.bones];lookup={n:i for i,n in enumerate(names)}
for name,cs in {'Object002':[0],'Object004':[12,253]}.items():
 o=bpy.data.objects[name]
 for i in [i for c in cs for i in ids(name,c)]:
  p=o.data.vertices[i].co;k=tuple(round(v,5) for v in p)
  nodes.setdefault(k,[]).append((o,i))
keys=list(nodes);tree=KDTree(len(keys));w=np.zeros((len(keys),len(names)))
for j,k in enumerate(keys):
 tree.insert(k,j)
 for o,i in nodes[k]:
  for g in o.data.vertices[i].groups:w[j,lookup[o.vertex_groups[g.group].name]]+=g.weight/len(nodes[k])
tree.balance();neighbors=[]
for k in keys:
 hits=tree.find_range(k,.075);js=[j for _,j,d in hits];coeff=np.array([math.exp(-.5*(d/.03)**2) for _,j,d in hits]);coeff/=coeff.sum();neighbors.append((js,coeff))
original=w.copy()
for _ in range(2):
 w=np.array([np.sum(w[js]*coeff[:,None],axis=0) for js,coeff in neighbors])
changed={}
for j,k in enumerate(keys):
 x,y,z=k
 amount=.5*smooth(1.47,1.53,z)*(1-smooth(1.65,1.73,z))*smooth(.045,.10,abs(x))*(1-smooth(.30,.40,abs(x)))
 if amount==0:continue
 final=original[j]*(1-amount)+w[j]*amount
 for o,i in nodes[k]:
  assign(o,i,{n:float(final[q]) for q,n in enumerate(names)});changed.setdefault(o.name,[]).append(i)
report['shoulder_changes']={'spatial_radius':.075,'gaussian_sigma':.03,'passes':2,'correction_strength':.5,'changed_indices':changed,'method':'Shared rest-space field across vest and sleeves; smooth boundary mask, top four normalized'}
# Compact torso hardware with cross-body seed weights: attach at its actual
# rest height, preserving the already corrected belt shell 1366.
report['torso_hardware_changes']=[]
for name,cid,bone in [('Object006',1400,'Root'),('Object007',2583,'Spine2'),('Object007',2611,'Spine2')]:
 o=bpy.data.objects[name]
 for i in ids(name,cid):assign(o,i,{bone:1})
 item={'object':name,'component':cid,'vertices':len(ids(name,cid)),'bone':bone}
 report['rigid_components'].append(item);report['torso_hardware_changes'].append(item)
assert_native_rig(rig)
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.data.update()
rig.animation_data.action=bpy.data.actions['braum_idle_01_loop'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(17)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_shoulders.blend'))
(ROOT/'validation/shoulder_refinement.json').write_text(json.dumps(report,indent=2))
print('Changed', {n:len(v) for n,v in changed.items()},'plus',report['torso_hardware_changes'])

