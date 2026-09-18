"""Read-only extraction of accepted atlas coordinates for palette shading."""
from pathlib import Path
import bpy, json, numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/palette_a_inputs'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_body_atlas_packed_trial.blend'),load_ui=False,use_scripts=False)
names=json.loads((ROOT/'validation/body_atlas_layout_trial.json').read_text())['body_objects']
for obj in bpy.context.scene.objects:
    if obj.type!='MESH':continue
    print('PALETTE_OBJECT',obj.name,[u.name for u in obj.data.uv_layers],[(s.material.name if s.material else '') for s in obj.material_slots])
    if obj.name not in names and 'ShieldAtlas' not in obj.data.uv_layers:continue
    mesh=obj.data;mesh.calc_loop_triangles();uv=mesh.uv_layers['BodyAtlas' if obj.name in names else 'ShieldAtlas']
    rows=[]
    normal_matrix=obj.matrix_world.to_3x3().inverted().transposed()
    for tri in mesh.loop_triangles:
        corners=[]
        for li in tri.loops:
            v=mesh.vertices[mesh.loops[li].vertex_index]
            corners.append([*uv.data[li].uv,*(obj.matrix_world@v.co),*(normal_matrix@v.normal).normalized()])
        rows.append(corners)
    np.save(OUT/(obj.name+'.npy'),np.asarray(rows,dtype=np.float32))
print('PALETTE_INPUTS_READY',OUT)
