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
p.add_argument('--isolate-grip',action='store_true',help='Hide torso/equipment occluders; retain skin, gloves and shield for contact inspection')
p.add_argument('--only-object',action='append',help='Only render these mesh objects (repeatable); temporary diagnostic visibility')
p.add_argument('--direction',help='Camera offset x,y,z; defaults to 3,-7,2 for body and 3,-7,3 for hands')
p.add_argument('--edge',help='Center on evaluated object:vertex:vertex for local deformation review')
p.add_argument('--scale',type=float,help='Explicit orthographic scale for matching detail views')
p.add_argument('--resolution',type=int,default=720,help='Square output pixels; use a fixed scale/resolution for gameplay-size comparisons')
p.add_argument('--hand-surfaces',action='store_true',help='With grip isolation, remove forearm/sleeve faces using hand/digit weights')
p.add_argument('--candidate-weights',help='Apply report.json:candidate weight experiment in memory only')
p.add_argument('--mark-vertices',help='Diagnostic spheres in red/green/blue/yellow: object:index:index...; no scene save')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes'/args.scene),load_ui=False,use_scripts=False)
scene=bpy.context.scene;rig=bpy.data.objects['Braum_Native'];camera=scene.camera
if args.candidate_weights:
    filename,label=args.candidate_weights.split(':');assert Path(filename).name==filename
    candidate_report=json.loads((ROOT/'validation'/filename).read_text())
    assert candidate_report['scene_sha256']==hashlib.sha256((ROOT/'work/scenes'/args.scene).read_bytes()).hexdigest()
    for name,changes in candidate_report['candidate_weights'][label].items():
        obj=bpy.data.objects[name]
        for index,weights in changes.items():
            index=int(index)
            for g in list(obj.data.vertices[index].groups):obj.vertex_groups[g.group].remove([index])
            for name,value in weights.items():obj.vertex_groups[name].add([index],value,'REPLACE')
        obj.data.update()
    for name,changes in candidate_report.get('candidate_positions',{}).get(label,{}).items():
        obj=bpy.data.objects[name]
        for index,position in changes.items():obj.data.vertices[int(index)].co=position
        obj.data.update()
if args.only_object:
    assert not args.vanilla and not args.isolate_grip
    assert all(bpy.data.objects.get(n) is not None for n in args.only_object)
    for obj in scene.objects:
        if obj.type=='MESH':obj.hide_render=obj.name not in args.only_object
if args.isolate_grip:
    for obj in scene.objects:
        if obj.type=='MESH' and obj.name not in ('Object009','Object004') and not obj.name.startswith('CCE_'):
            obj.hide_render=True
if args.vanilla:
    for obj in scene.objects:
        if obj.type=='MESH':obj.hide_render=True
    vanilla=bpy.data.objects['Vanilla_Reference'];vanilla.hide_set(False);vanilla.hide_render=False
    bm=bmesh.new();bm.from_mesh(vanilla.data)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==1],context='FACES')
    bm.to_mesh(vanilla.data);bm.free()
    if args.isolate_grip:
        # Retain shield and actual arm/hand surfaces; remove native torso occlusion.
        groups={g.index for g in vanilla.vertex_groups if g.name=='Shield' or
                (g.name.startswith(('L_','R_')) and any(s in g.name for s in ('Hand','Thumb','Index','Middle','Ring','Pinky','Elbow','Wrist')))}
        keep={v.index for v in vanilla.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.5}
        bm=bmesh.new();bm.from_mesh(vanilla.data);bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if not all(v.index in keep for v in f.verts)],context='FACES')
        bm.to_mesh(vanilla.data);bm.free()
if args.hand_surfaces:
    assert args.isolate_grip
    for obj in ([bpy.data.objects['Vanilla_Reference']] if args.vanilla else [bpy.data.objects[n] for n in ('Object004','Object009')]):
        groups={g.index for g in obj.vertex_groups if g.name=='Shield' or
                (g.name.startswith(('L_','R_')) and any(s in g.name for s in ('Hand','Thumb','Index','Middle','Ring','Pinky')))}
        keep={v.index for v in obj.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.5}
        bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if not all(v.index in keep for v in f.verts)],context='FACES')
        bm.to_mesh(obj.data);bm.free()
scene.cycles.samples=12
assert 64 <= args.resolution <= 4096
scene.render.resolution_x=args.resolution;scene.render.resolution_y=args.resolution
scene.render.resolution_percentage=100
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
markers=[]
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
        direction=Vector(tuple(float(x) for x in (args.direction or '3,-7,2').split(',')))
    elif focus in ('torso','pelvis','arms'):
        a,b={'torso':('Spine1','Spine3'),'pelvis':('Pelvis','Pelvis'),'arms':('L_Elbow','L_Hand')}[focus]
        center=(rig.pose.bones[a].head+rig.pose.bones[b].head)*.5
        scale={'torso':1.35,'pelvis':.95,'arms':.72}[focus]
        direction=Vector(tuple(float(x) for x in (args.direction or '3,-7,2').split(',')))
    else:
        hand=rig.pose.bones[focus]
        digit=rig.pose.bones[focus[:2]+'Middle2']
        center=(hand.matrix.translation+digit.matrix.translation)*.5
        scale=.43;direction=Vector(tuple(float(x) for x in (args.direction or '3,-7,3').split(',')))
    if args.edge:
        objname,va,vb=args.edge.split(':');obj=bpy.data.objects[objname]
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        center=ev.matrix_world@((mesh.vertices[int(va)].co+mesh.vertices[int(vb)].co)*.5)
        ev.to_mesh_clear()
    if args.scale is not None:scale=args.scale
    camera.location=center+direction
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale
    for marker in markers:
        data=marker.data;bpy.data.objects.remove(marker,do_unlink=True);bpy.data.meshes.remove(data)
    markers=[]
    if args.mark_vertices:
        marked_name,*marked_ids=args.mark_vertices.split(':');marked=bpy.data.objects[marked_name]
        evaluated=marked.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        locations=[evaluated.matrix_world@mesh.vertices[int(i)].co for i in marked_ids];evaluated.to_mesh_clear()
        for index,(vertex,location) in enumerate(zip(marked_ids,locations)):
            color=[(1,.02,.02,1),(.02,1,.02,1),(.02,.1,1,1),(1,1,.02,1)][index%4]
            material=bpy.data.materials.get(f'DiagnosticMarker_{index}') or bpy.data.materials.new(f'DiagnosticMarker_{index}')
            material.diffuse_color=color;material.use_nodes=True
            bsdf=material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=color
            bsdf.inputs['Emission Color'].default_value=color;bsdf.inputs['Emission Strength'].default_value=.5
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=scale*.008,location=location)
            marker=bpy.context.object;marker.name=f'Diagnostic_vertex_{vertex}';marker.data.materials.append(material);markers.append(marker)
    filename=f'{name}_{frame:03}_{focus}.png'
    scene.render.filepath=str(out/filename);bpy.ops.render.render(write_still=True)
    log.append({'clip':name,'frame':frame,'focus':focus,'file':str((out/filename).relative_to(ROOT))})
    print('RENDERED',filename,flush=True)
(ROOT/'validation'/f'{args.label}_render_manifest.json').write_text(json.dumps({
    'scene':args.scene,'scene_sha256':hashlib.sha256((ROOT/'work/scenes'/args.scene).read_bytes()).hexdigest(),'resolution':args.resolution,
    'vanilla_reference':args.vanilla,'isolate_grip':args.isolate_grip,'hand_surfaces':args.hand_surfaces,'only_objects':args.only_object,'camera_direction':args.direction,'edge_focus':args.edge,'ortho_scale':args.scale,'candidate_weights':args.candidate_weights,'marked_vertices':args.mark_vertices,'marker_colors':'red, green, blue, yellow in index order','renders':log},indent=2))
