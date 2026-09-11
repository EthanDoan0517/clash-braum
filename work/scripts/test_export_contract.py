"""Blender regression checks for palette matching, hard normals and rig protection."""
from pathlib import Path
import sys
import json
import hashlib
import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'work/tools'), str(ROOT/'work/scripts')]
from native_export import import_baseline, export_pair, assert_native_rig, write_palette_skl
from asset_formats import read_skl, read_skn, joint_weights, validate_pair

OUT = ROOT/'build/contract_tests'
OUT.mkdir(parents=True,exist_ok=True)
passed=[]

def expect_rejection(name, operation):
    try:
        operation()
    except (AssertionError, ValueError):
        passed.append(name)
    else:
        raise AssertionError(f'{name}: invalid input was accepted')

source=read_skl(ROOT/'Braum.wad/9b8248658ce51711.skl')
for name,palette in [('original',list(source['palette'])),('reordered',list(reversed(source['palette']))),('compact',[0,68])]:
    path=OUT/f'{name}.skl'
    write_palette_skl(path,palette)
    result=read_skl(path)
    assert result['joints']==source['joints'] and result['palette']==tuple(palette)
    if name=='original':assert path.read_bytes()==(ROOT/'Braum.wad/9b8248658ce51711.skl').read_bytes()
    passed.append(f'{name} palette preserves all native joint fields')
expect_rejection('Duplicate palette rejected',lambda:write_palette_skl(OUT/'invalid.skl',[0,0]))
expect_rejection('Out-of-range palette rejected',lambda:write_palette_skl(OUT/'invalid.skl',[97]))

bpy.ops.wm.read_factory_settings(use_empty=True)
rig,baseline=import_baseline()
mesh=bpy.data.meshes.new('HardEdgeFixture')
mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[],[(0,1,2),(1,0,3)])
obj=bpy.data.objects.new('Fixture',mesh);bpy.context.collection.objects.link(obj)
uv=mesh.uv_layers.new()
for polygon in mesh.polygons:
    for li,co in zip(polygon.loop_indices,[(0,0),(1,0),(0,1)]):uv.data[li].uv=co
obj.vertex_groups.new(name='Shield').add(list(range(4)),1,'REPLACE')
mat=bpy.data.materials.new('ShieldFrame');mesh.materials.append(mat)
bpy.context.view_layer.update()
export_pair(OUT/'hard_edge',[obj],rig)
result_mesh=read_skn(OUT/'hard_edge.skn');result_skl=read_skl(OUT/'hard_edge.skl')
assert result_skl['palette']==(68,)
assert len(result_mesh['vertices'])==6
assert all(joint_weights(v,result_skl)=={68:1.0} for v in result_mesh['vertices'])
assert all(v['normal']==(0,1,0) for v in result_mesh['vertices'][:3])
assert all(v['normal']==(0,0,-1) for v in result_mesh['vertices'][3:])
passed.append('Hard-edge corner splits and compact Shield palette match')
obj.vertex_groups[0].remove([0])
expect_rejection('Unweighted vertices rejected',lambda:export_pair(OUT/'unweighted',[obj],rig))
obj.vertex_groups[0].add([0],1,'REPLACE')
obj.vertex_groups[0].add([0],0.5,'REPLACE')
expect_rejection('Unnormalized weights rejected',lambda:export_pair(OUT/'unnormalized',[obj],rig))
obj.vertex_groups[0].add([0],0.2,'REPLACE')
for name in ['Root','Spine1','Spine2','Spine3']:obj.vertex_groups.new(name=name).add([0],0.2,'REPLACE')
expect_rejection('Five influences rejected',lambda:export_pair(OUT/'too_many_weights',[obj],rig))
rig.location.x=1;bpy.context.view_layer.update()
expect_rejection('Moved armature rejected',lambda:assert_native_rig(rig))
rig.location.x=0;bpy.context.view_layer.update()
old_name=rig.pose.bones['Shield'].name
rig.pose.bones['Shield'].name='ChangedShield'
expect_rejection('Renamed native joint rejected',lambda:assert_native_rig(rig))
rig.pose.bones['ChangedShield'].name=old_name
assert_native_rig(rig)
(ROOT/'validation/export_contract_tests.json').write_text(json.dumps(dict(passed=passed,count=len(passed)),indent=2))
print(json.dumps(passed,indent=2))
