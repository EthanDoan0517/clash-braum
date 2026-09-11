import bpy, mathutils
from pathlib import Path
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'Rework_Clash_Shield.blend'),load_ui=False,use_scripts=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=850;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.display.shading.light='STUDIO';s.display.shading.color_type='OBJECT';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world.color=(0.3,0.3,0.3)
colors=[(.8,.3,.2,1),(.55,.6,.65,1),(.2,.8,.3,1),(.7,.5,.1,1),(.1,.5,.85,1),(.8,.2,.8,1),(.9,.8,.2,1)]
for o,c in zip(sorted(bpy.data.objects,key=lambda o:o.name),colors):o.color=c;o.hide_render=False
bpy.ops.object.camera_add(location=(0,-7,1.2));cam=bpy.context.object;cam.rotation_euler=(mathutils.Vector((0,0,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.8;s.camera=cam
s.render.filepath=str(R/'audit/evidence/shield_geometry_front.png');bpy.ops.render.render(write_still=True)
