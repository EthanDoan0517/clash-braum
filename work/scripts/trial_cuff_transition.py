"""In-memory candidate weights aligning cuff transition with accepted forearm."""
from pathlib import Path
import hashlib,json
import bpy
ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];obj=bpy.data.objects['Object004']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
def smooth(a,b,t):
    t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
report={'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':'Diagnostic weights only; no scene saved','method':'Match accepted skin forearm elbow/hand axial law only within non-digit glove cuff; fade changes to zero at wrist','candidate_weights':{},'changed_vertices':{}}
for strength in (.5,1.):
    changes={}
    for side,cid in [('L',2539),('R',865)]:
        elbow=rig.data.bones[side+'_Elbow'].head_local;axis=rig.data.bones[side+'_Hand'].head_local-elbow
        for i in next(c['indices'] for c in regions['Object004'] if c['id']==cid):
            vertex=obj.data.vertices[i];old={obj.vertex_groups[g.group].name:g.weight for g in vertex.groups if g.weight>0}
            if not set(old)<={side+'_Hand',side+'_Elbow',side+'_Hand_Twist'}:continue
            t=(vertex.co-elbow).dot(axis)/axis.length_squared
            if not .55<t<1.:continue
            hand=smooth(.55,1.,t);amount=strength*(1-smooth(.96,1.,t))
            desired={side+'_Elbow':1-hand,side+'_Hand':hand}
            new={n:old.get(n,0)*(1-amount)+desired.get(n,0)*amount for n in set(old)|set(desired)}
            new={n:v for n,v in new.items() if v>1e-8};total=sum(new.values());new={n:v/total for n,v in new.items()}
            if max(abs(new.get(n,0)-old.get(n,0)) for n in set(new)|set(old))>1e-7:changes[str(i)]=new
    report['candidate_weights'][f'axial_{strength}']={'Object004':changes}
    report['changed_vertices'][f'axial_{strength}']=len(changes)
(ROOT/'validation/cuff_transition_candidates.json').write_text(json.dumps(report,indent=2))
print(report['changed_vertices'])
