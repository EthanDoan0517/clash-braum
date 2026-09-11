"""Export a development-only matched pair; never populate the release package."""
from pathlib import Path
import sys,json,argparse
import bpy
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/tools'),str(ROOT/'work/scripts')]
from native_export import export_pair
from asset_formats import read_skl,read_skn,validate_pair,joint_weights

p=argparse.ArgumentParser()
p.add_argument('--scene',default='clash_braum_fit_draft.blend')
p.add_argument('--output',default='model_draft')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert Path(args.scene).name==args.scene and Path(args.output).name==args.output
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes'/args.scene),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native']
meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH' and obj.name!='Vanilla_Reference']
out=ROOT/'build'/args.output/'braum_clash'
out.parent.mkdir(parents=True,exist_ok=True)
# All shield pieces share one export material. Join only in this export session.
shields=[o for o in meshes if o.name.startswith('CCE_')]
bpy.ops.object.select_all(action='DESELECT')
for obj in shields:obj.select_set(True)
bpy.context.view_layer.objects.active=shields[0]
bpy.ops.object.join()
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name!='Vanilla_Reference']
export_pair(out,meshes,rig)
m,s=read_skn(out.with_suffix('.skn')),read_skl(out.with_suffix('.skl'))
result=validate_pair(m,s)
assert len({sm['name'] for sm in m['submeshes']})==len(m['submeshes'])
assert s['joints']==read_skl(ROOT/'Braum.wad/9b8248658ce51711.skl')['joints']
shield=next(sm for sm in m['submeshes'] if sm['name']=='ShieldFrame')
assert all(joint_weights(v,s)=={68:1.0} for v in m['vertices'][shield['vertex_start']:shield['vertex_start']+shield['vertex_count']])
source_m=read_skn(ROOT/'Braum.wad/fbf88fcfc8ec8dc4.skn');source_s=read_skl(ROOT/'Braum.wad/9b8248658ce51711.skl')
poro=next(sm for sm in m['submeshes'] if sm['name']=='Poro')
source_poro=next(sm for sm in source_m['submeshes'] if sm['name']=='Poro')
assert poro['index_count']==source_poro['index_count']==3054
def corners(mesh,sm):return [mesh['vertices'][i] for i in mesh['indices'][sm['index_start']:sm['index_start']+sm['index_count']]]
poro_errors=dict(position=0,uv=0,normal=0,weight=0)
for a,b in zip(corners(source_m,source_poro),corners(m,poro)):
    for key in ('position','uv','normal'):
        poro_errors[key]=max(poro_errors[key],max(abs(x-y) for x,y in zip(a[key],b[key])))
    wa,wb=joint_weights(a,source_s),joint_weights(b,s)
    poro_errors['weight']=max(poro_errors['weight'],max(abs(wa[k]-wb[k]) for k in wa.keys()|wb.keys()))
assert poro_errors['position']<0.0001 and poro_errors['uv']==0 and poro_errors['normal']<0.00001 and poro_errors['weight']<0.00001,poro_errors
result.update(status='DEVELOPMENT ONLY: no texture atlas, skin0 BIN or game validation; not a release package',
              preserved_poro_triangles=1018,poro_max_errors=poro_errors,shield_rigid=True,exact_native_joint_records=True,
              palette=list(s['palette']))
result['input_scene']=args.scene
(ROOT/'validation'/f'{args.output}_export.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
