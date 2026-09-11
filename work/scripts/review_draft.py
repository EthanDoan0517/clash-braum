"""Load native motions into a review scene and render representative draft poses."""
from pathlib import Path
import sys
import json
import math
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/tools'),str(ROOT/'work/scripts')]
from Aventurine.io import import_anm
from native_export import assert_native_rig

OUT=ROOT/'validation/previews/draft'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_fit_draft.blend'),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native']
paths=json.loads((ROOT/'audit/evidence/path_map.json').read_text())
animations={Path(path).stem:ROOT/'Braum.wad'/f'{h}.anm' for h,path in paths.items()
            if path.startswith('assets/characters/braum/skins/base/animations/') and path.endswith('.anm')}
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard'
scene.world=bpy.data.worlds.new('ReviewWorld');scene.world.color=(.16,.16,.16)
for loc,power in [((-3,-5,5),500),((4,-1,3),400),((1,3,4),700)]:
    bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object
    light.data.energy=power;light.data.shape='DISK';light.data.size=4
    light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(3,-7,3))
camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=2.8;scene.camera=camera
meshes=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
report=[]
class Reporter:
    def report(self,level,message):print(','.join(level),message)

renders={'braum_idle_01_loop':.2,'braum_run_02':.35,'braum_attack_01':.5,
         'braum_spell1':.45,'braum_spell2':.5,'braum_spell4':.5,
         'braum_spell3_idle0':.3,'braum_recall':.5}
for name,path in sorted(animations.items()):
    bpy.context.view_layer.objects.active=rig
    result=import_anm.load(Reporter(),bpy.context,str(path),create_new_action=True,adapt_to_edits=False)
    assert result=={'FINISHED'},name
    action=rig.animation_data.action;action.name=name;action.use_fake_user=True
    data=import_anm.read_anm(str(path))
    frames=sorted({1,max(1,data.frame_count//2),max(1,data.frame_count)})
    checks=[]
    for frame in frames:
        scene.frame_set(frame)
        dependency=bpy.context.evaluated_depsgraph_get()
        points=[]
        for obj in meshes:
            evaluated=obj.evaluated_get(dependency)
            mesh=evaluated.to_mesh()
            points.extend(evaluated.matrix_world@v.co for v in mesh.vertices)
            evaluated.to_mesh_clear()
        assert all(math.isfinite(x) for p in points for x in p),(name,frame)
        bounds=[[min(p[a] for p in points),max(p[a] for p in points)] for a in range(3)]
        checks.append(dict(frame=frame,bounds=bounds))
    if name in renders:
        frame=max(1,round(data.frame_count*renders[name]));scene.frame_set(frame)
        dependency=bpy.context.evaluated_depsgraph_get()
        points=[]
        for obj in meshes:
            ev=obj.evaluated_get(dependency);mesh=ev.to_mesh()
            points.extend(ev.matrix_world@v.co for v in mesh.vertices);ev.to_mesh_clear()
        low=Vector(tuple(min(p[a] for p in points) for a in range(3)))
        high=Vector(tuple(max(p[a] for p in points) for a in range(3)))
        center=(low+high)*.5
        camera.location=center+Vector((3,-7,2))
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=max(2.3,(high-low).length*1.12)
        scene.render.filepath=str(OUT/f'{name}_{frame:03}.png');bpy.ops.render.render(write_still=True)
    report.append(dict(name=name,source=str(path.relative_to(ROOT)),frames=data.frame_count,fps=data.fps,
                       duration=data.duration,samples=checks))
    print('REVIEW',name,flush=True)
assert len(report)==59,len(report)
rig.animation_data.action=bpy.data.actions['braum_idle_01_loop']
if hasattr(rig.animation_data,'action_slot') and rig.animation_data.action.slots:
    rig.animation_data.action_slot=rig.animation_data.action.slots[0]
scene.frame_set(1)
assert_native_rig(rig)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_animation_review.blend'))
(ROOT/'validation/draft_animation_samples.json').write_text(json.dumps(dict(animations=report,
    status='Numerical finite-coordinate sampling and representative renders only; deformation/transition/runtime approval pending'),indent=2))
