"""Fixed-size, elevated-camera comparisons. Offline approximation, not game capture."""
from pathlib import Path
import sys, runpy, json
ROOT=Path(__file__).resolve().parents[2]
cases=json.loads((ROOT/'validation/cuff_seam_individual_search.json').read_text())['cases']
for variant, candidate in [('parent',None),('single','cuff_seam_combined_candidates.json:combined'),('ties','cuff_seam_tie_candidates.json:ties')]:
    for view,direction in [('front','3,-7,8'),('reverse','-3,7,8')]:
        sys.argv=['render_rig_refinement.py','--','--scene','clash_braum_torso.blend','--label',f'gameplay_{variant}_{view}',
                  '--resolution','360','--scale','5','--direction='+direction]
        if candidate:sys.argv+=['--candidate-weights',candidate]
        for clip,frame in cases:sys.argv+=['--case',f'{clip}:{frame}:body']
        runpy.run_path(str(ROOT/'work/scripts/render_rig_refinement.py'),run_name='__main__')
