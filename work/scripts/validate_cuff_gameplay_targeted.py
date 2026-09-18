"""Run unchanged strict surface checker at all 17 poses plus identity control."""
from pathlib import Path
import json,sys,runpy
ROOT=Path(__file__).resolve().parents[2]
ties=json.loads((ROOT/'validation/cuff_seam_tie_candidates.json').read_text())
single=json.loads((ROOT/'validation/cuff_seam_combined_candidates.json').read_text())
ids=single['candidate_weights']['combined']['Object004']
control={'scene_sha256':ties['scene_sha256'],'candidate_weights':{'control':{'Object004':{str(m['cloth_vertex']):m['old_weights'] for m in ties['matches'] if str(m['cloth_vertex']) in ids}}}}
(ROOT/'validation/cuff_gameplay_identity_candidates.json').write_text(json.dumps(control,indent=2))
cases=json.loads((ROOT/'validation/cuff_seam_individual_search.json').read_text())['cases']
for candidate,output in [('cuff_seam_combined_candidates.json:combined','cuff_gameplay_single_17.json'),('cuff_gameplay_identity_candidates.json:control','cuff_gameplay_identity_17.json')]:
    sys.argv=['validate_torso_coupled_targeted.py','--','--candidate-weights',candidate,'--output',output]
    for clip,frame in cases:sys.argv+=['--case',f'{clip}:{frame}']
    runpy.run_path(str(ROOT/'work/scripts/validate_torso_coupled_targeted.py'),run_name='__main__')
