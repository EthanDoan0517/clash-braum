"""Render targeted deformation comparisons from existing actions, no re-import."""
from pathlib import Path
import sys, argparse, json, hashlib
import bpy, bmesh
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--scene',default='clash_braum_rig_refined.blend')
p.add_argument('--label',default='refined')
p.add_argument('--quick',action='store_true')
p.add_argument('--case',action='append',help='Render only clip:frame:focus (repeatable)')
p.add_argument('--vanilla',action='store_true',help='Render original reference under exactly the same imported action')
p.add_argument('--direction',default='3,-7,2',help='Camera offset x,y,z; consistent across comparison scenes')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes'/args.scene),load_ui=False,use_scripts=False)
scene=bpy.context.scene;rig=bpy.data.objects['Braum_Native'];camera=scene.camera
if args.vanilla:
    for obj in scene.objects:
        if obj.type=='MESH':obj.hide_render=True
    vanilla=bpy.data.objects['Vanilla_Reference'];vanilla.hide_set(False);vanilla.hide_render=False
    bm=bmesh.new();bm.from_mesh(vanilla.data)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==1],context='FACES')
    bm.to_mesh(vanilla.data);bm.free()
scene.cycles.samples=12
scene.render.resolution_x=720;scene.render.resolution_y=720
out=ROOT/'validation/previews'/args.label;out.mkdir(parents=True,exist_ok=True)
cases=[('braum_idle_01_loop',17,'body'),('braum_spell3_idle0',17,'R_Hand'),
       ('braum_idle_01_loop',17,'L_Hand'),('braum_spell4',15,'body')]
if not args.quick:
    cases += [('braum_spell4',26,'body'),('braum_spell4',3,'body'),('braum_death',35,'body'),
              ('braum_recall',65,'body'),('braum_dance_loop',50,'body'),('braum_recall',138,'body'),
              ('braum_run_02',12,'body'),('braum_run_slow',12,'body'),('braum_run_haste_01',12,'body')]
    for name in sorted(a.name for a in bpy.data.actions if 'spell3' in a.name and any(x in a.name for x in ['180','179','90'])):
        action=bpy.data.actions[name]
        cases.append((name,round((action.frame_range[0]+action.frame_range[1])*.5),'body'))
log=[]
if args.case:
    cases=[(name,int(frame),focus) for name,frame,focus in (c.split(':') for c in args.case)]
for name,frame,focus in cases:
    action=bpy.data.actions.get(name)
    assert action is not None,name
    rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    scene.frame_set(frame)
    if focus=='body':
        points=[];dep=bpy.context.evaluated_depsgraph_get()
        for obj in scene.objects:
            if obj.type=='MESH' and not obj.hide_render:
                ev=obj.evaluated_get(dep);mesh=ev.to_mesh()
                points.extend(ev.matrix_world@v.co for v in mesh.vertices);ev.to_mesh_clear()
        lo=Vector(tuple(min(v[a] for v in points) for a in range(3)))
        hi=Vector(tuple(max(v[a] for v in points) for a in range(3)))
        center=(lo+hi)*.5;scale=max(2.3,(hi-lo).length*1.08)
        direction=Vector(tuple(float(x) for x in args.direction.split(',')))
    elif focus in ('torso','pelvis','arms'):
        a,b={'torso':('Spine1','Spine3'),'pelvis':('Pelvis','Pelvis'),'arms':('L_Elbow','L_Hand')}[focus]
        center=(rig.pose.bones[a].head+rig.pose.bones[b].head)*.5
        scale={'torso':1.35,'pelvis':.95,'arms':.72}[focus]
        direction=Vector(tuple(float(x) for x in args.direction.split(',')))
    else:
        hand=rig.pose.bones[focus]
        digit=rig.pose.bones[focus[:2]+'Middle2']
        center=(hand.matrix.translation+digit.matrix.translation)*.5
        scale=.43;direction=Vector((3,-7,3))
    camera.location=center+direction
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale
    filename=f'{name}_{frame:03}_{focus}.png'
    scene.render.filepath=str(out/filename);bpy.ops.render.render(write_still=True)
    log.append({'clip':name,'frame':frame,'focus':focus,'file':str((out/filename).relative_to(ROOT))})
    print('RENDERED',filename,flush=True)
(ROOT/'validation'/f'{args.label}_render_manifest.json').write_text(json.dumps({
    'scene':args.scene,'scene_sha256':hashlib.sha256((ROOT/'work/scenes'/args.scene).read_bytes()).hexdigest(),
    'vanilla_reference':args.vanilla,'renders':log},indent=2))
