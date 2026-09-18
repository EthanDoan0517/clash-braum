"""Read-only UV/normal interpolation and projected aperture comparisons.

Closest-surface correspondences can be ambiguous at coincident sheets; report
identity-control errors and distributions rather than claiming exact ancestry.
"""
from pathlib import Path
import json,hashlib,math,argparse,sys
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--scene',default='clash_braum_shield_collapse_trial.blend');parser.add_argument('--label',default='shield_surface_review')
parser.add_argument('--uv-layer',help='Compare a retained legacy layer; otherwise active UV')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert Path(args.scene).name==args.scene and args.label.replace('_','').isalnum()
def snapshot(filename):
    path=ROOT/'work/scenes'/filename
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    result={}
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or not o.name.startswith('CCE_'):continue
        m=o.data;m.calc_loop_triangles();normalmatrix=o.matrix_world.to_3x3().inverted().transposed()
        xyz=np.array([tuple(o.matrix_world@v.co) for v in m.vertices])
        tris=np.array([tuple(t.vertices) for t in m.loop_triangles]);loops=np.array([tuple(t.loops) for t in m.loop_triangles])
        layer=m.uv_layers.get(args.uv_layer) if args.uv_layer else None
        uv=np.array([tuple(x.uv) for x in (layer or m.uv_layers.active).data])[loops]
        normals=np.array([tuple((normalmatrix@n.vector).normalized()) for n in m.corner_normals])[loops]
        result[o.name]={'xyz':xyz,'tri':tris,'uv':uv,'normal':normals,
                        'materials':[s.material.name if s.material else None for s in o.material_slots],
                        'material_indices':np.array([t.material_index for t in m.loop_triangles])}
    return result,hashlib.sha256(path.read_bytes()).hexdigest()
def tree(s):return BVHTree.FromPolygons(s['xyz'].tolist(),s['tri'].tolist(),all_triangles=True)
def barycentric(point,triangle):
    a,b,c=triangle;v0=b-a;v1=c-a;v2=point-a
    d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1
    denom=d00*d11-d01*d01
    if abs(denom)<1e-24:return np.array([1.,0.,0.])
    v=(d11*d20-d01*d21)/denom;w=(d00*d21-d01*d20)/denom
    return np.array([1-v-w,v,w])
def interpolate_compare(old,new):
    bvh=tree(old);uv_errors=[];angles=[];distances=[];material_errors=0
    # Interior samples avoid ambiguous exact seams and hard-edge normals.
    for i,tri in enumerate(new['tri']):
        xyz=new['xyz'][tri]
        for weights in (np.array([1/3]*3),np.array([.8,.1,.1]),np.array([.1,.8,.1]),np.array([.1,.1,.8])):
            p=weights@xyz;hit,_,idx,d=bvh.find_nearest(Vector(p));assert hit is not None
            w=barycentric(np.array(hit),old['xyz'][old['tri'][idx]])
            uv_errors.append(float(np.linalg.norm(weights@new['uv'][i]-w@old['uv'][idx])))
            n1=weights@new['normal'][i];n2=w@old['normal'][idx]
            denom=np.linalg.norm(n1)*np.linalg.norm(n2)
            angles.append(math.degrees(math.acos(float(np.clip((n1@n2)/max(denom,1e-20),-1,1)))))
            distances.append(d);material_errors+=int(new['material_indices'][i]!=old['material_indices'][idx])
    def stats(values):return dict(zip(('p50','p95','p99','max'),map(float,np.quantile(values,[.5,.95,.99,1]))))
    return {'samples':len(angles),'uv_error':stats(uv_errors),'normal_angle_degrees':stats(angles),
            'surface_distance':stats(distances),'material_mismatch_samples':material_errors,'slots_equal':old['materials']==new['materials']}
def joined(data):
    xyz=[];tri=[]
    for s in data.values():
        tri.extend((s['tri']+len(xyz)).tolist());xyz.extend(s['xyz'].tolist())
    return {'xyz':np.array(xyz),'tri':np.array(tri)}
old,parent_hash=snapshot('clash_braum_gameplay_accepted.blend')
new,trial_hash=snapshot(args.scene)
rows={n:{'identity':interpolate_compare(old[n],old[n]),'trial':interpolate_compare(old[n],new[n])} for n in old}
a=joined(old);b=joined(new);center=a['xyz'].mean(axis=0)
_,basis=np.linalg.eigh(np.cov((a['xyz']-center).T));u=basis[:,1];v=basis[:,2];normal=basis[:,0]
projection=np.stack(((a['xyz']-center)@u,(a['xyz']-center)@v),axis=1)
lo=projection.min(axis=0)-.02;hi=projection.max(axis=0)+.02
width,height=256,512;mask=[]
for surface in (a,b):
    bvh=tree(surface);hits=np.zeros((height,width),dtype=bool)
    for y in range(height):
        for x in range(width):
            p=center+u*(lo[0]+(x+.5)/width*(hi[0]-lo[0]))+v*(lo[1]+(y+.5)/height*(hi[1]-lo[1]))
            front=bvh.ray_cast(Vector(p-normal*3),Vector(normal),6)[0]
            back=bvh.ray_cast(Vector(p+normal*3),Vector(-normal),6)[0]
            assert (front is None)==(back is None), 'Inconsistent bidirectional occupancy'
            hits[y,x]=front is not None
    mask.append(hits)
np.savez_compressed(ROOT/f'validation/{args.label}_masks.npz',parent=mask[0],trial=mask[1])
report={'status':'UV/normal and aperture diagnostics; visual judgment required','parent_sha256':parent_hash,'trial_sha256':trial_hash,'uv_layer':args.uv_layer or 'active',
 'method':'4 interior barycentric samples per triangle, nearest source surface; errors may include ambiguous coincident sheets. PCA-plane grid rays from both sides.',
 'objects':rows,'aperture':{'resolution':[width,height],'parent_occupied_pixels':int(mask[0].sum()),'trial_occupied_pixels':int(mask[1].sum()),
 'new_occupied_pixels':int((mask[1]&~mask[0]).sum()),'new_open_pixels':int((mask[0]&~mask[1]).sum()),
 'pixel_world_size':((hi-lo)/[width,height]).tolist()}}
(ROOT/f'validation/{args.label}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['aperture']))
for n,r in rows.items():print(n,json.dumps(r['trial']))
