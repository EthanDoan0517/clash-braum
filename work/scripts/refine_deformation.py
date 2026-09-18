"""Local Stage 3 corrections from the retained refined checkpoint (no re-import)."""
from pathlib import Path
import bpy, json, sys, hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/scripts'),str(ROOT/'work/tools')]
from native_export import assert_native_rig
source=ROOT/'work/scenes/clash_braum_rig_refined.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
report=json.loads((ROOT/'validation/rig_refinement.json').read_text())
report['deformation_input_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
report['deformation_changes']=[]
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)))
    return t*t*(3-2*t)
def weights(obj,i):
    return {obj.vertex_groups[g.group].name:g.weight for g in obj.data.vertices[i].groups if g.weight>0}
def assign(obj,i,w):
    w={n:v for n,v in w.items() if v>1e-6}
    w=dict(sorted(w.items(),key=lambda kv:-kv[1])[:4]);total=sum(w.values())
    assert total>0
    for g in list(obj.data.vertices[i].groups):obj.vertex_groups[g.group].remove([i])
    for n,v in w.items():(obj.vertex_groups.get(n) or obj.vertex_groups.new(name=n)).add([i],v/total,'REPLACE')
def ids(name,cid):return next(c['indices'] for c in regions[name] if c['id']==cid)
# Continuous skin forearms: replace the frozen x>.71 boundary with an axial
# wrist blend. Preserve proximal elbow/shoulder weights and all digit shells.
obj=bpy.data.objects['Object009']
for side,cid in [('R',652),('L',810)]:
    elbow=rig.data.bones[side+'_Elbow'].head_local
    wrist=rig.data.bones[side+'_Hand'].head_local
    axis=wrist-elbow
    count=0
    for i in ids(obj.name,cid):
        t=(obj.data.vertices[i].co-elbow).dot(axis)/axis.length_squared
        if t<=.45:continue
        amount=smooth(.45,.65,t)
        hand=smooth(.55,1.,t)
        old=weights(obj,i);desired={side+'_Elbow':1-hand,side+'_Hand':hand}
        w={n:v*(1-amount) for n,v in old.items()}
        for n,v in desired.items():w[n]=w.get(n,0)+v*amount
        assign(obj,i,w);count+=1
    report['deformation_changes'].append({'object':obj.name,'component':cid,'vertices':count,'method':'Axial elbow-to-hand blend, t .55..1; proximal blend .45...65'})
# Seat is below the root: upper-spine weights came from nearby folded donor
# surfaces. Move those weights to Root, retaining the authored hip/knee blend.
obj=bpy.data.objects['Object001'];count=0
for i in ids(obj.name,0):
    w=weights(obj,i);amount=1-smooth(1.04,1.14,obj.data.vertices[i].co.z)
    moved=0
    for n in ['Spine1','Spine2','Spine3']:
        v=w.get(n,0)*amount;w[n]=w.get(n,0)-v;moved+=v
    if moved>1e-6:
        w['Root']=w.get('Root',0)+moved;assign(obj,i,w);count+=1
report['deformation_changes'].append({'object':obj.name,'component':0,'vertices':count,'method':'Seat spine influence to Root; fade z 1.04..1.14; retain hips/knees'})
# The belt shell surrounds Root and sits next to existing rigid Root hardware.
obj=bpy.data.objects['Object006']
for i in ids(obj.name,1366):assign(obj,i,{'Root':1})
report['rigid_components'].append({'object':obj.name,'component':1366,'vertices':len(ids(obj.name,1366)),'bone':'Root'})
report['deformation_changes'].append({'object':obj.name,'component':1366,'vertices':len(ids(obj.name,1366)),'method':'Continuous belt follows Root'})
assert_native_rig(rig)
for obj in bpy.context.scene.objects:
    if obj.type=='MESH':obj.data.update()
rig.animation_data.action=bpy.data.actions['braum_idle_01_loop']
rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(17)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_deformation.blend'))
(ROOT/'validation/deformation_refinement.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['deformation_changes']))
