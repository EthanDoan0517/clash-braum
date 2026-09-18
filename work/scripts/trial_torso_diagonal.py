"""Rotate one internal vest diagonal in an isolated diagnostic child."""
from pathlib import Path
import hashlib,json
import bpy
ROOT=Path(__file__).resolve().parents[2]
parent=ROOT/'work/scenes/clash_braum_torso.blend'
out=ROOT/'work/scenes/clash_braum_torso_diagonal_trial.blend'
assert not out.exists(), 'Preserve existing trial; do not overwrite manual work'
expected=json.loads((ROOT/'validation/torso_local_alternatives.json').read_text())['scene_sha256']
assert hashlib.sha256(parent.read_bytes()).hexdigest()==expected
bpy.ops.wm.open_mainfile(filepath=str(parent),load_ui=False,use_scripts=False)
obj=bpy.data.objects['Object002'];old=obj.data
vertices=[tuple(v.co) for v in old.vertices]
weights=[[(g.group,g.weight) for g in v.groups] for v in old.vertices]
group_names=[g.name for g in obj.vertex_groups]
faces=[tuple(p.vertices) for p in old.polygons]
assert faces[316]==(142,143,190) and faces[557]==(190,143,337)
assert not any(set(e.vertices)=={142,337} for e in old.edges)
original={i:faces[i] for i in (316,557)}
normals=[tuple(n.vector) for n in old.corner_normals]
uvs={l.name:[tuple(d.uv) for d in l.data] for l in old.uv_layers}
sharp={tuple(sorted(e.vertices)):e.use_edge_sharp for e in old.edges}
faces[316]=(142,143,337);faces[557]=(142,337,190)
new=bpy.data.meshes.new(old.name+'_diagonal_trial');new.from_pydata(vertices,[],faces)
for mat in old.materials:new.materials.append(mat)
for a,b in zip(old.polygons,new.polygons):b.material_index=a.material_index;b.use_smooth=a.use_smooth
for name,values in uvs.items():
    layer=new.uv_layers.new(name=name)
    for i,value in enumerate(values):layer.data[i].uv=value
    for pid in original:
        for loop,index in zip(new.polygons[pid].loop_indices,new.polygons[pid].vertices):
            origin=next(l for f in original for l in old.polygons[f].loop_indices if old.loops[l].vertex_index==index)
            layer.data[loop].uv=values[origin]
for pid in original:
    for loop,index in zip(new.polygons[pid].loop_indices,new.polygons[pid].vertices):
        origin=next(l for f in original for l in old.polygons[f].loop_indices if old.loops[l].vertex_index==index)
        normals[loop]=tuple(old.corner_normals[origin].vector)
for edge in new.edges:edge.use_edge_sharp=sharp.get(tuple(sorted(edge.vertices)),False)
new.normals_split_custom_set(normals);obj.data=new
assert len(obj.vertex_groups)==0
for name in group_names:obj.vertex_groups.new(name=name)
for i,groups in enumerate(weights):
    for group,weight in groups:obj.vertex_groups[group].add([i],weight,'REPLACE')
new.update()
assert [tuple(v.co) for v in new.vertices]==vertices
assert [[(g.group,g.weight) for g in v.groups] for v in new.vertices]==weights
for pid,(a,b) in enumerate(zip(old.polygons,new.polygons)):
    if pid not in original:
        assert tuple(a.vertices)==tuple(b.vertices)
        for name,values in uvs.items():assert all(tuple(new.uv_layers[name].data[l].uv)==values[l] for l in a.loop_indices)
normal_error=max(abs(x-y) for a,b in zip(normals,new.corner_normals) for x,y in zip(a,b.vector))
assert normal_error<.0001,normal_error
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'status':'DIAGNOSTIC ONLY; requires local surface, visual and export acceptance','parent_sha256':expected,'scene_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'object':'Object002','patch_old':original,'patch_new':{i:faces[i] for i in original},'all_vertex_positions_and_weights_exact':True,'all_other_faces_and_uvs_exact':True,'corner_normal_max_error':normal_error,'surface_mapping':'Both triangles map to the same original quad boundary 142-143-337-190. Compare remote intersection surfaces across the whole two-triangle patch, not replacement face IDs.'}
(ROOT/'validation/torso_diagonal_trial.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
