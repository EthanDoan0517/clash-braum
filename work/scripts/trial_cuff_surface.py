"""Fit only cuff transition vertices to the accepted forearm skin surface."""
from pathlib import Path
import hashlib,json
import sys
import bpy
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];obj=bpy.data.objects['Object004'];skin=bpy.data.objects['Object009']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
allowed=json.loads((ROOT/'validation/cuff_transition_candidates.json').read_text())['candidate_weights']['axial_1.0']['Object004']
full_ring='--full-ring' in sys.argv
if full_ring:
    allowed={}
    for side,cid in [('L',2539),('R',865)]:
        elbow=rig.data.bones[side+'_Elbow'].head_local;axis=rig.data.bones[side+'_Hand'].head_local-elbow
        for i in next(c['indices'] for c in regions['Object004'] if c['id']==cid):
            t=(obj.data.vertices[i].co-elbow).dot(axis)/axis.length_squared
            if t<1.02:allowed[str(i)]=None
def weights(o,i):return {o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[i].groups if g.weight>0}
changes={};positions={};details=[]
for side,component in [('L',810),('R',652)]:
    ids=set(next(c['indices'] for c in regions['Object009'] if c['id']==component))
    faces=[tuple(f.vertices) for f in skin.data.polygons if set(f.vertices)<=ids]
    tree=BVHTree.FromPolygons([v.co for v in skin.data.vertices],faces)
    elbow=rig.data.bones[side+'_Elbow'].head_local;axis=rig.data.bones[side+'_Hand'].head_local-elbow
    for index in allowed:
        i=int(index);vertex=obj.data.vertices[i]
        if (vertex.co.x>0)!=(side=='L'):continue
        nearest,normal,face,distance=tree.find_nearest(vertex.co)
        assert len(faces[face])==3
        a,b,c=(skin.data.vertices[j].co for j in faces[face])
        bary=barycentric_transform(nearest,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        w={}
        for j,amount in zip(faces[face],bary):
            for n,value in weights(skin,j).items():w[n]=w.get(n,0)+max(0,amount)*value
        assert len([v for v in w.values() if v>1e-6])<=4
        w={n:v for n,v in w.items() if v>1e-6};total=sum(w.values());w={n:v/total for n,v in w.items()}
        radial=nearest-(elbow+axis*((nearest-elbow).dot(axis)/axis.length_squared))
        if normal.dot(radial)<0:normal=-normal
        # Preserve tangential placement; only lift cloth that lacks clearance.
        clearance=(vertex.co-nearest).dot(normal)
        point=vertex.co+normal*max(0,.003-clearance)
        if full_ring:
            t=(vertex.co-elbow).dot(axis)/axis.length_squared
            fade=max(0,min(1,(t-.98)/.04));fade=fade*fade*(3-2*fade)
            old=weights(obj,i);w={n:w.get(n,0)*(1-fade)+old.get(n,0)*fade for n in set(w)|set(old)}
            w={n:v for n,v in w.items() if v>1e-6};assert len(w)<=4
            total=sum(w.values());w={n:v/total for n,v in w.items()};point=vertex.co+(point-vertex.co)*(1-fade)
        changes[index]=w;positions[index]=list(point)
        details.append({'vertex':i,'side':side,'skin_face':faces[face],'barycentric':list(bary),'nearest_distance':distance,'rest_clearance_before':clearance,'rest_displacement':(point-vertex.co).length})
report={'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':'Diagnostic only; exact forearm-surface transfer and minimum .003 rest clearance; no scene saved','candidate_weights':{'surface':{'Object004':changes}},'candidate_positions':{'surface':{'Object004':positions}},'vertices':details}
(ROOT/'validation'/('cuff_surface_ring_candidates.json' if full_ring else 'cuff_surface_candidates.json')).write_text(json.dumps(report,indent=2))
print('Cuff vertices',len(changes),'max rest displacement',max(r['rest_displacement'] for r in details))
