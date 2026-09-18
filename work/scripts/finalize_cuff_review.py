"""Summarize completed cuff trials without rerunning or promoting any scene."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/scenes/clash_braum_torso.blend'
expected='2501fd57112bb324515e56dc33cb986905f0e50813f5aa946c56ad27e24f030a'
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
specs=[
 ('surface_ring','cuff_surface_ring_targeted.json','Surface transfer retains R17 stretch and introduces surface regressions.'),
 ('wrist_097','cuff_wrist_097_targeted.json','Strict influence filter leaves small thumb-weight cuff vertices uncorrected, creating spikes; surface regressions.'),
 ('wrist_cap003','cuff_wrist_cap003_targeted.json','Preserved finger influences and removed spikes, but cuff/forearm intersections remain.'),
 ('envelope','cuff_envelope_targeted.json','Outward-only fit needs excessive displacement and distorts silhouette; intersections remain.'),
 ('distal082','cuff_distal082_targeted.json','Better cuff attachment transfers excessive elongation and contour damage to bare forearm; surface regressions.')]
report={'accepted_scene':str(source.relative_to(ROOT)),'accepted_sha256':expected,'new_checkpoint_accepted':False,'full_validation_and_export_rerun':False,'trials':[]}
for label,file,reason in specs:
    r=json.loads((ROOT/'validation'/file).read_text());rows=r['revisions']['after']['poses']
    assert r['sample_count_per_revision']==15
    assert r['unlisted_rest_geometry_and_weights_unchanged'] and r['topology_and_uv_unchanged']
    bad=[p for p in rows if p['new_local_intersections']]
    assert bad
    report['trials'].append({'label':label,'status':'REJECTED','reason':reason,'report':file,
      'tested_poses':15,'poses_with_new_pairs':len({(p['clip'],p['frame']) for p in bad}),
      'new_directed_pair_row_occurrences':sum(len(p['new_local_intersections']) for p in rows),
      'protected_geometry_weights_topology_uv_checks_passed':True,
      'r17_rows':[p for p in rows if p['clip']=='braum_spell4' and p['frame']==17]})
envelope=json.loads((ROOT/'validation/cuff_envelope_candidates.json').read_text())
report['max_envelope_rest_displacement']=max(v['displacement'] for v in envelope['envelope'].values())
report['unvalidated_alternatives']=['cuff_wrist_candidates.json:hand_0.9','cuff_wrist_candidates.json:hand_1.0','cuff_wrist_candidates.json:cap_0.0','cuff_distal_skin_candidates.json:distal_0.88']
report['blocker']='Different cuff/skin weight distributions stretch or intersect during native wrist extension. Copying stretched skin preserves cuff elongation; wrist attachment exposes clearance mismatch; coupled skin transfer moves deformation into bare forearm. No local candidate passes surface and silhouette gates.'
report['next_action']='Design a local cuff/distal-forearm transition with additional support loops and explicit old/new polygon mapping. Start from untouched torso parent and the R17/recall65 cuff edge evidence. Preserve inner/outer cuff offsets and finger influences; distribute bare-forearm deformation continuously. Do not promote any existing candidate or restart torso/grip work.'
(ROOT/'validation/cuff_continuation_review.json').write_text(json.dumps(report,indent=2))
print(json.dumps([{k:v for k,v in row.items() if k!='r17_rows'} for row in report['trials']],indent=2))
