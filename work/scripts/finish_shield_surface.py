"""Restore source corner shading and author a shared shield atlas UV layout.

The shield has temporary untextured materials; its old preparation UVs are
retained as a named layer. Body materials and UVs are never changed.
"""
from pathlib import Path
import json,hashlib,math,argparse,sys
import bpy
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_gameplay_accepted.blend'
trial=ROOT/'work/scenes/clash_braum_shield_collapse_trial.blend'
parser=argparse.ArgumentParser();parser.add_argument('--label',default='shield_surface_v2_trial')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert args.label.replace('_','').isalnum()
target=ROOT/f'work/scenes/clash_braum_{args.label}.blend'
assert not target.exists()
bpy.ops.wm.open_mainfile(filepath=str(trial),load_ui=False,use_scripts=False)
targets={o.name:o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('CCE_')}
for obj in targets.values():
    for slot in obj.material_slots:
        if slot.material and slot.material.use_nodes:
            assert not any(n.type in ('TEX_IMAGE','UVMAP') for n in slot.material.node_tree.nodes), 'Review existing texture dependency before replacing active shield UV'
with bpy.data.libraries.load(str(source),link=False) as (available,loaded):loaded.objects=list(targets)
rows=[]
for name,donor in zip(targets,loaded.objects):
    obj=targets[name];bpy.context.collection.objects.link(donor)
    donor.modifiers.clear();donor.hide_render=True
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    assert obj.matrix_world==donor.matrix_world
    src=donor.data;dst=obj.data;src.calc_loop_triangles();dst.calc_loop_triangles()
    same=([tuple(v.co) for v in src.vertices]==[tuple(v.co) for v in dst.vertices] and
          [tuple(p.vertices) for p in src.polygons]==[tuple(p.vertices) for p in dst.polygons])
    if same:
        normals=[n.vector.copy() for n in src.corner_normals]
    else:
        points=[v.co.copy() for v in src.vertices];tris=list(src.loop_triangles)
        bvh=BVHTree.FromPolygons(points,[tuple(t.vertices) for t in tris],all_triangles=True)
        normals=[None]*len(dst.loops)
        for tri in dst.loop_triangles:
            center=sum((dst.vertices[i].co for i in tri.vertices),start=dst.vertices[tri.vertices[0]].co*0)/3
            for li in tri.loops:
                point=dst.vertices[dst.loops[li].vertex_index].co*.999+center*.001
                nearest=bvh.find_nearest(point)
                candidates=bvh.find_nearest_range(point,nearest[3]+.0001)
                hit,_,index,_=min(candidates,key=lambda h:h[3]+.001*(1-max(-1,min(1,tris[h[2]].normal.dot(tri.normal)))))
                t=tris[index]
                normal=barycentric_transform(hit,*(points[i] for i in t.vertices),*(src.corner_normals[i].vector for i in t.loops)).normalized()
                normals[li]=normal
    assert all(n is not None for n in normals)
    for poly in dst.polygons:poly.use_smooth=True
    dst.normals_split_custom_set(normals)
    bpy.data.objects.remove(donor,do_unlink=True)
    legacy=obj.data.uv_layers.active;legacy.name='ShieldLegacyUV'
    new=obj.data.uv_layers.new(name='ShieldAtlas');obj.data.uv_layers.active=new;new.active_render=True
    rows.append({'object':name,'legacy_uv_retained':True,'atlas_layer':'ShieldAtlas','triangles':sum(len(p.vertices)-2 for p in obj.data.polygons)})
bpy.ops.object.select_all(action='DESELECT')
for obj in targets.values():obj.select_set(True)
bpy.context.view_layer.objects.active=next(iter(targets.values()))
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,area_weight=0,correct_aspect=True,scale_to_bounds=True)
bpy.ops.uv.pack_islands(rotate=True,margin_method='FRACTION',margin=.004)
bpy.ops.object.mode_set(mode='OBJECT')
for obj in targets.values():
    assert all(math.isfinite(v) and -1e-6<=v<=1+1e-6 for item in obj.data.uv_layers.active.data for v in item.uv)
    assert all(math.isfinite(v) for normal in obj.data.corner_normals for v in normal.vector)
    assert len(obj.modifiers)==1 and obj.modifiers[0].type=='ARMATURE'
bpy.ops.wm.save_as_mainfile(filepath=str(target))
report={'status':'TRIAL: source-normal transfer and shared shield atlas UVs; requires visual/atlas/full-animation validation',
 'scene':target.name,'scene_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'parent_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'geometry_trial_sha256':hashlib.sha256(trial.read_bytes()).hexdigest(),'normal_method':'Unchanged topology: exact source corner normals. Reduced topology: explicit barycentric source normals, near-corner inset .001 and nearest candidates within .0001; orientation penalty .001. No evaluated modifier mapping.',
 'uv_method':'New shared ShieldAtlas layer; multi-object Smart UV Project 66 degrees then Pack Islands .004 fractional margin; legacy layer retained. No shield texture dependency existed.',
 'objects':rows}
(ROOT/f'validation/{args.label}.json').write_text(json.dumps(report,indent=2))
print(report['status'])
