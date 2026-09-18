"""Prepare a shared body atlas while keeping source-texture coordinates explicit."""
from pathlib import Path
import json,hashlib,math
import bpy
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_shield_reduced_accepted.blend'
target=ROOT/'work/scenes/clash_braum_body_atlas_layout_trial.blend'
assert not target.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
names=[r['group'] for r in json.loads((ROOT/'validation/body_source_preparation.json').read_text())['groups']]
objects=[bpy.data.objects[n] for n in names];materials={};source_uv={}
def geometry(o):
    return hashlib.sha256(repr(([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in o.data.vertices],
        [tuple(p.vertices) for p in o.data.polygons],[tuple(n.vector) for n in o.data.corner_normals])).encode()).hexdigest()
contracts={o.name:geometry(o) for o in bpy.context.scene.objects if o.type=='MESH'}
for obj in objects:
    obj.data.uv_layers.active.name='BodySourceUV'
    source_uv[obj.name]=hashlib.sha256(repr([tuple(d.uv) for d in obj.data.uv_layers.active.data]).encode()).hexdigest()
    atlas=obj.data.uv_layers.new(name='BodyAtlas');obj.data.uv_layers.active=atlas;atlas.active_render=True
    for slot in obj.material_slots:
        original=slot.material;assert original is not None
        if original.name not in materials:
            mat=original.copy();mat.name=original.name+'_AtlasSource';nodes=mat.node_tree.nodes;links=mat.node_tree.links
            uv=nodes.new('ShaderNodeUVMap');uv.uv_map='BodySourceUV';uv.name='Explicit source UV for atlas bake'
            for node in list(nodes):
                if node.type=='TEX_IMAGE' and not node.inputs['Vector'].is_linked:links.new(uv.outputs['UV'],node.inputs['Vector'])
                if node.type=='NORMAL_MAP':node.uv_map='BodySourceUV'
                if node.type=='TEX_COORD':
                    for link in list(node.outputs['UV'].links):links.new(uv.outputs['UV'],link.to_socket)
            materials[original.name]=mat
        slot.material=materials[original.name]
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.003,area_weight=0,correct_aspect=True,scale_to_bounds=True)
bpy.ops.uv.pack_islands(rotate=True,margin_method='FRACTION',margin=.002)
bpy.ops.object.mode_set(mode='OBJECT')
assert all(geometry(bpy.data.objects[n])==h for n,h in contracts.items())
assert all(hashlib.sha256(repr([tuple(d.uv) for d in bpy.data.objects[n].data.uv_layers['BodySourceUV'].data]).encode()).hexdigest()==h for n,h in source_uv.items())
bpy.ops.wm.save_as_mainfile(filepath=str(target))
report={'status':'BODY ATLAS LAYOUT TRIAL; source shaders remain active; do not export as a finished atlas build',
 'scene':target.name,'scene_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'parent_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'body_objects':names,'geometry_weights_topology_corner_normals_exact':True,'geometry_contracts':contracts,'source_uv_hashes':source_uv,
 'source_uv_layer':'BodySourceUV','atlas_uv_layer':'BodyAtlas','materials':{n:m.name for n,m in materials.items()},
 'next':'Validate/repair atlas overlaps, bake source base color and tangent-space normals, compare source and atlas materials at gameplay size.'}
(ROOT/'validation/body_atlas_layout_trial.json').write_text(json.dumps(report,indent=2))
print(report['status'])
