"""Bounded wrist attachment alternatives; immutable parent, no saved scene."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
obj=bpy.data.objects['Object004'];rig=bpy.data.objects['Braum_Native']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'Unaccepted diagnostic wrist attachment; no scene saved','candidate_weights':{}}
for amount in [.9,.97,1.]:
    changes={}
    for side,cid in [('L',2539),('R',865)]:
        elbow=rig.data.bones[side+'_Elbow'].head_local;axis=rig.data.bones[side+'_Hand'].head_local-elbow
        for i in next(c['indices'] for c in regions['Object004'] if c['id']==cid):
            v=obj.data.vertices[i];t=(v.co-elbow).dot(axis)/axis.length_squared
            if t>=1.02:continue
            old={obj.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}
            if not set(old)<={side+'_Hand',side+'_Elbow',side+'_Hand_Twist'}:continue
            # Raise proximal cuff to a near-uniform hand attachment; retain
            # already stronger hand weights at the glove boundary.
            hand=max(amount,old.get(side+'_Hand',0))
            w={side+'_Hand':hand}
            if hand<1:w[side+'_Elbow']=1-hand
            changes[str(i)]=w
    report['candidate_weights'][f'hand_{amount}']={'Object004':changes}
for cap in [.03,0.]:
    changes={}
    for side,cid in [('L',2539),('R',865)]:
        elbow=rig.data.bones[side+'_Elbow'].head_local;axis=rig.data.bones[side+'_Hand'].head_local-elbow
        for i in next(c['indices'] for c in regions['Object004'] if c['id']==cid):
            v=obj.data.vertices[i];t=(v.co-elbow).dot(axis)/axis.length_squared
            if t>=1.02:continue
            old={obj.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}
            w=dict(old);proximal=old.get(side+'_Elbow',0)+old.get(side+'_Hand_Twist',0)
            retained=min(cap,proximal)
            if proximal<=retained:continue
            for n in [side+'_Elbow',side+'_Hand_Twist']:
                if n in w:w[n]*=retained/proximal
            w[side+'_Hand']=w.get(side+'_Hand',0)+proximal-retained
            changes[str(i)]={n:v for n,v in w.items() if v>0}
    report['candidate_weights'][f'cap_{cap}']={'Object004':changes}
(ROOT/'validation/cuff_wrist_candidates.json').write_text(json.dumps(report,indent=2))
print({k:len(v['Object004']) for k,v in report['candidate_weights'].items()})
