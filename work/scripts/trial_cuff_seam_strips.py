"""Extend seam-ring attachment along cuff strips without changing skin or shape."""
from pathlib import Path
import bpy,json,hashlib,math,bisect
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];obj=bpy.data.objects['Object004']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
ties=json.loads((ROOT/'validation/cuff_seam_tie_candidates.json').read_text())
changes={};details=[]
for side,cid in [('L',2539),('R',865)]:
    elbow=rig.data.bones[side+'_Elbow'].head_local;axis=rig.data.bones[side+'_Hand'].head_local-elbow
    forward=axis.normalized();u=forward.cross(Vector((0,1,0))).normalized();v=forward.cross(u)
    def coords(i):
        p=obj.data.vertices[i].co-elbow
        return (math.atan2(p.dot(v),p.dot(u))%(2*math.pi),p.dot(axis)/axis.length_squared)
    anchors=sorted((coords(m['cloth_vertex'])[0],m) for m in ties['matches'] if m['side']==side)
    angles=[a for a,m in anchors]
    for i in next(c['indices'] for c in regions['Object004'] if c['id']==cid):
        angle,t=coords(i)
        if t>=1.02:continue
        b=bisect.bisect_right(angles,angle)%len(anchors);a=(b-1)%len(anchors)
        distance=(angles[b]-angles[a])%(2*math.pi);s=((angle-angles[a])%(2*math.pi))/distance
        wa,wb=anchors[a][1]['new_weights'],anchors[b][1]['new_weights']
        desired={n:wa.get(n,0)*(1-s)+wb.get(n,0)*s for n in set(wa)|set(wb)}
        seam_t=anchors[a][1]['axial_t']*(1-s)+anchors[b][1]['axial_t']*s
        old={obj.vertex_groups[g.group].name:g.weight for g in obj.data.vertices[i].groups if g.weight>0}
        fade=max(0,min(1,(t-seam_t)/(1.02-seam_t)));fade=fade*fade*(3-2*fade)
        w={n:desired.get(n,0)*(1-fade)+old.get(n,0)*fade for n in set(desired)|set(old)}
        w={n:v for n,v in w.items() if v>1e-7};assert len(w)<=4,(i,w)
        total=sum(w.values());w={n:v/total for n,v in w.items()}
        changes[str(i)]=w;details.append({'vertex':i,'side':side,'anchors':[anchors[a][1]['cloth_vertex'],anchors[b][1]['cloth_vertex']],'fraction':s,'distal_fade':fade})
changes.update(ties['candidate_weights']['ties']['Object004'])
report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'UNACCEPTED angular seam-strip attachment diagnostic','candidate_weights':{'strips':{'Object004':changes}},'attachment':details}
(ROOT/'validation/cuff_seam_strip_candidates.json').write_text(json.dumps(report,indent=2))
print('Strip vertices',len(changes))
