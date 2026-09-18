"""Unaccepted local auxiliary handle candidate; original shield meshes remain exact."""
from pathlib import Path
import bpy,json,math,hashlib,argparse,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'work/scenes/clash_braum_torso.blend'
p=argparse.ArgumentParser();p.add_argument('--offset',type=float,default=.035);p.add_argument('--half-length',type=float,default=.065);p.add_argument('--label',default='handle_trial');p.add_argument('--knuckles',action='store_true');p.add_argument('--normal',action='store_true');p.add_argument('--advance',type=float,default=0);args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert Path(args.label).name==args.label
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];a=bpy.data.actions['braum_spell3_run0'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(14)
s=rig.pose.bones['Shield'];deform=rig.matrix_world@s.matrix@s.bone.matrix_local.inverted();inv=deform.inverted()
palm=rig.matrix_world@((rig.pose.bones['L_Hand'].head+rig.pose.bones['L_Middle1'].head)*.5)
if args.knuckles:palm=rig.matrix_world@((rig.pose.bones['L_Index1'].head+rig.pose.bones['L_Pinky1'].head)*.5)
report=json.loads((ROOT/'validation/local_handle_diagnostics.json').read_text());c=next(c for c in report['components'] if c['object']=='CCE_mesh_14.001' and c['id']==20)
o=bpy.data.objects[c['object']];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],c['faces']);near=tree.find_nearest(palm)[0];ev.to_mesh_clear()
center=palm+(near-palm).normalized()*args.offset
axis=rig.matrix_world.to_3x3()@(rig.pose.bones['L_Index1'].head-rig.pose.bones['L_Pinky1'].head).normalized()
forward=rig.matrix_world.to_3x3()@(rig.pose.bones['L_Middle1'].head-rig.pose.bones['L_Hand'].head).normalized()
if args.normal:center=palm+axis.cross(forward).normalized()*args.offset
center+=forward*args.advance
ends=[center-axis*args.half_length,center+axis*args.half_length];anchors=[tree.find_nearest(p)[0] for p in ends]
segments=[(ends[0],ends[1],.014),(anchors[0],ends[0],.009),(ends[1],anchors[1],.009)]
verts=[];faces=[]
for start,end,radius in segments:
 start,end=inv@start,inv@end;z=(end-start).normalized();x=z.cross(Vector((0,0,1)))
 if x.length<.01:x=z.cross(Vector((0,1,0)))
 x.normalize();y=z.cross(x);offset=len(verts)
 for p in [start,end]:
  for k in range(12):verts.append(p+radius*(x*math.cos(k*math.tau/12)+y*math.sin(k*math.tau/12)))
 for k in range(12):faces.append((offset+k,offset+(k+1)%12,offset+12+(k+1)%12,offset+12+k))
 faces.append(tuple(offset+k for k in reversed(range(12))));faces.append(tuple(offset+12+k for k in range(12)))
mesh=bpy.data.meshes.new('CCE_auxiliary_grip_trial');mesh.from_pydata(verts,[],faces);mesh.update();mesh.uv_layers.new(name='UVMap')
for p in mesh.polygons:
 for j,li in enumerate(p.loop_indices):mesh.uv_layers.active.data[li].uv=(j%2,j//2)
obj=bpy.data.objects.new('CCE_auxiliary_grip_trial',mesh);bpy.context.collection.objects.link(obj);obj.vertex_groups.new(name='Shield').add(list(range(len(verts))),1,'REPLACE');mod=obj.modifiers.new('Native Shield','ARMATURE');mod.object=rig
obj.data.materials.append(o.data.materials[0])
record={'status':'UNACCEPTED geometry trial; requires palm/finger and multi-pose visual review','input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'new_object':obj.name,'offset':args.offset,'vertices':len(verts),'faces':len(faces),'world_run14_center':list(center),'world_run14_ends':[list(p) for p in ends],'world_run14_anchors':[list(p) for p in anchors],'method':'Auxiliary 12-sided grip and two supports attached to physical CCE side rail20. Center offset specified in report toward rail from native palm midpoint; axis Index1-Pinky1. All old geometry and weights unchanged.'}
record['knuckle_center']=args.knuckles
record['half_length']=args.half_length
record['normal_offset']=args.normal;record['advance']=args.advance
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/scenes'/f'clash_braum_{args.label}.blend'))
(ROOT/'validation'/f'local_{args.label}.json').write_text(json.dumps(record,indent=2))

