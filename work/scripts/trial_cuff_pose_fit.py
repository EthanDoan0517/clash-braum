"""Bounded multi-pose cuff fit against unchanged forearm surfaces.

Alternates nonnegative influence fitting and rest-position fitting. Original
finger influences remain fixed; free elbow/hand/twist weights total the remainder.
All fits are diagnostics, not accepted geometry or contact certificates.
"""
from pathlib import Path
import bpy,json,hashlib,numpy as np,itertools
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];cloth=bpy.data.objects['Object004'];skin=bpy.data.objects['Object009']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
cap=json.loads((ROOT/'validation/cuff_wrist_candidates.json').read_text())['candidate_weights']['cap_0.03']['Object004']
ties=json.loads((ROOT/'validation/cuff_seam_tie_candidates.json').read_text())
tie_map={str(m['cloth_vertex']):m['skin_vertex'] for m in ties['matches']}
cases=[('braum_recall',f) for f in [60,65,70]]+[('braum_dance_loop',f) for f in [45,50,55]]+[('braum_spell4',f) for f in [3,15,16,17,18,26]]+[('braum_idle_01_loop',17),('braum_spell3_idle180',29),('braum_run_02',12),('braum_spell3_run0',14),('braum_spell3_run-90',14)]
faces={};sides={};old={};rest={};targets={i:[] for i in cap};transforms=[]
for side,cid in [('L',810),('R',652)]:
    ids=set(next(c['indices'] for c in regions['Object009'] if c['id']==cid))
    faces[side]=[tuple(p.vertices) for p in skin.data.polygons if set(p.vertices)<=ids]
for i in cap:
    v=cloth.data.vertices[int(i)];sides[i]='L' if v.co.x>0 else 'R';rest[i]=np.array(v.co)
    old[i]={cloth.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}
for clip,frame in cases:
    action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(frame)
    matrices={b.name:np.array(rig.pose.bones[b.name].matrix@b.matrix_local.inverted()) for b in rig.data.bones};transforms.append(matrices)
    ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();points=[v.co.copy() for v in mesh.vertices]
    trees={side:BVHTree.FromPolygons(points,fs) for side,fs in faces.items()}
    for i,w in cap.items():
        if i in tie_map:target=points[tie_map[i]].copy()
        else:
            posed=sum((weight*(matrices[n]@np.r_[rest[i],1])[:3] for n,weight in w.items()),np.zeros(3))
            hit,normal,face,distance=trees[sides[i]].find_nearest(Vector(posed))
            elbow=rig.pose.bones[sides[i]+'_Elbow'].head;axis=rig.pose.bones[sides[i]+'_Hand'].head-elbow
            radial=hit-(elbow+axis*((hit-elbow).dot(axis)/axis.length_squared))
            if normal.dot(radial)<0:normal=-normal
            target=hit+normal*.004
        targets[i].append(np.array(target))
    ev.to_mesh_clear()
def simplex_fit(columns,target,total):
    best=None
    for count in range(1,len(columns)+1):
        for subset in itertools.combinations(range(len(columns)),count):
            pivot=columns[subset[-1]]
            if count==1:w=np.array([total])
            else:
                A=np.column_stack([columns[j]-pivot for j in subset[:-1]])
                x=np.linalg.lstsq(A,target-total*pivot,rcond=None)[0];w=np.r_[x,total-sum(x)]
            if min(w)<-1e-9:continue
            result=np.zeros(len(columns));result[list(subset)]=np.maximum(w,0)
            error=np.linalg.norm(np.column_stack(columns)@result-target)
            if best is None or error<best[0]:best=(error,result)
    assert best is not None
    return best[1]
changes={};positions={};details=[]
for i,w0 in old.items():
    if i in tie_map:
        # Exact sewn boundary is fixed to the unchanged donor, not optimized.
        changes[i]=ties['candidate_weights']['ties']['Object004'][i];positions[i]=list(rest[i]);continue
    names=[sides[i]+'_'+n for n in ['Hand','Elbow','Hand_Twist']]
    fixed={n:v for n,v in w0.items() if n not in names};total=1-sum(fixed.values())
    p=rest[i].copy();w=dict(cap[i]);target=np.array(targets[i]).reshape(-1)
    for iteration in range(8):
        fixed_points=np.concatenate([sum((v*(m[n]@np.r_[p,1])[:3] for n,v in fixed.items()),np.zeros(3)) for m in transforms])
        columns=[np.concatenate([(m[n]@np.r_[p,1])[:3] for m in transforms]) for n in names]
        fit=simplex_fit(columns,target-fixed_points,total)
        w={**fixed,**{n:float(v) for n,v in zip(names,fit) if v>1e-8}}
        if len(w)>4:
            # Keep finger influences; solve without the optional twist influence.
            fit=simplex_fit(columns[:2],target-fixed_points,total)
            w={**fixed,**{n:float(v) for n,v in zip(names[:2],fit) if v>1e-8}}
        matrix=[sum((v*m[n] for n,v in w.items()),np.zeros((4,4))) for m in transforms]
        A=np.vstack([m[:3,:3] for m in matrix]+[np.eye(3)*2])
        b=np.concatenate([np.array(targets[i][k])-m[:3,3] for k,m in enumerate(matrix)]+[rest[i]*2])
        q=np.linalg.lstsq(A,b,rcond=None)[0];delta=q-rest[i];length=np.linalg.norm(delta)
        p=rest[i]+delta*min(1,.015/max(length,1e-20))
    prediction=np.array([sum((v*(m[n]@np.r_[p,1])[:3] for n,v in w.items()),np.zeros(3)) for m in transforms])
    residual=np.linalg.norm(prediction-np.array(targets[i]),axis=1)
    changes[i]=w;positions[i]=list(p)
    details.append({'vertex':int(i),'rest_displacement':float(np.linalg.norm(p-rest[i])),'max_target_residual':float(max(residual)),'worst_case':cases[int(np.argmax(residual))]})
report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'UNACCEPTED multi-pose fit; no scene saved','cases':cases,'candidate_weights':{'fit':{'Object004':changes}},'candidate_positions':{'fit':{'Object004':positions}},'details':details,'fixed_seam_vertices':list(tie_map)}
(ROOT/'validation/cuff_pose_fit_candidates.json').write_text(json.dumps(report,indent=2,default=lambda v:v.item()))
print('Vertices',len(changes),'max residual',max(d['max_target_residual'] for d in details),'max displacement',max(d['rest_displacement'] for d in details))
