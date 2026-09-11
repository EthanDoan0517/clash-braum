import bpy, json, os, sys, collections
from pathlib import Path
root=Path(__file__).resolve().parents[2]
out=root/'audit/evidence'
def inspect(label):
    result={'blender':bpy.app.version_string,'file':bpy.data.filepath,'units':{'system':bpy.context.scene.unit_settings.system,'scale':bpy.context.scene.unit_settings.scale_length},'objects':[],'images':[],'materials':[],'libraries':[]}
    for o in bpy.data.objects:
        d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions),'modifiers':[(m.name,m.type) for m in o.modifiers]}
        if o.type=='MESH':
            m=o.data;m.calc_loop_triangles()
            d.update(vertices=len(m.vertices),edges=len(m.edges),faces=len(m.polygons),triangles=len(m.loop_triangles),uv_layers=[x.name for x in m.uv_layers],materials=[x.name if x else None for x in m.materials],vertex_groups=[x.name for x in o.vertex_groups],material_faces=dict(collections.Counter(p.material_index for p in m.polygons)),face_sizes=dict(collections.Counter(len(p.vertices) for p in m.polygons)))
            used=set(v for p in m.polygons for v in p.vertices)
            d['loose_vertices']=len(m.vertices)-len(used)
            d['bounds_world']=[[min((o.matrix_world@v.co)[i] for v in m.vertices),max((o.matrix_world@v.co)[i] for v in m.vertices)] for i in range(3)] if m.vertices else []
            d['uv_bounds']=[[[min(x.uv[i] for x in uv.data),max(x.uv[i] for x in uv.data)] for i in range(2)] for uv in m.uv_layers if len(uv.data)]
        if o.type=='ARMATURE':d['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None} for b in o.data.bones]
        result['objects'].append(d)
    for im in bpy.data.images:
        p=bpy.path.abspath(im.filepath)
        result['images'].append({'name':im.name,'path':im.filepath,'resolved_path':p,'exists':os.path.isfile(p),'packed':bool(im.packed_file),'size':list(im.size),'source':im.source})
    for m in bpy.data.materials:
        d={'name':m.name,'diffuse_color':list(m.diffuse_color),'nodes':[],'links':[]}
        if m.use_nodes and m.node_tree:
            d['nodes']=[{'name':n.name,'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') and not isinstance(i.default_value,str) else i.default_value for i in n.inputs if hasattr(i,'default_value') and not i.is_linked and isinstance(i.default_value,(float,int,str,tuple,list))}} for n in m.node_tree.nodes]
            d['links']=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]
        result['materials'].append(d)
    result['libraries']=[{'name':l.name,'path':l.filepath} for l in bpy.data.libraries]
    (out/(label+'.json')).write_text(json.dumps(result,indent=2),encoding='utf8')
    print(label,[(o['name'],o.get('vertices'),o.get('triangles')) for o in result['objects']])
bpy.ops.wm.open_mainfile(filepath=str(root/'Rework_Clash_Shield.blend'),load_ui=False,use_scripts=False)
inspect('shield_scene')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(root/'audit/scratch/CHR_Clash/CHR_Clash.obj'))
inspect('clash_obj_scene')
