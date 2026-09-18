"""Map the recurring support-trial regressions back to original geometry."""
from pathlib import Path
from collections import Counter
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
report={'parent_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'trials':[]}
def face(name,index):
    obj=bpy.data.objects[name];p=obj.data.polygons[index]
    return {'object':name,'source_polygon':index,'vertices':[{'index':i,'rest':list(obj.data.vertices[i].co),'weights':{obj.vertex_groups[g.group].name:g.weight for g in obj.data.vertices[i].groups if g.weight>0}} for i in p.vertices]}
for label in ['cuff_support_v2_trial','cuff_support_control','cuff_support_linear_trial']:
    r=json.loads((ROOT/'validation'/f'{label}_targeted.json').read_text())
    counts=Counter();cases={}
    for row in r['revisions']['after']:
        for a,remote,b in row['new_source_pairs']:
            key=(row['object'],a,remote,b);counts[key]+=1;cases.setdefault(key,[]).append([row['clip'],row['frame']])
    pairs=[]
    for key,count in counts.most_common(12):
        name,a,remote,b=key
        pairs.append({'source':face(name,a),'remote':face(remote,b),'pose_occurrences':count,'cases':cases[key],
          'shared_original_vertices':sorted(set(bpy.data.objects[name].data.polygons[a].vertices)&set(bpy.data.objects[name].data.polygons[b].vertices)) if name==remote else []})
    report['trials'].append({'label':label,'failing_poses':r['poses_with_new_pairs'],'new_directed_source_pair_rows':r['new_source_pair_row_occurrences'],
      'protected_contracts_passed':r['protected_contracts_passed'],'max_corner_normal_error':r['max_corner_normal_error'],'recurring_pairs':pairs,
      'r17_stretch':{revision:{row['object']:row['max_principal_stretch'] for row in rows if row['clip']=='braum_spell4' and row['frame']==17} for revision,rows in r['revisions'].items()}})
identity=json.loads((ROOT/'validation/cuff_support_v2_trial_identity_control_targeted.json').read_text())
assert identity['poses_with_new_pairs']==0 and identity['new_source_pair_row_occurrences']==0
report['identity_control_passed']=True;report['accepted_scene_unchanged']=report['parent_sha256']=='2501fd57112bb324515e56dc33cb986905f0e50813f5aa946c56ad27e24f030a'
assert report['accepted_scene_unchanged']
report['status']='All support candidates rejected; parent remains accepted. First cuff_support_trial is a superseded unvalidated generator draft, not a checkpoint.'
(ROOT/'validation/cuff_support_review.json').write_text(json.dumps(report,indent=2))
for r in report['trials']:
    print(r['label'],r['failing_poses'],r['new_directed_source_pair_rows'],r['r17_stretch'])
    print('RECURRING',[(p['source']['object'],p['source']['source_polygon'],p['remote']['object'],p['remote']['source_polygon'],p['pose_occurrences']) for p in r['recurring_pairs'][:4]])
