"""Compare a two-triangle retriangulation using the shared quad surface identity."""
from pathlib import Path
import argparse,sys,json,hashlib
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--all-frames',action='store_true');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
trial=json.loads((ROOT/'validation/torso_diagonal_trial.json').read_text())
cases=json.loads((ROOT/'validation/torso_outline_backoff_search.json').read_text())['cases']
if args.all_frames:cases=[(c['name'],f) for c in json.loads((ROOT/'validation/draft_animation_samples.json').read_text())['animations'] for f in range(1,c['frames']+1)]
output='torso_diagonal_all_frames.json' if args.all_frames else 'torso_diagonal_targeted.json'
report={'surface_mapping':trial['surface_mapping'],'revisions':{},'scope':'Changed quad patch against body/shield; shared-vertex self faces excluded. Not whole-body/runtime certification.'}
contracts={};before_rows={};patch={316,557}
for label,filename,hash_key in [('before','clash_braum_torso.blend','parent_sha256'),('after','clash_braum_torso_diagonal_trial.blend','scene_sha256')]:
    path=ROOT/'work/scenes'/filename;assert hashlib.sha256(path.read_bytes()).hexdigest()==trial[hash_key]
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    rig=bpy.data.objects['Braum_Native'];obj=bpy.data.objects['Object002'];objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in ('Vanilla_Reference','Poro')]
    topology={}
    for o in objects:
        fs=[tuple(f.vertices) for f in o.data.polygons];width=max(map(len,fs));topology[o.name]=(fs,np.array([f+(f[-1],)*(width-len(f)) for f in fs]))
        contract={'position':[tuple(v.co) for v in o.data.vertices],'weights':[{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0} for v in o.data.vertices],'matrix':[list(row) for row in o.matrix_world],'faces':fs,'uv':{l.name:[tuple(d.uv) for d in l.data] for l in o.data.uv_layers},'materials':[m.name if m else None for m in o.data.materials],'face_materials':[(f.material_index,f.use_smooth) for f in o.data.polygons]}
        if label=='before':contracts[o.name]=contract
        else:
            original=contracts[o.name]
            for key in ('position','weights','matrix','materials','face_materials'):assert contract[key]==original[key],(o.name,key)
            for i,fs in enumerate(contract['faces']):
                if o.name!='Object002' or i not in patch:assert fs==original['faces'][i],(o.name,i)
            for name,values in contract['uv'].items():
                for i,uv in enumerate(values):
                    if o.name!='Object002' or i//3 not in patch:assert uv==original['uv'][name][i],(o.name,name,i)
    faces=[tuple(obj.data.polygons[i].vertices) for i in sorted(patch)];ids=sorted({i for f in faces for i in f});rows=[]
    for clip,frame in cases:
        if frame==1:print(label,clip,flush=True)
        action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];bpy.context.scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
        ev=obj.evaluated_get(deps);m=ev.to_mesh();points=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',points);points=points.reshape(-1,3);ev.to_mesh_clear()
        assert np.isfinite(points).all()
        tree=BVHTree.FromPolygons(points.tolist(),faces);low=points[ids].min(axis=0)-1e-7;high=points[ids].max(axis=0)+1e-7
        contacts=set();pairs=[]
        for other in objects:
            other_ev=other.evaluated_get(deps);m=other_ev.to_mesh();v=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',v);v=v.reshape(-1,3);other_ev.to_mesh_clear()
            matrix=np.array(obj.matrix_world.inverted()@other.matrix_world);v=v@matrix[:3,:3].T+matrix[:3,3]
            fs,indices=topology[other.name];bounds=v[indices];near=np.flatnonzero(np.all(bounds.max(axis=1)>=low,axis=1)&np.all(bounds.min(axis=1)<=high,axis=1))
            if not len(near):continue
            remote_tree=BVHTree.FromPolygons(v.tolist(),[fs[i] for i in near])
            for local,remote in tree.overlap(remote_tree):
                remote=int(near[remote])
                if other==obj and set(faces[local])&set(fs[remote]):continue
                contacts.add((other.name,remote));pairs.append([sorted(patch)[local],other.name,remote])
        lengths=[float(np.linalg.norm(points[a]-points[b])) for a,b in [(142,143),(143,337),(337,190),(190,142),(143,190),(142,337)]]
        row={'clip':clip,'frame':frame,'remote_surfaces':[list(x) for x in sorted(contacts)],'pairs':pairs,'quad_boundary_and_diagonal_lengths':lengths}
        if label=='before':before_rows[(clip,frame)]=contacts
        else:
            row['new_remote_surfaces']=[list(x) for x in sorted(contacts-before_rows[(clip,frame)])]
            row['removed_remote_surfaces']=[list(x) for x in sorted(before_rows[(clip,frame)]-contacts)]
        rows.append(row)
    report['revisions'][label]={'scene_sha256':trial[hash_key],'poses':rows}
    (ROOT/'validation'/output).write_text(json.dumps(report,indent=2))
report['sample_count_per_revision']=len(cases);report['all_vertex_positions_weights_other_faces_uvs_and_materials_preserved']=True
bad=[r for r in rows if r['new_remote_surfaces']]
report['frames_with_new_remote_surfaces']=len(bad);report['new_remote_surface_frame_occurrences']=sum(len(r['new_remote_surfaces']) for r in rows)
report['removed_remote_surface_frame_occurrences']=sum(len(r['removed_remote_surfaces']) for r in rows)
(ROOT/'validation'/output).write_text(json.dumps(report,indent=2))
print('RESULT',len(cases),'frames; new contacts at',[(r['clip'],r['frame']) for r in bad])
