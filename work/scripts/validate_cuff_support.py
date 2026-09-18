"""Mapped topology contracts and local collision/stretch comparison.

New triangles retain an exact original triangle identity and barycentric UV map.
No relaxation of collision acceptance: report every newly intersecting source
pair, plus intra-source folds that an original triangle could not exhibit.
"""
from pathlib import Path
import bpy,json,hashlib,argparse,sys,numpy as np
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--trial',default='cuff_support_v2_trial');p.add_argument('--all-frames',action='store_true');p.add_argument('--identity-control',action='store_true');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
trial=json.loads((ROOT/'validation'/f'{args.trial}.json').read_text());maps=trial['objects']
if args.identity_control:
    trial['scene']='clash_braum_torso.blend';trial['scene_sha256']=trial['parent_sha256']
    for mapping in maps.values():
        mapping['face_source']=list(range(mapping['original_faces']))
        mapping['corner_barycentric']=[[[1,0,0],[0,1,0],[0,0,1]] for _ in mapping['face_source']]
        mapping['vertex_source']=[{str(i):1.} for i in range(mapping['original_vertices'])]
        mapping['changed_original_vertices']=[]
cases=[('braum_recall',f) for f in [60,65,70]]+[('braum_dance_loop',f) for f in [45,50,55]]+[('braum_spell4',f) for f in [3,15,16,17,18,26]]+[('braum_idle_01_loop',17),('braum_spell3_idle180',29),('braum_run_02',12),('braum_spell3_run0',14),('braum_spell3_run-90',14)]
if args.all_frames:cases=[(c['name'],f) for c in json.loads((ROOT/'validation/draft_animation_samples.json').read_text())['animations'] for f in range(1,c['frames']+1)]
report={'trial':args.trial,'cases':cases,'revisions':{},'scope':'Changed source triangles versus all body/shield; shared actual vertices excluded. Original face identities map subdivisions. Intra-source nonadjacent overlaps also fail.'}
baseline={};before_pairs={};normal_error=0
def contract(o):
    return {'positions':[list(v.co) for v in o.data.vertices], 'weights':[{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0} for v in o.data.vertices],
     'faces':[list(f.vertices) for f in o.data.polygons], 'uv':{l.name:[[list(l.data[i].uv) for i in f.loop_indices] for f in o.data.polygons] for l in o.data.uv_layers},
     'normals':[[list(o.data.corner_normals[i].vector) for i in f.loop_indices] for f in o.data.polygons],
     'materials':[m.name if m else None for m in o.data.materials],'face_materials':[(f.material_index,f.use_smooth) for f in o.data.polygons], 'matrix':[list(r) for r in o.matrix_world]}
for revision,file,hashkey in [('before','clash_braum_torso.blend','parent_sha256'),('after',trial['scene'],'scene_sha256')]:
    path=ROOT/'work/scenes'/file;assert hashlib.sha256(path.read_bytes()).hexdigest()==trial[hashkey]
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    rig=bpy.data.objects['Braum_Native'];objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in objects:
        c=contract(o)
        if revision=='before':baseline[o.name]=c;continue
        old=baseline[o.name]
        if o.name not in maps:assert c==old,(o.name,'protected object');continue
        mapping=maps[o.name]
        for field in ['materials','matrix']:assert c[field]==old[field],(o.name,field)
        count=mapping['original_vertices'];changed=set(mapping['changed_original_vertices'])
        assert c['positions'][:count]==old['positions']
        for i in range(count):
            if i not in changed:assert c['weights'][i]==old['weights'][i],(o.name,i,'protected weight')
        for i,w in enumerate(c['weights']):assert 0<len(w)<=4 and abs(sum(w.values())-1)<1e-5 and all(v>=0 for v in w.values()),(o.name,i,w)
        for i,source in enumerate(mapping['vertex_source']):
            expected=sum((np.array(old['positions'][int(j)])*v for j,v in source.items()),np.zeros(3))
            assert np.max(np.abs(expected-c['positions'][i]))<3e-7,(o.name,i,'rest mapping')
        for i,source in enumerate(mapping['face_source']):
            bary=np.array(mapping['corner_barycentric'][i])
            assert c['face_materials'][i]==old['face_materials'][source]
            for name,uv in c['uv'].items():assert np.max(np.abs(bary@np.array(old['uv'][name][source])-uv[i]))<3e-7,(o.name,i,'UV mapping')
            expected=bary@np.array(old['positions'])[old['faces'][source]]
            assert np.max(np.abs(expected-np.array(c['positions'])[c['faces'][i]]))<3e-7,(o.name,i,'corner position')
            expected=bary@np.array(old['normals'][source]);expected/=np.maximum(np.linalg.norm(expected,axis=1)[:,None],1e-20)
            err=np.max(np.abs(expected-np.array(c['normals'][i])));normal_error=max(normal_error,float(err))
            assert err<.001,(o.name,i,'normal preservation',err)
    topology={o.name:[tuple(f.vertices) for f in o.data.polygons] for o in objects}
    source_ids={o.name:(maps[o.name]['face_source'] if revision=='after' and o.name in maps else list(range(len(o.data.polygons)))) for o in objects}
    rows=[]
    for clip,frame in cases:
        action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(frame);dep=bpy.context.evaluated_depsgraph_get()
        posed={}
        for o in objects:
            if o.name in ['Vanilla_Reference','Poro']:continue
            ev=o.evaluated_get(dep);mesh=ev.to_mesh();v=np.array([tuple(x.co) for x in mesh.vertices]);ev.to_mesh_clear()
            mat=np.array(o.matrix_world);posed[o.name]=v@mat[:3,:3].T+mat[:3,3];assert np.isfinite(v).all()
        for name,mapping in maps.items():
            affected=set(mapping['affected_source_faces']);ids=[i for i,s in enumerate(source_ids[name]) if s in affected]
            if not ids:continue
            faces=[topology[name][i] for i in ids];v=posed[name]
            tree=BVHTree.FromPolygons(v.tolist(),faces);local=v[list(set().union(*map(set,faces)))];low=local.min(axis=0)-1e-7;high=local.max(axis=0)+1e-7
            pairs=set();folds=set()
            for remote,points in posed.items():
                fs=topology[remote];width=max(map(len,fs));indices=np.array([f+(f[-1],)*(width-len(f)) for f in fs]);bounds=points[indices]
                near=np.flatnonzero(np.all(bounds.max(axis=1)>=low,axis=1)&np.all(bounds.min(axis=1)<=high,axis=1))
                if not len(near):continue
                other=BVHTree.FromPolygons(points.tolist(),[fs[i] for i in near])
                for a,b in tree.overlap(other):
                    b=int(near[b])
                    if remote==name and set(faces[a])&set(fs[b]):continue
                    s1=source_ids[name][ids[a]];s2=source_ids[remote][b]
                    pair=(s1,remote,s2);pairs.add(pair)
                    if remote==name and s1==s2:folds.add((ids[a],b))
            # Dimensionless principal stretch cannot be made smaller merely by
            # subdividing an edge. Calculate in the triangle rest tangent basis.
            rest=np.array([list(x.co) for x in bpy.data.objects[name].data.vertices]);stretch=[]
            for f in faces:
                a,b,c=rest[list(f)];u=b-a;v0=c-a;length=np.linalg.norm(u);ux=u/max(length,1e-20);x=np.dot(v0,ux);y=np.linalg.norm(v0-x*ux)
                if y<1e-9:continue
                posed_tri=posed[name][list(f)];D=np.column_stack([posed_tri[1]-posed_tri[0],posed_tri[2]-posed_tri[0]])@np.linalg.inv(np.array([[length,x],[0,y]]))
                stretch.append(float(np.linalg.svd(D,compute_uv=False)[0]))
            key=(clip,frame,name)
            if revision=='before':before_pairs[key]=pairs
            row={'clip':clip,'frame':frame,'object':name,'pair_count':len(pairs),'new_source_pairs':[list(p) for p in sorted(pairs-before_pairs[key])], 'removed_source_pairs':[list(p) for p in sorted(before_pairs[key]-pairs)],'intra_source_folds':[list(f) for f in sorted(folds)],'max_principal_stretch':max(stretch,default=0)}
            rows.append(row)
        print(revision,clip,frame,flush=True)
    report['revisions'][revision]=rows
report['protected_contracts_passed']=True;report['max_corner_normal_error']=normal_error
report['poses_with_new_pairs']=len({(r['clip'],r['frame']) for r in rows if r['new_source_pairs'] or r['intra_source_folds']})
report['new_source_pair_row_occurrences']=sum(len(r['new_source_pairs']) for r in rows)
output=args.trial+('_identity_control' if args.identity_control else '')+('_all_frames' if args.all_frames else '_targeted')+'.json'
(ROOT/'validation'/output).write_text(json.dumps(report,indent=2))
print('RESULT',report['poses_with_new_pairs'],'failing poses;',report['new_source_pair_row_occurrences'],'new mapped pair rows')
