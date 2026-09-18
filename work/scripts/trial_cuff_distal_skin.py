"""Matched distal skin/cuff attachment; test shifting stretch into bare forearm."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'UNACCEPTED coupled cuff/distal forearm diagnostic; no scene saved','candidate_weights':{}}
for end in [.82,.88]:
    changes={}
    for name,components in [('Object004',[('L',2539),('R',865)]),('Object009',[('L',810),('R',652)])]:
        obj=bpy.data.objects[name];changes[name]={}
        for side,cid in components:
            elbow=rig.data.bones[side+'_Elbow'].head_local;axis=rig.data.bones[side+'_Hand'].head_local-elbow
            for i in next(c['indices'] for c in regions[name] if c['id']==cid):
                v=obj.data.vertices[i];t=(v.co-elbow).dot(axis)/axis.length_squared
                if t<=.65 or (name=='Object004' and t>=1.02):continue
                old={obj.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}
                u=max(0,min(1,(t-.55)/(end-.55)));desired=u*u*(3-2*u)
                proximal=old.get(side+'_Elbow',0)+old.get(side+'_Hand_Twist',0)
                transfer=min(proximal,max(0,desired-old.get(side+'_Hand',0)))
                if transfer<1e-7:continue
                w=dict(old)
                for n in [side+'_Elbow',side+'_Hand_Twist']:
                    if n in w:w[n]*=(proximal-transfer)/proximal
                w[side+'_Hand']=w.get(side+'_Hand',0)+transfer
                changes[name][str(i)]={n:v for n,v in w.items() if v>0}
    report['candidate_weights'][f'distal_{end}']=changes
(ROOT/'validation/cuff_distal_skin_candidates.json').write_text(json.dumps(report,indent=2))
print({key:{n:len(v) for n,v in changes.items()} for key,changes in report['candidate_weights'].items()})
