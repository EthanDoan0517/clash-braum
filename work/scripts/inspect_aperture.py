from pathlib import Path
import bpy
import json
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/shield_prepared.blend'),load_ui=False,use_scripts=False)
vertices,faces=[],[]
for obj in bpy.data.objects:
    if obj.type!='MESH':continue
    offset=len(vertices)
    vertices.extend(obj.matrix_world@v.co for v in obj.data.vertices)
    faces.extend([offset+i for i in p.vertices] for p in obj.data.polygons)
tree=BVHTree.FromPolygons(vertices,faces)
samples=[]
for label,x,z in [('upper_center',0,2.12),('upper_left',-.17,2.13),('upper_right',.17,2.13),
                  ('view_center',0,1.90),('view_left',-.25,1.80),('view_right',.25,1.80),
                  ('hardware_control',0,1.50),('lower_armor_control',0,.40)]:
    hits=[]
    for y,dy in [(-2,1),(2,-1)]:
        hit,normal,index,distance=tree.ray_cast(Vector((x,y,z)),Vector((0,dy,0)),4)
        hits.append(None if hit is None else list(hit))
    samples.append(dict(label=label,x=x,z=z,front_hit=hits[0],back_hit=hits[1],open=all(h is None for h in hits)))
result=dict(samples=samples,interpretation='Geometry ray tests identify existing open areas; do not prove shader or runtime behavior')
(ROOT/'validation/shield_aperture.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
