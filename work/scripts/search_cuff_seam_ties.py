"""Test each exact seam tie independently with unchanged strict BVH semantics."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
candidate=json.loads((ROOT/'validation/cuff_seam_tie_candidates.json').read_text())
cases=[(r['clip'],r['frame']) for r in json.loads((ROOT/'validation/cuff_seam_tie_targeted.json').read_text())['revisions']['before']['poses']]+[('braum_spell4',16),('braum_spell4',18)]
rig=bpy.data.objects['Braum_Native'];cloth=bpy.data.objects['Object004'];skin=bpy.data.objects['Object009']
assert cloth.matrix_world==skin.matrix_world
assert [(m.type,m.object.name) for m in cloth.modifiers]==[(m.type,m.object.name) for m in skin.modifiers]
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in ['Poro','Vanilla_Reference']]
faces={o.name:[tuple(f.vertices) for f in o.data.polygons] for o in objects}
indices={}
for n,fs in faces.items():
    width=max(map(len,fs));indices[n]=np.array([f+(f[-1],)*(width-len(f)) for f in fs])
affected={m['cloth_vertex']:[i for i,f in enumerate(faces['Object004']) if m['cloth_vertex'] in f] for m in candidate['matches']}
results={str(m['cloth_vertex']):{'match':m,'poses':[]} for m in candidate['matches']}
for clip,frame in cases:
    action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(frame);dep=bpy.context.evaluated_depsgraph_get()
    points={};bounds={}
    for o in objects:
        ev=o.evaluated_get(dep);mesh=ev.to_mesh();v=np.array([list(ev.matrix_world@x.co) for x in mesh.vertices]);ev.to_mesh_clear();points[o.name]=v
        b=v[indices[o.name]];bounds[o.name]=(b.min(axis=1),b.max(axis=1))
    for match in candidate['matches']:
        vertex=match['cloth_vertex'];ids=affected[vertex];fs=[faces['Object004'][i] for i in ids];used=list(set().union(*map(set,fs)))
        before=None
        for revision in ['before','after']:
            local=points['Object004'].copy()
            if revision=='after':local[vertex]=points['Object009'][match['skin_vertex']]
            tree=BVHTree.FromPolygons(local.tolist(),fs);lo=local[used].min(axis=0)-1e-7;hi=local[used].max(axis=0)+1e-7;pairs=set()
            for name,remote in points.items():
                lower,upper=bounds[name]
                if name=='Object004':
                    remote=local;lower=lower.copy();upper=upper.copy();b=remote[indices[name][ids]];lower[ids]=b.min(axis=1);upper[ids]=b.max(axis=1)
                near=np.flatnonzero(np.all(upper>=lo,axis=1)&np.all(lower<=hi,axis=1))
                if not len(near):continue
                other=BVHTree.FromPolygons(remote.tolist(),[faces[name][i] for i in near])
                for a,b in tree.overlap(other):
                    b=int(near[b])
                    if name=='Object004' and set(fs[a])&set(faces[name][b]):continue
                    pairs.add((ids[a],name,b))
            if revision=='before':before=pairs
            else:results[str(vertex)]['poses'].append({'clip':clip,'frame':frame,'new_pairs':[list(p) for p in sorted(pairs-before)],'removed_pairs':len(before-pairs),'seam_gap_before':float(np.linalg.norm(points['Object004'][vertex]-points['Object009'][match['skin_vertex']]))})
    print('CASE',clip,frame,flush=True)
passed=[]
for i,r in results.items():
    r['failing_poses']=sum(bool(p['new_pairs']) for p in r['poses'])
    if not r['failing_poses']:passed.append(i)
report={'status':'Individual tie diagnostics only; passing samples require combined/wider acceptance','cases':cases,'results':results,'passing_vertices':passed}
(ROOT/'validation/cuff_seam_individual_search.json').write_text(json.dumps(report,indent=2))
combined={'scene_sha256':candidate['scene_sha256'],'status':'UNACCEPTED combined individually passing ties','candidate_weights':{'combined':{'Object004':{i:candidate['candidate_weights']['ties']['Object004'][i] for i in passed}}}}
if passed:(ROOT/'validation/cuff_seam_combined_candidates.json').write_text(json.dumps(combined,indent=2))
print('PASSING',passed,'FAILURES',[(i,r['failing_poses']) for i,r in results.items()])
