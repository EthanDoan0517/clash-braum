"""Narrow adapter around Aventurine for unchanged Braum skeletons.

The supplied importer drops normals and mirrors positions without reversing winding.
The supplied exporter averages normals across hard edges and regenerates inverse binds.
Keep Aventurine's SKN packing/palette logic, but collect evaluated corner normals with
proper winding, and retain the supplied SKL joint records byte for byte.
"""
from pathlib import Path
import struct
import math
import bpy
from mathutils import Matrix, Vector
from Aventurine.io import import_skn, import_skl, export_skn
from asset_formats import read_skn, read_skl, validate_pair

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SKL = ROOT / 'Braum.wad/9b8248658ce51711.skl'

def import_baseline():
    joints, palette = import_skl.read_skl(str(SOURCE_SKL))
    rig = import_skl.create_armature(joints, name='Braum_Native', bone_orient='NATIVE')
    data = read_skn(ROOT / 'Braum.wad/fbf88fcfc8ec8dc4.skn')
    indices, vertices, submeshes = import_skn.read_skn(str(ROOT / 'Braum.wad/fbf88fcfc8ec8dc4.skn'))
    # Reflection into Blender changes handedness. Reverse triangles for outward faces.
    flipped = [indices[i+j] for i in range(0, len(indices), 3) for j in (0, 2, 1)]
    mesh = import_skn.create_mesh(flipped, vertices, submeshes, 'Braum', rig, joints, palette)
    normals = [(-v['normal'][0], -v['normal'][2], v['normal'][1]) for v in data['vertices']]
    for poly in mesh.data.polygons:
        poly.use_smooth = True
    mesh.data.normals_split_custom_set([normals[loop.vertex_index] for loop in mesh.data.loops])
    # Blender's encoded custom normals lose precision at a few near-degenerate
    # source corners. Keep float normals for the immutable baseline/Poro only.
    frozen = mesh.data.attributes.new('clash_frozen_normal', 'FLOAT_VECTOR', 'CORNER')
    for loop in mesh.data.loops:
        frozen.data[loop.index].vector = normals[loop.vertex_index]
    frozen_pos = mesh.data.attributes.new('clash_frozen_position', 'FLOAT_VECTOR', 'POINT')
    for vertex in mesh.data.vertices:
        frozen_pos.data[vertex.index].vector = vertex.co
    for pb in rig.pose.bones:
        pb['clash_verified_rest_matrix'] = [x for row in pb.bone.matrix_local for x in row]
    rig['clash_native_contract'] = 1
    bpy.context.view_layer.update()
    return rig, mesh

def assert_native_rig(rig):
    source = read_skl(SOURCE_SKL)
    bones = sorted(rig.pose.bones, key=lambda pb: pb.get('native_bone_index', -1))
    assert rig.get('clash_native_contract') == 1
    assert len(bones) == len(source['joints']) == 97
    assert max(abs(rig.matrix_world[r][c] - (1 if r == c else 0)) for r in range(4) for c in range(4)) < 1e-7
    for i, (pb, joint) in enumerate(zip(bones, source['joints'])):
        assert pb.name == joint['name'] and pb['native_bone_index'] == i
        expected_parent = source['joints'][joint['parent']]['name'] if joint['parent'] >= 0 else None
        assert (pb.parent.name if pb.parent else None) == expected_parent
        assert max(abs(x-y) for x,y in zip(pb['clash_verified_rest_matrix'], [x for row in pb.bone.matrix_local for x in row])) < 1e-7

def collect_mesh_data(mesh_obj, armature_obj, bone_to_idx, submesh_name, material_index=None,
                      disable_scaling=False, disable_transforms=False, deformed_positions=None,
                      deformed_poly_normals=None, apply_object_transform=True, model_scale=1.0):
    assert not disable_scaling and not disable_transforms and model_scale == 1.0
    assert deformed_positions is None and deformed_poly_normals is None
    assert all(m.type == 'ARMATURE' or not m.show_viewport for m in mesh_obj.modifiers), 'Apply geometry modifiers before export'
    mesh = mesh_obj.data
    mesh.calc_loop_triangles()
    assert mesh.uv_layers.active is not None
    transform = mesh_obj.matrix_world if apply_object_transform else armature_obj.matrix_world.inverted() @ mesh_obj.matrix_world
    normal_matrix = transform.to_3x3().inverted().transposed()
    # League conversion has negative determinant; account for negative object scales too.
    reverse = transform.to_3x3().determinant() > 0
    groups = {g.index: bone_to_idx[g.name] for g in mesh_obj.vertex_groups if g.name in bone_to_idx}
    uv_data = mesh.uv_layers.active.data
    frozen = mesh.attributes.get('clash_frozen_normal')
    if frozen:
        positions = mesh.attributes['clash_frozen_position']
        assert all((v.co - positions.data[v.index].vector).length < 1e-8 for v in mesh.vertices), 'Frozen vanilla geometry changed'
    vertices, indices, unique = [], [], {}
    for tri in mesh.loop_triangles:
        if material_index is not None and tri.material_index != material_index:
            continue
        loops = list(tri.loops)
        if reverse:
            loops = [loops[0], loops[2], loops[1]]
        for li in loops:
            vi = mesh.loops[li].vertex_index
            uv = uv_data[li].uv
            normal = frozen.data[li].vector if frozen else mesh.corner_normals[li].vector
            key = (vi, tuple(uv), tuple(normal))
            if key not in unique:
                v = mesh.vertices[vi]
                weights = sorted(((groups[g.group], g.weight) for g in v.groups if g.group in groups and g.weight > 0), key=lambda x: (-x[1], x[0]))
                assert 1 <= len(weights) <= 4, (mesh_obj.name, vi, weights)
                total = sum(w for _,w in weights)
                assert abs(total-1) < 1e-5, (mesh_obj.name, vi, total)
                p = transform @ v.co
                n = (normal_matrix @ normal).normalized()
                assert all(math.isfinite(x) for x in (*p, *n, *uv))
                unique[key] = len(vertices)
                vertices.append(dict(pos=Vector((-p.x*100, p.z*100, -p.y*100)),
                                     normal=Vector((-n.x, n.z, -n.y)), uv=(uv.x, 1-uv.y),
                                     inf=[i for i,_ in weights]+[0]*(4-len(weights)),
                                     weight=[w/total for _,w in weights]+[0.]*(4-len(weights))))
            indices.append(unique[key])
    return dict(name=submesh_name, vertices=vertices, indices=indices)

def write_palette_skl(path, palette):
    source = read_skl(SOURCE_SKL)
    assert len(palette) == len(set(palette)) and 0 < len(palette) <= 256
    assert all(isinstance(i, int) and 0 <= i < len(source['joints']) for i in palette)
    data = bytearray(SOURCE_SKL.read_bytes())
    if tuple(palette) != source['palette']:
        # Append a new table so every existing relative pointer stays valid.
        if len(data) % 2:
            data.append(0)
        offset = len(data)
        data.extend(struct.pack(f'<{len(palette)}H', *palette))
        struct.pack_into('<I', data, 0, len(data))
        struct.pack_into('<I', data, 16, len(palette))
        struct.pack_into('<i', data, 28, offset)
    Path(path).write_bytes(data)
    result = read_skl(path)
    assert result['joints'] == source['joints']
    assert tuple(palette) == result['palette']

def export_pair(stem, meshes, rig):
    assert_native_rig(rig)
    original = export_skn.collect_mesh_data
    try:
        export_skn.collect_mesh_data = collect_mesh_data
        result = export_skn.write_skn_multi(str(Path(stem).with_suffix('.skn')), meshes, rig, clean_names=False)
    finally:
        export_skn.collect_mesh_data = original
    write_palette_skl(Path(stem).with_suffix('.skl'), result[2])
    validate_pair(read_skn(Path(stem).with_suffix('.skn')), read_skl(Path(stem).with_suffix('.skl')))
    return result
