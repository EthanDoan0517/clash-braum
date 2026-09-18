"""Continuous UV triangle-interior overlap check across selected meshes."""
from pathlib import Path
import sys,json,argparse,hashlib
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2]
def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])
def area(poly):
    return abs(sum(cross(poly[i],poly[(i+1)%len(poly)]) for i in range(len(poly))))*.5 if len(poly)>2 else 0.
def overlap(a,b):
    if cross(b[1]-b[0],b[2]-b[0])<0:b=b[::-1]
    poly=list(a)
    for i in range(3):
        origin=b[i];edge=b[(i+1)%3]-origin;result=[]
        for j,s in enumerate(poly):
            e=poly[(j+1)%len(poly)];s_in=cross(edge,s-origin)>=-1e-12;e_in=cross(edge,e-origin)>=-1e-12
            if s_in!=e_in:
                denom=cross(e-s,edge)
                if abs(denom)>1e-20:result.append(s+(e-s)*(cross(origin-s,edge)/denom))
            if e_in:result.append(e)
        poly=result
        if not poly:break
    return area(poly)
def broadphase(triangles):
    bounds=[(t.min(axis=0),t.max(axis=0)) for t in triangles]
    ordered=sorted(range(len(triangles)),key=lambda i:bounds[i][0][0])
    active=[]
    for i in ordered:
        lo,hi=bounds[i]
        active=[j for j in active if bounds[j][1][0]>=lo[0]]
        for j in active:
            if bounds[j][1][1]>=lo[1] and bounds[j][0][1]<=hi[1]:yield j,i
        active.append(i)
# Independent geometry fixtures: coincident, disjoint, edge-touch, contained.
t=np.array([[0.,0.],[1.,0.],[0.,1.]])
assert abs(overlap(t,t)-.5)<1e-12 and overlap(t,t+2)==0
assert overlap(t,np.array([[1.,0.],[1.,1.],[0.,1.]]))<1e-12
assert abs(overlap(t,t*.5)-.125)<1e-12
assert list(broadphase([t,t*.5]))==[(0,1)]
assert not list(broadphase([t,t+2]))
parser=argparse.ArgumentParser();parser.add_argument('--scene',default='clash_braum_shield_surface_v2_trial.blend');parser.add_argument('--prefix',default='CCE_');parser.add_argument('--output',default='shield_atlas_uv_validation.json')
parser.add_argument('--body',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert Path(args.scene).name==args.scene and Path(args.output).name==args.output
path=ROOT/'work/scenes'/args.scene;bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
triangles=[];identities=[];zero=[]
for obj in bpy.context.scene.objects:
    if obj.type!='MESH':continue
    if args.body:
        if obj.name.startswith('CCE_') or obj.name in ('Poro','Vanilla_Reference'):continue
    elif not obj.name.startswith(args.prefix):continue
    obj.data.calc_loop_triangles();layer=obj.data.uv_layers.active
    for tri in obj.data.loop_triangles:
        uv=np.array([tuple(layer.data[i].uv) for i in tri.loops]);assert np.isfinite(uv).all() and uv.min()>=-1e-6 and uv.max()<=1+1e-6
        if area(uv)<1e-14:zero.append([obj.name,tri.index]);continue
        triangles.append(uv);identities.append([obj.name,tri.index])
assert triangles
errors=[];checked=0
for a,b in broadphase(triangles):
    checked+=1;amount=overlap(triangles[a],triangles[b])
    if amount>1e-11:errors.append({'a':identities[a],'b':identities[b],'overlap_area':amount})
out={'scene':args.scene,'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':len(triangles),'zero_area_uv_triangles':zero,
 'uv_bounds_finite_unit_square':True,'sum_uv_triangle_area':sum(area(t) for t in triangles),'broadphase_pairs_checked':checked,'interior_overlaps':errors,
 'pass':not errors and not zero,'scope':'2D sweep-line bounding boxes followed by polygon clipping across all matching meshes; positive overlap area >1e-11 is reported. Edge contacts do not count. No texture-bleed or mipmap certificate.'}
(ROOT/'validation'/args.output).write_text(json.dumps(out,indent=2))
print('ATLAS',out['pass'],'TRIANGLES',len(triangles),'ZERO',len(zero),'OVERLAPS',len(errors),'AREA',out['sum_uv_triangle_area'])
