"""Complete existing 28-tie search with incident-edge and projected-gap evidence."""
from pathlib import Path
import json, hashlib
import bpy, numpy as np
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
search=json.loads((ROOT/'validation/cuff_seam_individual_search.json').read_text())
candidate=json.loads((ROOT/'validation/cuff_seam_tie_candidates.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==candidate['scene_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
cloth=bpy.data.objects['Object004'];skin=bpy.data.objects['Object009'];rig=bpy.data.objects['Braum_Native']
rest=np.array([list(v.co) for v in cloth.data.vertices]);edges=np.array([list(e.vertices) for e in cloth.data.edges])
lengths=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
out={'scene_sha256':candidate['scene_sha256'],'method':'Exact rest-coincident vertices with identical object transforms and modifiers; replacement posed position equals donor. Gap pixel upper bound uses 360/5 pixels per world unit, before view projection/occlusion. Existing strict collision results preserved.', 'attachments':{}}
for vertex,r in search['results'].items():
    pairs={}
    for pose in r['poses']:
        for face,name,remote in pose['new_pairs']:
            key=f'Object004:{face}/{name}:{remote}'
            pairs.setdefault(key,{'cuff_vertices':list(cloth.data.polygons[face].vertices),'remote_vertices':list(bpy.data.objects[name].data.polygons[remote].vertices),'poses':[]})['poses'].append([pose['clip'],pose['frame']])
    out['attachments'][vertex]={'match':r['match'],'failing_poses':r['failing_poses'],'contact_triangles':pairs,'poses':[]}
for clip,frame in search['cases']:
    action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(frame)
    dep=bpy.context.evaluated_depsgraph_get();points={}
    for obj in (cloth,skin):
        ev=obj.evaluated_get(dep);mesh=ev.to_mesh();points[obj.name]=np.array([list(v.co) for v in mesh.vertices]);ev.to_mesh_clear()
    p=points[cloth.name]
    for vertex,row in out['attachments'].items():
        i=int(vertex);incident=np.flatnonzero(np.any(edges==i,axis=1));es=edges[incident]
        after=p.copy();after[i]=points[skin.name][row['match']['skin_vertex']]
        before_len=np.linalg.norm(p[es[:,0]]-p[es[:,1]],axis=1);after_len=np.linalg.norm(after[es[:,0]]-after[es[:,1]],axis=1)
        gap=float(np.linalg.norm(after[i]-p[i]))
        row['poses'].append({'clip':clip,'frame':frame,'gap_before':gap,'gap_after':0,'gap_screen_upper_bound_px':gap*72,
                            'incident_max_elongation_before':float((before_len-lengths[incident]).max()),'incident_max_elongation_after':float((after_len-lengths[incident]).max()),
                            'incident_max_ratio_before':float((before_len/np.maximum(lengths[incident],.0001)).max()),'incident_max_ratio_after':float((after_len/np.maximum(lengths[incident],.0001)).max())})
out['passing_vertices']=search['passing_vertices']
(ROOT/'validation/cuff_seam_measured_options.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out['attachments']['871'],indent=2))
