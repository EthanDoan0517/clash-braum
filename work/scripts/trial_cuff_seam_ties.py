"""Tie only coincident cuff/forearm boundary vertices; preserve all rest geometry."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];cloth=bpy.data.objects['Object004'];skin=bpy.data.objects['Object009']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
def weights(obj,i):return {obj.vertex_groups[g.group].name:g.weight for g in obj.data.vertices[i].groups if g.weight>0}
changes={};matches=[]
for side,glove,arm in [('L',2539,810),('R',865,652)]:
    glove_ids=next(c['indices'] for c in regions['Object004'] if c['id']==glove)
    arm_ids=next(c['indices'] for c in regions['Object009'] if c['id']==arm)
    elbow=rig.data.bones[side+'_Elbow'].head_local;axis=rig.data.bones[side+'_Hand'].head_local-elbow
    for i in glove_ids:
        v=cloth.data.vertices[i];t=(v.co-elbow).dot(axis)/axis.length_squared
        if t>1.02:continue
        nearest=min(arm_ids,key=lambda j:(v.co-skin.data.vertices[j].co).length_squared)
        distance=(v.co-skin.data.vertices[nearest].co).length
        if distance>1e-7:continue
        old=weights(cloth,i);new=weights(skin,nearest)
        if old==new:continue
        changes[str(i)]=new
        matches.append({'side':side,'cloth_vertex':i,'skin_vertex':nearest,'distance':distance,'axial_t':t,'old_weights':old,'new_weights':new})
report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'UNACCEPTED coincident-boundary tie diagnostic, no scene saved','candidate_weights':{'ties':{'Object004':changes}},'matches':matches}
(ROOT/'validation/cuff_seam_tie_candidates.json').write_text(json.dumps(report,indent=2))
print('Coincident changed vertices',len(changes));print(json.dumps(matches,indent=2))
