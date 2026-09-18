"""Classify strict seam-tie BVH findings without suppressing any validator pair."""
from pathlib import Path
import bpy,json,numpy as np
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
candidate=json.loads((ROOT/'validation/cuff_seam_tie_candidates.json').read_text())
validation=json.loads((ROOT/'validation/cuff_seam_tie_targeted.json').read_text())
source=ROOT/'work/scenes/clash_braum_torso.blend'
report={'classification_only':True,'strict_validator_unchanged':True,'tolerance':1e-7,'poses':[]}
def classify(a,b):
    na=np.cross(a[1]-a[0],a[2]-a[0]);nb=np.cross(b[1]-b[0],b[2]-b[0])
    if min(np.linalg.norm(na),np.linalg.norm(nb))<1e-12:return 'degenerate_requires_review'
    na/=np.linalg.norm(na);nb/=np.linalg.norm(nb)
    da=(a-b[0])@nb;db=(b-a[0])@na
    if max(abs(da).max(),abs(db).max())<1e-7:return 'coplanar_requires_review'
    if da.min()<-1e-7 and da.max()>1e-7 and db.min()<-1e-7 and db.max()>1e-7:return 'proper_crossing'
    return 'boundary_or_tolerance_contact'
for revision in ['before','after']:
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    rig=bpy.data.objects['Braum_Native'];cloth=bpy.data.objects['Object004']
    if revision=='after':
        for index,w in candidate['candidate_weights']['ties']['Object004'].items():
            i=int(index)
            for g in list(cloth.data.vertices[i].groups):cloth.vertex_groups[g.group].remove([i])
            for n,v in w.items():cloth.vertex_groups[n].add([i],v,'REPLACE')
        cloth.data.update()
    for row in validation['revisions']['after']['poses']:
        clip,frame=row['clip'],row['frame'];action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(frame)
        names={'Object004','Object009'}|{p[1] for p in row['new_local_intersections']};points={}
        for name in names:
            obj=bpy.data.objects[name];ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
            points[name]=np.array([list(ev.matrix_world@v.co) for v in mesh.vertices]);ev.to_mesh_clear()
        gaps=[float(np.linalg.norm(points['Object004'][m['cloth_vertex']]-points['Object009'][m['skin_vertex']])) for m in candidate['matches']]
        contacts=[]
        if revision=='after':
            for a,remote,b in row['new_local_intersections']:
                ta=points['Object004'][list(cloth.data.polygons[a].vertices)];tb=points[remote][list(bpy.data.objects[remote].data.polygons[b].vertices)]
                assert len(ta)==len(tb)==3
                contacts.append({'pair':[a,remote,b],'classification':classify(ta,tb)})
        report['poses'].append({'revision':revision,'clip':clip,'frame':frame,'maximum_seam_gap':max(gaps),'contacts':contacts,'classes':dict(Counter(c['classification'] for c in contacts))})
(ROOT/'validation/cuff_seam_tie_contacts.json').write_text(json.dumps(report,indent=2))
print('Classes',dict(Counter(c['classification'] for row in report['poses'] for c in row['contacts'])))
print('Seam max',{rev:max(r['maximum_seam_gap'] for r in report['poses'] if r['revision']==rev) for rev in ['before','after']})
