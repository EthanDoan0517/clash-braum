"""Bounded local weight search using measured poses and unchanged obstacle BVHs.

Only vertex143 varies. Predicted LBS is checked against Blender before use;
any proposed result still requires the evaluated-mesh validator and full sweep.
"""
from pathlib import Path
import itertools
import json
import hashlib
import sys
from collections import Counter
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
source=json.loads((ROOT/'validation/torso_local_alternatives.json').read_text())
cases=json.loads((ROOT/'validation/torso_outline_backoff_search.json').read_text())['cases']
path=ROOT/'work/scenes/clash_braum_torso.blend'
assert hashlib.sha256(path.read_bytes()).hexdigest()==source['scene_sha256']
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];obj=bpy.data.objects['Object002']
assert np.allclose(np.array(obj.matrix_world),np.eye(4))
names=['Spine1','Spine2','Spine3','Root']
base=np.array([source['endpoint_data']['143']['weights'][n] for n in names]);base/=base.sum()
half=np.array([source['candidate_weights']['outline_s0.5']['Object002']['143'][n] for n in names]);half/=half.sum()
weights=[base,half];labels=['baseline','half_strength']
for root_scale,spine2_scale,spine3_delta in itertools.product([0,.25,.5,1,1.5,2], [0,.25,.5,1,1.5,2],[-.004,-.002,-.001,0,.001,.002,.004]):
    w=base.copy();w[3]+=root_scale*(half[3]-base[3]);w[1]+=spine2_scale*(half[1]-base[1]);w[2]+=spine3_delta;w[0]=1-w[1:].sum()
    if np.min(w)<=0:continue
    weights.append(w);labels.append(f'r{root_scale}_s{spine2_scale}_z{spine3_delta}')
weights=np.array(weights)
clearance='--clearance' in sys.argv
offsets=np.zeros((len(weights),3))
if clearance:
    rng=np.random.default_rng(143190)
    weights=[base,half];labels=['baseline','half_strength'];offsets=[np.zeros(3),np.zeros(3)]
    for i in range(2048):
        w=base+rng.uniform(.25,1.25)*(half-base)
        delta=rng.uniform(-.003,.003,3);w[1:]+=delta;w[0]=1-w[1:].sum()
        weights.append(w);labels.append(f'clearance_{i}')
        offsets.append(rng.uniform(-.002,.002,3))
    weights=np.array(weights);offsets=np.array(offsets)
affected=[f.index for f in obj.data.polygons if 143 in f.vertices]
faces=[tuple(obj.data.polygons[i].vertices) for i in affected]
local_ids=sorted({i for f in faces for i in f});local_map={v:i for i,v in enumerate(local_ids)}
local_faces=[tuple(local_map[i] for i in f) for f in faces]
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in ('Vanilla_Reference','Poro')]
topology={}
for o in objects:
    fs=[tuple(f.vertices) for f in o.data.polygons];width=max(map(len,fs))
    topology[o.name]=(fs,np.array([f+(f[-1],)*(width-len(f)) for f in fs]))
failures=[[] for _ in weights];scores=[{} for _ in weights];max_motion=np.zeros(len(weights));max_prediction_error=0.
for clip,frame in cases:
    action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(frame)
    deps=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
    points=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',points);points=points.reshape(-1,3);ev.to_mesh_clear()
    transformed=np.array([tuple(rig.pose.bones[n].matrix@rig.pose.bones[n].bone.matrix_local.inverted()@obj.data.vertices[143].co) for n in names])
    prediction=weights@transformed
    rotations=np.array([np.array(rig.pose.bones[n].matrix@rig.pose.bones[n].bone.matrix_local.inverted())[:3,:3] for n in names])
    prediction+=np.einsum('cb,bij,cj->ci',weights,rotations,offsets)
    error=float(np.max(np.abs(prediction[0]-points[143])));max_prediction_error=max(max_prediction_error,error);assert error<1e-6,(clip,frame,error)
    # Anchor predictions to Blender's baseline point to avoid zero-change drift.
    prediction+=points[143]-prediction[0]
    max_motion=np.maximum(max_motion,np.linalg.norm(prediction-points[143],axis=1))
    region=np.concatenate([points[local_ids],prediction]);low=region.min(axis=0)-1e-6;high=region.max(axis=0)+1e-6
    obstacles=[]
    for other in objects:
        other_ev=other.evaluated_get(deps);m=other_ev.to_mesh();p=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',p);p=p.reshape(-1,3);other_ev.to_mesh_clear()
        mat=np.array(other.matrix_world);p=p@mat[:3,:3].T+mat[:3,3]
        fs,indices=topology[other.name];bound=p[indices]
        nearby=np.flatnonzero(np.all(bound.max(axis=1)>=low,axis=1)&np.all(bound.min(axis=1)<=high,axis=1))
        if len(nearby):obstacles.append((other.name,BVHTree.FromPolygons(p.tolist(),[fs[i] for i in nearby]),nearby,fs))
    baseline=None
    for i,pos in enumerate(prediction):
        p=points[local_ids].copy();p[local_map[143]]=pos;tree=BVHTree.FromPolygons(p.tolist(),local_faces);pairs=set()
        for name,remote_tree,remote_ids,remote_faces in obstacles:
            for local,remote in tree.overlap(remote_tree):
                remote=int(remote_ids[remote])
                if name=='Object002' and set(faces[local])&set(remote_faces[remote]):continue
                pairs.add((affected[local],name,remote))
        if i==0:baseline=pairs
        new=pairs-baseline
        if new:failures[i].append({'clip':clip,'frame':frame,'pairs':[list(v) for v in sorted(new)]})
        if (clip,frame) in [('braum_spell4',17),('braum_dance_loop',50)]:scores[i][clip]=float(np.linalg.norm(pos-points[190]))
    print('SEARCH POSE',clip,frame,flush=True)
base_score=scores[0]
ranked=[]
for i,w in enumerate(weights):
    gains={k:base_score[k]-v for k,v in scores[i].items()}
    ranked.append({'label':labels[i],'weights':dict(zip(names,map(float,w))),'rest_offset':list(map(float,offsets[i])),'failure_frames':len(failures[i]),'failures':failures[i],'target_edge_improvements':gains,'max_vertex_motion':float(max_motion[i])})
eligible=[r for r in ranked if r['failure_frames']==0 and min(r['target_edge_improvements'].values())>0.0001]
eligible.sort(key=lambda r:min(r['target_edge_improvements'].values()),reverse=True)
report={'scene_sha256':source['scene_sha256'],'cases':cases,'candidate_count':len(weights),'max_lbs_prediction_error':max_prediction_error,'status':'Diagnostic search only; no scene saved','best_feasible':eligible[:5],'trials':ranked,'candidate_weights':{}}
for i,row in enumerate(eligible[:5]):report['candidate_weights'][f'feasible_{i}']={'Object002':{'143':row['weights']}}
if clearance:
    report['candidate_positions']={f'feasible_{i}':{'Object002':{'143':list(map(float,np.array(obj.data.vertices[143].co)+row['rest_offset']))}} for i,row in enumerate(eligible[:5])}
    # Keep every tested parameter/result without repeating tens of megabytes
    # of identical obstacle polygon IDs for rejected numerical candidates.
    for row in report['trials'][2:]:
        failures=row.pop('failures')
        row['failure_frames_by_clip']=dict(Counter(f['clip'] for f in failures))
        row['failure_examples']=failures[:2]
(ROOT/'validation'/('torso_clearance_search.json' if clearance else 'torso_outline_constrained_search.json')).write_text(json.dumps(report,indent=2))
print('FEASIBLE',json.dumps(eligible[:5],indent=2))
