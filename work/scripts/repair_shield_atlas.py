"""Split only overlapping projected faces into UV islands and repack the atlas."""
from pathlib import Path
import json,hashlib,math,argparse,sys
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--scene',default='clash_braum_shield_surface_v2_trial.blend');parser.add_argument('--label',default='shield_atlas_trial');parser.add_argument('--uv-report',default='shield_atlas_uv_validation.json');parser.add_argument('--body',action='store_true');parser.add_argument('--aabb',action='store_true',help='Conservative rectangular island packing to avoid concave packing collisions')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert Path(args.scene).name==args.scene and Path(args.uv_report).name==args.uv_report and args.label.replace('_','').isalnum()
source=ROOT/'work/scenes'/args.scene
target=ROOT/f'work/scenes/clash_braum_{args.label}.blend'
assert not target.exists()
audit=json.loads((ROOT/'validation'/args.uv_report).read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==audit['scene_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
def contract(obj):
    m=obj.data
    return hashlib.sha256(repr((list(map(tuple,obj.matrix_world)),[(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in m.vertices],
        [tuple(p.vertices) for p in m.polygons],[tuple(n.vector) for n in m.corner_normals],
        [p.material_index for p in m.polygons])).encode()).hexdigest()
before={o.name:contract(o) for o in bpy.context.scene.objects if o.type=='MESH'}
changed=sorted({tuple(pair[k]) for pair in audit['interior_overlaps'] for k in ('a','b')})
for ordinal,(name,triangle) in enumerate(changed):
    obj=bpy.data.objects[name];m=obj.data;m.calc_loop_triangles();tri=m.loop_triangles[triangle]
    p=m.polygons[tri.polygon_index];assert len(p.vertices)==3
    layer=m.uv_layers.active;old=[layer.data[li].uv.copy() for li in tri.loops]
    a,b,c=[m.vertices[i].co for i in tri.vertices];x=(b-a).normalized();normal=(b-a).cross(c-a).normalized();y=normal.cross(x)
    projected=[Vector(((point-a).dot(x),(point-a).dot(y))) for point in (a,b,c)]
    def area(t):return abs((t[1].x-t[0].x)*(t[2].y-t[0].y)-(t[1].y-t[0].y)*(t[2].x-t[0].x))*.5
    factor=math.sqrt(area(old)/max(area(projected),1e-20))
    for li,uv in zip(tri.loops,projected):layer.data[li].uv=uv*factor+Vector((10+ordinal*2,10))
bpy.ops.object.select_all(action='DESELECT')
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and
         ((not o.name.startswith('CCE_') and o.name not in ('Poro','Vanilla_Reference')) if args.body else o.name.startswith('CCE_'))]
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.pack_islands(rotate=True,shape_method='AABB' if args.aabb else 'CONCAVE',margin_method='FRACTION',margin=.004 if args.aabb else (.002 if args.body else .004));bpy.ops.object.mode_set(mode='OBJECT')
assert all(contract(bpy.data.objects[n])==h for n,h in before.items())
bpy.ops.wm.save_as_mainfile(filepath=str(target))
report={'scene':target.name,'scene_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'parent_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'uv_only_change':True,'geometry_weights_topology_corner_normals_material_indices_transforms_exact':True,'mesh_contracts':before,
 'isolated_triangles':changed,'full_animation_evidence':'shield_surface_v2_full_validation.json','status':'UV-only trial; requires fresh UV check and export. Geometry full-animation evidence reusable through exact contracts.'}
(ROOT/f'validation/{args.label}.json').write_text(json.dumps(report,indent=2))
print('SPLIT UV TRIANGLES',len(changed))
