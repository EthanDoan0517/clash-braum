"""Render source preparation for front/back inspection and record shield components."""
from pathlib import Path
import bpy
import bmesh
import json
import math
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'validation/previews'
OUT.mkdir(parents=True, exist_ok=True)

def render_scene(stem, target, distance, scale, views, workbench=False):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH' if workbench else 'CYCLES'
    if not workbench:
        scene.cycles.samples = 24
        scene.cycles.use_denoising = True
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    if scene.world is None:
        scene.world = bpy.data.worlds.new('PreviewWorld')
    scene.world.color = (0.15, 0.15, 0.15)
    scene.view_settings.view_transform = 'Standard'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    if not workbench:
        for location, energy, size in [((-3,-4,5),500,4),((3,-2,3),300,3),((0,3,4),600,3)]:
            bpy.ops.object.light_add(type='AREA', location=location)
            light = bpy.context.object
            light.data.energy = energy; light.data.shape='DISK'; light.data.size=size
            light.rotation_euler = (Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
    for name, direction in views:
        bpy.ops.object.camera_add(location=Vector(target)+Vector(direction).normalized()*distance)
        camera = bpy.context.object
        camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type='ORTHO'; camera.data.ortho_scale=scale
        scene.camera=camera
        scene.render.filepath=str(OUT / f'{stem}_{name}.png')
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(camera, do_unlink=True)

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_source_materials.blend'),load_ui=False,use_scripts=False)
render_scene('clash_source', (0,0,0.91), 5, 2.05, [('front',(0,-1,0)), ('back',(0,1,0))])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/shield_prepared.blend'),load_ui=False,use_scripts=False)
components=[]
for obj in bpy.data.objects:
    if obj.type != 'MESH': continue
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    remaining=set(bm.verts)
    while remaining:
        stack=[remaining.pop()]; found=set(stack)
        while stack:
            for edge in stack.pop().link_edges:
                for v in edge.verts:
                    if v in remaining:
                        remaining.remove(v);found.add(v);stack.append(v)
        faces={f for v in found for f in v.link_faces}
        bounds=[[min(v.co[a] for v in found),max(v.co[a] for v in found)] for a in range(3)]
        components.append(dict(object=obj.name,vertices=len(found),faces=len(faces),bounds=bounds,
                               area=sum(f.calc_area() for f in faces)))
    bm.free()
(ROOT/'validation/shield_components.json').write_text(json.dumps(sorted(components,key=lambda x:-x['area']),indent=2))
render_scene('shield_prepared', (0,0,1.2), 7, 2.7, [('front',(0,-1,0)), ('back',(0,1,0)),('oblique',(1,-2,0.3))],workbench=True)
