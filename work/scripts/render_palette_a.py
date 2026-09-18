"""Review new textures on accepted meshes without saving or exporting geometry."""
from pathlib import Path
import bpy,json,sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/palette_a_v2'
if '--candidate' in sys.argv:
    OUT=ROOT/'build'/sys.argv[sys.argv.index('--candidate')+1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_body_atlas_packed_trial.blend'),load_ui=False,use_scripts=False)
names=json.loads((ROOT/'validation/body_atlas_layout_trial.json').read_text())['body_objects']
def material(kind,uvname):
    mat=bpy.data.materials.new('PaletteA_'+kind);mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=uvname
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/(kind+'_mip0.png')))
    emission=nodes.new('ShaderNodeEmission');output=nodes.new('ShaderNodeOutputMaterial')
    links.new(uv.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],emission.inputs['Color']);links.new(emission.outputs[0],output.inputs['Surface'])
    return mat
body=material('body','BodyAtlas');shield=material('shield_frame','ShieldAtlas')
points=[]
for obj in bpy.context.scene.objects:
    if obj.type=='ARMATURE':obj.data.pose_position='REST'
    if obj.type!='MESH':continue
    isbody=obj.name in names;isshield='ShieldAtlas' in obj.data.uv_layers
    obj.hide_render=not (isbody or isshield)
    if obj.hide_render:continue
    obj.data.materials.clear();obj.data.materials.append(body if isbody else shield)
    for poly in obj.data.polygons:poly.material_index=0
    for v in obj.data.vertices:points.append(obj.matrix_world@v.co)
lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
center=(lo+hi)/2;extent=max(hi-lo)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False
scene.world.color=(.12,.12,.12);scene.view_settings.view_transform='Standard'
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for label,direction in [('front',(0,-1,.15)),('back',(0,1,.15)),('game_angle',(0,-1,1.1))]:
    bpy.ops.object.camera_add(location=center+Vector(direction)*extent*3);cam=bpy.context.object
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=extent*1.12;scene.camera=cam
    scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
print('PALETTE_REVIEW_READY')
