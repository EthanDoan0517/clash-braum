"""Bake reconstructed source body materials to a controlled preview atlas.

This preserves mesh positions, authored weights, topology and corner normals.
The result is a texture-stage trial, not a final game-shader integration.
"""
from pathlib import Path
import json,hashlib,math
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_body_atlas_packed_trial.blend'
target=ROOT/'work/scenes/clash_braum_body_atlas_preview_trial.blend'
out=ROOT/'work/textures/body_atlas_trial';out.mkdir(parents=True,exist_ok=True)
assert not target.exists()
check=json.loads((ROOT/'validation/body_atlas_packed_uv_validation.json').read_text())
assert check['pass'] and check['scene_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
scene=bpy.context.scene;rig=bpy.data.objects['Braum_Native'];old_pose=rig.data.pose_position;rig.data.pose_position='REST'
names=json.loads((ROOT/'validation/body_atlas_layout_trial.json').read_text())['body_objects']
objects=[bpy.data.objects[n] for n in names]
materials=list({slot.material for o in objects for slot in o.material_slots})
old_engine=scene.render.engine;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.device='CPU'
scene.render.bake.use_clear=False;scene.render.bake.margin=4;scene.render.bake.use_selected_to_active=False
scene.render.bake.normal_space='TANGENT'
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
size=2048;images={};stats={}
for channel in ('basecolor','opacity','normal'):
    image=bpy.data.images.new('ClashBodyAtlas_'+channel,width=size,height=size,alpha=True,float_buffer=False)
    image.colorspace_settings.name='sRGB' if channel=='basecolor' else 'Non-Color'
    image.generated_color=(.5,.5,1,1) if channel=='normal' else (0,0,0,0)
    images[channel]=image;restore=[]
    for material in materials:
        nodes=material.node_tree.nodes;links=material.node_tree.links
        for node in nodes:node.select=False
        target_node=nodes.new('ShaderNodeTexImage');target_node.image=image;target_node.select=True;nodes.active=target_node
        output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
        previous=output.inputs['Surface'].links[0].from_socket
        emission=None
        if channel!='normal':
            bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
            socket=bsdf.inputs['Base Color' if channel=='basecolor' else 'Alpha']
            emission=nodes.new('ShaderNodeEmission')
            if socket.is_linked:links.new(socket.links[0].from_socket,emission.inputs['Color'])
            else:
                color=socket.default_value
                emission.inputs['Color'].default_value=(color,color,color,1) if channel=='opacity' else color
            links.new(emission.outputs['Emission'],output.inputs['Surface'])
        restore.append((material,output,previous,emission,target_node))
    bpy.ops.object.bake(type='NORMAL' if channel=='normal' else 'EMIT')
    pixels=np.empty(size*size*4,dtype=np.float32);image.pixels.foreach_get(pixels)
    assert np.isfinite(pixels).all();stats[channel]={'min':float(pixels.min()),'max':float(pixels.max()),'nonzero_rgb_values':int(np.count_nonzero(pixels.reshape(-1,4)[:,:3]))}
    for material,output,previous,emission,target_node in restore:
        material.node_tree.links.new(previous,output.inputs['Surface'])
        if emission:material.node_tree.nodes.remove(emission)
        material.node_tree.nodes.remove(target_node)
    print('BAKED',channel,stats[channel],flush=True)
# Preserve source eyelash/eye-region opacity in the base-color alpha channel.
base=np.empty(size*size*4,dtype=np.float32);images['basecolor'].pixels.foreach_get(base)
alpha=np.empty_like(base);images['opacity'].pixels.foreach_get(alpha)
base.reshape(-1,4)[:,3]=np.clip(alpha.reshape(-1,4)[:,0],0,1)
images['basecolor'].pixels.foreach_set(base);images['basecolor'].update()
files={}
for channel in ('basecolor','opacity','normal'):
    image=images[channel];path=out/f'clash_body_{channel}.png';image.filepath_raw=str(path);image.file_format='PNG';image.save()
    image.filepath=bpy.path.relpath(str(path));files[channel]={'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':[size,size]}
material=bpy.data.materials.new('Braum');material.use_nodes=True
nodes=material.node_tree.nodes;links=material.node_tree.links;bsdf=nodes.get('Principled BSDF')
bsdf.inputs['Roughness'].default_value=.55;bsdf.inputs['Specular IOR Level'].default_value=.22
uv=nodes.new('ShaderNodeUVMap');uv.uv_map='BodyAtlas'
color=nodes.new('ShaderNodeTexImage');color.image=images['basecolor'];links.new(uv.outputs['UV'],color.inputs['Vector'])
links.new(color.outputs['Color'],bsdf.inputs['Base Color']);links.new(color.outputs['Alpha'],bsdf.inputs['Alpha']);material.surface_render_method='DITHERED'
normaltex=nodes.new('ShaderNodeTexImage');normaltex.image=images['normal'];links.new(uv.outputs['UV'],normaltex.inputs['Vector'])
normal=nodes.new('ShaderNodeNormalMap');normal.uv_map='BodyAtlas';links.new(normaltex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
for obj in objects:
    obj.data.materials.clear();obj.data.materials.append(material)
    for poly in obj.data.polygons:poly.material_index=0
rig.data.pose_position=old_pose;scene.render.engine=old_engine
bpy.ops.wm.save_as_mainfile(filepath=str(target))
report={'status':'BODY ATLAS PREVIEW TRIAL: source base color/opacity and tangent normal baked; visual and export checks required',
 'scene':target.name,'scene_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'textures':files,'bake_channels':stats,'body_material':'Braum','body_objects':names,
 'method':'Cycles rest-pose self bake, 2048 square, 1 sample, 4px dilation. SourceUV remains explicit in source materials. Emission base color and opacity; tangent normal bake. Shared preview Principled roughness .55/specular .22.',
 'limits':'Prototype atlas density and mipmap quality need gameplay review; source material reconstruction remains approximate. Not final Riot material/shader or DDS integration.'}
(ROOT/'validation/body_atlas_bake_trial.json').write_text(json.dumps(report,indent=2))
print(report['status'])
