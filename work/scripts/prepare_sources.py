"""Build separate, reproducible source scenes; preserve original archives and meshes."""
from pathlib import Path
import sys
import json
import re
import math
import collections
import bpy
import bmesh
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'audit/scratch/CHR_Clash'

# Exact group/material relationships recovered from the supplied tbscene strings.
# Ranges are 1-based lines in audit/evidence/tbscene_strings.txt.
MATERIALS = {
    'body_main': (52, 144), 'body_main (1)': (145, 237),
    'body_main (1) (1)': (238, 313), 'body_main_skin': (314, 406),
    'body_main_skirt': (407, 477), 'boots': (478, 570),
    'boots (1)': (571, 665), 'boots (2)': (666, 757),
    'eye': (758, 827), 'hair_front (1)': (880, 949), 'head': (950, 1024),
}

def material_records():
    lines = (ROOT / 'audit/evidence/tbscene_strings.txt').read_text().splitlines()
    records = {}
    for name, (start, end) in MATERIALS.items():
        block = '\n'.join(lines[start-1:end])
        maps = {}
        for label, path, srgb in re.findall(r'^\s+([^=\n]+?) = @Tex file "([^"]+)" srgb ([01])', block, re.M):
            maps[label] = dict(path=path, srgb=bool(int(srgb)))
        records[name] = dict(evidence_lines=[start,end], maps=maps,
                             source_block=block, approximation='Principled preview; custom detail shader and source response not fully reproduced')
    return records, lines

def make_material(name, record):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = 0.55
    bsdf.inputs['Specular IOR Level'].default_value = 0.22
    images = {}
    for label, entry in record['maps'].items():
        path = SOURCE / entry['path']
        if not path.exists():
            if entry['path'] == 'Textures/CHR_Clash_Eyes_DiffuseMap.dds':
                entry['substitute'] = 'Textures/CHR_Clash_Eyes_DiffuseMap.tga'
                entry['substitution_reason'] = 'DDS absent; supplied TGA used as a preview candidate, requires visual review'
                path = SOURCE / entry['substitute']
            else:
                entry['missing'] = True
                continue
        # Separate datablocks when the source scene assigns different spaces.
        im = bpy.data.images.load(str(path), check_existing=False)
        im.colorspace_settings.name = 'sRGB' if entry['srgb'] else 'Non-Color'
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.name = label
        tex.label = label + ' (source)'
        tex.image = im
        tex.location = (-800, -200 * len(images))
        tex.extension = 'REPEAT'
        images[label] = tex
    if 'Albedo Map' in images:
        mat.node_tree.links.new(images['Albedo Map'].outputs['Color'], bsdf.inputs['Base Color'])
    if 'Normal Map' in images:
        normal = mat.node_tree.nodes.new('ShaderNodeNormalMap')
        mat.node_tree.links.new(images['Normal Map'].outputs['Color'], normal.inputs['Color'])
        mat.node_tree.links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    if name == 'hair_front (1)' and 'Albedo Map' in images:
        mat.node_tree.links.new(images['Albedo Map'].outputs['Alpha'], bsdf.inputs['Alpha'])
        mat.surface_render_method = 'DITHERED'
    mat['source_material'] = name
    return mat

def parse_obj():
    positions, uv, normals = [], [], []
    groups = collections.OrderedDict()
    current = None
    rejected = []
    face_count = 0
    for line_no, line in enumerate((SOURCE / 'CHR_Clash.obj').read_text().splitlines(), 1):
        words = line.split()
        if not words:
            continue
        if words[0] == 'v': positions.append(tuple(map(float, words[1:4])))
        elif words[0] == 'vt': uv.append(tuple(map(float, words[1:3])))
        elif words[0] == 'vn': normals.append(tuple(map(float, words[1:4])))
        elif words[0] == 'g':
            current = words[1]
            groups.setdefault(current, [])
        elif words[0] == 'f':
            face_count += 1
            face = [tuple(int(x)-1 for x in word.split('/')) for word in words[1:]]
            assert len(face) == 3 and all(len(x)==3 for x in face)
            a,b,c = [Vector(positions[x[0]]) for x in face]
            repeated = len(set(x[0] for x in face)) < 3
            area = (b-a).cross(c-a).length / 2
            if repeated:
                rejected.append(dict(line=line_no, group=current, reason='Repeated position index', face=line, area=area))
                continue
            groups[current].append(face)
    return positions, uv, normals, groups, dict(raw_face_statements=face_count, rejected_faces=rejected)

def prepare_body():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    records, lines = material_records()
    positions, uv, normals, groups, report = parse_obj()
    mats = {name: make_material(name, rec) for name, rec in records.items()}
    report['groups'] = []
    for name, faces in groups.items():
        at = lines.index(name)
        matline = lines.index('matName', at) + 1
        material = lines[matline].removesuffix('SChilds')
        assert material in mats
        used = sorted({v[0] for face in faces for v in face})
        mapping = {vi:i for i,vi in enumerate(used)}
        # Source Y-up to Blender Z-up, preserving handedness; staging scale only.
        coords = [(positions[i][0]*0.01, -positions[i][2]*0.01, positions[i][1]*0.01) for i in used]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(coords, [], [[mapping[v[0]] for v in face] for face in faces])
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        mesh.materials.append(mats[material])
        layer = mesh.uv_layers.new(name='SourceUV')
        loop_normals = []
        for poly, face in zip(mesh.polygons, faces):
            poly.use_smooth = True
            for li, v in zip(poly.loop_indices, face):
                layer.data[li].uv = uv[v[1]]
                n = normals[v[2]]
                loop_normals.append((n[0], -n[2], n[1]))
        mesh.normals_split_custom_set(loop_normals)
        obj['source_obj_group'] = name
        obj['source_material'] = material
        obj['source_units_assumption'] = '0.01 staging scale; actual fitting must use Braum landmarks'
        mesh.calc_loop_triangles()
        report['groups'].append(dict(group=name, material=material, material_evidence_line=matline+1,
                                     vertices=len(mesh.vertices), triangles=len(mesh.loop_triangles),
                                     bounds=[[min(v.co[a] for v in mesh.vertices),max(v.co[a] for v in mesh.vertices)] for a in range(3)]))
    report['imported_triangles'] = sum(g['triangles'] for g in report['groups'])
    report['material_records'] = records
    report['unassigned_groups'] = []
    report['missing_active_images'] = [entry['path'] for rec in records.values() for entry in rec['maps'].values() if entry.get('missing')]
    (ROOT / 'validation/body_source_preparation.json').write_text(json.dumps(report, indent=2))
    bpy.context.scene['stage'] = 'Source materials reconstructed; proportions, detail bake and rig remain pending'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'work/scenes/clash_source_materials.blend'))
    return report

def prepare_shield():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'Rework_Clash_Shield.blend'), load_ui=False, use_scripts=False)
    objects = [o for o in bpy.data.objects if o.type == 'MESH']
    world = {o.name: o.matrix_world.copy() for o in objects}
    report = dict(objects=[], missing_texture_strategy='Author replacements; source maps unavailable', viewport='Pending face/component inspection')
    # Remove unused source datablocks from this in-memory working copy.
    for obj in list(bpy.data.objects):
        if obj.type != 'MESH': bpy.data.objects.remove(obj, do_unlink=True)
    for obj in objects:
        mesh = obj.data.copy()
        obj.data = mesh
        before = [world[obj.name] @ v.co for v in mesh.vertices]
        determinant = world[obj.name].to_3x3().determinant()
        mesh.transform(world[obj.name])
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
        # Rebuild normals from finite, consistently oriented geometry.
        bm = bmesh.new(); bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh); bm.free()
        max_error = max((v.co-p).length for v,p in zip(mesh.vertices,before))
        assert max_error < 1e-5
        old_uvs = [layer.name for layer in mesh.uv_layers]
        for layer in list(mesh.uv_layers): mesh.uv_layers.remove(layer)
        mesh.uv_layers.new(name='ShieldUV')
        mesh.materials.clear()
        mat = bpy.data.materials.get('ShieldPreview') or bpy.data.materials.new('ShieldPreview')
        mat.diffuse_color = (0.09, 0.11, 0.12, 1)
        mesh.materials.append(mat)
        obj['source_object'] = obj.name
        obj['source_world_determinant'] = determinant
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True); bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.015)
        bpy.ops.object.mode_set(mode='OBJECT')
        assert all(math.isfinite(x) and -1e-5 <= x <= 1.00001 for item in mesh.uv_layers.active.data for x in item.uv)
        mesh.calc_loop_triangles()
        report['objects'].append(dict(name=obj.name, vertices=len(mesh.vertices), triangles=len(mesh.loop_triangles),
                                     removed_uv_layers=old_uvs, max_world_position_error=max_error,
                                     original_world_determinant=determinant, uv_layers=len(mesh.uv_layers)))
    # Garbage collection only on the working scene, never the original file.
    for material in list(bpy.data.materials):
        if material.name != 'ShieldPreview': bpy.data.materials.remove(material)
    for im in list(bpy.data.images): bpy.data.images.remove(im)
    bpy.context.scene['stage'] = 'Transforms baked and finite UVs rebuilt; viewport and materials not finished'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'work/scenes/shield_prepared.blend'))
    (ROOT / 'validation/shield_source_preparation.json').write_text(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    body = prepare_body()
    shield = prepare_shield()
    print(json.dumps(dict(body_triangles=body['imported_triangles'], rejected_faces=body['rejected_faces'],
                         missing_images=body['missing_active_images'], shield_objects=len(shield['objects'])), indent=2))
