"""Correct short-edge lower-vest transfer discontinuities from the shoulder checkpoint."""
from pathlib import Path
import bpy,json,sys,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'work/scripts'),str(ROOT/'work/tools')]
from native_export import assert_native_rig
source=ROOT/'work/scenes/clash_braum_shoulders.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
report=json.loads((ROOT/'validation/shoulder_refinement.json').read_text());report['torso_input_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
def assign(o,i,w):
 w=dict(sorted(((n,v) for n,v in w.items() if v>1e-6),key=lambda kv:-kv[1])[:4]);total=sum(w.values())
 for g in list(o.data.vertices[i].groups):o.vertex_groups[g.group].remove([i])
 for n,v in w.items():(o.vertex_groups.get(n) or o.vertex_groups.new(name=n)).add([i],v/total,'REPLACE')
o=bpy.data.objects['Object002'];changed=[]
indices=next(c['indices'] for c in regions[o.name] if c['id']==0)
# Correct actual short-edge transfer discontinuities without replacing the
# lower-vest field. Physical seam clusters are bounded to the R17 crease.
parent={i:i for i in indices if 1.30<o.data.vertices[i].co.z<1.36}
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for e in o.data.edges:
 a,b=e.vertices
 if a in parent and b in parent and (o.data.vertices[a].co-o.data.vertices[b].co).length<.008:
  parent[find(a)]=find(b)
clusters={}
for i in parent:clusters.setdefault(find(i),[]).append(i)
accepted=[]
for group in clusters.values():
 if len(group)<2:continue
 w={}
 for i in group:
  for g in o.data.vertices[i].groups:
   n=o.vertex_groups[g.group].name;w[n]=w.get(n,0)+g.weight/len(group)
 for i in group:assign(o,i,w);changed.append(i)
 accepted.append(group)
report['torso_changes']={'changed_indices':{o.name:changed},'clusters':accepted,'method':'Average original weights across connected edges shorter than .008 in rest z1.30..1.36; normalize top-four. All other weights unchanged.'}
assert_native_rig(rig);o.data.update()
rig.animation_data.action=bpy.data.actions['braum_idle_01_loop'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(17)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_torso.blend'))
(ROOT/'validation/torso_refinement.json').write_text(json.dumps(report,indent=2));print('Changed',len(changed),'vest vertices')
