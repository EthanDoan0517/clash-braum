"""Author and bake a restrained replacement shield coating, retaining accepted geometry."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_body_atlas_accepted.blend'
target=ROOT/'work/scenes/clash_braum_shield_material_trial.blend'
assert not target.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
scene=bpy.context.scene;rig=bpy.data.objects['Braum_Native'];pose=rig.data.pose_position;rig.data.pose_position='REST'
objects=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('CCE_')]
def contract(o):
    m=o.data
    return hashlib.sha256(repr(([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in m.vertices],[tuple(p.vertices) for p in m.polygons],[tuple(n.vector) for n in m.corner_normals],{u.name:[tuple(d.uv) for d in u.data] for u in m.uv_layers})).encode()).hexdigest()
before={o.name:contract(o) for o in scene.objects if o.type=='MESH'}
settings={};materials=[]
for o in objects:
    # Main armored panel, frame, and attached hardware have controlled value separation.
    main=o.name=='CCE_mesh_14.001';frame=o.name=='CCE_mesh_13.001'
    color=(.023,.029,.034,1) if main else ((.047,.058,.067,1) if frame else (.065,.072,.078,1))
    rough=.68 if main else .48;metal=.15 if main else .45
    settings[o.name]=dict(linear_color=color,roughness=rough,metallic=metal)
    mat=bpy.data.materials.new(o.name+'_CoatingSource');mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links;b=n.get('Principled BSDF')
    b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    coord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=160;noise.inputs['Detail'].default_value=2
    l.new(coord.outputs['Generated'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=tuple(c*.93 for c in color[:3])+(1,)
    ramp.color_ramp.elements[1].color=tuple(c*1.07 for c in color[:3])+(1,)
    l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],b.inputs['Base Color'])
    o.data.materials.clear();o.data.materials.append(mat)
    for p in o.data.polygons:p.material_index=0
    materials.append(mat)
engine=scene.render.engine;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
scene.render.bake.use_clear=False;scene.render.bake.margin=4;scene.render.bake.use_selected_to_active=False
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
out=ROOT/'work/textures/shield_material_trial';out.mkdir(parents=True,exist_ok=True);images={};files={}
for channel,socket in [('basecolor','Base Color'),('roughness','Roughness'),('metallic','Metallic')]:
    image=bpy.data.images.new('ShieldAtlas_'+channel,width=2048,height=2048,alpha=True)
    image.colorspace_settings.name='sRGB' if channel=='basecolor' else 'Non-Color';images[channel]=image;restore=[]
    for mat in materials:
        n=mat.node_tree.nodes;l=mat.node_tree.links;b=n.get('Principled BSDF');output=n.get('Material Output')
        tex=n.new('ShaderNodeTexImage');tex.image=image;n.active=tex
        emission=n.new('ShaderNodeEmission');s=b.inputs[socket]
        if s.is_linked:l.new(s.links[0].from_socket,emission.inputs['Color'])
        else:
            v=s.default_value;emission.inputs['Color'].default_value=(v,v,v,1)
        l.new(emission.outputs[0],output.inputs['Surface']);restore.append((mat,tex,emission))
    bpy.ops.object.bake(type='EMIT')
    for mat,tex,emission in restore:
        mat.node_tree.links.new(mat.node_tree.nodes.get('Principled BSDF').outputs[0],mat.node_tree.nodes.get('Material Output').inputs['Surface'])
        mat.node_tree.nodes.remove(tex);mat.node_tree.nodes.remove(emission)
    a=np.empty(2048*2048*4,dtype=np.float32);image.pixels.foreach_get(a);assert np.isfinite(a).all()
    path=out/f'clash_shield_{channel}.png';image.filepath_raw=str(path);image.file_format='PNG';image.save();image.filepath=bpy.path.relpath(str(path))
    files[channel]={'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
mat=bpy.data.materials.new('ShieldFrame_Atlas');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;b=n.get('Principled BSDF')
uv=n.new('ShaderNodeUVMap');uv.uv_map='ShieldAtlas'
for channel,socket in [('basecolor','Base Color'),('roughness','Roughness'),('metallic','Metallic')]:
    tex=n.new('ShaderNodeTexImage');tex.image=images[channel];l.new(uv.outputs['UV'],tex.inputs['Vector']);l.new(tex.outputs['Color'],b.inputs[socket])
for o in objects:o.data.materials.clear();o.data.materials.append(mat)
assert all(contract(bpy.data.objects[n])==h for n,h in before.items())
rig.data.pose_position=pose;scene.render.engine=engine
bpy.ops.wm.save_as_mainfile(filepath=str(target))
report=dict(status='SHIELD MATERIAL TRIAL: authored charcoal coating and hardware value separation; gameplay review pending',scene=target.name,scene_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),textures=files,settings=settings,geometry_weights_normals_uvs_exact=True,limits='Replacement coating, not recovered source textures. No glass pane or electrical VFX. Metallic/roughness are Blender preview channels; runtime gloss mapping needs explicit integration.')
(ROOT/'validation/shield_material_trial.json').write_text(json.dumps(report,indent=2))
print(report['status'])
