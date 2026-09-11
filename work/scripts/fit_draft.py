"""Create a reviewable first fit and weight seed, not a final deformation-approved rig."""
from pathlib import Path
import sys
import json
import math
import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/tools'),str(ROOT/'work/scripts')]
from native_export import import_baseline, export_pair, assert_native_rig
from asset_formats import read_skn,read_skl,validate_pair

def append_meshes(path):
    with bpy.data.libraries.load(str(path),link=False) as (src,dst):
        dst.objects=src.objects
    meshes=[]
    for obj in dst.objects:
        if obj.type=='MESH':bpy.context.collection.objects.link(obj);meshes.append(obj)
    return meshes

def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True);bpy.context.view_layer.objects.active=obj

def smoothstep(a,b,v):
    t=max(0,min(1,(v-a)/(b-a)))
    return t*t*(3-2*t)

def lerp_height(z):
    anchors=[(-.002,-.006),(0.12,0.13),(0.53,.594),(1.04,1.033),(1.19,1.23),(1.48,1.60),(1.58,1.73),(1.80,1.95)]
    for (a,b),(c,d) in zip(anchors,anchors[1:]):
        if z<=c:return b+(z-a)/(c-a)*(d-b)
    return z+.15

def fit_body_point(co, group):
    x,y,z=co;side=1 if x>=0 else -1;ax=abs(x)
    # Lower body stays near the native hip/foot spacing. Broaden only the torso.
    width=1+0.48*smoothstep(1.0,1.43,z)
    torso=Vector((x*width,y*1.20-.04,lerp_height(z)))
    if group in ('hjhjh_4','hjhjh_3','hjhjh_16'):
        # Keep facial proportions uniform; blend only the lower neck into torso.
        head=Vector((x*1.08,y*1.08-.015,(z-1.66)*1.08+1.805))
        return torso.lerp(head,smoothstep(1.40,1.56,z))
    if group in ('Object004','Object009'):
        source=[Vector((.205,.015,1.46)),Vector((.368,-.01,1.255)),Vector((.48,-.095,1.09)),Vector((.555,-.12,1.00))]
        target=[Vector((.294,.04,1.60)),Vector((.546,.047,1.312)),Vector((.754,-.069,1.07)),Vector((.865,-.10,.96))]
        p=Vector((ax,y,z));best=None
        for a,b,c,d in zip(source,source[1:],target,target[1:]):
            segment=b-a;t=max(0,min(1,(p-a).dot(segment)/segment.length_squared))
            center=a+segment*t;dist=(p-center).length_squared
            if best is None or dist<best[0]:
                rot=segment.rotation_difference(d-c)
                q=c+(d-c)*t+rot@(p-center)*1.12
                best=(dist,q)
        arm=best[1];arm.x*=side
        return torso.lerp(arm,smoothstep(.16,.255,ax))
    return torso

bpy.ops.wm.read_factory_settings(use_empty=True)
rig,vanilla=import_baseline()
vanilla.name='Vanilla_Reference'
# BVH seed donor: only original Braum body faces, excluding rigid Shield and Poro.
shield_index=vanilla.vertex_groups['Shield'].index
def is_shield(v):return any(g.group==shield_index and g.weight>.9999 for g in v.groups)
donor_faces=[list(p.vertices) for p in vanilla.data.polygons if p.material_index==0 and not any(is_shield(vanilla.data.vertices[i]) for i in p.vertices)]
assert not any(is_shield(vanilla.data.vertices[i]) for face in donor_faces for i in face)
tree=BVHTree.FromPolygons([v.co for v in vanilla.data.vertices],donor_faces,all_triangles=True)
body=append_meshes(ROOT/'work/scenes/clash_source_materials.blend')
report=dict(stage='Draft fit and automatic weight seed; manual joint/finger/equipment refinement required',
            donor_faces=len(donor_faces), donor_excludes=['Shield','Poro'],objects=[])
bone_names=[g.name for g in vanilla.vertex_groups]
for obj in body:
    group=obj['source_obj_group']
    # Normals from source no longer describe the reshaped surface.
    if obj.data.has_custom_normals:
        obj.data.normals_split_custom_set([(0,0,0)]*len(obj.data.loops))
    for v in obj.data.vertices:v.co=fit_body_point(v.co,group)
    for name in bone_names:obj.vertex_groups.new(name=name)
    distances=[]
    for v in obj.data.vertices:
        near,_,face_index,distance=tree.find_nearest(v.co)
        distances.append(distance)
        face=donor_faces[face_index]
        a,b,c=[vanilla.data.vertices[i].co for i in face]
        bary=barycentric_transform(near,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        weights={}
        for vi,factor in zip(face,bary):
            for g in vanilla.data.vertices[vi].groups:
                if g.weight>0 and factor>0:weights[g.group]=weights.get(g.group,0)+g.weight*factor
        # Facial detail is rigid to Head. Neck remains blended into source weights.
        if group in ('hjhjh_3','hjhjh_16') or (group=='hjhjh_4' and v.co.z>1.74):
            weights={vanilla.vertex_groups['Head'].index:1.}
        # Reviewed idle frame 17: collar vertices borrowed clavicle/pauldron
        # weights and pulled into a broad flap. Anchor collar to upper spine.
        if group=='Object002' and v.co.z>1.60:
            amount=smoothstep(1.60,1.70,v.co.z)
            weights={index:w*(1-amount) for index,w in weights.items()}
            spine=vanilla.vertex_groups['Spine3'].index
            weights[spine]=weights.get(spine,0)+amount
        # Exclude decorative original armor helper weights when copying onto cloth.
        replacements={'Necklace':'Spine3','Necklace_Back':'Spine3','Buckle':'Pelvis','Armor_Back':'Spine2',
                      'L_Pauldron_Plates':'L_Shoulder','L_Pauldron':'L_Shoulder','R_Pauldron_Plates':'R_Shoulder',
                      'R_Pauldron':'R_Shoulder','L_Arm_Band1':'L_Shoulder','L_Arm_Band2':'L_Shoulder',
                      'L_Knuckle_Armor':'L_Hand','L_Hand_Armor':'L_Hand','L_Arm_Armor':'L_Elbow'}
        cleaned={}
        for index,weight in weights.items():
            name=replacements.get(bone_names[index],bone_names[index])
            if weight>=0.0001:cleaned[name]=cleaned.get(name,0)+weight
        keep=sorted(cleaned.items(),key=lambda p:-p[1])[:4]
        total=sum(w for _,w in keep)
        assert total>0
        for name,w in keep:obj.vertex_groups[name].add([v.index],w/total,'REPLACE')
    obj.parent=rig
    mod=obj.modifiers.new('Braum native deformation','ARMATURE');mod.object=rig
    obj['rig_status']='Draft: nearest surface seed with rigid head correction; manual review required'
    report['objects'].append(dict(name=obj.name,source_group=group,max_transfer_distance=max(distances),
                                  mean_transfer_distance=sum(distances)/len(distances),vertices=len(obj.data.vertices)))

# Preserve Poro with the exact original material name and normals.
poro=vanilla.copy();poro.data=vanilla.data.copy();bpy.context.collection.objects.link(poro);poro.name='Poro'
bm=bmesh.new();bm.from_mesh(poro.data)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bm.to_mesh(poro.data);bm.free()
poro.data.materials.clear();poro.data.materials.append(bpy.data.materials['Poro'])
for p in poro.data.polygons:p.material_index=0
poro.hide_render=True;poro.hide_set(True)

shield=append_meshes(ROOT/'work/scenes/shield_prepared.blend')
# Align the supplied prop upright to the stock shield's native bind position.
# This is an initial prop fit: actual handle/snap alignment is a later animation gate.
stock=[v.co for v in vanilla.data.vertices if is_shield(v)]
stock_center=Vector(tuple((min(p[a] for p in stock)+max(p[a] for p in stock))/2 for a in range(3)))
stock_height=max(p.z for p in stock)-min(p.z for p in stock)
all_shield=[v.co for o in shield for v in o.data.vertices]
source_center=Vector(tuple((min(p[a] for p in all_shield)+max(p[a] for p in all_shield))/2 for a in range(3)))
source_height=max(p.z for p in all_shield)-min(p.z for p in all_shield)
scale=stock_height/source_height
handle_anchor=Vector((0,.06,1.50))
# Native R_Hand transformed back through Shield at idle/E/run was measured
# around (-1.82,-.17,1.04). Fit the handle to that region, not the prop bounds.
grip_target=Vector((-1.81,-.17,1.04))
frame_mat=bpy.data.materials.get('ShieldFrame') or bpy.data.materials.new('ShieldFrame')
frame_mat.use_nodes=True
frame_bsdf=frame_mat.node_tree.nodes.get('Principled BSDF')
frame_bsdf.inputs['Base Color'].default_value=(.035,.05,.065,1)
frame_bsdf.inputs['Roughness'].default_value=.65
frame_bsdf.inputs['Metallic'].default_value=.25
frame_mat.diffuse_color=(.035,.05,.065,1)
for obj in shield:
    for v in obj.data.vertices:v.co=(v.co-handle_anchor)*scale+grip_target
    obj.vertex_groups.new(name='Shield').add(list(range(len(obj.data.vertices))),1,'REPLACE')
    obj.parent=rig;mod=obj.modifiers.new('Rigid Shield','ARMATURE');mod.object=rig
    obj['rig_status']='Rigid Shield; bind fit only, handle alignment pending'
    obj.data.materials[0]=frame_mat
    obj.name='CCE_'+obj['source_object']
report['shield_fit']=dict(scale=scale,source_center=list(source_center),stock_center=list(stock_center),
                          handle_anchor=list(handle_anchor),grip_target=list(grip_target),
                          all_vertices_rigid_to='Shield',handle_alignment='Revised from measured native idle/E/run grip landmarks; further review pending')
vanilla.hide_render=True;vanilla.hide_set(True)
assert_native_rig(rig)
bpy.context.scene['stage']=report['stage']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_fit_draft.blend'))
(ROOT/'validation/draft_fit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
