"""Child candidate: ten percent coupled correction at the long-edge lower endpoint."""
from pathlib import Path
import bpy,json,sys,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'work/scripts'),str(ROOT/'work/tools')]
from native_export import assert_native_rig
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
o=bpy.data.objects['Object002'];rig=bpy.data.objects['Braum_Native']
def weights(i):return {o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[i].groups}
a,b=weights(143),weights(190)
w={n:.9*a.get(n,0)+.1*b.get(n,0) for n in a.keys()|b.keys()};w=dict(sorted(w.items(),key=lambda x:-x[1])[:4]);total=sum(w.values())
for g in list(o.data.vertices[143].groups):o.vertex_groups[g.group].remove([143])
for n,v in w.items():o.vertex_groups[n].add([143],v/total,'REPLACE')
o.data.update();assert_native_rig(rig)
r=json.loads((ROOT/'validation/torso_refinement.json').read_text());r['coupled_changes']={'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'changed_indices':{'Object002':[143]},'before':a,'after':weights(143),'method':'Blend vertex143 ten percent toward vertex190, then normalize largest four. All 67 accepted seam vertices remain unchanged.'}
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_torso_coupled.blend'))
(ROOT/'validation/torso_coupled_refinement.json').write_text(json.dumps(r,indent=2))

