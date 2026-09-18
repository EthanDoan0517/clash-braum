"""Validate actual evaluated poses, authored regions, seams and preserved actions.

Every native frame is sampled. Geometric metrics diagnose deformation; they do
not establish collision-free motion, graph transitions or runtime acceptance.
"""
from pathlib import Path
import sys, json, hashlib, argparse
import bpy
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/tools'),str(ROOT/'work/scripts')]
from native_export import assert_native_rig

p=argparse.ArgumentParser()
p.add_argument('--scene',default='clash_braum_rig_refined.blend')
p.add_argument('--refinement',default='rig_refinement.json')
p.add_argument('--report',default='rig_refinement_validation.json')
p.add_argument('--reuse-before',action='store_true')
p.add_argument('--candidate-weights',help='Validate report.json:candidate in memory before saving a checkpoint')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert all(Path(v).name==v for v in [args.scene,args.refinement,args.report])
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())
refinement=json.loads((ROOT/'validation'/args.refinement).read_text())
clips=json.loads((ROOT/'validation/draft_animation_samples.json').read_text())['animations']
assert len(clips)==59
report={'status':'Offline checks only; visual and runtime gates tracked separately',
        'sample_policy':'Every integer frame 1..frame_count for all 59 original clips',
        'input_scene_sha256':{},'revisions':{},'source_anm_sha256':{}}
report['candidate_weights']=args.candidate_weights
previous=json.loads((ROOT/'validation/rig_refinement_validation.json').read_text()) if args.reuse_before else None
for clip in clips:
    path=ROOT/clip['source'];report['source_anm_sha256'][clip['name']]=hashlib.sha256(path.read_bytes()).hexdigest()

def coords(mesh):
    values=np.empty(len(mesh.vertices)*3,dtype=np.float64)
    mesh.vertices.foreach_get('co',values)
    return values.reshape(-1,3)

def action_signature(action):
    curves=[]
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag=strip.channelbag(slot,ensure=False)
                if bag:
                    for fc in bag.fcurves:
                        curves.append((fc.data_path,fc.array_index,[(tuple(k.co),k.interpolation) for k in fc.keyframe_points]))
    return hashlib.sha256(repr(curves).encode()).hexdigest()

signatures=None
for label,filename in [('before','clash_braum_animation_review.blend'),('refined',args.scene)]:
    path=ROOT/'work/scenes'/filename
    report['input_scene_sha256'][label]=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    scene=bpy.context.scene;rig=bpy.data.objects['Braum_Native'];assert_native_rig(rig)
    if label=='refined' and args.candidate_weights:
        filename,key=args.candidate_weights.split(':');assert Path(filename).name==filename
        candidate=json.loads((ROOT/'validation'/filename).read_text());assert candidate['scene_sha256']==report['input_scene_sha256'][label]
        report['authored_candidate_weights']=candidate['candidate_weights'][key]
        for name,changes in report['authored_candidate_weights'].items():
            obj=bpy.data.objects[name]
            for index,weights in changes.items():
                index=int(index)
                for g in list(obj.data.vertices[index].groups):obj.vertex_groups[g.group].remove([index])
                for name,value in weights.items():
                    if value>0:obj.vertex_groups[name].add([index],value,'REPLACE')
            obj.data.update()
    signature={c['name']:action_signature(bpy.data.actions[c['name']]) for c in clips}
    if signatures is not None:assert signatures==signature,'Imported native actions changed'
    signatures=signature
    if label=='before' and previous:
        assert previous['input_scene_sha256']['before']==report['input_scene_sha256']['before']
        assert previous['source_anm_sha256']==report['source_anm_sha256']
        report['revisions']['before']=previous['revisions']['before']
        report['before_pose_measurements_reused_for_identical_scene_and_anms']=True
        continue
    objects=[o for o in scene.objects if o.type=='MESH' and o.name!='Vanilla_Reference']
    rest={o.name:coords(o.data) for o in objects}
    edges={};edge_lengths={};metrics={}
    for obj in objects:
        p=rest[obj.name]
        e=np.array([tuple(e.vertices) for e in obj.data.edges])
        lengths=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)
        mask=lengths>.0001
        edges[obj.name]=e[mask];edge_lengths[obj.name]=lengths[mask]
        metrics[obj.name]={'max_edge_ratio':0.,'max_p99_edge_ratio':0.,'worst_frame':None}
        for v in obj.data.vertices:
            weights=[g.weight for g in v.groups if g.weight>0]
            assert 1<=len(weights)<=4 and abs(sum(weights)-1)<1e-5,(obj.name,v.index,weights)
    digit_counts={}
    if label=='refined':
        skin=bpy.data.objects['Object009']
        for hand in refinement['hands']:
            for digit,cid in hand['digit_shell_ids'].items():
                ids=next(c['indices'] for c in regions['objects']['Object009'] if c['id']==cid)
                expected={hand['side']+'_'+digit+str(i) for i in [1,2]}
                totals=[]
                for i in ids:
                    w={skin.vertex_groups[g.group].name:g.weight for g in skin.data.vertices[i].groups if g.weight>0}
                    assert all(n in expected or n==hand['side']+'_Hand' for n in w),(digit,i,w)
                    totals.append(sum(w.get(n,0) for n in expected))
                assert min(totals)>.5,(digit,min(totals))
                digit_counts[hand['side']+'_'+digit]={'vertices':len(ids),'min_digit_weight':min(totals)}
    rigid_error=0.;samples=[];total_frames=0
    for clip in clips:
        action=bpy.data.actions[clip['name']]
        rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
        clip_worst={'ratio':0.,'frame':None,'object':None}
        for frame in range(1,clip['frames']+1):
            scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
            posed={}
            for obj in objects:
                ev=obj.evaluated_get(deps);mesh=ev.to_mesh();p=coords(mesh);ev.to_mesh_clear()
                assert p.shape==rest[obj.name].shape and np.isfinite(p).all(),(label,clip['name'],frame,obj.name)
                posed[obj.name]=p
                e=edges[obj.name]
                ratio=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)/edge_lengths[obj.name]
                high=float(ratio.max());p99=float(np.quantile(ratio,.99))
                metric=metrics[obj.name]
                if high>metric['max_edge_ratio']:
                    metric.update(max_edge_ratio=high,worst_frame=[clip['name'],frame])
                metric['max_p99_edge_ratio']=max(metric['max_p99_edge_ratio'],p99)
                if high>clip_worst['ratio']:clip_worst={'ratio':high,'frame':frame,'object':obj.name}
            if label=='refined':
                # Compare evaluated points to the intended native bone transform,
                # including stock animated scale; this is stronger than edge lengths.
                for component in refinement['rigid_components']:
                    name=component['object'];bone=rig.pose.bones[component['bone']]
                    ids=next(c['indices'] for c in regions['objects'][name] if c['id']==component['component'])
                    matrix=np.array(bone.matrix@bone.bone.matrix_local.inverted())
                    expected=rest[name][ids]@matrix[:3,:3].T+matrix[:3,3]
                    rigid_error=max(rigid_error,float(np.max(np.abs(expected-posed[name][ids]))))
            total_frames+=1
        samples.append({'clip':clip['name'],'frames_checked':clip['frames'],'worst_edge_stretch':clip_worst})
        print(label,clip['name'],clip['frames'],flush=True)
    if label=='refined':assert rigid_error<.00001,rigid_error
    report['revisions'][label]={'total_frames':total_frames,'all_coordinates_finite':True,
        'normalized_max_four_weights':True,'edge_stretch_metrics':metrics,'digit_assignments':digit_counts,
        'rigid_component_max_position_error':rigid_error,'clips':samples}
    (ROOT/'validation'/args.report).write_text(json.dumps(report,indent=2))
report['imported_action_channels_unchanged']=True
report['native_rest_contract_unchanged']=True
(ROOT/'validation'/args.report).write_text(json.dumps(report,indent=2))
print('PASS',json.dumps({k:v['total_frames'] for k,v in report['revisions'].items()}))
