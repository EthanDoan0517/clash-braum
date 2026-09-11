"""Inspect current draft topology and native pivots without modifying the scene."""
from pathlib import Path
import bpy, json
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_animation_review.blend'), load_ui=False, use_scripts=False)
rig = bpy.data.objects['Braum_Native']
report = {'bones': {}, 'objects': {}}
for bone in rig.data.bones:
    report['bones'][bone.name] = {'head': list(bone.head_local), 'tail': list(bone.tail_local),
                                 'parent': bone.parent.name if bone.parent else None}
for obj in bpy.context.scene.objects:
    if 'source_obj_group' not in obj:
        continue
    vertices = obj.data.vertices
    parents = list(range(len(vertices)))
    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    def union(a, b):
        parents[root(b)] = root(a)
    for edge in obj.data.edges:
        union(*edge.vertices)
    # Treat duplicated positions at UV/hard-normal seams as one physical shell.
    positions = {}
    for v in vertices:
        key = tuple(round(x, 5) for x in v.co)
        if key in positions:
            union(v.index, positions[key])
        positions[key] = v.index
    groups = {}
    for v in vertices:
        groups.setdefault(root(v.index), []).append(v.index)
    components = []
    for ids in sorted(groups.values(), key=lambda ids: min(ids)):
        weights = {}
        for i in ids:
            for g in vertices[i].groups:
                if g.weight > 0:
                    name = obj.vertex_groups[g.group].name
                    weights[name] = weights.get(name, 0) + g.weight/len(ids)
        components.append({'id': min(ids), 'vertices': len(ids),
                           'bounds': [[min(vertices[i].co[a] for i in ids), max(vertices[i].co[a] for i in ids)] for a in range(3)],
                           'weights': dict(sorted(weights.items(), key=lambda p: -p[1])), 'indices': ids})
    report['objects'][obj.name] = components
    if obj.name in ('Object004', 'Object009'):
        report.setdefault('hand_geometry', {})[obj.name] = {
            'points': [list(v.co) for v in vertices],
            'edges': [list(e.vertices) for e in obj.data.edges]}
(ROOT/'validation/rig_regions.json').write_text(json.dumps(report, indent=2))
print('Wrote rig region evidence; original scene unchanged')
