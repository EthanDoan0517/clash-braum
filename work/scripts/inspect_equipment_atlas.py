"""Read accepted UVs and render material groups; never saves or exports a scene."""
from pathlib import Path
import bpy,json,sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'validation/equipment_atlas';OUT.mkdir(exist_ok=True)
texture=sys.argv[sys.argv.index('--texture')+1] if '--texture' in sys.argv else None
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_body_atlas_packed_trial.blend'),load_ui=False,use_scripts=False)
names=json.loads((ROOT/'validation/body_atlas_layout_trial.json').read_text())['body_objects']
if texture:
    material=bpy.data.materials.new('EquipmentTextureReview');material.use_nodes=True
    nodes=material.node_tree.nodes;nodes.clear();links=material.node_tree.links
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='BodyAtlas';tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/texture))
    emission=nodes.new('ShaderNodeEmission');output=nodes.new('ShaderNodeOutputMaterial')
    links.new(uv.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],emission.inputs['Color']);links.new(emission.outputs[0],output.inputs['Surface'])
palette={'Object001':(0.8,.12,.12,1),'Object002':(.3,.3,.8,1),'Object004':(.5,.18,.6,1),'Object005':(.5,.5,.5,1),'Object006':(1,.7,.1,1),'Object007':(.05,.8,.8,1),'Object009':(.9,.4,.05,1),'hjhjh_2':(.2,.8,.2,1)}
records=[];points=[]
for obj in bpy.context.scene.objects:
    if obj.type=='ARMATURE':obj.data.pose_position='REST'
    if obj.type!='MESH':continue
    obj.hide_render=obj.name not in names
    if obj.name not in names:continue
    obj.color=palette.get(obj.name,(.7,.7,.7,1))
    if texture:
        obj.data.materials.clear();obj.data.materials.append(material)
        for poly in obj.data.polygons:poly.material_index=0
    for v in obj.data.vertices:points.append(obj.matrix_world@v.co)
    uv=obj.data.uv_layers['BodyAtlas']
    records.append(dict(name=obj.name,source_material=obj.get('source_material'),color=list(obj.color),
      polygons=[dict(uv=[list(uv.data[i].uv) for i in poly.loop_indices],center=list(obj.matrix_world@poly.center)) for poly in obj.data.polygons]))
if not texture:(OUT/'groups.json').write_text(json.dumps(records))
lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
center=(lo+hi)/2;extent=max(hi-lo)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='OBJECT';scene.display.shading.light='STUDIO';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.view_settings.view_transform='Standard';scene.render.resolution_x=600;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
if texture:scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False
for label,direction in [('front',(0,-1,.1)),('back',(0,1,.1))]:
    bpy.ops.object.camera_add(location=center+Vector(direction)*extent*3);cam=bpy.context.object
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=extent*1.15;scene.camera=cam
    scene.render.filepath=str(OUT/(('refined_' if texture else '')+label+'.png'));bpy.ops.render.render(write_still=True)
print('GROUP_COLORS',palette,'BOUNDS',list(lo),list(hi))
