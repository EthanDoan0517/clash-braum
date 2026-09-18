"""Stage 4: remove redundant planar shield tessellation in a separate trial.

Body topology, weights, UVs and all accepted seam corrections stay exact.
Surface samples diagnose geometric drift; they are not a Hausdorff certificate.
"""
from pathlib import Path
import sys,json,hashlib,math,argparse
import bpy
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--weld',action='store_true')
parser.add_argument('--collapse',action='store_true',help='Separate approximate Stage 4 LOD trial, not exact planar cleanup')
parser.add_argument('--max-surface-error',type=float,default=1e-5,help='Explicit sampled surface budget for this geometry trial')
parser.add_argument('--label',help='Distinct trial name; existing scenes are never overwritten')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert 0<args.max_surface_error<=.003
label='shield_collapse_trial' if args.collapse else ('shield_weld_planar_trial' if args.weld else 'shield_planar_trial')
if args.label:
    assert args.label.replace('_','').isalnum();label=args.label
source=ROOT/'work/scenes/clash_braum_torso.blend'
target=ROOT/f'work/scenes/clash_braum_{label}.blend'
assert not target.exists(), 'Preserve prior trial; use a new output for a changed algorithm'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
def signature(o):
    m=o.data
    return hashlib.sha256(repr((list(map(tuple,o.matrix_world)),[(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in m.vertices],
        [tuple(p.vertices) for p in m.polygons],[[tuple(x.uv) for x in l.data] for l in m.uv_layers],
        [tuple(n.vector) for n in m.corner_normals],[p.material_index for p in m.polygons],
        [s.material.name if s.material else None for s in o.material_slots])).encode()).hexdigest()
def surface(mesh):
    mesh.calc_loop_triangles()
    points=[v.co.copy() for v in mesh.vertices]
    triangles=[tuple(t.vertices) for t in mesh.loop_triangles]
    return points,triangles,BVHTree.FromPolygons(points,triangles,all_triangles=True)
def compare(points,triangles,tree):
    maximum=0.;mapping=[]
    for i,tri in enumerate(triangles):
        a,b,c=[points[j] for j in tri]
        samples=[a,b,c,(a+b)*.5,(b+c)*.5,(c+a)*.5,(a+b+c)/3]
        hits=[tree.find_nearest(p) for p in samples]
        assert all(h[0] is not None for h in hits)
        distance=max(h[3] for h in hits);maximum=max(maximum,distance)
        mapping.append({'triangle':i,'nearest_source_triangle_at_centroid':hits[-1][2],'max_sample_distance':distance})
    return maximum,mapping
protected={o.name:signature(o) for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('CCE_')}
rows=[]
for obj in sorted((o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('CCE_')),key=lambda o:o.name):
    original_mesh=obj.data.copy()
    old=surface(obj.data);before_vertices=len(obj.data.vertices)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    if args.weld:
        weld=obj.modifiers.new('Join exact coincident rigid shield vertices','WELD');weld.merge_threshold=1e-7
        bpy.ops.object.modifier_move_up(modifier=weld.name)
        bpy.ops.object.modifier_apply(modifier=weld.name)
    modifier=obj.modifiers.new('Planar redundant tessellation','DECIMATE');modifier.decimate_type='DISSOLVE'
    modifier.angle_limit=.0001;modifier.use_dissolve_boundaries=False
    modifier.delimit={'NORMAL','MATERIAL','SEAM','SHARP','UV'}
    if args.collapse:
        modifier.decimate_type='COLLAPSE';modifier.ratio=.5;modifier.use_collapse_triangulate=True
    # Dissolve rest geometry before skinning; keep the native Armature modifier.
    bpy.ops.object.modifier_move_up(modifier=modifier.name)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    new=surface(obj.data)
    a,mapping=compare(new[0],new[1],old[2]);b,_=compare(old[0],old[1],new[2])
    proposed_triangles=len(new[1]);retained=max(a,b)<args.max_surface_error
    if not retained:
        rejected_mesh=obj.data;obj.data=original_mesh;bpy.data.meshes.remove(rejected_mesh)
        new=surface(obj.data);mapping=[]
    else:
        bpy.data.meshes.remove(original_mesh)
    for v in obj.data.vertices:
        w={obj.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}
        assert w=={'Shield':1.0},(obj.name,v.index,w)
    assert all(math.isfinite(x) for layer in obj.data.uv_layers for loop in layer.data for x in loop.uv)
    rows.append({'object':obj.name,'retained':retained,'proposed_triangles':proposed_triangles,'before_vertices':before_vertices,'after_vertices':len(obj.data.vertices),
        'before_triangles':len(old[1]),'after_triangles':len(new[1]),'candidate_to_source_max_sample_distance':a,
        'source_to_candidate_max_sample_distance':b,'source_triangle_mapping':mapping})
assert all(signature(bpy.data.objects[n])==s for n,s in protected.items())
report={'status':'STAGE 4 TRIAL: protected body contract and sampled shield surface checks passed; visual/export review required',
    'parent_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scene':target.name,
    'method':{'weld_threshold':1e-7 if args.weld else None,'decimate_type':'COLLAPSE' if args.collapse else 'DISSOLVE','ratio':.5 if args.collapse else None,'max_sample_surface_error':args.max_surface_error,'angle_limit_radians':.0001,'dissolve_delimit':['NORMAL','MATERIAL','SEAM','SHARP','UV'],'dissolve_boundaries':False},
    'protected_mesh_signatures':protected,'protected_meshes_exact':True,'shield_weights_rigid':True,'uv_finite':True,
    'before_shield_triangles':sum(r['before_triangles'] for r in rows),'after_shield_triangles':sum(r['after_triangles'] for r in rows),'objects':rows}
bpy.ops.wm.save_as_mainfile(filepath=str(target))
report['scene_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
(ROOT/f'validation/{label}.json').write_text(json.dumps(report,indent=2))
print('SHIELD TRIANGLES',report['before_shield_triangles'],'->',report['after_shield_triangles'])
