"""Read-only cuff/forearm mapping and deformation evidence from the accepted scene."""
from pathlib import Path
import bpy, json, hashlib,sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native']; obj=bpy.data.objects['Object004']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
spec=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'cuff_surface_ring_candidates.json:surface'
filename,key=spec.split(':');candidate=json.loads((ROOT/'validation'/filename).read_text())
def weights(o,i):return {o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[i].groups if g.weight>0}
shells={side:set(next(c['indices'] for c in regions['Object004'] if c['id']==cid)) for side,cid in [('L',2539),('R',865)]}
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate':spec,'shells':{},'poses':[]}
for side,ids in shells.items():
    elbow=rig.data.bones[side+'_Elbow'].head_local; axis=rig.data.bones[side+'_Hand'].head_local-elbow
    report['shells'][side]={'vertices':[{'index':i,'co':list(obj.data.vertices[i].co),'t':(obj.data.vertices[i].co-elbow).dot(axis)/axis.length_squared,'weights':weights(obj,i)} for i in sorted(ids)]}
for label in ['parent',key]:
    if label==key:
        for index,w in candidate['candidate_weights'][key]['Object004'].items():
            i=int(index)
            for g in list(obj.data.vertices[i].groups):obj.vertex_groups[g.group].remove([i])
            for n,v in w.items():obj.vertex_groups[n].add([i],v,'REPLACE')
        for i,p in candidate.get('candidate_positions',{}).get(key,{}).get('Object004',{}).items():obj.data.vertices[int(i)].co=p
        obj.data.update()
    for clip,frame in [('braum_idle_01_loop',17),('braum_spell4',17),('braum_recall',65)]:
        a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame)
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=ev.to_mesh()
        for side,ids in shells.items():
            edges=[]
            for edge in obj.data.edges:
                i,j=edge.vertices
                if i not in ids or j not in ids:continue
                rest=(obj.data.vertices[i].co-obj.data.vertices[j].co).length
                posed=(mesh.vertices[i].co-mesh.vertices[j].co).length
                edges.append({'edge':[i,j],'rest':rest,'posed':posed,'ratio':posed/max(rest,1e-8),'elongation':posed-rest})
            report['poses'].append({'revision':label,'clip':clip,'frame':frame,'side':side,'worst_edges':sorted(edges,key=lambda r:-r['elongation'])[:12], 'bones':{n:list(rig.pose.bones[side+'_'+n].head) for n in ['Elbow','Hand','Hand_Twist']}})
        ev.to_mesh_clear()
(ROOT/'validation'/('cuff_attachment_inspection.json' if '--' not in sys.argv else 'cuff_wrist_inspection.json')).write_text(json.dumps(report,indent=2))
for r in report['poses']:print(r['revision'],r['clip'],r['side'],r['worst_edges'][:2])
