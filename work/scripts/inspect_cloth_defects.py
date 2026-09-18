"""Locate remaining absolute edge elongations in the current refinement."""
from pathlib import Path
import bpy,json,sys,argparse
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--scene',default='clash_braum_rig_refined.blend')
p.add_argument('--output',default='cloth_defects.json')
p.add_argument('--case',action='append',help='Optional clip:frame diagnostic, repeatable')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert Path(args.scene).name==args.scene and Path(args.output).name==args.output
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes'/args.scene),load_ui=False,use_scripts=False)
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())
rig=bpy.data.objects['Braum_Native'];report=[]
cases=[('braum_recall',65),('braum_dance_loop',50)]
if args.case:cases=[(name,int(frame)) for name,frame in (c.split(':') for c in args.case)]
for clip,frame in cases:
    action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    bpy.context.scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
    for obj in bpy.context.scene.objects:
        if 'source_obj_group' not in obj:continue
        comps={i:c['id'] for c in regions['objects'][obj.name] for i in c['indices']}
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();rows=[]
        for edge in obj.data.edges:
            a,b=edge.vertices
            length=(mesh.vertices[a].co-mesh.vertices[b].co).length
            rest=(obj.data.vertices[a].co-obj.data.vertices[b].co).length
            if length-rest>.05:
                rows.append({'indices':[a,b],'component':comps[a],'rest':rest,'posed':length,
                    'rest_points':[list(obj.data.vertices[i].co) for i in [a,b]],
                    'weights':[{obj.vertex_groups[g.group].name:g.weight for g in obj.data.vertices[i].groups if g.weight>0} for i in [a,b]]})
        ev.to_mesh_clear()
        report.append({'clip':clip,'frame':frame,'object':obj.name,'worst_edges':sorted(rows,key=lambda r:r['posed']-r['rest'],reverse=True)[:4]})
(ROOT/'validation'/args.output).write_text(json.dumps(report,indent=2))
print(json.dumps([{'clip':r['clip'],'obj':r['object'],'edges':[{k:v for k,v in e.items() if k not in ['rest_points','weights']} for e in r['worst_edges']]} for r in report if r['worst_edges']],indent=2))
